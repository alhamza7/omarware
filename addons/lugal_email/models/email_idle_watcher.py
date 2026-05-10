# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_idle_watcher.py
"""
IMAP poll-based email watcher — simple, reliable inbox notification.

Design (v3 — polling only, no IMAP IDLE)
-----------------------------------------
One polling thread per unique (imap_host, imap_port, username) credential
group.  Every _POLL_INTERVAL_SECS the thread calls action_sync() for every
account in the group.

When new messages are found, action_sync() automatically fires WebSocket
push notifications to the frontend via lugal_email_ws.py — the user sees
new email arrive without hitting sync or refreshing the screen.

Why polling instead of IMAP IDLE
---------------------------------
The mail server enforces a global 20-connection limit per source IP.
With 27 accounts all holding persistent IDLE connections we exceed that
limit, causing [LIMIT] errors and dropped notifications.  Polling opens
a connection, checks for mail, and closes it — so we never hold more than
a handful of connections simultaneously.  Maximum email arrival delay is
≤ _POLL_INTERVAL_SECS (15 s), which is acceptable for a business CRM.

Single-process ownership
------------------------
Odoo runs with workers=N OS processes. Without coordination every cron
worker would start its own duplicate polling threads.

We use a PostgreSQL row-level lock on ir.config_parameter (FOR UPDATE
NOWAIT) to ensure only ONE worker claims ownership.  The owning PID is
stored in the parameter.  When the owner dies the next cron run claims
the role.  _register_hook() clears stale PIDs at module load time.

Thread lifecycle
----------------
  start_all()          — called by the supervisor cron every minute.
  stop_credential(key) — gracefully stop one credential group's thread.
  stop_all()           — called during Odoo shutdown.
  status()             — returns monitoring info.
"""

import logging
import os
import threading
import time

from odoo import api, models

_logger = logging.getLogger(__name__)

# ── Cross-process ownership ───────────────────────────────────────────────────
_I_AM_OWNER: bool = False
_OWNER_PARAM = 'lugal.idle.supervisor.pid'

# ── Thread registry ───────────────────────────────────────────────────────────
# Key: (imap_host, imap_port, username)
_poll_threads:  dict[tuple, threading.Thread] = {}
_stop_events:   dict[tuple, threading.Event]  = {}
_poll_lock = threading.Lock()

# Maps cred_key → current set of account IDs in the thread.
# Updated atomically (under _poll_lock) when start_all() detects new accounts
# for a credential group that already has a live thread — no restart needed.
_thread_acc_ids: dict[tuple, set] = {}

# ── Timing constants ──────────────────────────────────────────────────────────
_POLL_INTERVAL_SECS     = 15   # maximum email arrival delay for any account
_WATCHDOG_INTERVAL_SECS = 30   # how often to detect newly-added accounts
_STAGGER_SECS           = 1.5  # stagger between thread starts on restart

# ── Watchdog ──────────────────────────────────────────────────────────────────
_watchdog_thread: threading.Thread | None = None
_watchdog_db:     str = ''


def _watchdog_loop(db_name: str):
    """
    Long-running background thread (owner process only).
    Calls start_all() every _WATCHDOG_INTERVAL_SECS so newly created
    email accounts start being polled within 30 s instead of up to 60 s
    (the cron interval).
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
            pass  # non-critical; cron is the fallback
    _logger.info('Poll watcher watchdog exited (pid=%d)', os.getpid())


def _pid_alive(pid: int) -> bool:
    """True if a process with this PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _sync_account(acc_id: int, db_name: str):
    """
    Open a short-lived DB cursor and run action_sync() for one account.
    Auth failures and network errors are logged but never crash the thread.
    """
    try:
        from odoo.modules.registry import Registry as _Registry
        import odoo as _odoo
        with _Registry(db_name).cursor() as cr:
            env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
            acc = env['lugal.email.account'].browse(acc_id)
            if acc.exists() and acc.is_active and not acc.is_deleted and (acc.password or '').strip():
                acc.action_sync()
                cr.commit()
    except Exception:
        _logger.exception('Poll sync failed for account %s', acc_id)


def _run_poll_watcher(
    cred_key:     tuple,   # (imap_host, imap_port, username)
    db_name:      str,
    imap_host:    str,
    username:     str,
    acc_ids:      list,
    stop_event:   threading.Event,
):
    """
    Simple polling loop for one credential group.

    Every _POLL_INTERVAL_SECS seconds:
      1. Sync every account in the group (action_sync checks for new IMAP
         messages and fires WebSocket notifications when new mail arrives).
      2. Sleep until the next interval.

    The thread exits only when stop_event is set (graceful shutdown) or
    _I_AM_OWNER becomes False (ownership transferred to another process).
    Individual sync errors are logged but do not stop the thread.
    """
    _logger.info(
        '[PollWatcher] Thread started for %s@%s (accounts=%s)',
        username, imap_host, acc_ids,
    )

    while not stop_event.is_set():
        if not _I_AM_OWNER:
            _logger.info(
                '[PollWatcher] %s@%s: no longer owner — thread exiting',
                username, imap_host,
            )
            break

        current_acc_ids = list(_thread_acc_ids.get(cred_key, set(acc_ids)))
        for acc_id in current_acc_ids:
            if stop_event.is_set():
                break
            _sync_account(acc_id, db_name)

        # Wait for the next poll cycle. stop_event.wait() wakes immediately
        # on shutdown so we never block a graceful restart for 15 seconds.
        stop_event.wait(_POLL_INTERVAL_SECS)

    with _poll_lock:
        _poll_threads.pop(cred_key, None)
        _stop_events.pop(cred_key, None)
        _thread_acc_ids.pop(cred_key, None)

    _logger.info(
        '[PollWatcher] Thread exited for %s@%s',
        username, imap_host,
    )


class LugalEmailIdleWatcher(models.Model):
    """
    Supervisor model — manages background polling threads that keep every
    user's inbox in sync without any user interaction.

    One thread per unique (imap_host, imap_port, username) credential group.
    """
    _name        = 'lugal.email.idle.watcher'
    _description = 'IMAP Poll Watcher Supervisor'

    def _register_hook(self):
        """
        Called once per process when Odoo loads the registry.

        Clears the stale owner PID from ir.config_parameter if the recorded
        process is no longer alive.  This prevents new workers from being
        blocked by a dead owner after an Odoo restart.
        """
        super()._register_hook()
        try:
            cr = self.env.cr
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                (_OWNER_PARAM,),
            )
            row = cr.fetchone()
            if row and row[0]:
                try:
                    stored_pid = int(row[0])
                    if not _pid_alive(stored_pid):
                        cr.execute(
                            "UPDATE ir_config_parameter SET value = '' WHERE key = %s",
                            (_OWNER_PARAM,),
                        )
                        _logger.info(
                            'Poll supervisor: cleared stale owner pid=%d (process is dead)',
                            stored_pid,
                        )
                except (ValueError, TypeError):
                    cr.execute(
                        "UPDATE ir_config_parameter SET value = '' WHERE key = %s",
                        (_OWNER_PARAM,),
                    )
        except Exception:
            pass

    @api.model
    def start_all(self):
        """
        Start polling threads for every active credential group that does
        not already have a running thread.

        Cross-process ownership: only ONE Odoo worker process runs threads.
        Uses FOR UPDATE NOWAIT on ir.config_parameter for atomic ownership
        claim — eliminates the race where two cron workers both try to claim.

        Called by the supervisor cron every minute and by the watchdog every
        _WATCHDOG_INTERVAL_SECS seconds.
        """
        global _I_AM_OWNER

        my_pid = os.getpid()

        # ── Ownership check / claim ──────────────────────────────────────────
        if _I_AM_OWNER:
            # Verify we still hold the stored PID (guards against zombie workers).
            cr = self.env.cr
            try:
                cr.execute(
                    "SELECT value FROM ir_config_parameter WHERE key = %s",
                    (_OWNER_PARAM,),
                )
                row = cr.fetchone()
                stored_pid_str = (row[0] if row else '') or ''
                stored_pid = int(stored_pid_str) if stored_pid_str.strip().isdigit() else 0
                if stored_pid and stored_pid != my_pid and _pid_alive(stored_pid):
                    _I_AM_OWNER = False
                    _logger.info(
                        'Poll supervisor: pid=%d lost ownership to pid=%d — stopping threads',
                        my_pid, stored_pid,
                    )
                    stop_all()
                    return 0
            except Exception:
                pass

        if not _I_AM_OWNER:
            cr = self.env.cr
            claimed = False
            try:
                with cr.savepoint():
                    cr.execute(
                        "SELECT value FROM ir_config_parameter "
                        "WHERE key = %s FOR UPDATE NOWAIT",
                        (_OWNER_PARAM,),
                    )
                    row = cr.fetchone()
                    stored = (row[0] if row else '') or ''
                    if stored:
                        try:
                            owner_pid = int(stored)
                            if _pid_alive(owner_pid) and owner_pid != my_pid:
                                _logger.debug(
                                    'Poll supervisor: pid=%d owns threads — '
                                    'this worker (pid=%d) skips',
                                    owner_pid, my_pid,
                                )
                                return 0
                        except (ValueError, TypeError):
                            pass
                    # Claim ownership while still holding the row lock.
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
                _logger.debug(
                    'Poll supervisor: pid=%d lost ownership race — skipping', my_pid,
                )
                return 0
            if not claimed:
                return 0

            _I_AM_OWNER = True
            _logger.info('Poll supervisor: pid=%d claimed ownership', my_pid)

            # Start the watchdog so newly added accounts get picked up fast.
            global _watchdog_thread, _watchdog_db
            _watchdog_db = self.env.cr.dbname
            if _watchdog_thread is None or not _watchdog_thread.is_alive():
                _watchdog_thread = threading.Thread(
                    target=_watchdog_loop,
                    args=(_watchdog_db,),
                    daemon=True,
                    name='imap-poll-watchdog',
                )
                _watchdog_thread.start()
                _logger.info(
                    'Poll watchdog started (pid=%d, interval=%ds)',
                    my_pid, _WATCHDOG_INTERVAL_SECS,
                )

        # ── Build credential groups ──────────────────────────────────────────
        db_name  = self.env.cr.dbname
        accounts = self.env['lugal.email.account'].sudo().search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])

        groups: dict[tuple, tuple] = {}
        for acc in accounts:
            pw = (acc.password or '').strip()
            if not pw:
                continue
            host  = (acc.imap_host or '').strip()
            port  = int(acc.imap_port or 993)
            uname = (acc.username or acc.email_address or '').strip()
            if not host or not uname:
                continue
            key = (host, port, uname)
            if key not in groups:
                groups[key] = ({'imap_host': host, 'imap_port': port,
                                'username': uname, 'password': pw}, [])
            groups[key][1].append(acc.id)

        stagger = 0.0
        started = 0

        # Stop threads for credential groups that no longer have active accounts.
        with _poll_lock:
            orphaned = [k for k in list(_poll_threads.keys()) if k not in groups]
        for key in orphaned:
            ev = _stop_events.get(key)
            if ev:
                ev.set()
                _logger.info(
                    'Poll supervisor: stopping orphaned thread for %s:%s/%s',
                    key[0], key[1], key[2],
                )

        for key, (cfg, acc_ids) in groups.items():
            with _poll_lock:
                existing = _poll_threads.get(key)
                if existing and existing.is_alive():
                    # Thread is healthy — just update the account list if needed.
                    current_ids = _thread_acc_ids.get(key, set())
                    new_ids = set(acc_ids) - current_ids
                    if new_ids:
                        _thread_acc_ids[key] = current_ids | new_ids
                        _logger.info(
                            'Poll supervisor: added %d new account(s) to live thread '
                            'for %s:%s/%s (total=%s)',
                            len(new_ids), key[0], key[1], key[2],
                            sorted(_thread_acc_ids[key]),
                        )
                    continue  # already running

                stop_ev = threading.Event()
                _thread_acc_ids[key] = set(acc_ids)

                def _make_target(k, c, ids, ev, delay):
                    def _target():
                        if delay:
                            time.sleep(delay)
                        _run_poll_watcher(
                            k, db_name,
                            c['imap_host'],
                            c['username'],
                            ids, ev,
                        )
                    return _target

                t = threading.Thread(
                    target=_make_target(key, cfg, list(acc_ids), stop_ev, stagger),
                    daemon=True,
                    name=f'imap-poll-{cfg["username"][:20]}',
                )
                _poll_threads[key] = t
                _stop_events[key]  = stop_ev
                t.start()
                stagger += _STAGGER_SECS
                started += 1

        if started:
            _logger.info(
                'Poll supervisor: started %d new thread(s) '
                '(%d credential group(s) total, poll interval=%ds)',
                started, len(groups), _POLL_INTERVAL_SECS,
            )
        return started

    @api.model
    def clear_backoff_for_account(self, account_id: int):
        """
        Legacy API — kept for compatibility.  With polling there is no backoff
        state to clear, so this simply calls start_all() to ensure the thread
        is running for the given account's credential group.
        """
        self.start_all()

    @api.model
    def stop_credential(self, imap_host, imap_port, username):
        """Stop the polling thread for a specific credential group."""
        key = (imap_host, int(imap_port), username)
        with _poll_lock:
            ev = _stop_events.get(key)
        if ev:
            ev.set()
            _logger.info('Poll supervisor: stop requested for %s:%s/%s', *key)

    @api.model
    def stop_all(self):
        """Signal all polling threads to stop (called on Odoo shutdown)."""
        global _I_AM_OWNER
        _I_AM_OWNER = False  # causes watchdog loop to exit
        with _poll_lock:
            events = list(_stop_events.values())
        for ev in events:
            ev.set()
        _logger.info('Poll supervisor: stop_all — %d thread(s) signalled', len(events))

    @api.model
    def status(self):
        """Return monitoring info for all polling threads."""
        result = []
        with _poll_lock:
            for key, t in _poll_threads.items():
                result.append({
                    'host':     key[0],
                    'port':     key[1],
                    'username': key[2],
                    'alive':    t.is_alive(),
                    'accounts': sorted(_thread_acc_ids.get(key, set())),
                    'mode':     'poll',
                    'interval': _POLL_INTERVAL_SECS,
                })
        return result
