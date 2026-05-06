# -*- coding: utf-8 -*-

import json
import logging
import re
import threading
import email as email_lib
from email import policy
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime, parseaddr

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

# Per-account mutex to prevent concurrent _upsert_inbox_message calls for the
# same account from creating duplicate rows when IDLE and polling threads fire
# at the same instant for the same new message.
_upsert_locks: dict = {}
_upsert_locks_guard = threading.Lock()


def _get_upsert_lock(account_id: int) -> threading.Lock:
    with _upsert_locks_guard:
        if account_id not in _upsert_locks:
            _upsert_locks[account_id] = threading.Lock()
        return _upsert_locks[account_id]

# How many IMAP messages to pull on first / incremental catch-up (per sync call).
SYNC_MAX_MESSAGES = 150
# Auto-sync throttle when inbox already has cached messages (seconds).
# Kept short so the background cron + on-request sync together give near-real-time updates.
SYNC_THROTTLE_SECONDS = 15
# When inbox is empty, sync more aggressively.
SYNC_THROTTLE_EMPTY_SECONDS = 10


class LugalEmailAccount(models.Model):
    """
    IMAP/SMTP email account linked to an Odoo user.
    Each CRM agent can configure one or more personal email accounts.
    """
    _name = 'lugal.email.account'
    _description = 'Lugal Email Account'
    _order = 'is_default desc, name asc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name            = fields.Char(string='Account Label', required=True)
    email_address   = fields.Char(string='Email Address', required=True, index=True)
    display_name_field = fields.Char(string='Display Name (Sender)')
    user_id         = fields.Many2one('res.users', string='Owner', required=True,
                                      default=lambda self: self.env.user, ondelete='cascade', index=True)

    # ── IMAP ──────────────────────────────────────────────────────────────────
    imap_host       = fields.Char(string='IMAP Host', default='imap.gmail.com')
    imap_port       = fields.Integer(string='IMAP Port', default=993)
    imap_use_ssl    = fields.Boolean(string='IMAP SSL', default=True)
    username        = fields.Char(string='Username / Login')
    password        = fields.Char(string='App Password')

    # ── SMTP ──────────────────────────────────────────────────────────────────
    smtp_host       = fields.Char(string='SMTP Host', default='smtp.gmail.com')
    smtp_port       = fields.Integer(string='SMTP Port', default=587)
    smtp_use_tls    = fields.Boolean(string='SMTP TLS', default=True)

    # ── Status ────────────────────────────────────────────────────────────────
    is_default      = fields.Boolean(string='Default Account', default=False, index=True)
    is_active       = fields.Boolean(string='Active', default=True)
    sync_status     = fields.Selection([
        ('ok',       'OK'),
        ('error',    'Error'),
        ('pending',  'Pending'),
        ('never',    'Never Synced'),
    ], string='Sync Status', default='never')
    last_sync_date  = fields.Datetime(string='Last Sync')
    sync_error_msg  = fields.Text(string='Last Sync Error')

    # ── Stats (denormalised for performance) ──────────────────────────────────
    unread_count    = fields.Integer(string='Unread Count', default=0)
    # Highest IMAP UID we have imported for INBOX (incremental sync).
    imap_inbox_max_uid = fields.Integer(string='IMAP Inbox Max UID', default=0)

    active          = fields.Boolean(default=True)
    is_deleted      = fields.Boolean(default=False, index=True)

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if (rec.password or '').strip():
                # Start the IDLE watcher for this account as soon as the
                # transaction commits, without waiting for the 1-minute cron.
                rec_id = rec.id
                rec._schedule_idle_start()
        return records

    @api.constrains('is_default', 'user_id')
    def _check_single_default(self):
        """Enforce at most one default account per user."""
        for rec in self:
            if rec.is_default:
                others = self.search([
                    ('user_id', '=', rec.user_id.id),
                    ('is_default', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    others.write({'is_default': False})

    def action_set_default(self):
        """Mark this account as the user's default, unset others."""
        self.ensure_one()
        self.search([('user_id', '=', self.user_id.id)]).write({'is_default': False})
        self.write({'is_default': True})

    def action_test_connection(self):
        """Test IMAP connection and update sync_status accordingly.

        On success, the IDLE supervisor is triggered immediately so the new
        account starts receiving live notifications without waiting for the
        next supervisor cron run (which fires every minute).
        """
        self.ensure_one()
        try:
            import imaplib
            conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
            conn = conn_cls(self.imap_host, self.imap_port)
            conn.login(self.username or self.email_address, self.password or '')
            conn.logout()
            self.write({'sync_status': 'ok', 'sync_error_msg': False})
            # Trigger the IDLE supervisor in the background so the new account
            # gets its watcher thread immediately (within the owning process).
            self._schedule_idle_start()
            return {'status': 'ok', 'message': 'Connection successful'}
        except Exception as exc:
            self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            return {'status': 'error', 'message': str(exc)}

    def _schedule_idle_start(self):
        """
        Spawn a one-shot background thread that clears any backoff for this
        account's credential group and calls start_all() so the IDLE supervisor
        picks it up immediately.

        If the current OS process is not the IDLE supervisor owner, start_all()
        returns 0 (skips) and the account will be picked up by the owning
        process on its next cron run (≤ 1 minute).
        """
        import threading
        db_name = self.env.cr.dbname
        acc_id  = self.id

        def _trigger():
            import time
            time.sleep(0.5)   # give the write() commit time to propagate
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    env['lugal.email.idle.watcher'].clear_backoff_for_account(acc_id)
            except Exception:
                pass   # cron will catch it within 1 minute

        threading.Thread(target=_trigger, daemon=True, name='idle-on-test').start()

    def _imap_connect(self):
        """Return a logged-in IMAP connection."""
        import imaplib
        conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
        conn = conn_cls(self.imap_host, self.imap_port)
        conn.login(self.username or self.email_address, self.password or '')
        return conn

    # ── Bidirectional IMAP sync helpers ──────────────────────────────────────

    def _get_server_folder_name(self, purpose):
        """Return the IMAP server folder name for a logical purpose.

        purpose: 'trash' | 'archive' | 'sent' | 'drafts' | 'spam'

        Detects per-account folder names via IMAP LIST on first call, then caches
        in ir.config_parameter so subsequent calls are instant (no extra connection).
        """
        self.ensure_one()
        import re as _re

        cache_key = f'lugal.email.folder.{self.id}.{purpose}'
        ICP = self.env['ir.config_parameter'].sudo()
        cached = ICP.get_param(cache_key, '')
        if cached:
            return cached

        # Provider-aware defaults (avoids an extra IMAP LIST round-trip for known hosts)
        host = (self.imap_host or '').lower()
        if 'gmail.com' in host:
            defaults = {
                'trash': '[Gmail]/Trash', 'archive': '[Gmail]/All Mail',
                'sent': '[Gmail]/Sent Mail', 'drafts': '[Gmail]/Drafts',
                'spam': '[Gmail]/Spam',
            }
        else:
            defaults = {
                'trash': 'Trash', 'archive': 'Archive',
                'sent': 'Sent', 'drafts': 'Drafts', 'spam': 'Spam',
            }

        # Attempt auto-discovery via IMAP LIST
        # LIST response format: (flags) "delimiter" folder_name
        # e.g. (\HasNoChildren \Trash) "." INBOX.Trash
        #      (\Trash) "/" "[Gmail]/Trash"
        keywords = {
            'trash':   ['trash', 'deleted'],
            'archive': ['archive'],
            'sent':    ['sent'],
            'drafts':  ['draft'],
            'spam':    ['spam', 'junk'],
        }
        try:
            conn = self._imap_connect()
            typ, listing = conn.list()
            conn.logout()
            if typ == 'OK' and listing:
                for entry in listing:
                    if not entry:
                        continue
                    raw = entry.decode('utf-8', errors='replace') if isinstance(entry, bytes) else str(entry)
                    # Strip the flags section "(...)" and delimiter, get the folder name
                    # Handles both: (\Flags) "." INBOX.Trash
                    #           and (\Flags) "/" "[Gmail]/Trash"
                    m = _re.search(r'\(.*?\)\s+"[^"]+"\s+"?(.+?)"?\s*$', raw)
                    if not m:
                        m = _re.search(r'\(.*?\)\s+\S+\s+"?(.+?)"?\s*$', raw)
                    folder_raw = m.group(1).strip().strip('"') if m else ''
                    if not folder_raw:
                        continue
                    for kw in keywords.get(purpose, []):
                        if kw in folder_raw.lower():
                            ICP.set_param(cache_key, folder_raw)
                            return folder_raw
        except Exception:
            pass  # fall through to defaults

        result = defaults.get(purpose, purpose.capitalize())
        ICP.set_param(cache_key, result)
        return result

    def _imap_store_async(self, imap_uid, imap_folder, add_flags=None, remove_flags=None):
        """Push flag changes to the IMAP server in a background thread (fire-and-forget).

        Called after local DB updates so API responses are never blocked by IMAP latency.
        Failures are logged as warnings — the local DB state is always authoritative.
        """
        self.ensure_one()
        if not imap_uid or not (add_flags or remove_flags):
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_store():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    conn = acc._imap_connect()
                    conn.select(imap_folder, readonly=False)
                    uid_str = str(imap_uid)
                    if add_flags:
                        conn.uid('store', uid_str, '+FLAGS', '(' + ' '.join(add_flags) + ')')
                    if remove_flags:
                        conn.uid('store', uid_str, '-FLAGS', '(' + ' '.join(remove_flags) + ')')
                    conn.logout()
                    _logger.info(
                        'IMAP flags pushed for acc=%s uid=%s folder=%s +%s -%s',
                        acc_id, imap_uid, imap_folder, add_flags, remove_flags,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP flag push failed for acc=%s uid=%s folder=%s: %s',
                    acc_id, imap_uid, imap_folder, exc,
                )

        threading.Thread(target=_do_store, daemon=True,
                         name=f'imap-store-{imap_uid}').start()

    def _imap_append_sent_async(self, raw_message):
        """
        Upload a copy of a just-sent email to the IMAP Sent folder so it appears
        in webmail, Outlook, and any other email client connected to the same account.

        raw_message: the RFC-2822 email as a bytes or str object.
        Runs in a background daemon thread — the HTTP response is never blocked.
        """
        self.ensure_one()

        import threading
        import imaplib

        acc_id   = self.id
        db_name  = self.env.cr.dbname
        imap_host    = self.imap_host
        imap_port    = int(self.imap_port or 993)
        imap_use_ssl = bool(self.imap_use_ssl)
        username     = self.username or self.email_address
        password     = self.password or ''

        def _do_append():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo

                # Discover the server-side Sent folder name (cached after first run).
                sent_folder = 'Sent'
                try:
                    with _Registry(db_name).cursor() as _cr:
                        env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                        acc = env['lugal.email.account'].browse(acc_id)
                        if acc.exists():
                            sent_folder = acc._get_server_folder_name('sent')
                except Exception:
                    pass  # fall back to 'Sent'

                conn_cls = imaplib.IMAP4_SSL if imap_use_ssl else imaplib.IMAP4
                conn = conn_cls(imap_host, imap_port)
                conn.login(username, password)

                # APPEND expects bytes; encode if we received a string.
                msg_bytes = (
                    raw_message.encode('utf-8')
                    if isinstance(raw_message, str)
                    else raw_message
                )

                # Append to Sent with \Seen so the copy appears already-read.
                typ, data = conn.append(sent_folder, '(\\Seen)', None, msg_bytes)
                conn.logout()

                if typ == 'OK':
                    _logger.info(
                        'IMAP APPEND to Sent succeeded: acc=%s folder=%s',
                        acc_id, sent_folder,
                    )
                else:
                    _logger.warning(
                        'IMAP APPEND to Sent returned %s for acc=%s folder=%s: %s',
                        typ, acc_id, sent_folder, data,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP APPEND to Sent failed for acc=%s: %s',
                    acc_id, exc,
                )

        threading.Thread(
            target=_do_append, daemon=True, name=f'imap-append-sent-{acc_id}'
        ).start()

    def _imap_move_async(self, imap_uid, from_folder, to_folder_purpose):
        """Move a message between IMAP folders in a background thread.

        Uses the MOVE extension (RFC 6851, supported by Dovecot and cPanel/WHM).
        Falls back to COPY + STORE(\\Deleted) + EXPUNGE if MOVE is unavailable.

        to_folder_purpose: logical name ('trash'|'archive'|'inbox'|'sent'|'drafts')
        """
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_move():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)

                    if to_folder_purpose == 'inbox':
                        dest_folder = 'INBOX'
                    else:
                        dest_folder = acc._get_server_folder_name(to_folder_purpose)

                    conn = acc._imap_connect()
                    conn.select(from_folder, readonly=False)
                    uid_str = str(imap_uid)

                    # Prefer MOVE (atomic, server-side)
                    typ, data = conn.uid('move', uid_str, dest_folder)
                    if typ != 'OK':
                        # Fall back: COPY + mark deleted + EXPUNGE
                        conn.uid('copy', uid_str, dest_folder)
                        conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                        conn.expunge()

                    conn.logout()
                    _logger.info(
                        'IMAP move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP move failed acc=%s uid=%s: %s',
                    acc_id, imap_uid, exc,
                )

        threading.Thread(target=_do_move, daemon=True,
                         name=f'imap-move-{imap_uid}').start()

    def _imap_move_to_raw_path_async(self, imap_uid, from_folder, dest_folder_path):
        """Move a message to an arbitrary IMAP folder path (e.g. 'INBOX.AllFromUmar').

        Unlike _imap_move_async, this accepts the raw IMAP destination path directly
        instead of a logical purpose name.  Used by inbox rules that target custom folders.
        """
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_move():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    conn = acc._imap_connect()
                    conn.select(from_folder, readonly=False)
                    uid_str = str(imap_uid)

                    typ, data = conn.uid('move', uid_str, dest_folder_path)
                    if typ != 'OK':
                        conn.uid('copy', uid_str, dest_folder_path)
                        conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                        conn.expunge()

                    conn.logout()
                    _logger.info(
                        'IMAP raw-move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder_path,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP raw-move failed acc=%s uid=%s: %s',
                    acc_id, imap_uid, exc,
                )

        threading.Thread(target=_do_move, daemon=True,
                         name=f'imap-rawmove-{imap_uid}').start()

    def _imap_ensure_folder(self, path):
        """Create *path* on the IMAP server if it does not already exist.

        Returns the final folder path on success, raises on hard failure.
        Safe to call when the folder already exists (no-op in that case).
        """
        self.ensure_one()
        conn = self._imap_connect()
        try:
            # LIST to check existence
            typ, listing = conn.list('""', path)
            exists = typ == 'OK' and any(listing)
            if not exists:
                conn.create(path)
                conn.subscribe(path)
                _logger.info('IMAP folder created: acc=%s path=%s', self.id, path)
            else:
                _logger.info('IMAP folder already exists: acc=%s path=%s', self.id, path)
        finally:
            try:
                conn.logout()
            except Exception:
                pass
        return path

    def _imap_expunge_async(self, imap_uid, imap_folder):
        """Mark a message \\Deleted on the server and EXPUNGE it (permanent delete)."""
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_expunge():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    conn = acc._imap_connect()
                    conn.select(imap_folder, readonly=False)
                    conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                    conn.expunge()
                    conn.logout()
                    _logger.info('IMAP expunge acc=%s uid=%s folder=%s', acc_id, imap_uid, imap_folder)
            except Exception as exc:
                _logger.warning('IMAP expunge failed acc=%s uid=%s: %s', acc_id, imap_uid, exc)

        threading.Thread(target=_do_expunge, daemon=True,
                         name=f'imap-expunge-{imap_uid}').start()

    @staticmethod
    def _decode_mime_header(value):
        if not value:
            return ''
        out = []
        for frag, enc in decode_header(value):
            if isinstance(frag, bytes):
                out.append(frag.decode(enc or 'utf-8', errors='replace'))
            else:
                out.append(frag)
        return ''.join(out)

    @staticmethod
    def _extract_best_body(msg):
        """Return (body_text, body_html) from an email.message.Message."""
        body_text = ''
        body_html = ''
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == 'text/plain' and not body_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='replace')
                elif ctype == 'text/html' and not body_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_html = payload.decode(charset, errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                decoded = payload.decode(charset, errors='replace')
                if msg.get_content_type() == 'text/html':
                    body_html = decoded
                else:
                    body_text = decoded
        return body_text, body_html

    def _parse_flags_from_fetch_response(self, meta_bytes):
        """Detect \\Seen in IMAP fetch metadata bytes."""
        if not meta_bytes:
            return False
        try:
            s = meta_bytes.decode('utf-8', errors='replace') if isinstance(meta_bytes, bytes) else str(meta_bytes)
        except Exception:
            s = str(meta_bytes)
        return '\\Seen' in s

    def _upsert_inbox_message(self, uid_int, raw_bytes, flags_meta, headers_only=False,
                              folder_key='inbox', run_rules=True):
        """Create or update one mailbox row from raw RFC822 bytes.

        folder_key: logical name ('inbox', 'sent', …) or full IMAP path for custom
                    folders (e.g. 'INBOX.syednaqvi.Important').
        run_rules:  when False, skip apply_inbox_rules (used when importing from
                    a custom folder to avoid re-firing move rules).
        """
        self.ensure_one()
        import email
        msg = email.message_from_bytes(raw_bytes, policy=policy.default)
        message_id = (msg.get('Message-ID') or '').strip() or False
        subject = self._decode_mime_header(msg.get('Subject', ''))
        from_name, from_addr = parseaddr(msg.get('From', ''))
        if from_name:
            from_name = self._decode_mime_header(from_name)
        date_hdr = msg.get('Date')
        dt = None
        if date_hdr:
            try:
                dt = parsedate_to_datetime(date_hdr)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
            except Exception:
                dt = None
        if not dt:
            dt = fields.Datetime.now()
        to_raw = msg.get_all('To', [])
        pairs = getaddresses(to_raw) if to_raw else []
        to_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in pairs if e]
        cc_raw = msg.get_all('Cc', [])
        cc_pairs = getaddresses(cc_raw) if cc_raw else []
        cc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in cc_pairs if e]
        bcc_raw = msg.get_all('Bcc', [])
        bcc_pairs = getaddresses(bcc_raw) if bcc_raw else []
        bcc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in bcc_pairs if e]
        # Reply-To: used by reply/reply_all to address the reply correctly
        reply_to_raw = msg.get('Reply-To', '')
        reply_to_addr = ''
        if reply_to_raw:
            rt_pairs = getaddresses([reply_to_raw])
            reply_to_addr = rt_pairs[0][1] if rt_pairs else ''

        # References: chain of ancestor Message-IDs used for thread grouping
        references_raw = (msg.get('References') or msg.get('references') or '').strip()
        references_ids = references_raw.split() if references_raw else []
        # Also consider In-Reply-To in case References is absent (some clients)
        in_reply_to_hdr = (msg.get('In-Reply-To') or '').strip()

        # thread_id = the oldest ancestor Message-ID (first in References chain).
        # If References is absent, use In-Reply-To. If neither present, this
        # message is the root — use its own Message-ID.
        if references_ids:
            thread_id = references_ids[0].strip()
        elif in_reply_to_hdr:
            thread_id = in_reply_to_hdr
        else:
            thread_id = message_id or ''

        body_text, body_html = self._extract_best_body(msg)
        is_read = self._parse_flags_from_fetch_response(flags_meta)

        # is_mentioned: True when the account owner's email is in the To: header
        # (direct recipient, not just CC). Matches Outlook "Mentioned Mail".
        own_email = (self.email_address or '').strip().lower()
        to_emails_lower = [pair[1].lower() for pair in getaddresses(msg.get_all('To', [])) if pair[1]]
        is_mentioned = bool(own_email and own_email in to_emails_lower)

        # is_important: parse standard priority/importance headers sent by the
        # sender. Check in priority order:
        #   1. Importance: high / normal / low  (RFC 2156 / Outlook)
        #   2. X-Priority: 1 or 2 = high (Outlook, many clients)
        #   3. X-MSMail-Priority: High / Normal / Low (Outlook legacy)
        is_important = False
        _importance_hdr = (msg.get('Importance') or '').strip().lower()
        if _importance_hdr == 'high':
            is_important = True
        elif _importance_hdr not in ('', 'normal', 'low'):
            # Some clients send numeric values in this header too
            pass

        if not is_important:
            _xpriority = (msg.get('X-Priority') or '').strip()
            try:
                _xprio_int = int(_xpriority.split()[0]) if _xpriority else 3
                if _xprio_int in (1, 2):
                    is_important = True
            except (ValueError, IndexError):
                pass

        if not is_important:
            _msmail = (msg.get('X-MSMail-Priority') or '').strip().lower()
            if _msmail == 'high':
                is_important = True

        # message_size: approximate RFC-822 size in bytes
        message_size = len(raw_bytes) if raw_bytes else 0

        Message = self.env['lugal.email.message'].sudo()
        # Search by imap_uid first; also check message_id as a secondary key so
        # we never store the same RFC-2822 message twice even if the UID changed.
        domain = [('account_id', '=', self.id), ('folder', '=', folder_key), ('imap_uid', '=', uid_int)]
        existing = Message.search(domain, limit=1)
        if not existing and message_id:
            existing = Message.search(
                [('account_id', '=', self.id), ('message_id', '=', message_id)],
                limit=1,
            )
        vals = {
            'account_id':    self.id,
            'folder':        folder_key,
            'imap_uid':      uid_int,
            'subject':       subject or '(no subject)',
            'from_name':     from_name or '',
            'from_address':  from_addr or '',
            'to_addresses':  json.dumps(to_list),
            'cc_addresses':  json.dumps(cc_list),
            'bcc_addresses': json.dumps(bcc_list),
            'reply_to':      reply_to_addr or False,
            'message_id':    message_id,
            'in_reply_to':   in_reply_to_hdr or False,
            'references':    references_raw or False,
            'thread_id':     thread_id or False,
            'date':          dt,
            'is_read':       is_read,
            'is_deleted':    False,
            'active':        True,
            'is_mentioned':  is_mentioned,
            'is_important':  is_important,
            'message_size':  message_size,
        }
        if headers_only:
            # Do not overwrite body if we already have it from a previous full fetch.
            if not existing:
                vals['body_text']     = ''
                vals['body_html']     = False
                vals['body_fetched']  = False
        else:
            vals['body_text']    = body_text
            vals['body_html']    = body_html or False
            vals['body_fetched'] = True
        if existing:
            # Never downgrade a fully-fetched body to headers-only.
            if headers_only and existing.body_fetched:
                vals.pop('body_text', None)
                vals.pop('body_html', None)
                vals.pop('body_fetched', None)
            existing.write(vals)
            stored_msg = existing
        else:
            # Acquire a per-account mutex before the INSERT to prevent two threads
            # (IDLE push + polling fallback) racing on the same new message and
            # each inserting a separate row for the same imap_uid / message_id.
            _acc_lock = _get_upsert_lock(self.id)
            with _acc_lock:
                # Re-check inside the lock — the other thread may have just created it.
                stored_msg = Message.search(domain, limit=1)
                if not stored_msg and message_id:
                    stored_msg = Message.search(
                        [('account_id', '=', self.id), ('message_id', '=', message_id)],
                        limit=1,
                    )

                if stored_msg:
                    # Another thread won the race — just update.
                    if not (headers_only and stored_msg.body_fetched):
                        stored_msg.write(vals)
                else:
                    # We are the first — create, using a SAVEPOINT so a concurrent
                    # INSERT at the DB level (unlikely but possible) rolls back
                    # only the inner block and leaves the cursor usable.
                    try:
                        with self.env.cr.savepoint():
                            stored_msg = Message.create(vals)
                    except Exception as dup_exc:
                        # Unique-constraint violation from a concurrent INSERT —
                        # fall back to search and update.
                        _logger.warning(
                            '_upsert_inbox_message: duplicate INSERT caught for '
                            'account=%s uid=%s message_id=%s — %s',
                            self.id, uid_int, message_id, dup_exc,
                        )
                        stored_msg = Message.search(domain, limit=1)
                        if not stored_msg and message_id:
                            stored_msg = Message.search(
                                [('account_id', '=', self.id), ('message_id', '=', message_id)],
                                limit=1,
                            )
                        if stored_msg and not (headers_only and stored_msg.body_fetched):
                            stored_msg.write(vals)

                    # Run inbox rules only on genuinely new messages (inbox ingest).
                    if stored_msg and run_rules:
                        try:
                            self.env['lugal.email.rule'].sudo().apply_inbox_rules(stored_msg, vals)
                        except Exception as _re:
                            _logger.warning('Inbox rule execution failed for msg %s: %s', stored_msg.id, _re)

        # Extract and persist file attachments when we have the full body.
        if not headers_only:
            self._store_imap_attachments(stored_msg, msg)

        return stored_msg

    def action_sync_if_stale(self, force=False):
        """
        Run IMAP inbox import unless recently synced (reduces load on mailbox polling).
        If inbox has no rows, sync runs unless the last attempt was very recent.

        Accounts with sync_status='never' (never successfully synced) always bypass
        the throttle — we want the very first sync to happen as soon as possible.
        """
        self.ensure_one()
        if not (self.password or '').strip():
            return {'skipped': True, 'reason': 'no_password'}

        # Always sync if this account has never been synced successfully.
        if not self.last_sync_date or self.sync_status == 'never':
            _logger.info(
                'action_sync_if_stale: account %s has sync_status=%s — forcing immediate sync',
                self.id, self.sync_status,
            )
            return self.action_sync()

        now = fields.Datetime.now()
        Msg = self.env['lugal.email.message'].sudo()
        inbox_count = Msg.search_count([
            ('account_id', '=', self.id),
            ('folder', '=', 'inbox'),
            ('is_deleted', '=', False),
        ])
        if not force:
            delta = (now - self.last_sync_date).total_seconds()
            limit = SYNC_THROTTLE_EMPTY_SECONDS if inbox_count == 0 else SYNC_THROTTLE_SECONDS
            if delta < limit:
                return {'skipped': True, 'reason': 'throttle', 'sync_status': self.sync_status}

        return self.action_sync()

    def _sync_sent_folder(self, conn):
        """
        Incrementally import messages from the IMAP Sent folder into Odoo
        so they appear in the "sent" mailbox view.

        Uses an ir.config_parameter as the UID cursor so no model change is needed.
        Skips messages that already exist in the local DB (e.g. sent via our system).
        Called from action_sync with the already-open IMAP connection.
        """
        import email as _email
        import json as _json

        Msg = self.env['lugal.email.message'].sudo()
        ICP = self.env['ir.config_parameter'].sudo()
        cursor_key = f'lugal.email.sent_max_uid.{self.id}'

        try:
            sent_folder = self._get_server_folder_name('sent')
        except Exception:
            sent_folder = 'Sent'

        try:
            typ, data = conn.select(sent_folder, readonly=True)
            if typ != 'OK' or not data:
                _logger.warning(
                    'Sent folder sync: SELECT %r failed for acc=%s (typ=%s) — '
                    'clearing cached name and retrying discovery',
                    sent_folder, self.id, typ,
                )
                # Clear cached folder name and try auto-discovery again
                cache_key = f'lugal.email.folder.{self.id}.sent'
                self.env['ir.config_parameter'].sudo().set_param(cache_key, '')
                try:
                    sent_folder = self._get_server_folder_name('sent')
                    typ, data = conn.select(sent_folder, readonly=True)
                    if typ != 'OK' or not data:
                        _logger.warning(
                            'Sent folder fallback also failed for acc=%s: folder=%r',
                            self.id, sent_folder,
                        )
                        return
                except Exception:
                    return
        except Exception as exc:
            _logger.warning('Sent folder select failed for acc=%s: %s', self.id, exc)
            return

        try:
            max_uid_cursor = int(ICP.get_param(cursor_key, '0') or '0')
        except (ValueError, TypeError):
            max_uid_cursor = 0

        # Fetch only new UIDs (above our cursor)
        search_criteria = f'UID {max_uid_cursor + 1}:*' if max_uid_cursor else 'ALL'
        try:
            typ, uid_data = conn.uid('search', None, search_criteria)
        except Exception as exc:
            _logger.debug('Sent UID search failed for acc=%s: %s', self.id, exc)
            return

        if typ != 'OK' or not uid_data or not uid_data[0]:
            return

        uid_list = [int(u) for u in uid_data[0].split() if u.isdigit() and int(u) > max_uid_cursor]
        if not uid_list:
            return

        # Fetch in batches of 25 (Sent folder items are usually larger)
        BATCH = 25
        max_seen = max_uid_cursor
        uid_re = re.compile(br'UID\s+(\d+)')

        for i in range(0, len(uid_list), BATCH):
            batch = uid_list[i:i + BATCH]
            uid_set = ','.join(str(u) for u in batch)
            try:
                typ, items = conn.uid('fetch', uid_set, '(FLAGS RFC822.HEADER)')
            except Exception:
                continue
            if typ != 'OK' or not items:
                continue

            for item in items:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                meta, header_bytes = item[0], item[1]
                if not isinstance(meta, bytes):
                    continue
                m = uid_re.search(meta)
                if not m:
                    continue
                uid_int = int(m.group(1))
                if uid_int <= max_uid_cursor:
                    continue

                try:
                    msg = _email.message_from_bytes(header_bytes, policy=policy.default)
                    message_id = (msg.get('Message-ID') or '').strip() or False
                    subject    = self._decode_mime_header(msg.get('Subject', ''))
                    from_name, from_addr = parseaddr(msg.get('From', ''))
                    if from_name:
                        from_name = self._decode_mime_header(from_name)

                    date_hdr = msg.get('Date')
                    dt = None
                    if date_hdr:
                        try:
                            from email.utils import parsedate_to_datetime as _p2d
                            dt = _p2d(date_hdr)
                            if dt.tzinfo is not None:
                                dt = dt.replace(tzinfo=None)
                        except Exception:
                            pass
                    if not dt:
                        dt = fields.Datetime.now()

                    to_raw  = msg.get_all('To', [])
                    to_list = [{'name': self._decode_mime_header(n or ''), 'email': e}
                               for n, e in getaddresses(to_raw) if e]
                    cc_raw  = msg.get_all('Cc', [])
                    cc_list = [{'name': self._decode_mime_header(n or ''), 'email': e}
                               for n, e in getaddresses(cc_raw) if e]

                    # Skip if already in local DB (e.g. sent via our own SMTP send)
                    domain = [
                        ('account_id', '=', self.id),
                        ('folder', '=', 'sent'),
                    ]
                    if message_id:
                        domain.append(('message_id', '=', message_id))
                    else:
                        domain += [('subject', '=', subject or '(no subject)'), ('date', '=', dt)]

                    if not Msg.search_count(domain):
                        Msg.create({
                            'account_id':   self.id,
                            'folder':       'sent',
                            'imap_uid':     uid_int,
                            'subject':      subject or '(no subject)',
                            'from_name':    from_name or '',
                            'from_address': from_addr or '',
                            'to_addresses': _json.dumps(to_list),
                            'cc_addresses': _json.dumps(cc_list),
                            'message_id':   message_id or False,
                            'date':         dt,
                            'is_read':      True,  # sent messages are always read
                            'smtp_delivered': True,
                            'body_fetched': False,
                        })

                    if uid_int > max_seen:
                        max_seen = uid_int

                except Exception as exc:
                    _logger.warning('Sent folder upsert failed uid=%s acc=%s: %s', uid_int, self.id, exc)

        if max_seen > max_uid_cursor:
            ICP.set_param(cursor_key, str(max_seen))
            _logger.info(
                'Sent folder sync: acc=%s new_max_uid=%s (was %s)',
                self.id, max_seen, max_uid_cursor,
            )

    def action_sync(self):
        """Import INBOX and Sent folder messages over IMAP."""
        self.ensure_one()
        Msg = self.env['lugal.email.message'].sudo()
        if not (self.password or '').strip():
            self.write({'sync_status': 'error', 'sync_error_msg': 'Missing app password on email account'})
            return {'sync_status': 'error', 'message': 'Missing app password on email account'}

        # Full re-bootstrap if cache was cleared but UID cursor is stale.
        if not Msg.search_count([
            ('account_id', '=', self.id), ('folder', '=', 'inbox'), ('is_deleted', '=', False),
        ]):
            self.imap_inbox_max_uid = 0

        try:
            import imaplib
            conn = self._imap_connect()
            typ, data = conn.select('INBOX', readonly=True)
            if typ != 'OK' or not data:
                raise imaplib.IMAP4.error('INBOX select failed')
            num_msgs = int(data[0])
            max_uid_cursor = self.imap_inbox_max_uid or 0
            uid_re = re.compile(br'UID\s+(\d+)')

            def _parse_batch_fetch(data_list):
                """
                Parse an imaplib FETCH response list into [(uid_int, raw_bytes, meta_bytes)].
                Works for both conn.fetch(...) and conn.uid('fetch', ...) responses.
                imaplib interleaves (meta, body) tuples with b')' separators; we skip
                anything that is not a (meta, body) tuple with non-empty payload.
                """
                parsed = []
                for item in data_list:
                    if not isinstance(item, tuple) or len(item) < 2:
                        continue
                    meta, payload = item[0], item[1]
                    if not isinstance(meta, bytes):
                        continue
                    if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                        continue
                    m = uid_re.search(meta)
                    if m:
                        parsed.append((int(m.group(1)), bytes(payload), meta))
                return parsed

            imported = 0
            max_seen = max_uid_cursor

            def _upsert_batch(items, min_uid=0, headers_only=False):
                """Upsert a parsed batch, skipping UIDs we already have."""
                nonlocal imported, max_seen
                for uid_val, raw, flags_meta in items:
                    if uid_val <= min_uid:
                        continue
                    try:
                        self._upsert_inbox_message(uid_val, raw, flags_meta, headers_only=headers_only)
                        imported += 1
                        if uid_val > max_seen:
                            max_seen = uid_val
                    except Exception:
                        _logger.warning(
                            'IMAP upsert failed uid=%s account=%s', uid_val, self.id, exc_info=True,
                        )

            # IMAP fetch specs:
            # • Header-only (fast, ~1 KB/msg) — used for initial bulk import
            # • Full body  (slow, ~50 KB/msg) — used for incremental (typically 1-10 new msgs)
            HEADERS_FETCH = '(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO CC REPLY-TO DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
            BODY_FETCH    = '(UID FLAGS BODY.PEEK[])'

            if max_uid_cursor == 0:
                # ── First import: headers only ────────────────────────────────
                # Avoids downloading MBs of body data for hundreds of old emails.
                if num_msgs > 0:
                    start_seq = max(1, num_msgs - SYNC_MAX_MESSAGES + 1)
                    seq_range = f'{start_seq}:{num_msgs}'
                    typ, data_list = conn.fetch(seq_range, HEADERS_FETCH)
                    if typ == 'OK' and data_list:
                        _upsert_batch(_parse_batch_fetch(data_list), min_uid=0, headers_only=True)
            else:
                # ── Incremental: only fetch new UIDs (full body, typically 1-10 msgs) ──
                typ, uid_data = conn.uid('search', None, 'UID', '%d:*' % (max_uid_cursor + 1))
                todo = []
                if typ == 'OK' and uid_data and uid_data[0]:
                    # Filter out Dovecot's quirk: UID N:* returns current max when N > max.
                    todo = [
                        u for u in sorted(int(x) for x in uid_data[0].split())
                        if u > max_uid_cursor
                    ][:SYNC_MAX_MESSAGES]

                if not todo and num_msgs > 0:
                    # Fallback: server may not support UID range — batch tail scan (headers only).
                    start_seq = max(1, num_msgs - SYNC_MAX_MESSAGES + 1)
                    seq_range = f'{start_seq}:{num_msgs}'
                    typ, data_list = conn.fetch(seq_range, HEADERS_FETCH)
                    if typ == 'OK' and data_list:
                        _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=True)
                elif todo:
                    # Full body for new messages — few messages, typically fast.
                    uid_set = ','.join(str(u) for u in todo)
                    typ, data_list = conn.uid('fetch', uid_set, BODY_FETCH)
                    if typ == 'OK' and data_list:
                        _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=False)

            # ── Sent folder sync ─────────────────────────────────────────────
            # Reuse the same connection to also pull sent messages so they
            # appear in our "sent" mailbox and match webmail / Outlook.
            try:
                self._sync_sent_folder(conn)
            except Exception:
                _logger.warning('Sent folder sync failed for acc=%s', self.id, exc_info=True)

            conn.logout()

            unread = Msg.search_count([
                ('account_id', '=', self.id),
                ('folder', '=', 'inbox'),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])

            # Use a savepoint so that a concurrent-update / serialization error
            # from updating the account row does NOT abort the outer transaction.
            # Without this, PostgreSQL would roll back all the message INSERTs
            # created above, making newly-arrived emails disappear.
            now_dt = fields.Datetime.now()
            try:
                with self.env.cr.savepoint():
                    self.write({
                        'sync_status':        'ok',
                        'last_sync_date':     now_dt,
                        'unread_count':       unread,
                        'imap_inbox_max_uid': max_seen,
                        'sync_error_msg':     False,
                    })
            except Exception:
                _logger.warning(
                    'action_sync: account %s status write failed (concurrent update) '
                    '— message inserts are preserved', self.id,
                )

            return {
                'sync_status':    'ok',
                'last_sync_date': now_dt.isoformat(),
                'unread_count':   unread,
                'imported':       imported,
            }
        except Exception as exc:
            # Wrap this write in a savepoint too: if the outer exception left the
            # transaction in a bad state (e.g. IMAP connect error after a prior
            # failed SQL), we still want to record the error without aborting again.
            try:
                with self.env.cr.savepoint():
                    self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            except Exception:
                pass
            _logger.exception('action_sync failed for account %s', self.id)
            return {'sync_status': 'error', 'message': str(exc)}

    def sync_custom_imap_folder(self, imap_folder_path, headers_only=True):
        """Import messages from a single non-standard IMAP folder into Odoo.

        ``action_sync`` only pulls INBOX + Sent.  User-created folders (rule
        destinations like ``INBOX.syednaqvi.Important``) must be imported here
        so ``GET …/sync?folder=…`` returns rows.

        * ``imap_folder_path`` must match the LIST path (same casing as server).
        * Uses the same header-only tail fetch strategy as first-time INBOX import.
        * Does **not** run inbox rules on imported rows (avoids move loops).
        """
        self.ensure_one()
        if not (self.password or '').strip():
            return {'imported': 0, 'error': 'no password', 'resolved_path': ''}
        if not (imap_folder_path or '').strip():
            return {'imported': 0, 'error': 'empty path', 'resolved_path': ''}

        path = self._resolve_imap_mailbox_path(imap_folder_path.strip())
        _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        if path.lower() in _LOGICAL:
            return {'imported': 0, 'error': 'use action_sync for standard folders', 'resolved_path': path}

        imported = 0
        try:
            import imaplib
            conn = self._imap_connect()
            typ, data = conn.select(path, readonly=True)
            if typ != 'OK' or not data:
                try:
                    conn.logout()
                except Exception:
                    pass
                return {'imported': 0, 'error': f'select failed typ={typ!r} path={path!r}', 'resolved_path': path}

            uid_re = re.compile(br'UID\s+(\d+)')

            def _parse_batch_fetch(data_list):
                parsed = []
                for item in data_list:
                    if not isinstance(item, tuple) or len(item) < 2:
                        continue
                    meta, payload = item[0], item[1]
                    if not isinstance(meta, bytes):
                        continue
                    if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                        continue
                    m = uid_re.search(meta)
                    if m:
                        parsed.append((int(m.group(1)), bytes(payload), meta))
                return parsed

            # Prefer UID SEARCH + UID FETCH — sequence-number FETCH is unreliable on
            # some Dovecot/cPanel builds when the mailbox was just created or after
            # concurrent expunges.  This matches how we incrementally fetch INBOX.
            HEADERS_FETCH = (
                '(UID FLAGS BODY.PEEK[HEADER.FIELDS '
                '(FROM TO CC BCC REPLY-TO DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
            )

            typ_s, d_s = conn.uid('search', None, 'ALL')
            uids = []
            if typ_s == 'OK' and d_s and d_s[0]:
                uids = sorted(int(x) for x in d_s[0].split() if x.isdigit())

            if not uids:
                try:
                    conn.logout()
                except Exception:
                    pass
                return {
                    'imported': 0,
                    'error':      None,
                    'resolved_path': path,
                    'note':       'mailbox_empty_or_uid_search_empty',
                }

            tail = uids[-SYNC_MAX_MESSAGES:]
            uid_csv = ','.join(str(u) for u in tail)
            typ_f, data_list = conn.uid('fetch', uid_csv, HEADERS_FETCH)
            if typ_f == 'OK' and data_list:
                for uid_val, raw, flags_meta in _parse_batch_fetch(data_list):
                    try:
                        self._upsert_inbox_message(
                            uid_val, raw, flags_meta,
                            headers_only=headers_only,
                            folder_key=path,
                            run_rules=False,
                        )
                        imported += 1
                    except Exception:
                        _logger.warning(
                            'custom folder upsert failed uid=%s folder=%s acc=%s',
                            uid_val, path, self.id, exc_info=True,
                        )

            try:
                conn.logout()
            except Exception:
                pass
        except Exception as exc:
            _logger.warning('sync_custom_imap_folder acc=%s path=%s: %s', self.id, path, exc)
            return {'imported': imported, 'error': str(exc), 'resolved_path': path}
        return {'imported': imported, 'error': None, 'resolved_path': path}

    def _resolve_imap_mailbox_path(self, requested_path: str) -> str:
        """Return the server's exact mailbox name for a path (case / delimiter)."""
        req = (requested_path or '').strip()
        if not req:
            return req
        _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        if req.lower() in _LOGICAL:
            return req
        try:
            conn = self._imap_connect()
            typ, raw_list = conn.list()
            try:
                conn.logout()
            except Exception:
                pass
            if typ != 'OK' or not raw_list:
                return req
            # Delimiter may be quoted ("." or "/") or NIL on some servers.
            lr = re.compile(
                r'^\((?P<flags>[^)]*)\)\s+'
                r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                r'(?P<name>.+?)\s*$'
            )
            req_lower = req.lower()
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = lr.match(line.strip())
                if not m:
                    continue
                name = m.group('name').strip().strip('"')
                if name.lower() == req_lower:
                    return name
        except Exception:
            return req
        return req

    @api.model
    def action_sync_all_accounts(self):
        """
        Background cron entry-point.
        Syncs INBOX for every active account that has a password configured.
        Called by the ir.cron scheduler; runs each account in its own savepoint
        so one failure does not abort the others.

        De-duplicates by IMAP credential so accounts sharing the same login
        only open ONE connection per cron run, preventing per-user connection
        limit errors on the mail server.

        Also detects accounts with a stale sync_status='ok' that have never
        actually imported any messages — these are typically accounts where the
        password was set up during a previous test run but auth has since failed.
        Such accounts are included in the cron run so their status is updated.
        """
        accounts = self.search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])
        synced_creds: set = set()
        for acc in accounts:
            if not (acc.password or '').strip():
                # Mark completely unconfigured accounts clearly
                if acc.sync_status not in ('never',):
                    try:
                        with self.env.cr.savepoint():
                            acc.write({'sync_status': 'never', 'sync_error_msg': False})
                    except Exception:
                        pass
                continue
            cred = (
                (acc.imap_host or '').strip(),
                int(acc.imap_port or 993),
                (acc.username or acc.email_address or '').strip(),
            )
            if cred in synced_creds:
                continue  # already synced this mailbox in this cron run
            synced_creds.add(cred)
            try:
                acc.action_sync()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception('Cron IMAP sync failed for account %s (%s)', acc.id, acc.email_address)

    def _store_imap_attachments(self, msg_record, email_msg):
        """Extract MIME attachments from a parsed email and store as ir.attachment.

        Skips parts that are already stored (deduplicates by name + size).
        Called after the full message body is downloaded from IMAP.
        """
        import base64 as _b64
        import uuid as _uuid
        import mimetypes as _mimetypes

        IrAtt = self.env['ir.attachment'].sudo()
        existing_names = {
            a.name
            for a in IrAtt.search([
                ('res_model', '=', 'lugal.email.message'),
                ('res_id',    '=', msg_record.id),
            ])
        }

        for part in email_msg.walk():
            # Only process attachment/inline parts with a filename
            disposition = part.get_content_disposition() or ''
            filename = part.get_filename()
            if not filename and 'attachment' not in disposition and 'inline' not in disposition:
                continue
            if not filename:
                continue
            filename = self._decode_mime_header(filename)
            if filename in existing_names:
                continue

            att_data = part.get_payload(decode=True)
            if not att_data:
                continue

            mime = part.get_content_type() or _mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            att_token = _uuid.uuid4().hex

            # Detect inline (embedded) parts: Content-Disposition = inline AND has Content-ID.
            # These are pasted / drag-dropped / signature images embedded in the body.
            # We tag them with "__inline_cid__:<cid>" in the description field so the
            # API response separates them into `inline_attachments` instead of `attachments`.
            raw_cid = part.get('Content-ID') or ''
            # Content-ID is usually wrapped in angle brackets: <img-abc@lugal.mail>
            cid_value = raw_cid.strip('<> ')
            is_inline_part = ('inline' in disposition) and bool(cid_value)
            description = f'__inline_cid__:{cid_value}' if is_inline_part else None

            try:
                IrAtt.create({
                    'name':         filename,
                    'mimetype':     mime,
                    'datas':        _b64.b64encode(att_data).decode('utf-8'),
                    'type':         'binary',
                    'res_model':    'lugal.email.message',
                    'res_id':       msg_record.id,
                    'access_token': att_token,
                    **(({'description': description}) if description else {}),
                })
                existing_names.add(filename)
                _logger.debug(
                    'Stored IMAP attachment %r (%d bytes) for msg=%s inline=%s',
                    filename, len(att_data), msg_record.id, is_inline_part,
                )
            except Exception:
                _logger.warning(
                    'Failed to store IMAP attachment %r for msg=%s',
                    filename, msg_record.id, exc_info=True,
                )

    def fetch_message_body(self, message_id):
        """
        Fetch the full body of a single message from IMAP on demand.
        Called when the user opens an email that was imported headers-only.
        Returns the updated message record, or None on failure.
        """
        self.ensure_one()
        Msg = self.env['lugal.email.message'].sudo()
        msg = Msg.browse(message_id)
        if not msg.exists() or msg.account_id.id != self.id:
            return None
        if msg.body_fetched:
            return msg
        if not msg.imap_uid:
            return msg

        try:
            import imaplib
            conn = self._imap_connect()
            # Map logical folder names to real IMAP paths.
            # msg.folder is stored as 'inbox'|'sent'|'drafts'|'trash'|'archive'|'spam'
            # for standard folders, or the raw IMAP path for custom folders.
            _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            raw_folder = msg.folder or 'inbox'
            if raw_folder == 'inbox':
                folder = 'INBOX'
            elif raw_folder in _LOGICAL:
                try:
                    folder = self._get_server_folder_name(raw_folder)
                except Exception:
                    folder = raw_folder.capitalize()   # fallback e.g. 'Sent'
            else:
                folder = raw_folder   # already a real IMAP path (e.g. 'INBOX.AllFromUmar')
            typ, _ = conn.select(folder, readonly=True)
            if typ != 'OK':
                return msg
            typ, data_list = conn.uid('fetch', str(msg.imap_uid), '(FLAGS BODY.PEEK[])')
            conn.logout()
            if typ != 'OK' or not data_list:
                return msg

            for item in data_list:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                meta, payload = item[0], item[1]
                if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                    continue
                email_msg = email_lib.message_from_bytes(bytes(payload))
                body_text, body_html = self._extract_best_body(email_msg)
                msg.write({
                    'body_text':    body_text or '',
                    'body_html':    body_html or False,
                    'body_fetched': True,
                })
                # Extract and store file attachments
                self._store_imap_attachments(msg, email_msg)
                return msg
        except Exception:
            _logger.exception('fetch_message_body failed for msg=%s account=%s', message_id, self.id)
        return msg
