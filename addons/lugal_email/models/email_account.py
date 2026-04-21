# -*- coding: utf-8 -*-

import json
import logging
import re
import email as email_lib
from email import policy
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime, parseaddr

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

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
        """Test IMAP connection and update sync_status accordingly."""
        self.ensure_one()
        try:
            import imaplib
            conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
            conn = conn_cls(self.imap_host, self.imap_port)
            conn.login(self.username or self.email_address, self.password or '')
            conn.logout()
            self.write({'sync_status': 'ok', 'sync_error_msg': False})
            return {'status': 'ok', 'message': 'Connection successful'}
        except Exception as exc:
            self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            return {'status': 'error', 'message': str(exc)}

    def _imap_connect(self):
        """Return a logged-in IMAP connection."""
        import imaplib
        conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
        conn = conn_cls(self.imap_host, self.imap_port)
        conn.login(self.username or self.email_address, self.password or '')
        return conn

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

    def _upsert_inbox_message(self, uid_int, raw_bytes, flags_meta, headers_only=False):
        """Create or update one inbox row from raw RFC822 bytes."""
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
        body_text, body_html = self._extract_best_body(msg)
        is_read = self._parse_flags_from_fetch_response(flags_meta)

        Message = self.env['lugal.email.message'].sudo()
        domain = [('account_id', '=', self.id), ('folder', '=', 'inbox'), ('imap_uid', '=', uid_int)]
        existing = Message.search(domain, limit=1)
        vals = {
            'account_id':    self.id,
            'folder':        'inbox',
            'imap_uid':      uid_int,
            'subject':       subject or '(no subject)',
            'from_name':     from_name or '',
            'from_address':  from_addr or '',
            'to_addresses':  json.dumps(to_list),
            'cc_addresses':  json.dumps(cc_list),
            'message_id':    message_id,
            'date':          dt,
            'is_read':       is_read,
            'is_deleted':    False,
            'active':        True,
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
            return existing
        return Message.create(vals)

    def action_sync_if_stale(self, force=False):
        """
        Run IMAP inbox import unless recently synced (reduces load on mailbox polling).
        If inbox has no rows, sync runs unless the last attempt was very recent.
        """
        self.ensure_one()
        if not (self.password or '').strip():
            return {'skipped': True, 'reason': 'no_password'}
        now = fields.Datetime.now()
        Msg = self.env['lugal.email.message'].sudo()
        inbox_count = Msg.search_count([
            ('account_id', '=', self.id),
            ('folder', '=', 'inbox'),
            ('is_deleted', '=', False),
        ])
        if not force and self.last_sync_date:
            delta = (now - self.last_sync_date).total_seconds()
            limit = SYNC_THROTTLE_EMPTY_SECONDS if inbox_count == 0 else SYNC_THROTTLE_SECONDS
            if delta < limit:
                return {'skipped': True, 'reason': 'throttle', 'sync_status': self.sync_status}

        return self.action_sync()

    def action_sync(self):
        """Import INBOX messages over IMAP and refresh unread_count from the database."""
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
            HEADERS_FETCH = '(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
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
                    # Full body for new messages — few messages, fast.
                    uid_set = ','.join(str(u) for u in todo)
                    typ, data_list = conn.uid('fetch', uid_set, BODY_FETCH)
                    if typ == 'OK' and data_list:
                        _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=False)

            conn.logout()

            unread = Msg.search_count([
                ('account_id', '=', self.id),
                ('folder', '=', 'inbox'),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])
            self.write({
                'sync_status':       'ok',
                'last_sync_date':    fields.Datetime.now(),
                'unread_count':      unread,
                'imap_inbox_max_uid': max_seen,
                'sync_error_msg':    False,
            })
            return {
                'sync_status':    'ok',
                'last_sync_date': self.last_sync_date.isoformat() if self.last_sync_date else None,
                'unread_count':   unread,
                'imported':       imported,
            }
        except Exception as exc:
            self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            _logger.exception('action_sync failed for account %s', self.id)
            return {'sync_status': 'error', 'message': str(exc)}

    @api.model
    def action_sync_all_accounts(self):
        """
        Background cron entry-point.
        Syncs INBOX for every active account that has a password configured.
        Called by the ir.cron scheduler; runs each account in its own savepoint
        so one failure does not abort the others.
        """
        accounts = self.search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])
        for acc in accounts:
            if not (acc.password or '').strip():
                continue
            try:
                acc.action_sync()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception('Cron IMAP sync failed for account %s (%s)', acc.id, acc.email_address)

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
            folder = 'INBOX' if msg.folder == 'inbox' else msg.folder
            typ, _ = conn.select(folder, readonly=True)
            if typ != 'OK':
                return msg
            uid_re = re.compile(br'UID\s+(\d+)')
            typ, data_list = conn.uid('fetch', str(msg.imap_uid), '(FLAGS BODY.PEEK[])')
            conn.logout()
            if typ != 'OK' or not data_list:
                return msg

            # Parse the single-message response
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
                return msg
        except Exception:
            _logger.exception('fetch_message_body failed for msg=%s account=%s', message_id, self.id)
        return msg
