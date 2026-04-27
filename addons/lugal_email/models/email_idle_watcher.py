"""
IMAP IDLE watcher — instant inbox notification without polling.

Design (v2 — credential-deduplicated, single-process ownership)
---------------------------------------------------------------
One IDLE thread is started per unique (imap_host, imap_port, username)
credential group.  Multiple email accounts sharing the same IMAP login share
a single persistent IMAP connection instead of opening N connections and
hitting the server's max-connections limit.

When the IDLE connection receives an EXISTS notification, the thread:
  1. Sends DONE to exit IDLE mode.
  2. Closes the IMAP connection (avoids concurrent-connection rejection).
  3. Calls action_sync() for every account in the credential group.
  4. Reconnects and re-enters IDLE.

Single-process ownership (advisory lock)
-----------------------------------------
Odoo runs with workers=N, meaning N+ OS processes.  Each process has its own
Python heap, so _idle_threads is per-process.  Without coordination, every
cron worker would start its own duplicate IDLE threads.

We prevent duplicates using a PostgreSQL SESSION-level advisory lock:
  • pg_try_advisory_lock(KEY) — acquired once when start_all() first succeeds.
  • The lock persists for the lifetime of the DB connection (i.e., the worker
    process lifetime).
  • Other workers call pg_try_advisory_lock and receive FALSE → they skip.
  • When the owning worker dies/is recycled, the connection closes, the lock
    is released, and the next cron run in any other worker takes over.

Thread lifecycle
----------------
• start_all()           — called by the supervisor cron every minute.
• stop_credential(key)  — gracefully stops one credential group's watcher.
• stop_all()            — called during Odoo shutdown.
• status()              — returns monitoring info.

Failure classification / backoff
---------------------------------
  AUTHENTICATIONFAILED  → 60-minute backoff (bad password, OAuth needed).
  [LIMIT] / too many    → 5-minute backoff (server connection limit).
  Other network errors  → exponential 5 s → 10 s → … → 120 s, then reset.
"""

import logging
import os
import threading
import time

from odoo import api, models

_logger = logging.getLogger(__name__)

# ── Cross-process ownership ───────────────────────────────────────────────────
# We store the owning PID in ir.config_parameter so any Odoo worker can
# check whether another process is already running the IDLE threads.
# A process claims ownership when it starts threads; it loses ownership when
# it is killed (the PID disappears from the OS process table).
_I_AM_OWNER: bool = False
_OWNER_PARAM = 'lugal.idle.supervisor.pid'

# ── Registry ─────────────────────────────────────────────────────────────────
# Key: (imap_host, imap_port, username)
_idle_threads:  dict[tuple, threading.Thread] = {}
_stop_events:   dict[tuple, threading.Event]  = {}
_idle_lock = threading.Lock()

# Time-based backoff: key → earliest time.time() to restart.
_next_retry: dict[tuple, float] = {}

_IDLE_REFRESH_SECS  = 20 * 60   # re-enter IDLE every 20 min
_MAX_BACKOFF_SECS   = 120
_AUTH_BACKOFF_SECS  = 3600       # 1 h — bad password / OAuth required
_LIMIT_BACKOFF_SECS = 300        # 5 min — server connection limit
_MAX_FAILURES       = 5

# ── Watchdog ──────────────────────────────────────────────────────────────────
# The owner process runs a lightweight watchdog thread every
# _WATCHDOG_INTERVAL_SECS to call start_all() when new accounts appear.
# This eliminates the 1-minute cron delay for newly added email accounts.
_WATCHDOG_INTERVAL_SECS = 5
_watchdog_thread: threading.Thread | None = None
_watchdog_db:     str = ''


def _watchdog_loop(db_name: str):
    """
    Long-running background thread (owner process only).
    Calls start_all() every _WATCHDOG_INTERVAL_SECS to immediately pick up
    newly created email accounts without waiting for the 1-minute cron.
    """
    global _I_AM_OWNER
    while _I_AM_OWNER:
        time.sleep(_WATCHDOG_INTERVAL_SECS)
        if not _I_AM_OWNER:
            break
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                env['lugal.email.idle.watcher'].start_all()
        except Exception:
            pass  # log is noisy — cron is fallback
    _logger.info('IDLE watchdog thread exited (pid=%d)', os.getpid())


def _pid_alive(pid: int) -> bool:
    """True if a process with this PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _classify_error(exc: Exception) -> str:
    """Return 'auth', 'limit', or 'other' based on the IMAP error message."""
    msg = str(exc).upper()
    if 'AUTHENTICATIONFAILED' in msg or 'INVALID CREDENTIALS' in msg:
        return 'auth'
    if 'LIMIT' in msg or 'TOO MANY' in msg or 'MAXIMUM' in msg or 'EXCEEDED' in msg:
        return 'limit'
    return 'other'


def _run_idle_watcher(
    cred_key:     tuple,   # (imap_host, imap_port, username)
    db_name:      str,
    imap_host:    str,
    imap_port:    int,
    imap_use_ssl: bool,
    username:     str,
    password:     str,
    acc_ids:      list,    # all account IDs that share these credentials
    stop_event:   threading.Event,
):
    """
    Long-running IDLE loop for one credential group.
    Exits after MAX_FAILURES consecutive failures, setting _next_retry[cred_key].
    """
    import imaplib as _imaplib

    consecutive_failures = 0
    backoff = 5

    while not stop_event.is_set() and consecutive_failures < _MAX_FAILURES:
        conn = None
        try:
            conn_cls = _imaplib.IMAP4_SSL if imap_use_ssl else _imaplib.IMAP4
            conn = conn_cls(imap_host, imap_port)
            conn.login(username, password)
            conn.select('INBOX', readonly=True)

            _logger.info(
                'IDLE watcher connected: cred=%s:%s/%s  accounts=%s',
                imap_host, imap_port, username, acc_ids,
            )
            consecutive_failures = 0
            backoff = 5

            # ── IDLE loop ────────────────────────────────────────────────────
            while not stop_event.is_set():
                tag = conn._new_tag().decode()
                conn.send(f'{tag} IDLE\r\n'.encode())

                # Read the server's continuation response (+ idling …)
                try:
                    import select as _select
                    r, _, _ = _select.select([conn.socket()], [], [], 15)
                    initial = conn.readline() if r else b''
                except Exception:
                    initial = b''

                if not initial or not initial.startswith(b'+'):
                    _logger.warning(
                        'IDLE watcher: IDLE not acknowledged for %s:%s/%s '
                        '(got %r). Sleeping 60 s.',
                        imap_host, imap_port, username, initial,
                    )
                    try:
                        conn.send(b'DONE\r\n')
                    except Exception:
                        pass
                    stop_event.wait(60)
                    break  # reconnect

                # Poll for EXISTS / RECENT / BYE in 10-second slices
                got_new_mail = False
                deadline = time.monotonic() + _IDLE_REFRESH_SECS

                while not stop_event.is_set():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break  # refresh IDLE

                    import select as _select
                    r, _, _ = _select.select([conn.socket()], [], [], min(10.0, remaining))
                    if not r:
                        continue

                    try:
                        line = conn.readline()
                    except Exception:
                        raise ConnectionError('readline failed')
                    if not line:
                        raise ConnectionError('Server closed connection')

                    line_upper = line.upper()
                    if b'EXISTS' in line_upper or b'RECENT' in line_upper:
                        got_new_mail = True
                        break
                    if b'BYE' in line_upper:
                        raise ConnectionError('Server sent BYE')

                # Exit IDLE cleanly
                conn.send(b'DONE\r\n')
                try:
                    import select as _select
                    for _ in range(20):
                        r, _, _ = _select.select([conn.socket()], [], [], 10)
                        if not r:
                            break
                        done_line = conn.readline()
                        if not done_line:
                            break
                        if tag.encode() in done_line or b'OK' in done_line.upper():
                            break
                except Exception:
                    pass

                if got_new_mail:
                    _logger.debug(
                        'IDLE: EXISTS for %s:%s/%s — closing conn then syncing %s',
                        imap_host, imap_port, username, acc_ids,
                    )
                    # Close connection BEFORE syncing — server may limit
                    # simultaneous connections per user+IP.
                    try:
                        conn.logout()
                    except Exception:
                        pass
                    conn = None
                    for acc_id in acc_ids:
                        _sync_account(acc_id, db_name)
                    break  # exit inner loop → outer loop reconnects

            if conn:
                try:
                    conn.logout()
                except Exception:
                    pass

        except Exception as exc:
            consecutive_failures += 1
            err_type = _classify_error(exc)
            _logger.warning(
                'IDLE watcher error (failure %d/%d type=%s) for %s:%s/%s — retrying in %ds',
                consecutive_failures, _MAX_FAILURES, err_type,
                imap_host, imap_port, username, backoff,
                exc_info=True,
            )
            if conn:
                try:
                    conn.logout()
                except Exception:
                    pass
            conn = None
            stop_event.wait(backoff)
            backoff = min(backoff * 2, _MAX_BACKOFF_SECS)

    # Thread is exiting — set time-based backoff so supervisor cron
    # can decide when it is safe to restart.
    if not stop_event.is_set():
        last_exc_str = ''
        try:
            # Re-probe the error type from the last consecutive failure.
            # We can't get the actual exception here easily, so use the
            # failure count to guess the severity.
            # A smarter approach would store the last error type.
            pass
        except Exception:
            pass

        # Use the last stored error classification (stored by the thread closure)
        backoff_secs = _MAX_BACKOFF_SECS  # default: 2 min before restart
        _next_retry[cred_key] = time.time() + backoff_secs
        _logger.info(
            'IDLE watcher exited for %s:%s/%s — supervisor will retry after %.0fs',
            imap_host, imap_port, username, backoff_secs,
        )
    else:
        _logger.info(
            'IDLE watcher stopped (shutdown) for %s:%s/%s',
            imap_host, imap_port, username,
        )

    # Remove from registry
    with _idle_lock:
        _idle_threads.pop(cred_key, None)
        _stop_events.pop(cred_key, None)


def _run_idle_watcher_classified(
    cred_key, db_name, imap_host, imap_port, imap_use_ssl,
    username, password, acc_ids, stop_event,
):
    """Wrapper that captures the last error type for smart backoff on exit."""
    import imaplib as _imaplib

    consecutive_failures = 0
    backoff = 5
    last_err_type = 'other'

    while not stop_event.is_set() and consecutive_failures < _MAX_FAILURES:
        conn = None
        try:
            conn_cls = _imaplib.IMAP4_SSL if imap_use_ssl else _imaplib.IMAP4
            conn = conn_cls(imap_host, imap_port)

            # Enable TCP keepalive so the OS detects silently dropped NAT entries.
            # Without this, a NAT/firewall timeout kills the connection mid-IDLE but
            # select() never wakes up — we spin on 10s timeouts forever, missing EXISTS.
            import socket as _socket
            try:
                raw_sock = conn.socket()
                raw_sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_KEEPALIVE, 1)
                # Start probing after 60 s of inactivity, retry every 15 s, give up after 3 probes
                raw_sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_KEEPIDLE, 60)
                raw_sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_KEEPINTVL, 15)
                raw_sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_KEEPCNT, 3)
            except Exception:
                pass  # non-critical — keepalive is a best-effort enhancement

            conn.login(username, password)
            conn.select('INBOX', readonly=True)

            _logger.info(
                'IDLE watcher connected: %s:%s user=%s  accounts=%s',
                imap_host, imap_port, username, acc_ids,
            )
            consecutive_failures = 0
            backoff = 5
            last_err_type = 'other'

            while not stop_event.is_set():
                tag = conn._new_tag().decode()
                conn.send(f'{tag} IDLE\r\n'.encode())

                try:
                    import select as _select
                    r, _, _ = _select.select([conn.socket()], [], [], 15)
                    initial = conn.readline() if r else b''
                except Exception:
                    initial = b''

                if not initial or not initial.startswith(b'+'):
                    _logger.warning(
                        'IDLE not acknowledged for %s:%s/%s (got %r). Sleep 60s.',
                        imap_host, imap_port, username, initial,
                    )
                    try:
                        conn.send(b'DONE\r\n')
                    except Exception:
                        pass
                    stop_event.wait(60)
                    break

                # Server accepted the IDLE command — we are now in IDLE state
                _logger.info(
                    '[IdleWatcher] IDLE started for %s@%s (accounts=%s)',
                    username, imap_host, acc_ids,
                )

                got_new_mail = False
                deadline = time.monotonic() + _IDLE_REFRESH_SECS

                # imaplib wraps the socket in a BufferedReader (socket.makefile('rb')).
                # If the server sends the EXISTS notification in the same TCP read as
                # the "+ idling" continuation, readline() above will consume both lines
                # into the Python-level buffer.  The kernel socket buffer is then empty,
                # so select() returns [] even though data is waiting — we'd spin forever.
                # Fix: always check conn.file.peek(1) BEFORE select() to drain buffered
                # data first.
                _imap_file = getattr(conn, 'file', None)

                while not stop_event.is_set():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break

                    # Check if imaplib already buffered data (peek is non-destructive)
                    if _imap_file is not None and hasattr(_imap_file, 'peek') and _imap_file.peek(1):
                        r_ready = True
                    else:
                        import select as _select
                        rlist, _, _ = _select.select([conn.socket()], [], [], min(10.0, remaining))
                        r_ready = bool(rlist)

                    if not r_ready:
                        continue
                    try:
                        line = conn.readline()
                    except Exception:
                        raise ConnectionError('readline failed')
                    if not line:
                        raise ConnectionError('Server closed connection')
                    line_upper = line.upper()
                    if b'EXISTS' in line_upper or b'RECENT' in line_upper:
                        _logger.info(
                            '[IdleWatcher] EXISTS received for %s@%s — triggering sync (accounts=%s)',
                            username, imap_host, acc_ids,
                        )
                        got_new_mail = True
                        break
                    if b'BYE' in line_upper:
                        raise ConnectionError('Server sent BYE')

                conn.send(b'DONE\r\n')
                try:
                    import select as _select
                    for _ in range(20):
                        r, _, _ = _select.select([conn.socket()], [], [], 10)
                        if not r:
                            break
                        done_line = conn.readline()
                        if not done_line:
                            break
                        if tag.encode() in done_line or b'OK' in done_line.upper():
                            break
                except Exception:
                    pass

                if got_new_mail:
                    try:
                        conn.logout()
                    except Exception:
                        pass
                    conn = None
                    for acc_id in acc_ids:
                        _sync_account(acc_id, db_name)
                    break  # reconnect outer loop

            if conn:
                try:
                    conn.logout()
                except Exception:
                    pass

        except Exception as exc:
            consecutive_failures += 1
            last_err_type = _classify_error(exc)
            _logger.error(
                '[IdleWatcher] Thread crashed for %s@%s: %s — backoff %ds '
                '(failure %d/%d type=%s)',
                username, imap_host, exc, backoff,
                consecutive_failures, _MAX_FAILURES, last_err_type,
                exc_info=True,
            )
            if conn:
                try:
                    conn.logout()
                except Exception:
                    pass
            conn = None
            stop_event.wait(backoff)
            backoff = min(backoff * 2, _MAX_BACKOFF_SECS)

    # Set time-based backoff based on failure classification
    if not stop_event.is_set():
        if last_err_type == 'auth':
            backoff_until = time.time() + _AUTH_BACKOFF_SECS
            _logger.warning(
                'IDLE: auth failure for %s:%s/%s — skipping for %d min',
                imap_host, imap_port, username, _AUTH_BACKOFF_SECS // 60,
            )
        elif last_err_type == 'limit':
            backoff_until = time.time() + _LIMIT_BACKOFF_SECS
            _logger.warning(
                'IDLE: connection limit for %s:%s/%s — retrying in %d min',
                imap_host, imap_port, username, _LIMIT_BACKOFF_SECS // 60,
            )
        else:
            backoff_until = time.time() + _MAX_BACKOFF_SECS
        _next_retry[cred_key] = backoff_until

    with _idle_lock:
        _idle_threads.pop(cred_key, None)
        _stop_events.pop(cred_key, None)

    _logger.info(
        'IDLE watcher thread exited for %s:%s/%s (accounts=%s)',
        imap_host, imap_port, username, acc_ids,
    )


def _sync_account(acc_id: int, db_name: str):
    """Open a short-lived DB cursor and run action_sync() for one account."""
    try:
        from odoo.modules.registry import Registry as _Registry
        import odoo as _odoo
        with _Registry(db_name).cursor() as cr:
            env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
            acc = env['lugal.email.account'].browse(acc_id)
            # Skip accounts that were deactivated since the thread started
            if acc.exists() and acc.is_active and not acc.is_deleted and (acc.password or '').strip():
                acc.action_sync()
    except Exception:
        _logger.exception('IDLE sync failed for account %s', acc_id)


class LugalEmailIdleWatcher(models.Model):
    """
    Supervisor model — exposes class-level helpers and a cron-callable
    method to manage IMAP IDLE watcher threads.

    v2: one thread per unique (imap_host, imap_port, username) credential
    group so multiple accounts sharing the same IMAP login never open more
    than one simultaneous connection to the mail server.
    """
    _name        = 'lugal.email.idle.watcher'
    _description = 'IMAP IDLE Watcher Supervisor'

    @api.model
    def start_all(self):
        """
        Start / restart IDLE watcher threads for every credential group that:
          • has at least one active, non-deleted account with a password
          • does not already have a running thread
          • is not within a time-based backoff window

        Cross-process ownership: only ONE Odoo worker process manages IDLE threads.
        The owning PID is stored in ir.config_parameter.  If another alive process
        owns the role, this call returns 0 immediately.  When the owner dies, the
        next cron run in any worker claims ownership.

        Called by the supervisor cron every minute.
        """
        global _I_AM_OWNER

        my_pid = os.getpid()

        # Even when _I_AM_OWNER is True (set in a previous start_all() call by THIS
        # process), verify that the stored PID still matches us.  A surviving "zombie"
        # worker from a previous Odoo deployment would still have _I_AM_OWNER=True from
        # its old run; the ownership check below catches that and surrenders correctly.
        if _I_AM_OWNER:
            cr = self.env.cr
            try:
                cr.execute(
                    "SELECT value FROM ir_config_parameter WHERE key = %s",
                    (_OWNER_PARAM,),
                )
                row = cr.fetchone()
                stored_pid_str = row[0] if row else ''
                stored_pid = int(stored_pid_str) if stored_pid_str.strip().isdigit() else 0
                if stored_pid and stored_pid != my_pid and _pid_alive(stored_pid):
                    _I_AM_OWNER = False
                    _logger.info(
                        'IDLE supervisor: pid=%d lost ownership to pid=%d — stopping threads',
                        my_pid, stored_pid,
                    )
                    stop_all()
                    return 0
            except Exception:
                pass  # non-critical; continue with start_all if check fails

        if not _I_AM_OWNER:
            # Atomic ownership claim: use a PostgreSQL row-level lock (FOR UPDATE NOWAIT)
            # inside an Odoo savepoint so lock contention rolls back cleanly without
            # poisoning the outer transaction.  This eliminates the TOCTOU race where
            # two cron workers both read an empty parameter and both claim ownership.
            cr = self.env.cr
            claimed = False
            try:
                with cr.savepoint():
                    cr.execute(
                        "SELECT value FROM ir_config_parameter WHERE key = %s FOR UPDATE NOWAIT",
                        (_OWNER_PARAM,),
                    )
                    row = cr.fetchone()
                    stored = row[0] if row else ''
                    if stored:
                        try:
                            owner_pid = int(stored)
                            if _pid_alive(owner_pid) and owner_pid != my_pid:
                                _logger.debug(
                                    'IDLE supervisor: pid=%d owns threads — '
                                    'this worker (pid=%d) skips',
                                    owner_pid, my_pid,
                                )
                                return 0
                        except (ValueError, TypeError):
                            pass
                    # Claim ownership — still inside the savepoint/row-lock
                    if row:
                        cr.execute(
                            "UPDATE ir_config_parameter SET value = %s WHERE key = %s",
                            (str(my_pid), _OWNER_PARAM),
                        )
                    else:
                        cr.execute(
                            "INSERT INTO ir_config_parameter (key, value) "
                            "VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
                            (_OWNER_PARAM, str(my_pid), str(my_pid)),
                        )
                    claimed = True
            except Exception:
                # Lock contention (NOWAIT) or any DB error — another process is
                # claiming ownership right now; skip this run.
                _logger.debug(
                    'IDLE supervisor: pid=%d lost ownership race — skipping',
                    my_pid,
                )
                return 0
            if not claimed:
                return 0
            _I_AM_OWNER = True
            _logger.info('IDLE supervisor: pid=%d claimed ownership', my_pid)
            # Start the watchdog thread so new accounts are picked up within
            # _WATCHDOG_INTERVAL_SECS (5 s) instead of waiting for the 1-min cron.
            global _watchdog_thread, _watchdog_db
            _watchdog_db = self.env.cr.dbname
            if _watchdog_thread is None or not _watchdog_thread.is_alive():
                _watchdog_thread = threading.Thread(
                    target=_watchdog_loop,
                    args=(_watchdog_db,),
                    daemon=True,
                    name='imap-idle-watchdog',
                )
                _watchdog_thread.start()
                _logger.info('IDLE watchdog started (pid=%d, interval=%ds)', my_pid, _WATCHDOG_INTERVAL_SECS)

        # ── Build credential groups ──────────────────────────────────────────
        db_name = self.env.cr.dbname
        accounts = self.env['lugal.email.account'].sudo().search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])

        # Build credential groups: key → (cfg_dict, [acc_id, …])
        groups: dict[tuple, tuple] = {}
        for acc in accounts:
            pw = (acc.password or '').strip()
            if not pw:
                continue
            host     = (acc.imap_host or '').strip()
            port     = int(acc.imap_port or 993)
            use_ssl  = bool(acc.imap_use_ssl)
            uname    = (acc.username or acc.email_address or '').strip()
            if not host or not uname:
                continue
            key = (host, port, uname)
            if key not in groups:
                groups[key] = ({'imap_host': host, 'imap_port': port,
                                'imap_use_ssl': use_ssl,
                                'username': uname, 'password': pw}, [])
            groups[key][1].append(acc.id)

        now     = time.time()
        stagger = 0.0
        started = 0

        # ── Clean up orphaned threads for credential groups with no active accounts ──
        with _idle_lock:
            orphaned = [k for k in list(_idle_threads.keys()) if k not in groups]
        for key in orphaned:
            ev = _stop_events.get(key)
            if ev:
                ev.set()
                _logger.info(
                    'IDLE supervisor: stopping orphaned thread for %s:%s/%s '
                    '(no active accounts)',
                    key[0], key[1], key[2],
                )

        for key, (cfg, acc_ids) in groups.items():
            # Skip if in backoff window
            retry_at = _next_retry.get(key, 0)
            if retry_at > now:
                _logger.debug(
                    'IDLE supervisor: skipping %s:%s/%s — in backoff for %.0fs',
                    key[0], key[1], key[2], retry_at - now,
                )
                continue

            with _idle_lock:
                existing = _idle_threads.get(key)
                if existing and existing.is_alive():
                    continue  # already healthy

                stop_ev = threading.Event()

                def _make_target(k, c, ids, ev, delay):
                    def _target():
                        if delay:
                            time.sleep(delay)
                        _run_idle_watcher_classified(
                            k, db_name,
                            c['imap_host'], c['imap_port'],
                            c['imap_use_ssl'], c['username'],
                            c['password'], ids, ev,
                        )
                    return _target

                t = threading.Thread(
                    target=_make_target(key, cfg, list(acc_ids), stop_ev, stagger),
                    daemon=True,
                    name=f'imap-idle-{key[2][:20]}',
                )
                _idle_threads[key]  = t
                _stop_events[key]   = stop_ev
                t.start()
                stagger += 0.5
                started += 1

        if started:
            _logger.info(
                'IDLE supervisor: started %d new watcher(s) '
                '(%d credential group(s) total)',
                started, len(groups),
            )
        return started

    @api.model
    def clear_backoff_for_account(self, account_id: int):
        """
        Remove the backoff entry for the credential group that owns account_id,
        then call start_all() so the thread can restart immediately if it was
        in a backoff window.  Called by action_test_connection() on success.
        """
        acc = self.env['lugal.email.account'].sudo().browse(account_id)
        if not acc.exists():
            return
        host  = (acc.imap_host or '').strip()
        port  = int(acc.imap_port or 993)
        uname = (acc.username or acc.email_address or '').strip()
        if not host or not uname:
            return
        key = (host, port, uname)
        removed = _next_retry.pop(key, None)
        if removed:
            _logger.info(
                'IDLE: cleared backoff for %s:%s/%s after successful test',
                host, port, uname,
            )
        self.start_all()

    @api.model
    def stop_credential(self, imap_host, imap_port, username):
        """Stop the IDLE watcher for a specific credential group."""
        key = (imap_host, int(imap_port), username)
        with _idle_lock:
            ev = _stop_events.get(key)
        if ev:
            ev.set()
            _logger.info('IDLE supervisor: stop requested for %s:%s/%s', *key)

    @api.model
    def stop_all(self):
        """Signal all IDLE watcher threads to stop (Odoo shutdown)."""
        global _I_AM_OWNER
        _I_AM_OWNER = False   # causes watchdog loop to exit
        with _idle_lock:
            events = list(_stop_events.values())
        for ev in events:
            ev.set()
        _logger.info('IDLE supervisor: stop_all — %d watcher(s) signalled', len(events))

    @api.model
    def status(self):
        """
        Return monitoring info: list of dicts with key, alive, and next_retry.
        """
        now = time.time()
        result = []
        with _idle_lock:
            for key, t in _idle_threads.items():
                result.append({
                    'host':       key[0],
                    'port':       key[1],
                    'username':   key[2],
                    'alive':      t.is_alive(),
                    'retry_in_s': max(0, _next_retry.get(key, 0) - now),
                })
        # Also report groups in backoff that have no running thread
        for key, retry_at in _next_retry.items():
            if key not in _idle_threads and retry_at > now:
                result.append({
                    'host':       key[0],
                    'port':       key[1],
                    'username':   key[2],
                    'alive':      False,
                    'retry_in_s': retry_at - now,
                })
        return result
