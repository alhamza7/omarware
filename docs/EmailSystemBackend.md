# Email + WebSocket System — Full Backend Source Reference

This document contains every backend file related to the email, IMAP, WebSocket,
and push-notification systems. Generated Thu May 14 02:17:04 PM UTC 2026 for agent context handoff.

---

## Module: lugal_email

start of email_message.py
email_message.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_message.py
# Component: Lugal Email — lugal.email.message model (email_message.py)

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


def _is_sent_folder_value(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent',
        'sent items',
        'sent messages',
    }


class LugalEmailMessage(models.Model):
    """
    Cached/stored email message.
    Both inbound (fetched via IMAP) and outbound (sent via SMTP) messages land here.
    """
    _name = 'lugal.email.message'
    _description = 'Lugal Email Message'
    _order = 'date desc'
    _rec_name = 'subject'

    # ── Account / Folder ──────────────────────────────────────────────────────
    account_id = fields.Many2one(
        'lugal.email.account', string='Email Account',
        required=True, ondelete='cascade', index=True,
    )
    # Logical folders use lowercase names (inbox, sent, …).  Rules and moves may
    # store a full IMAP path (e.g. INBOX.sender_Important) — must be Char, not
    # Selection, or ORM writes silently fail and mail never leaves the inbox.
    folder = fields.Char(
        string='Folder',
        default='inbox',
        index=True,
        help='Logical mailbox (inbox, sent, …) or full IMAP folder path for custom mailboxes.',
    )

    # IMAP UID within the folder (used for dedup / incremental sync). Null for purely local rows.
    imap_uid       = fields.Integer(string='IMAP UID', index=True)

    # ── Headers ───────────────────────────────────────────────────────────────
    subject        = fields.Char(string='Subject')
    from_name      = fields.Char(string='From Name')
    from_address   = fields.Char(string='From Address', index=True)
    to_addresses   = fields.Text(string='To (JSON list of {name, email})')
    cc_addresses   = fields.Text(string='CC (JSON)')
    bcc_addresses  = fields.Text(string='BCC (JSON)')
    reply_to       = fields.Char(string='Reply-To')
    message_id     = fields.Char(string='Message-ID (IMAP)', index=True)
    in_reply_to    = fields.Char(string='In-Reply-To')
    # Space-separated chain of ancestor Message-IDs (RFC 2822 References header).
    # Column quoted because "references" is a reserved word in PostgreSQL.
    references     = fields.Text(string='References', column='references')
    # Root Message-ID of the conversation thread.  All messages in the same
    # thread share the same thread_id.  Set to the first entry in References
    # (or to the message's own Message-ID when it is the root).
    thread_id      = fields.Char(string='Thread ID', index=True)
    date           = fields.Datetime(string='Date', index=True)

    # ── Body ──────────────────────────────────────────────────────────────────
    body_html = fields.Html(string='Body HTML', sanitize=False)
    body_text = fields.Text(string='Body Text')
    written_in_arabic = fields.Boolean(
        string='Written in Arabic / RTL',
        default=False,
        index=True,
        help='Frontend compose hint: render this outbound message right-to-left when true.',
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_read      = fields.Boolean(string='Read',      default=False, index=True)
    is_starred   = fields.Boolean(string='Starred',    default=False)
    is_draft     = fields.Boolean(string='Draft',      default=False)
    # is_flagged maps to the IMAP \Flagged flag — independent of is_starred.
    # is_starred is a UI bookmark; is_flagged is the IMAP protocol flag.
    is_flagged   = fields.Boolean(string='Flagged',    default=False, index=True)
    # is_important stores the "important" marker (Gmail \Important or manual).
    is_important = fields.Boolean(string='Important', default=False, index=True)

    # Timestamp set the first time this message is marked as read.
    # Null for messages that have never been opened.
    read_at    = fields.Datetime(string='Read At', readonly=False)

    # ── CRM Links (generic — no direct Many2one to avoid circular deps) ───────
    linked_model       = fields.Char(string='Linked Model', index=True)
    linked_record_id   = fields.Integer(string='Linked Record ID', index=True)
    linked_record_name = fields.Char(string='Linked Record Name')

    # Convenience integer shortcuts — resolved at API layer, not at ORM layer
    linked_customer_id = fields.Integer(string='Linked Customer ID', index=True)
    linked_customer_name = fields.Char(string='Linked Customer Name')
    linked_ticket_id   = fields.Integer(string='Linked Ticket ID', index=True)
    linked_ticket_name = fields.Char(string='Linked Ticket Name')

    # ── SMTP Delivery Status ───────────────────────────────────────────────────
    smtp_delivered = fields.Boolean(
        string='SMTP Delivered', default=False,
        help='True when the message was successfully handed off to the SMTP server.',
    )
    smtp_error = fields.Char(
        string='SMTP Error',
        help='Last SMTP error message if delivery failed.',
    )
    # smtp_status is the canonical delivery state returned to the FE.
    # 'pending'   = queued in background thread, not yet attempted
    # 'delivered' = SMTP server accepted the message
    # 'failed'    = SMTP server rejected or network error
    # Only meaningful for outbound (sent/draft) messages.
    smtp_status = fields.Selection([
        ('pending',   'Pending'),
        ('delivered', 'Delivered'),
        ('failed',    'Failed'),
    ], string='SMTP Status', default='pending', index=True)

    # True for messages we created locally (sent/reply/forward) or once the full
    # IMAP body has been downloaded on-demand. False for inbox rows that were
    # imported with headers only (body_html/body_text may be blank).
    body_fetched = fields.Boolean(
        string='Full Body Fetched', default=False,
        help='False = only headers synced; body fetched on first open.',
    )

    # ── Mention / direct-address flag ────────────────────────────────────────
    # True when the account owner's email appears in the To: header
    # (i.e. the message was sent directly to them, not just CC'd).
    # Matches Outlook "Mentioned Mail" / Exchange behaviour.
    is_mentioned = fields.Boolean(string='Mentioned', default=False, index=True)

    # ── RFC-822 message size in bytes (approx; populated on full-body sync) ──
    message_size = fields.Integer(string='Message Size (bytes)', default=0)

    # ── Read receipt (MDN) tracking ───────────────────────────────────────────
    # True when the sender requested a read receipt (Disposition-Notification-To).
    request_read_receipt = fields.Boolean(
        string='Read Receipt Requested', default=False,
        help='True when the outgoing message included a Disposition-Notification-To header.',
    )
    # Populated when an MDN (Message Disposition Notification) is received from
    # the recipient confirming they opened the message.  Null until that event.
    recipient_read_at = fields.Datetime(
        string='Recipient Read At',
        help='Timestamp from the MDN returned by the recipient\'s email client.',
    )

    # ── Soft delete ───────────────────────────────────────────────────────────
    active     = fields.Boolean(default=True)
    is_deleted = fields.Boolean(default=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Sent-folder is_read/read_at is a recipient-read signal. Sender-owned
        # actions must not initialize or stamp it unless an explicit recipient
        # read event (internal read propagation or MDN) allows it.
        allow_recipient_read = bool(self.env.context.get('lugal_recipient_read'))
        if not allow_recipient_read:
            for vals in vals_list:
                if _is_sent_folder_value(vals.get('folder')):
                    if vals.get('is_read'):
                        vals['is_read'] = False
                    vals.pop('read_at', None)

        # Auto-stamp read_at when a non-sent message is created already marked as
        # read.
        # Skip when called from IMAP sync — read_at must only be set when the
        # user explicitly opens the mail in the Lugal app.
        is_imap_sync = bool(self.env.context.get('lugal_imap_sync'))
        if not is_imap_sync:
            now = fields.Datetime.now()
            for vals in vals_list:
                if vals.get('is_read') and not vals.get('read_at'):
                    vals['read_at'] = now
        return super().create(vals_list)

    def write(self, vals):
        # Hard invariant: for sent-folder rows, is_read/read_at mean "recipient
        # read this", never "sender opened their Sent item".  Any normal write
        # attempting to change those fields on sent rows is stripped unless it is
        # explicitly marked as a recipient-read event.
        allow_recipient_read = bool(self.env.context.get('lugal_recipient_read'))
        read_fields = {'is_read', 'read_at'} & set(vals)
        if read_fields and not allow_recipient_read:
            sent_records = self.filtered(lambda rec: _is_sent_folder_value(rec.folder))
            if sent_records:
                other_records = self - sent_records
                sent_vals = {key: value for key, value in vals.items() if key not in read_fields}
                result = True
                if other_records:
                    result = super(LugalEmailMessage, other_records).write(vals) and result
                if sent_vals:
                    result = super(LugalEmailMessage, sent_records).write(sent_vals) and result
                return result

        # Auto-stamp read_at the first time is_read transitions to True.
        # Skip when called from IMAP sync — only stamp read_at on explicit
        # user actions (open, mark-read, notification dismiss).
        is_imap_sync = bool(self.env.context.get('lugal_imap_sync'))
        if (
            not is_imap_sync
            and vals.get('is_read')
            and not vals.get('read_at')
            and any(not rec.is_read and not rec.read_at for rec in self)
        ):
            vals = dict(vals, read_at=fields.Datetime.now())
        return super().write(vals)

end of file email_message.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of email_account.py
email_account.py

# -*- coding: utf-8 -*-
# Component: Lugal Email — lugal.email.account model (email_account.py)

import json
import hashlib
import logging
import re
import threading
from contextlib import contextmanager
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


def _pg_advisory_lock_key(*parts) -> int:
    """Stable signed-bigint key for cross-worker PostgreSQL advisory locks."""
    raw = '|'.join(str(p or '') for p in parts).encode('utf-8', 'ignore')
    digest = hashlib.blake2b(raw, digest_size=8).digest()
    # Keep it in signed BIGINT's positive range for pg_advisory_xact_lock(bigint).
    return int.from_bytes(digest, 'big') & 0x7FFFFFFFFFFFFFFF


def _extract_composed_text(body_text, body_html):
    """Return only the newly-composed text of an email, stripping:
    - Quoted/replied content (lines starting with ">", or <blockquote> in HTML)
    - Email signature (content after "-- " RFC 3676 delimiter, or common sig divs)

    Used exclusively for is_mentioned detection so we don't fire on mentions
    that appear only in quoted history or signatures.
    """
    text = ''

    if body_text:
        composed_lines = []
        for line in body_text.splitlines():
            # RFC 3676 signature separator: standalone "--" or "-- "
            if line.rstrip() in ('--', '-- '):
                break
            # Skip quoted lines (lines starting with ">")
            if line.startswith('>'):
                continue
            composed_lines.append(line)
        text = '\n'.join(composed_lines).strip()

    if not text and body_html:
        html = body_html
        # Remove blockquote elements (quoted/replied content)
        html = re.sub(r'<blockquote[^>]*>.*?</blockquote>', '', html,
                      flags=re.DOTALL | re.IGNORECASE)
        # Remove common signature containers
        html = re.sub(
            r'<(?:div|p|span)[^>]*(?:class|id)\s*=\s*["\'][^"\']*'
            r'(?:signature|gmail_signature|yahoo_quoted|x_gmail_com|moz-signature)[^"\']*["\'][^>]*>.*?</(?:div|p|span)>',
            '', html, flags=re.DOTALL | re.IGNORECASE,
        )
        # Strip all remaining tags and collapse whitespace
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'&(?:nbsp|amp|lt|gt|quot);', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()

    return text


# Serialize IMAP logins for the same (host, port, login) within this OS process.
# Parallel HTTP handlers, polling, and fire-and-forget MOVE/STORE threads otherwise
# burst past mail_max_userip_connections on shared mail hosts.
_IMAP_CRED_LOCKS: dict = {}
_IMAP_CRED_LOCKS_GUARD = threading.Lock()

# How many IMAP messages to pull on first / incremental catch-up (per sync call).
SYNC_MAX_MESSAGES = 150
# Auto-sync throttle when inbox already has cached messages (seconds).
SYNC_THROTTLE_SECONDS = 15
# When inbox is empty, sync more aggressively.
SYNC_THROTTLE_EMPTY_SECONDS = 10

# Keywords that indicate an IMAP connection-limit error from the server.
_CONN_LIMIT_KEYWORDS = (
    'limit', 'maximum', 'too many', '[limit]', 'mail_max_userip',
)

# Keywords that indicate a transient IMAP / network error worth retrying.
_TRANSIENT_KEYWORDS = (
    'limit', 'maximum', 'too many', 'connection',
    'eof', 'socket', 'temporarily', 'unavailable',
)


def _is_conn_limit_err(exc) -> bool:
    """Return True when the exception looks like a per-user connection-limit error."""
    parts = []
    for a in getattr(exc, 'args', ()) or ():
        parts.append(a.decode('utf-8', errors='replace') if isinstance(a, bytes) else str(a))
    text = ' '.join(parts).lower()
    return any(k in text for k in _CONN_LIMIT_KEYWORDS)


def _is_transient_err(exc) -> bool:
    """Return True when the exception is a transient IMAP/network error worth retrying."""
    parts = []
    for a in getattr(exc, 'args', ()) or ():
        parts.append(a.decode('utf-8', errors='replace') if isinstance(a, bytes) else str(a))
    text = ' '.join(parts).lower()
    return any(k in text for k in _TRANSIENT_KEYWORDS)


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
    # Used as the cursor for incremental fetch: only UIDs above this value
    # are fetched on subsequent syncs, keeping each sync fast.
    imap_inbox_max_uid = fields.Integer(string='IMAP Inbox Max UID', default=0)

    active          = fields.Boolean(default=True)
    is_deleted      = fields.Boolean(default=False, index=True)

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.model
    def _normalize_connection_vals(self, vals):
        """Normalize common mail-setting mistakes before they reach production."""
        vals = dict(vals or {})
        if 'smtp_port' in vals:
            try:
                port = int(vals.get('smtp_port') or 0)
            except (TypeError, ValueError):
                port = 0
            if port == 475:
                # Common typo for implicit TLS SMTP. Port 475 is not reachable
                # on our mail hosts and leaves outbound mail failed locally.
                port = 465
            if port:
                vals['smtp_port'] = port
                if port == 465:
                    vals['smtp_use_tls'] = False
                elif port == 587:
                    vals['smtp_use_tls'] = True
        if 'imap_port' in vals:
            try:
                vals['imap_port'] = int(vals.get('imap_port') or 993)
            except (TypeError, ValueError):
                vals['imap_port'] = 993
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._normalize_connection_vals(vals) for vals in vals_list]
        records = super().create(vals_list)
        for rec in records:
            if (rec.password or '').strip():
                # Start the IDLE watcher for this account as soon as the
                # transaction commits, without waiting for the 1-minute cron.
                rec._schedule_idle_start()
        return records

    def write(self, vals):
        return super().write(self._normalize_connection_vals(vals))

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
        """Test both IMAP and SMTP credentials.

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
        except Exception as exc:
            self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            return {
                'status': 'error',
                'imap_status': 'error',
                'smtp_status': 'not_tested',
                'message': str(exc),
            }

        try:
            import smtplib
            smtp_port = int(self.smtp_port or 587)
            if smtp_port == 465:
                smtp = smtplib.SMTP_SSL(self.smtp_host, smtp_port, timeout=15)
            else:
                smtp = smtplib.SMTP(self.smtp_host, smtp_port, timeout=15)
            try:
                smtp.ehlo()
                if smtp_port != 465 and self.smtp_use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(self.username or self.email_address, self.password or '')
            finally:
                try:
                    smtp.quit()
                except Exception:
                    pass

            self.write({'sync_status': 'ok', 'sync_error_msg': False})
            self._schedule_idle_start()
            return {
                'status': 'ok',
                'imap_status': 'ok',
                'smtp_status': 'ok',
                'message': 'IMAP and SMTP connection successful',
            }
        except Exception as exc:
            # IMAP is healthy, so keep inbox sync status OK. Surface SMTP failure
            # to the caller without making notifications/inbox treat the account
            # as broken.
            self.write({'sync_status': 'ok', 'sync_error_msg': False})
            return {
                'status': 'error',
                'imap_status': 'ok',
                'smtp_status': 'error',
                'message': f'SMTP failed: {exc}',
            }

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
            time.sleep(0.5)
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    env['lugal.email.idle.watcher'].clear_backoff_for_account(acc_id)
            except Exception:
                pass

        threading.Thread(target=_trigger, daemon=True, name='idle-on-test').start()

    def _imap_credentials_key(self):
        """Stable tuple for locking IMAP access (same login = one gate)."""
        self.ensure_one()
        host = (self.imap_host or '').strip().lower()
        port = int(self.imap_port or (993 if self.imap_use_ssl else 143))
        user = (self.username or self.email_address or '').strip().lower()
        return host, port, user

    def _imap_connect_unlocked(self):
        """Open a raw IMAP connection without taking the credential lock.
        Internal use only — callers must hold the credential lock via _imap_session.
        """
        import imaplib
        conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
        port = int(self.imap_port or (993 if self.imap_use_ssl else 143))
        conn = conn_cls(self.imap_host, port)
        conn.login(self.username or self.email_address, self.password or '')
        return conn

    @contextmanager
    def _imap_session(self, connect_attempts=6, retry_delay=2.0):
        """Serialize IMAP for this account's credentials.

        Opens ONE authenticated connection, yields it to the caller, then
        always logs out in the finally block.

        KEY FIX (Composer 2 regression):
        ─────────────────────────────────
        The previous implementation had ``yield conn`` inside the retry loop's
        try/except.  Any exception raised by the *caller's* code (e.g. an IMAP
        command error inside ``account_folders``) was caught by the retry except,
        treated as a connection-limit error, slept, and re-connected — opening
        multiple new IMAP sessions and burning all connect_attempts before
        finally re-raising.  On a server near the 20-connection limit this
        reliably triggered [LIMIT] on every API call.

        The fix separates the two phases:
          Phase 1 — *connect*: retry with backoff on transient/limit errors.
          Phase 2 — *use*: yield to caller; any exception here is NOT retried
                    and propagates immediately after logout.
        """
        import time as _time
        self.ensure_one()
        key = self._imap_credentials_key()
        with _IMAP_CRED_LOCKS_GUARD:
            lock = _IMAP_CRED_LOCKS.setdefault(key, threading.Lock())
        lock.acquire()
        conn = None
        try:
            # ── Phase 1: connect (with retry on transient errors) ────────────
            last_exc = None
            for attempt in range(connect_attempts):
                try:
                    conn = self._imap_connect_unlocked()
                    last_exc = None
                    break   # connected successfully
                except Exception as exc:
                    last_exc = exc
                    if conn is not None:
                        try:
                            conn.logout()
                        except Exception:
                            try:
                                conn.shutdown()
                            except Exception:
                                pass
                        conn = None
                    if attempt < connect_attempts - 1 and _is_transient_err(exc):
                        _time.sleep(retry_delay * (attempt + 1))
                        continue
                    raise   # non-retryable or exhausted

            if last_exc is not None:
                raise last_exc

            # ── Phase 2: use — yield to caller; never retry caller exceptions ──
            try:
                yield conn
            except Exception:
                # Caller's exception: log and re-raise immediately — do NOT retry.
                raise
        finally:
            # Always log out, regardless of which phase raised.
            if conn is not None:
                try:
                    conn.logout()
                except Exception:
                    try:
                        conn.shutdown()
                    except Exception:
                        pass
            lock.release()

    # ── Bidirectional IMAP sync helpers ──────────────────────────────────────

    def _get_server_folder_name(self, purpose, existing_conn=None):
        """Return the IMAP server folder name for a logical purpose.

        purpose: 'trash' | 'archive' | 'sent' | 'drafts' | 'spam'

        Detects per-account folder names via IMAP LIST on first call, then caches
        in ir.config_parameter so subsequent calls are instant (no extra connection).

        ``existing_conn``: when provided, LIST on this connection (caller must
        already hold the credential lock via ``_imap_session``) to avoid nested
        IMAP logins and deadlocks.
        """
        self.ensure_one()
        import re as _re

        cache_key = f'lugal.email.folder.{self.id}.{purpose}'
        ICP = self.env['ir.config_parameter'].sudo()
        cached = ICP.get_param(cache_key, '')
        if cached:
            return cached

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

        keywords = {
            'trash':   ['trash', 'deleted'],
            'archive': ['archive'],
            'sent':    ['sent'],
            'drafts':  ['draft'],
            'spam':    ['spam', 'junk'],
        }

        def _match_folder_from_listing(listing):
            if not listing:
                return None
            for entry in listing:
                if not entry:
                    continue
                raw = entry.decode('utf-8', errors='replace') if isinstance(entry, bytes) else str(entry)
                m = _re.search(r'\(.*?\)\s+"[^"]+"\s+"?(.+?)"?\s*$', raw)
                if not m:
                    m = _re.search(r'\(.*?\)\s+\S+\s+"?(.+?)"?\s*$', raw)
                folder_raw = m.group(1).strip().strip('"') if m else ''
                if not folder_raw:
                    continue
                for kw in keywords.get(purpose, []):
                    if kw in folder_raw.lower():
                        return folder_raw
            return None

        try:
            if existing_conn is not None:
                typ, listing = existing_conn.list()
                if typ == 'OK' and listing:
                    hit = _match_folder_from_listing(listing)
                    if hit:
                        ICP.set_param(cache_key, hit)
                        return hit
            else:
                with self._imap_session() as conn:
                    typ, listing = conn.list()
                    if typ == 'OK' and listing:
                        hit = _match_folder_from_listing(listing)
                        if hit:
                            ICP.set_param(cache_key, hit)
                            return hit
        except Exception:
            pass

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
                    with acc._imap_session() as conn:
                        conn.select(imap_folder, readonly=False)
                        uid_str = str(imap_uid)
                        if add_flags:
                            conn.uid('store', uid_str, '+FLAGS', '(' + ' '.join(add_flags) + ')')
                        if remove_flags:
                            conn.uid('store', uid_str, '-FLAGS', '(' + ' '.join(remove_flags) + ')')
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
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_append():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo

                with _Registry(db_name).cursor() as _cr:
                    env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    if not acc.exists():
                        return
                    with acc._imap_session() as conn:
                        sent_folder = acc._get_server_folder_name('sent', existing_conn=conn)
                        msg_bytes = (
                            raw_message.encode('utf-8')
                            if isinstance(raw_message, str)
                            else raw_message
                        )
                        typ, data = conn.append(sent_folder, '(\\Seen)', None, msg_bytes)

                    if typ == 'OK':
                        _logger.info('IMAP APPEND to Sent succeeded: acc=%s folder=%s', acc_id, sent_folder)
                    else:
                        _logger.warning('IMAP APPEND to Sent returned %s for acc=%s: %s', typ, acc_id, data)
            except Exception as exc:
                _logger.warning('IMAP APPEND to Sent failed for acc=%s: %s', acc_id, exc)

        threading.Thread(target=_do_append, daemon=True, name=f'imap-append-sent-{acc_id}').start()

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

                    with acc._imap_session() as conn:
                        if to_folder_purpose == 'inbox':
                            dest_folder = 'INBOX'
                        else:
                            dest_folder = acc._get_server_folder_name(
                                to_folder_purpose, existing_conn=conn,
                            )
                        conn.select(from_folder, readonly=False)
                        uid_str = str(imap_uid)

                        typ, data = conn.uid('move', uid_str, dest_folder)
                        if typ != 'OK':
                            conn.uid('copy', uid_str, dest_folder)
                            conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                            conn.expunge()

                    _logger.info(
                        'IMAP move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder,
                    )
            except Exception as exc:
                _logger.warning('IMAP move failed acc=%s uid=%s: %s', acc_id, imap_uid, exc)

        threading.Thread(target=_do_move, daemon=True, name=f'imap-move-{imap_uid}').start()

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
                    with acc._imap_session() as conn:
                        conn.select(from_folder, readonly=False)
                        uid_str = str(imap_uid)

                        typ, data = conn.uid('move', uid_str, dest_folder_path)
                        if typ != 'OK':
                            conn.uid('copy', uid_str, dest_folder_path)
                            conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                            conn.expunge()

                    _logger.info(
                        'IMAP raw-move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder_path,
                    )
            except Exception as exc:
                _logger.warning('IMAP raw-move failed acc=%s uid=%s: %s', acc_id, imap_uid, exc)

        threading.Thread(target=_do_move, daemon=True, name=f'imap-rawmove-{imap_uid}').start()

    def _imap_ensure_folder(self, path, existing_conn=None):
        """Create *path* on the IMAP server if it does not already exist.

        Returns the final folder path on success, raises on hard failure.
        Safe to call when the folder already exists (no-op in that case).

        ``existing_conn``: optional open connection (same lock as caller's session).
        Uses LIST-all approach instead of conn.list('""', path) to avoid
        "Invalid pattern" errors on servers that reject dotted paths as patterns.
        """

        def _ensure_on_conn(conn):
            # Use LIST to check existence — conn.list('""', path) can give
            # "Invalid pattern" on some servers when path contains dots.
            # List ALL and search instead.
            typ, raw = conn.list()
            exists = False
            if typ == 'OK' and raw:
                path_lower = path.lower()
                for item in raw:
                    if not item:
                        continue
                    line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                    # Extract the folder name from the LIST response line
                    import re as _re2
                    m = _re2.search(r'\)\s+(?:"[^"]*"|NIL)\s+"?(.+?)"?\s*$', line.strip())
                    if m and m.group(1).strip().lower() == path_lower:
                        exists = True
                        break
            if not exists:
                conn.create(path)
                conn.subscribe(path)
                _logger.info('IMAP folder created: acc=%s path=%s', self.id, path)
            else:
                _logger.info('IMAP folder already exists: acc=%s path=%s', self.id, path)
            return path

        self.ensure_one()
        if existing_conn is not None:
            return _ensure_on_conn(existing_conn)
        with self._imap_session() as conn:
            return _ensure_on_conn(conn)

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
                    with acc._imap_session() as conn:
                        conn.select(imap_folder, readonly=False)
                        conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                        conn.expunge()
                    _logger.info('IMAP expunge acc=%s uid=%s folder=%s', acc_id, imap_uid, imap_folder)
            except Exception as exc:
                _logger.warning('IMAP expunge failed acc=%s uid=%s: %s', acc_id, imap_uid, exc)

        threading.Thread(target=_do_expunge, daemon=True, name=f'imap-expunge-{imap_uid}').start()

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

        # ── MDN (Message Disposition Notification / read receipt) detection ──
        # When a recipient's mail client returns a read receipt, it arrives as a
        # multipart/report email with report-type=disposition-notification.
        # We parse the Original-Message-ID from the notification part, find the
        # corresponding outbound sent message, stamp its recipient_read_at, and
        # silently discard the MDN so it never appears as a regular inbox item.
        try:
            _ct = (msg.get_content_type() or '').lower()
            _report_type = (msg.get_param('report-type') or '').lower()
            if 'report' in _ct and 'disposition-notification' in _report_type:
                _orig_mid = None
                for _part in msg.walk():
                    if 'disposition-notification' in (_part.get_content_type() or '').lower():
                        try:
                            _notif_text = _part.get_payload(decode=True)
                            if isinstance(_notif_text, bytes):
                                _notif_text = _notif_text.decode('utf-8', errors='replace')
                            for _line in (_notif_text or '').splitlines():
                                _key, _, _val = _line.partition(':')
                                if _key.strip().lower() == 'original-message-id':
                                    _orig_mid = _val.strip()
                                    break
                        except Exception:
                            pass
                        break
                if _orig_mid:
                    _sent = self.env['lugal.email.message'].sudo().search([
                        ('account_id', '=', self.id),
                        ('message_id', '=', _orig_mid),
                        ('folder',     '=', 'sent'),
                        ('is_deleted', '=', False),
                    ], limit=1)
                    if _sent:
                        _read_ts = dt or fields.Datetime.now()
                        # Update both recipient_read_at (MDN provenance) and the
                        # canonical is_read/read_at so the sender's sent-folder view
                        # correctly shows the message as read by the recipient.
                        _sent.with_context(lugal_recipient_read=True).write({
                            'recipient_read_at': _read_ts,
                            'is_read':           True,
                            'read_at':           _read_ts,
                        })
                        _logger.info(
                            'MDN: marked sent msg id=%s (mid=%s) read '
                            'recipient_read_at=%s',
                            _sent.id, _orig_mid, _read_ts,
                        )
                    # Discard MDN — do not store it as a regular inbox message
                    return None
        except Exception:
            pass  # never let MDN parsing block regular email import
        to_raw = msg.get_all('To', [])
        pairs = getaddresses(to_raw) if to_raw else []
        to_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in pairs if e]
        cc_raw = msg.get_all('Cc', [])
        cc_pairs = getaddresses(cc_raw) if cc_raw else []
        cc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in cc_pairs if e]
        bcc_raw = msg.get_all('Bcc', [])
        bcc_pairs = getaddresses(bcc_raw) if bcc_raw else []
        bcc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in bcc_pairs if e]
        reply_to_raw = msg.get('Reply-To', '')
        reply_to_addr = ''
        if reply_to_raw:
            rt_pairs = getaddresses([reply_to_raw])
            reply_to_addr = rt_pairs[0][1] if rt_pairs else ''

        # Detect whether the sender requested a read receipt (RFC 3798).
        # We honour both the standard header and the legacy Return-Receipt-To.
        # Setting request_read_receipt=True on the received message tells the
        # mark-read endpoints to send back an MDN when the user reads this email.
        _dnt_raw = (msg.get('Disposition-Notification-To') or
                    msg.get('Return-Receipt-To') or '').strip()
        _incoming_request_receipt = bool(_dnt_raw)
        # Also store the notification address so we know exactly where to send
        # the MDN (usually identical to From, but not always).
        _dnt_address = ''
        if _dnt_raw:
            _dnt_pairs = getaddresses([_dnt_raw])
            _dnt_address = _dnt_pairs[0][1] if _dnt_pairs else ''

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
        # For sent-folder messages the IMAP \Seen flag means the SENDER has viewed
        # their own copy — it has nothing to do with whether the RECIPIENT read it.
        # is_read/read_at on sent messages are driven exclusively by inbox-to-sent
        # propagation (_propagate_read_to_sent_copies) and MDN receipts.
        # Ignoring \Seen here prevents IMAP re-sync from falsely marking sent
        # messages read whenever the sender's mail client opens the Sent folder.
        if folder_key == 'sent':
            is_read = False

        own_email = (self.email_address or '').strip().lower()
        own_username = own_email.split('@')[0] if '@' in own_email else own_email

        # Collect all participant addresses (To + Cc + Bcc headers).
        all_recipient_hdrs = (
            msg.get_all('To', []) + msg.get_all('Cc', []) + msg.get_all('Bcc', [])
        )
        participant_emails = {
            pair[1].strip().lower()
            for pair in getaddresses(all_recipient_hdrs)
            if pair[1]
        }

        # is_mentioned: True ONLY when:
        #   1. The account owner is a participant (in To/Cc/Bcc), AND
        #   2. They are explicitly @-mentioned or referenced by full email in the
        #      COMPOSED body text (not in headers, signature, or quoted reply).
        # Matching is case-insensitive.  Patterns:
        #   a) Full email address  — omar@nooralnibras.com
        #   b) @username           — @omar
        #   c) @full-email         — @omar@nooralnibras.com
        is_mentioned = False
        if own_email and own_email in participant_emails and own_username:
            composed_text = _extract_composed_text(body_text, body_html)
            if composed_text:
                _body_check = composed_text.lower()
                _mention_patterns = [
                    # Full standalone email (not part of a longer token)
                    r'(?<![a-zA-Z0-9._+\-])' + re.escape(own_email) + r'(?![a-zA-Z0-9._+\-@])',
                    # @full-email
                    r'@' + re.escape(own_email),
                    # @username NOT followed by @ (to avoid matching @user as prefix of @user@domain
                    # which is already caught by the @full-email pattern above)
                    r'@' + re.escape(own_username) + r'(?![a-zA-Z0-9._\-@])',
                ]
                for _pat in _mention_patterns:
                    if re.search(_pat, _body_check, re.IGNORECASE):
                        is_mentioned = True
                        break

        # is_important: parse standard priority/importance headers sent by the
        # sender. Check in priority order:
        #   1. Importance: high / normal / low  (RFC 2156 / Outlook)
        #   2. X-Priority: 1 or 2 = high (Outlook, many clients)
        #   3. X-MSMail-Priority: High / Normal / Low (Outlook legacy)
        is_important = False
        _importance_hdr = (msg.get('Importance') or '').strip().lower()
        if _importance_hdr == 'high':
            is_important = True

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

        if not is_important:
            # Some clients/users do not send RFC priority headers but mark the
            # message in the subject itself.  Honour common spellings/typos used
            # in this product flow so "Important from sender" rules still route
            # the message into the Important child folder.
            _subj_l = (subject or '').lower()
            if any(token in _subj_l for token in (
                'important', 'imporant', 'imporatn', 'imporatnt', 'importnat',
            )):
                is_important = True

        if not is_important:
            # Folder context is authoritative: if the message is being imported
            # from an Important child mailbox, keep the DB flag aligned so the
            # Important API does not hide it.
            _folder_tail = (folder_key or '').replace('/', '.').split('.')[-1].lower()
            if _folder_tail == 'important':
                is_important = True

        message_size = len(raw_bytes) if raw_bytes else 0
        has_mime_attachments = False
        try:
            for _part in msg.walk():
                _disp = (_part.get_content_disposition() or '').lower()
                if _part.get_filename() or 'attachment' in _disp:
                    has_mime_attachments = True
                    break
        except Exception:
            has_mime_attachments = False

        # ── written_in_arabic detection ───────────────────────────────────────
        # Primary: honour the X-Written-In-Arabic header set by Lugal at send
        # time so the FE can render the body RTL on the receiving side.
        # Fallback: auto-detect Arabic Unicode characters in the body so emails
        # sent from any client (not just Lugal) are handled correctly.
        _x_arabic = (msg.get('X-Written-In-Arabic') or '').strip().lower()
        if _x_arabic == 'true':
            written_in_arabic = True
        else:
            # Auto-detect: check whether plain-text or HTML body contains at
            # least one Arabic character (U+0600–U+06FF, extended range
            # U+0750–U+077F, and supplement U+FB50–U+FDFF, U+FE70–U+FEFF).
            _arabic_re = re.compile(
                r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]'
            )
            _body_for_detect = body_text or ''
            if not _body_for_detect and body_html:
                # Strip HTML tags for a lightweight text sample
                _body_for_detect = re.sub(r'<[^>]+>', '', body_html)
            written_in_arabic = bool(_arabic_re.search(_body_for_detect))

        # lugal_imap_sync context prevents the create/write overrides from
        # auto-stamping read_at.  read_at must only be set when the user
        # explicitly opens the mail inside the Lugal app.
        Message = self.env['lugal.email.message'].sudo().with_context(lugal_imap_sync=True)

        # ── Subject-based thread linking (fallback) ───────────────────────────
        # Some email clients (mobile apps, certain web mailers) do NOT include
        # References or In-Reply-To headers on reply emails even when the subject
        # carries the "Re:" prefix.  Without this fallback every incoming "Re:"
        # email without headers becomes its own thread root, causing back-and-forth
        # conversations to appear as separate unrelated inbox items.
        #
        # Rule: only activate when:
        #  1. thread_id == message_id  (no parent was found via standard headers)
        #  2. subject starts with a reply/forward prefix ("Re:", "Fwd:", …)
        #  3. a matching message exists in this account with the same normalised subject
        #
        # We look for the OLDEST matching message (order by id asc, limit 1) so
        # all subsequent replies converge on the true root thread_id.
        _REPLY_PREFIXES = re.compile(
            r'^(?:re|fwd?|aw|rif|sv|vs|antw|回复|回覆|答复|返回)[\s:]+',
            re.IGNORECASE,
        )
        if thread_id == (message_id or '') and _REPLY_PREFIXES.match(subject or ''):
            _norm_subj = _REPLY_PREFIXES.sub('', subject or '').strip()
            if _norm_subj:
                try:
                    # Build candidate subject strings for an exact-match search.
                    # We use 'in' (case-sensitive equality in Odoo ORM) rather than
                    # 'ilike' (LIKE '%value%') which was causing substring matches
                    # that merged unrelated historical threads.  We include common
                    # prefix variants to handle both prefixed and bare stored subjects.
                    _subject_candidates = list({
                        _norm_subj,
                        f'Re: {_norm_subj}',
                        f'RE: {_norm_subj}',
                        f're: {_norm_subj}',
                        f'Fwd: {_norm_subj}',
                        f'FWD: {_norm_subj}',
                        f'Fw: {_norm_subj}',
                        f'FW: {_norm_subj}',
                    })

                    # Participant filter: only link to a thread that involves the
                    # sender of the incoming message.  Without this, a reply with a
                    # generic subject ("test", "hello") would link to any old message
                    # with the same subject, even from completely different people.
                    _sender_addr = (from_addr or '').strip().lower()
                    _participant_domain = []
                    if _sender_addr:
                        _participant_domain = [
                            '|',
                            ('from_address', '=ilike', _sender_addr),
                            ('to_addresses', 'ilike', _sender_addr),
                        ]

                    # Recency filter: only link to messages from the last 90 days.
                    # A reply with no headers is almost certainly to a recent email.
                    # Without this, old unrelated threads with identical subjects
                    # (e.g. recurring "Weekly Update" emails) get merged forever.
                    from datetime import timedelta as _timedelta
                    _cutoff = fields.Datetime.now() - _timedelta(days=90)
                    _recency_domain = [('date', '>=', _cutoff)]

                    # Step 1: prefer an existing message that already has a thread_id.
                    _root = Message.search([
                        ('account_id', '=', self.id),
                        ('subject',    'in', _subject_candidates),
                        ('is_deleted', '=', False),
                        ('thread_id',  '!=', False),
                    ] + _participant_domain + _recency_domain, order='id asc', limit=1)

                    # Fallback 1a: participant match but any age (older conversation)
                    if not _root and _participant_domain:
                        _root = Message.search([
                            ('account_id', '=', self.id),
                            ('subject',    'in', _subject_candidates),
                            ('is_deleted', '=', False),
                            ('thread_id',  '!=', False),
                        ] + _participant_domain, order='id asc', limit=1)

                    if _root and _root.thread_id != (message_id or ''):
                        thread_id = _root.thread_id
                    else:
                        # Step 2: no message with thread_id yet — find the earliest
                        # matching message (by participant + subject) and bootstrap.
                        _any = Message.search([
                            ('account_id', '=', self.id),
                            ('subject',    'in', _subject_candidates),
                            ('is_deleted', '=', False),
                        ] + _participant_domain + _recency_domain, order='id asc', limit=1)

                        # Fallback 2a: any age, same participant
                        if not _any and _participant_domain:
                            _any = Message.search([
                                ('account_id', '=', self.id),
                                ('subject',    'in', _subject_candidates),
                                ('is_deleted', '=', False),
                            ] + _participant_domain, order='id asc', limit=1)

                        if _any and _any.id:
                            _root_tid = (_any.message_id or '').strip() or f'<local.thread.{_any.id}@lugalai>'
                            if _root_tid != (message_id or ''):
                                if not _any.thread_id:
                                    try:
                                        _any.write({'thread_id': _root_tid})
                                    except Exception:
                                        pass
                                thread_id = _root_tid

                    if thread_id != (message_id or ''):
                        _logger.debug(
                            'subject-thread-link: msg_id=%s subject=%r sender=%s → thread_id=%s',
                            message_id, _norm_subj, _sender_addr, thread_id,
                        )
                except Exception:
                    pass  # never fail message import due to thread-link search error

        # Search by imap_uid first; also check message_id as a secondary key so
        # we never store the same RFC-2822 message twice even if the UID changed.
        lock_identity = message_id or f'{folder_key}:{uid_int}'
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    'SELECT pg_advisory_xact_lock(%s)',
                    [_pg_advisory_lock_key('lugal.email.message.upsert', self.id, lock_identity)],
                )
        except Exception:
            _logger.debug(
                '_upsert_inbox_message: advisory lock failed account=%s identity=%s',
                self.id, lock_identity, exc_info=True,
            )

        domain = [('account_id', '=', self.id), ('folder', '=', folder_key), ('imap_uid', '=', uid_int)]
        existing = Message.search(domain, limit=1)
        existing_found_by_uid = bool(existing)
        existing_found_by_message_id_only = False
        if not existing and message_id:
            existing = Message.search(
                [
                    ('account_id', '=', self.id),
                    ('folder', '=', folder_key),
                    ('message_id', '=', message_id),
                ],
                limit=1,
            )
        if not existing and message_id:
            existing = Message.search(
                [('account_id', '=', self.id), ('message_id', '=', message_id)],
                limit=1,
            )
            existing_found_by_message_id_only = bool(existing)
        vals = {
            'account_id':           self.id,
            'folder':               folder_key,
            'imap_uid':             uid_int,
            'subject':              subject or '(no subject)',
            'from_name':            from_name or '',
            'from_address':         from_addr or '',
            'to_addresses':         json.dumps(to_list),
            'cc_addresses':         json.dumps(cc_list),
            'bcc_addresses':        json.dumps(bcc_list),
            'reply_to':             reply_to_addr or False,
            'message_id':           message_id,
            'in_reply_to':          in_reply_to_hdr or False,
            'references':           references_raw or False,
            'thread_id':            thread_id or False,
            'date':                 dt,
            'is_read':              is_read,
            'is_deleted':           False,
            'active':               True,
            'is_mentioned':         is_mentioned,
            'is_important':         is_important,
            'message_size':         message_size,
            # True when the sender included Disposition-Notification-To.
            # The mark-read endpoints use this to send an MDN back.
            'request_read_receipt': _incoming_request_receipt,
            # Propagated via X-Written-In-Arabic header (Lugal → Lugal)
            # or auto-detected from Arabic Unicode characters in the body.
            'written_in_arabic':    written_in_arabic,
        }
        if headers_only:
            if not existing:
                vals['body_text']     = ''
                vals['body_html']     = False
                vals['body_fetched']  = False
        else:
            vals['body_text']    = body_text
            vals['body_html']    = body_html or False
            vals['body_fetched'] = True

        # read_at is intentionally NOT set here, even when the message arrives
        # already \Seen on the IMAP server.  read_at must only be stamped when
        # the user explicitly opens or marks the email read inside the Lugal app
        # (via GET /messages/<id> in CRM, POST /messages/<id>/read, or PATCH).
        # Setting it to the IMAP message date (delivery time) or to the sync
        # timestamp gives a misleading "when you read it" value.
        # The lugal_imap_sync context on the Message env above also prevents the
        # model's create/write overrides from auto-stamping read_at.

        created_new = False

        if existing:
            existing_identity_changed = bool(
                existing_found_by_uid
                and message_id
                and existing.message_id
                and existing.message_id != message_id
            )

            if existing_identity_changed:
                # Some custom folders have stale DB rows whose IMAP UID now
                # points at a different RFC message.  Treat this as a new
                # message occupying the old row: do not inherit read/body/thread
                # state from the previous occupant.
                vals['read_at'] = dt if is_read else False
                if headers_only:
                    vals['body_text'] = ''
                    vals['body_html'] = False
                    vals['body_fetched'] = False

            # Merge historical duplicates for the same RFC Message-ID.  Older
            # versions could create one row from source INBOX and another from a
            # custom-folder sync.  The custom-folder UID-holder is the row that
            # should survive, but it must inherit read/important state from the
            # duplicate so unread badges do not resurrect after reload.
            if message_id and not existing_identity_changed:
                _dupes = Message.search([
                    ('account_id', '=', self.id),
                    ('message_id', '=', message_id),
                    ('id', '!=', existing.id),
                    ('is_deleted', '=', False),
                ])
                if _dupes:
                    _read_dupe = _dupes.filtered(lambda d: d.is_read or d.read_at)[:1]
                    if _read_dupe:
                        vals['is_read'] = True
                        vals['read_at'] = _read_dupe.read_at or fields.Datetime.now()
                    if any(_dupes.mapped('is_important')):
                        vals['is_important'] = True
                    if not vals.get('thread_id'):
                        _thread_dupe = _dupes.filtered(lambda d: bool(d.thread_id))[:1]
                        if _thread_dupe:
                            vals['thread_id'] = _thread_dupe.thread_id
                    try:
                        # Do not clear imap_uid through ORM.  Integer False is
                        # written as 0 in this Odoo version, which can collide
                        # with the unique (account_id, imap_uid, folder) index.
                        _dupes.write({'is_deleted': True, 'active': False})
                    except Exception:
                        _logger.warning(
                            '_upsert_inbox_message: duplicate merge cleanup failed '
                            'account=%s message_id=%s',
                            self.id, message_id, exc_info=True,
                        )

            # Never downgrade a fully-fetched body to headers-only.
            if headers_only and existing.body_fetched:
                vals.pop('body_text', None)
                vals.pop('body_html', None)
                vals.pop('body_fetched', None)

            # Protect is_read from the async-flag-push race condition.
            # Scenario: user marks message read in Odoo → DB is_read=True →
            # _imap_store_async pushes +\Seen to IMAP in background → next
            # sync runs before the push completes → IMAP still reports
            # \Seen=False → without this guard, sync would write is_read=False,
            # erasing the user's action.
            # Rule: NEVER downgrade is_read from True (DB) to False (IMAP).
            # Upgrading False→True (user read in webmail) is always allowed.
            stale_read_marker = bool(
                existing.read_at
                and dt
                and existing.read_at < dt
            )
            if (
                not existing_identity_changed
                and not stale_read_marker
                and not is_read
                and existing.is_read
            ):
                vals.pop('is_read', None)
                # Keep existing read_at as well — don't nullify it.
                vals.pop('read_at', None)
            elif stale_read_marker and not is_read:
                vals['read_at'] = False

            # Never wipe a thread_id that was already bootstrapped (e.g. by
            # the SMTP async write-back) with a None from a subject-fallback
            # race where the new message hasn't been matched yet.
            if not existing_identity_changed and not vals.get('thread_id') and existing.thread_id:
                vals.pop('thread_id', None)

            # Don't downgrade request_read_receipt from True to False on
            # re-sync (e.g. a sent record set True by the send endpoint, but
            # the Sent folder IMAP copy was imported before the fix landed).
            if (
                not existing_identity_changed
                and not vals.get('request_read_receipt')
                and existing.request_read_receipt
            ):
                vals.pop('request_read_receipt', None)

            # Guard the DB unique constraint (account_id, imap_uid, folder).
            # Historical duplicate rows can share Message-ID but have older UIDs
            # from previous custom-folder sync bugs.  If assigning this UID to
            # the selected row would collide, update the UID-holder instead and
            # soft-delete the stale duplicate.
            uid_for_write = vals.get('imap_uid')
            folder_for_write = vals.get('folder') or existing.folder
            if uid_for_write and folder_for_write:
                _uid_holder = Message.with_context(active_test=False).search([
                    ('account_id', '=', self.id),
                    ('folder', '=', folder_for_write),
                    ('imap_uid', '=', uid_for_write),
                    ('id', '!=', existing.id),
                ], limit=1)
                if _uid_holder:
                    try:
                        # Do not clear imap_uid through ORM; Integer False is
                        # stored as 0 and can violate the unique UID constraint.
                        existing.write({'is_deleted': True, 'active': False})
                    except Exception:
                        pass
                    existing = _uid_holder

            # If a rule already moved a message to a custom folder in the DB but
            # the source INBOX still contains the server copy until async UID MOVE
            # completes, do not let a later INBOX sync move the DB row back to
            # inbox or replace the destination folder's UID with the source UID.
            if (
                existing_found_by_message_id_only
                and (existing.folder or '') != folder_key
                and (folder_key or '').lower() == 'inbox'
                and (existing.folder or '').lower() != 'inbox'
            ):
                vals.pop('folder', None)
                vals.pop('imap_uid', None)

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
                        [
                            ('account_id', '=', self.id),
                            ('folder', '=', folder_key),
                            ('message_id', '=', message_id),
                        ],
                        limit=1,
                    )
                if not stored_msg and message_id:
                    stored_msg = Message.search(
                        [('account_id', '=', self.id), ('message_id', '=', message_id)],
                        limit=1,
                    )

                if stored_msg:
                    # Another thread won the race — just update.
                    if not (headers_only and stored_msg.body_fetched):
                        write_vals = dict(vals)
                        if (
                            (stored_msg.folder or '') != folder_key
                            and (folder_key or '').lower() == 'inbox'
                            and (stored_msg.folder or '').lower() != 'inbox'
                        ):
                            write_vals.pop('folder', None)
                            write_vals.pop('imap_uid', None)
                        stored_msg.write(write_vals)
                else:
                    # We are the first — create, using a SAVEPOINT so a concurrent
                    # INSERT at the DB level (unlikely but possible) rolls back
                    # only the inner block and leaves the cursor usable.
                    try:
                        with self.env.cr.savepoint():
                            stored_msg = Message.with_context(
                                lugal_email_defer_new_message_ws=True,
                            ).create(vals)
                            created_new = True
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
                            write_vals = dict(vals)
                            if (
                                (stored_msg.folder or '') != folder_key
                                and (folder_key or '').lower() == 'inbox'
                                and (stored_msg.folder or '').lower() != 'inbox'
                            ):
                                write_vals.pop('folder', None)
                                write_vals.pop('imap_uid', None)
                            stored_msg.write(write_vals)

        if not headers_only:
            self._store_imap_attachments(stored_msg, msg)

        if stored_msg and created_new and run_rules:
            try:
                rule_vals = dict(vals, has_attachments=has_mime_attachments)
                self.env['lugal.email.rule'].sudo().apply_inbox_rules(stored_msg, rule_vals)
            except Exception as _re:
                _logger.warning('Inbox rule execution failed for msg %s: %s', stored_msg.id, _re)

        if stored_msg and created_new:
            try:
                notifier = getattr(stored_msg.sudo(), '_lugal_send_new_email_notification', None)
                if callable(notifier):
                    notifier()
            except Exception:
                _logger.debug(
                    '_upsert_inbox_message: deferred realtime notification failed msg=%s',
                    stored_msg.id, exc_info=True,
                )

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
            sent_folder = self._get_server_folder_name('sent', existing_conn=conn)
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
                cache_key = f'lugal.email.folder.{self.id}.sent'
                self.env['ir.config_parameter'].sudo().set_param(cache_key, '')
                try:
                    sent_folder = self._get_server_folder_name('sent', existing_conn=conn)
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

                    domain = [('account_id', '=', self.id), ('folder', '=', 'sent')]
                    if message_id:
                        domain.append(('message_id', '=', message_id))
                    else:
                        domain += [('subject', '=', subject or '(no subject)'), ('date', '=', dt)]

                    # Detect written_in_arabic from X-Written-In-Arabic header
                    _x_arabic_sent = (msg.get('X-Written-In-Arabic') or '').strip().lower()
                    _sent_written_in_arabic = (_x_arabic_sent == 'true')

                    if not Msg.search_count(domain):
                        Msg.create({
                            'account_id':        self.id,
                            'folder':            'sent',
                            'imap_uid':          uid_int,
                            'subject':           subject or '(no subject)',
                            'from_name':         from_name or '',
                            'from_address':      from_addr or '',
                            'to_addresses':      _json.dumps(to_list),
                            'cc_addresses':      _json.dumps(cc_list),
                            'message_id':        message_id or False,
                            'date':              dt,
                            'is_read':           True,
                            'smtp_delivered':    True,
                            'body_fetched':      False,
                            'written_in_arabic': _sent_written_in_arabic,
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
        """Import INBOX and Sent folder messages over IMAP.

        Strategy:
          • First import (max_uid_cursor == 0): headers-only tail fetch of the
            last SYNC_MAX_MESSAGES messages — avoids downloading MBs of body data
            for hundreds of old emails on first run.
          • Incremental (max_uid_cursor > 0): UID SEARCH for new UIDs, full body
            fetch for each (typically 1-10 messages, so fast).
          • Sent folder is synced on the same connection after INBOX.
        """
        self.ensure_one()
        Msg = self.env['lugal.email.message'].sudo()
        if not (self.password or '').strip():
            self.write({'sync_status': 'error', 'sync_error_msg': 'Missing app password on email account'})
            return {'sync_status': 'error', 'message': 'Missing app password on email account'}

        # Cross-process guard: HTTP reconnects, notifications polling, cron, and
        # the poll watcher can all request a sync at the same time after a long
        # idle period or service restart.  Only one worker should talk to IMAP
        # and update lugal.email.account state for this mailbox at a time.
        try:
            self.env.cr.execute(
                'SELECT pg_try_advisory_xact_lock(%s)',
                [_pg_advisory_lock_key('lugal.email.account.action_sync', self.id)],
            )
            if not bool((self.env.cr.fetchone() or [False])[0]):
                _logger.info(
                    'action_sync: account %s skipped because another worker is syncing it',
                    self.id,
                )
                return {
                    'sync_status': self.sync_status or 'syncing',
                    'skipped': True,
                    'reason': 'already_syncing',
                }
        except Exception:
            _logger.debug(
                'action_sync: advisory lock failed account=%s; continuing without lock',
                self.id,
                exc_info=True,
            )

        if not Msg.search_count([
            ('account_id', '=', self.id), ('folder', '=', 'inbox'), ('is_deleted', '=', False),
        ]):
            self.imap_inbox_max_uid = 0

        try:
            import imaplib
            with self._imap_session() as conn:
                typ, data = conn.select('INBOX', readonly=True)
                if typ != 'OK' or not data:
                    raise imaplib.IMAP4.error('INBOX select failed')
                num_msgs = int(data[0])
                max_uid_cursor = self.imap_inbox_max_uid or 0
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

                imported = 0
                max_seen = max_uid_cursor

                def _upsert_batch(items, min_uid=0, headers_only=False):
                    nonlocal imported, max_seen
                    for uid_val, raw, flags_meta in items:
                        if uid_val <= min_uid:
                            continue
                        try:
                            with self.env.cr.savepoint():
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
                        uid_set = ','.join(str(u) for u in todo)
                        typ, data_list = conn.uid('fetch', uid_set, BODY_FETCH)
                        if typ == 'OK' and data_list:
                            _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=False)

                try:
                    self._sync_sent_folder(conn)
                except Exception:
                    _logger.warning('Sent folder sync failed for acc=%s', self.id, exc_info=True)

            # Count unread across inbound folders (inbox + custom user folders).
            # Exclude outbound/system folders so this cache matches notifications,
            # folder badges, and account DTOs.
            unread = Msg.search_count([
                ('account_id', '=', self.id),
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])

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
            try:
                with self.env.cr.savepoint():
                    self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            except Exception:
                pass
            _logger.exception('action_sync failed for account %s', self.id)
            return {'sync_status': 'error', 'message': str(exc)}

    def sync_custom_imap_folder(self, imap_folder_path, headers_only=True):
        """Import messages from a single non-standard IMAP folder into Odoo.

        action_sync only pulls INBOX + Sent. User-created rule destinations
        (e.g. INBOX.syed_naqvi.Important) must be imported here so
        GET .../sync?folder=... returns rows.
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
        diag = None
        try:
            import imaplib
            with self._imap_session() as conn:
                typ, data = conn.select(path, readonly=True)
                if typ != 'OK' or not data:
                    return {'imported': 0, 'error': f'select failed typ={typ!r} path={path!r}', 'resolved_path': path}

                uid_re = re.compile(br'UID\s+(\d+)')

                def _parse_batch_fetch(data_list):
                    parsed = []
                    if not data_list:
                        return parsed
                    for item in data_list:
                        if not isinstance(item, tuple) or len(item) < 2:
                            continue
                        meta, payload = item[0], item[1]
                        if not isinstance(meta, bytes):
                            continue
                        if isinstance(payload, str):
                            payload = payload.encode('utf-8', errors='replace')
                        if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                            continue
                        m = uid_re.search(meta)
                        if m:
                            parsed.append((int(m.group(1)), bytes(payload), meta))
                    return parsed

                HEADERS_FETCH = (
                    '(UID FLAGS BODY.PEEK[HEADER.FIELDS '
                    '(FROM TO CC BCC REPLY-TO DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
                )
                FULL_HDR_FETCH = '(UID FLAGS BODY.PEEK[HEADER])'

                typ_s, d_s = conn.uid('search', None, 'ALL')
                uids = []
                raw_search = b''
                if typ_s == 'OK' and d_s and d_s[0] is not None:
                    raw_search = d_s[0] if isinstance(d_s[0], (bytes, bytearray)) else str(d_s[0]).encode()
                    parts = raw_search.split()
                    uids = sorted(int(x) for x in parts if x.isdigit())

                diag = {
                    'uid_search_typ': typ_s,
                    'uid_count':      len(uids),
                }

                if not uids:
                    return {
                        'imported':      0,
                        'error':         None,
                        'resolved_path': path,
                        'note':          'mailbox_empty_or_uid_search_empty',
                        'diagnostics':   diag,
                    }

                tail = uids[-SYNC_MAX_MESSAGES:]
                diag['fetch_uid_min'] = tail[0] if tail else None
                diag['fetch_uid_max'] = tail[-1] if tail else None

                def _do_fetch(uid_chunk, fetch_macro):
                    nonlocal imported
                    uid_csv = ','.join(str(u) for u in uid_chunk)
                    typ_f, data_list = conn.uid('fetch', uid_csv, fetch_macro)
                    diag.setdefault('fetch_typs', []).append(typ_f)
                    if typ_f != 'OK' or not data_list:
                        return 0
                    parsed = _parse_batch_fetch(data_list)
                    diag.setdefault('parsed_per_fetch', []).append(len(parsed))
                    n = 0
                    for uid_val, raw, flags_meta in parsed:
                        try:
                            with self.env.cr.savepoint():
                                self._upsert_inbox_message(
                                    uid_val, raw, flags_meta,
                                    headers_only=headers_only,
                                    folder_key=path,
                                    run_rules=False,
                                )
                            n += 1
                        except Exception:
                            _logger.warning(
                                'custom folder upsert failed uid=%s folder=%s acc=%s',
                                uid_val, path, self.id, exc_info=True,
                            )
                    imported += n
                    return n

                _BATCH = 45
                for i in range(0, len(tail), _BATCH):
                    _do_fetch(tail[i:i + _BATCH], HEADERS_FETCH)

                if imported == 0 and tail:
                    for i in range(0, len(tail), _BATCH):
                        _do_fetch(tail[i:i + _BATCH], FULL_HDR_FETCH)

                if imported == 0 and tail:
                    diag['note'] = 'uid_search_ok_but_fetch_or_upsert_yielded_zero'

        except Exception as exc:
            _logger.warning('sync_custom_imap_folder acc=%s path=%s: %s', self.id, path, exc)
            ret = {'imported': imported, 'error': str(exc), 'resolved_path': path}
            if diag is not None:
                ret['diagnostics'] = diag
            return ret
        ret = {'imported': imported, 'error': None, 'resolved_path': path}
        if diag is not None:
            ret['diagnostics'] = diag
        return ret

    def _imap_list_all_mailbox_names(self):
        """Return every mailbox path from IMAP LIST (raw server strings)."""
        self.ensure_one()
        try:
            with self._imap_session() as conn:
                typ, raw_list = conn.list()
            if typ != 'OK' or not raw_list:
                return []
            lr = re.compile(
                r'^\((?P<flags>[^)]*)\)\s+'
                r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                r'(?P<name>.+?)\s*$'
            )
            names = []
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = lr.match(line.strip())
                if not m:
                    continue
                name = m.group('name').strip().strip('"')
                if name:
                    names.append(name)
            return names
        except Exception:
            _logger.warning('_imap_list_all_mailbox_names failed acc=%s', self.id, exc_info=True)
            return []

    def imap_child_mailboxes(self, parent_path):
        """Return full IMAP paths of mailboxes directly under parent_path."""
        self.ensure_one()
        parent = self._resolve_imap_mailbox_path((parent_path or '').strip())
        if not parent:
            return []
        pl = parent.lower()
        all_names = self._imap_list_all_mailbox_names()
        out = []
        for n in all_names:
            nl = n.lower()
            if nl == pl:
                continue
            if nl.startswith(pl + '.') or n.startswith(parent + '/'):
                out.append(n)
        return sorted(set(out))

    def sync_imap_branch_mailboxes(self, parent_path, max_children=40):
        """Run sync_custom_imap_folder on parent_path and every child mailbox."""
        self.ensure_one()
        parent = self._resolve_imap_mailbox_path((parent_path or '').strip())
        children = self.imap_child_mailboxes(parent)
        detail = []
        total = 0
        pr = self.sync_custom_imap_folder(parent)
        total += int(pr.get('imported') or 0)
        detail.append({'path': parent, **pr})
        for ch in children[:max_children]:
            r = self.sync_custom_imap_folder(ch)
            total += int(r.get('imported') or 0)
            detail.append({'path': ch, **r})
        return {
            'parent_resolved': parent,
            'children':        children,
            'imported_total':  total,
            'per_mailbox':     detail,
        }

    def _resolve_imap_mailbox_path(self, requested_path: str) -> str:
        """Return the server's exact mailbox name for a path (corrects casing)."""
        req = (requested_path or '').strip()
        if not req:
            return req
        _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        if req.lower() in _LOGICAL:
            return req
        try:
            with self._imap_session() as conn:
                typ, raw_list = conn.list()
            if typ != 'OK' or not raw_list:
                return req
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
        """Background cron entry-point. Syncs INBOX for every active account."""
        accounts = self.search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])
        synced_creds: set = set()
        for acc in accounts:
            if not (acc.password or '').strip():
                if acc.sync_status not in ('never',):
                    try:
                        with self.env.cr.savepoint():
                            acc.write({'sync_status': 'never', 'sync_error_msg': False})
                    except Exception:
                        pass
                continue
            cred = (
                (acc.imap_host or '').strip().lower(),
                int(acc.imap_port or (993 if acc.imap_use_ssl else 143)),
                (acc.username or acc.email_address or '').strip().lower(),
            )
            if cred in synced_creds:
                continue
            synced_creds.add(cred)
            try:
                acc.action_sync()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception('Cron IMAP sync failed for account %s (%s)', acc.id, acc.email_address)

    def _store_imap_attachments(self, msg_record, email_msg):
        """Extract MIME attachments from a parsed email and store as ir.attachment."""
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
            disposition = part.get_content_disposition() or ''
            filename = part.get_filename()

            # Extract Content-ID early — needed for inline-without-filename handling.
            raw_cid = part.get('Content-ID') or ''
            cid_value = raw_cid.strip('<> ')

            # Skip non-attachment, non-inline parts that also have no filename.
            if not filename and 'attachment' not in disposition and 'inline' not in disposition:
                continue

            # Some senders (mobile apps, certain webmail clients) emit inline images
            # with a Content-ID and Content-Disposition: inline but WITHOUT an
            # explicit filename parameter.  Synthesise a filename from the MIME type
            # so the image is stored and served correctly.
            if not filename and 'inline' in disposition and cid_value:
                _mime_type = part.get_content_type().lower()
                _ext_map = {
                    'image/jpeg': 'jpg', 'image/jpg': 'jpg',
                    'image/png': 'png', 'image/gif': 'gif',
                    'image/webp': 'webp', 'image/svg+xml': 'svg',
                    'image/bmp': 'bmp', 'image/tiff': 'tiff',
                }
                _ext = _ext_map.get(_mime_type, 'bin')
                filename = f'inline_{cid_value[:12]}.{_ext}'

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
        """Fetch the full body of a single message from IMAP on demand."""
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
            with self._imap_session() as conn:
                _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
                raw_folder = msg.folder or 'inbox'
                if raw_folder == 'inbox':
                    folder = 'INBOX'
                elif raw_folder in _LOGICAL:
                    try:
                        folder = self._get_server_folder_name(raw_folder, existing_conn=conn)
                    except Exception:
                        folder = raw_folder.capitalize()
                else:
                    folder = raw_folder
                typ, _ = conn.select(folder, readonly=True)
                if typ != 'OK':
                    return msg
                typ, data_list = conn.uid('fetch', str(msg.imap_uid), '(FLAGS BODY.PEEK[])')
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
                    self._store_imap_attachments(msg, email_msg)
                    return msg
        except Exception:
            _logger.exception('fetch_message_body failed for msg=%s account=%s', message_id, self.id)
        return msg
# TODO: remove - cherry-pick marker

end of file email_account.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of email_idle_watcher.py
email_idle_watcher.py

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
_OWNER_HEARTBEAT_PARAM = 'lugal.idle.supervisor.heartbeat'
_OWNER_STALE_SECS = 90

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


def _heartbeat_is_fresh(value) -> bool:
    """True when the poll owner heartbeat was updated recently."""
    try:
        return (time.time() - float(value or 0)) <= _OWNER_STALE_SECS
    except (TypeError, ValueError):
        return False


def _write_owner_heartbeat(cr):
    """Persist an owner heartbeat so another worker can recover stale ownership."""
    now = str(time.time())
    cr.execute(
        """
        INSERT INTO ir_config_parameter (key, value)
        VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """,
        (_OWNER_HEARTBEAT_PARAM, now),
    )


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
        try:
            from odoo.modules.registry import Registry as _Registry
            with _Registry(db_name).cursor() as cr:
                _write_owner_heartbeat(cr)
                cr.commit()
        except Exception:
            pass
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
                _write_owner_heartbeat(cr)
            except Exception:
                pass

        if not _I_AM_OWNER:
            cr = self.env.cr
            claimed = False
            try:
                with cr.savepoint():
                    cr.execute(
                        "SELECT key, value FROM ir_config_parameter "
                        "WHERE key IN %s FOR UPDATE NOWAIT",
                        ((tuple([_OWNER_PARAM, _OWNER_HEARTBEAT_PARAM])),),
                    )
                    rows = dict(cr.fetchall())
                    row = (_OWNER_PARAM, rows.get(_OWNER_PARAM)) if _OWNER_PARAM in rows else None
                    stored = (rows.get(_OWNER_PARAM) or '')
                    heartbeat = rows.get(_OWNER_HEARTBEAT_PARAM)
                    if stored:
                        try:
                            owner_pid = int(stored)
                            owner_alive = _pid_alive(owner_pid)
                            heartbeat_fresh = _heartbeat_is_fresh(heartbeat)
                            if owner_alive and owner_pid != my_pid and heartbeat_fresh:
                                _logger.debug(
                                    'Poll supervisor: pid=%d owns threads — '
                                    'this worker (pid=%d) skips',
                                    owner_pid, my_pid,
                                )
                                return 0
                            if owner_alive and owner_pid != my_pid and not heartbeat_fresh:
                                _logger.warning(
                                    'Poll supervisor: stealing stale owner pid=%d '
                                    '(heartbeat older than %ss)',
                                    owner_pid, _OWNER_STALE_SECS,
                                )
                        except (ValueError, TypeError):
                            pass
                    # Claim ownership while still holding the row lock.
                    cr.execute(
                        """
                        INSERT INTO ir_config_parameter (key, value)
                        VALUES (%s, %s)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                        """,
                        (_OWNER_PARAM, str(my_pid)),
                    )
                    _write_owner_heartbeat(cr)
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
# TODO: remove - cherry-pick marker

end of file email_idle_watcher.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of email_rule.py
email_rule.py

# -*- coding: utf-8 -*-
# Component: Lugal Email — lugal.email.rule model (email_rule.py)
"""
lugal.email.rule  — per-user / per-account inbox rules.

A rule has:
  • A set of conditions  (evaluated AND or OR)
  • A list of ordered actions applied when all conditions match
  • Optional stop-processing flag

Conditions JSON schema (list):
  [{"field": "from_address", "operator": "contains", "value": "boss@"}, ...]

  Supported fields:    from_address | to_addresses | cc_addresses | bcc_addresses
                       | subject | body_text
                       has_attachments | is_important | folder
  Supported operators: contains | not_contains | starts_with | ends_with
                       equals | not_equals | is_empty | is_not_empty

Actions JSON schema (list, executed in order):
  [{"action": "move_folder", "value": "archive"}, ...]

  Supported actions:
    mark_read          — set is_read = True
    mark_important     — set is_important = True
    mark_unimportant   — set is_important = False
    mark_starred       — set is_starred = True
    move_folder        — value = folder name (logical or IMAP path)
    forward_to         — value = email address (sends a copy via SMTP)
    stop_processing    — no more rules processed for this message
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Folders that are valid sources for inbox rule execution.
# Rules only fire when a message arrives in one of these folders.
# This prevents rules from re-firing on messages that were already
# moved to a custom folder (e.g. by a previous rule application).
_RULE_SOURCE_FOLDERS = {'inbox'}


class LugalEmailRule(models.Model):
    _name        = 'lugal.email.rule'
    _description = 'Email Inbox Rule'
    _order       = 'sequence asc, id asc'

    name       = fields.Char(string='Rule Name', required=True)
    user_id    = fields.Many2one('res.users', string='Owner', required=True,
                                 default=lambda self: self.env.user, ondelete='cascade', index=True)
    account_id = fields.Many2one('lugal.email.account', string='Account (optional)',
                                 ondelete='cascade', index=True,
                                 help='Leave blank to apply to all accounts of the user.')
    is_active  = fields.Boolean(string='Active', default=True, index=True)
    sequence   = fields.Integer(string='Priority', default=10)

    # "all" = AND logic;  "any" = OR logic across conditions
    match_mode = fields.Selection([
        ('all', 'All conditions match (AND)'),
        ('any', 'Any condition matches (OR)'),
    ], string='Match Mode', default='all', required=True)

    conditions_json = fields.Text(
        string='Conditions (JSON)', default='[]',
        help='List of {field, operator, value} dicts.',
    )
    actions_json = fields.Text(
        string='Actions (JSON)', default='[]',
        help='Ordered list of {action, value} dicts.',
    )
    stop_processing = fields.Boolean(
        string='Stop processing further rules', default=False,
    )

    # Audit
    last_triggered_at = fields.Datetime(string='Last Triggered', readonly=True)
    trigger_count     = fields.Integer(string='Times Triggered', default=0, readonly=True)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @api.model
    def _message_has_attachments(self, msg_record=None, msg_vals=None) -> bool:
        """Return whether a message has stored or MIME-detected attachments.

        Attachment rules are evaluated in two places:
        - live IMAP import, where attachments may only exist in the parsed MIME
          payload at rule-evaluation time;
        - retroactive apply-all/template flows, where attachments are already
          stored as ir.attachment rows.
        """
        msg_vals = msg_vals or {}
        raw = msg_vals.get('has_attachments')
        if isinstance(raw, bool) and raw:
            return True
        if isinstance(raw, str) and raw.strip().lower() in ('1', 'true', 'yes', 'on'):
            return True
        if msg_record and msg_record.exists():
            return bool(self.env['ir.attachment'].sudo().search_count([
                ('res_model', '=', 'lugal.email.message'),
                ('res_id', '=', msg_record.id),
            ]))
        return False

    def _get_conditions(self):
        try:
            return json.loads(self.conditions_json or '[]') or []
        except Exception:
            return []

    def _get_actions(self):
        try:
            return json.loads(self.actions_json or '[]') or []
        except Exception:
            return []

    # ── Condition evaluation ────────────────────────────────────────────────────

    @staticmethod
    def _eval_condition(cond, msg_vals: dict) -> bool:
        field    = cond.get('field', '')
        operator = cond.get('operator', 'contains')
        value    = str(cond.get('value', '')).lower()

        raw = msg_vals.get(field, '')

        # Boolean-like fields (msg_vals may use real bools or legacy strings)
        if field in ('has_attachments', 'is_important', 'is_read', 'is_starred'):
            if isinstance(raw, bool):
                raw_bool = raw
            else:
                s = str(raw).lower().strip()
                raw_bool = s in ('true', '1', 'yes', 'on')
            if operator == 'equals':
                return raw_bool == (value in ('true', '1', 'yes'))
            if operator == 'not_equals':
                return raw_bool != (value in ('true', '1', 'yes'))
            return False

        raw_str = str(raw).lower() if raw else ''

        if operator == 'contains':
            if value in raw_str:
                return True
            # from_address may be "Name <addr@host>"; match on parsed addr too
            if field == 'from_address' and '@' in value:
                try:
                    from email.utils import parseaddr
                    _, addr = parseaddr(str(raw or ''))
                    if addr and value in addr.lower():
                        return True
                except Exception:
                    pass
            return False
        if operator == 'not_contains':
            return value not in raw_str
        if operator == 'starts_with':
            return raw_str.startswith(value)
        if operator == 'ends_with':
            return raw_str.endswith(value)
        if operator == 'equals':
            return raw_str == value
        if operator == 'not_equals':
            return raw_str != value
        if operator == 'is_empty':
            return not raw_str
        if operator == 'is_not_empty':
            return bool(raw_str)
        return False

    def _matches(self, msg_vals: dict) -> bool:
        conds = self._get_conditions()
        if not conds:
            return True
        results = [self._eval_condition(c, msg_vals) for c in conds]
        if self.match_mode == 'any':
            return any(results)
        return all(results)

    # ── Action execution ────────────────────────────────────────────────────────

    def _apply_actions(self, msg_record):
        """Apply this rule's actions to a lugal.email.message record.

        Returns True if stop_processing should halt further rules.
        """
        write_vals = {}
        stop       = self.stop_processing
        _imap_moves = []   # list of (kind, imap_uid, from_imap_path, dest)

        LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

        for act in self._get_actions():
            action = act.get('action', '')
            value  = (act.get('value') or '').strip()
            try:
                if action == 'mark_read':
                    write_vals['is_read'] = True
                elif action == 'mark_important':
                    write_vals['is_important'] = True
                elif action == 'mark_unimportant':
                    write_vals['is_important'] = False
                elif action == 'mark_starred':
                    write_vals['is_starred'] = True
                elif action == 'move_folder':
                    if not value:
                        continue
                    if value.replace('/', '.').split('.')[-1].lower() == 'important':
                        # Folder semantics are authoritative.  Anything routed
                        # into an Important child folder must remain visible in
                        # that folder's API, which filters on is_important.
                        write_vals['is_important'] = True
                    if value.lower() in LOGICAL:
                        write_vals['folder'] = value.lower()
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            cur = msg_record.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                from_imap = 'INBOX'
                            elif cur.lower() in LOGICAL:
                                from_imap = acc._get_server_folder_name(cur.lower())
                            else:
                                from_imap = cur
                            _imap_moves.append(('logical', msg_record.imap_uid, from_imap, value.lower()))
                    else:
                        # Custom IMAP path — store raw path in folder field
                        write_vals['folder'] = value
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            cur = msg_record.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                from_imap = 'INBOX'
                            elif cur.lower() in LOGICAL:
                                try:
                                    from_imap = acc._get_server_folder_name(cur.lower())
                                except Exception:
                                    from_imap = 'INBOX'
                            else:
                                from_imap = cur
                            _imap_moves.append(('raw', msg_record.imap_uid, from_imap, value))
                elif action == 'stop_processing':
                    stop = True
            except Exception as _e:
                _logger.warning('Email rule action %r failed: %s', action, _e)

        if write_vals:
            try:
                msg_record.write(write_vals)
                if msg_record.account_id and (
                    'folder' in write_vals or 'is_read' in write_vals
                ):
                    unread_count = self.env['lugal.email.message'].sudo().search_count([
                        ('account_id', '=', msg_record.account_id.id),
                        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ])
                    msg_record.account_id.sudo().write({'unread_count': unread_count})
            except Exception as _e:
                _logger.warning('Email rule write failed: %s', _e)

        # Fire IMAP moves after the DB write
        for move in _imap_moves:
            try:
                kind, imap_uid, from_imap, dest = move
                acc = msg_record.account_id
                if kind == 'raw':
                    acc._imap_move_to_raw_path_async(imap_uid, from_imap, dest)
                else:
                    acc._imap_move_async(imap_uid, from_imap, dest)
            except Exception as _me:
                _logger.warning('Email rule IMAP move failed: %s', _me)

        # Audit
        try:
            self.write({
                'last_triggered_at': fields.Datetime.now(),
                'trigger_count':     self.trigger_count + 1,
            })
        except Exception:
            pass

        return stop

    # ── Class-level executor called from _upsert_inbox_message ────────────────

    @api.model
    def apply_inbox_rules(self, msg_record, msg_vals: dict):
        """Run all active rules for the message owner against a freshly-imported message.

        IMPORTANT: Rules only fire when the message is in the inbox folder.
        This prevents:
          1. Rules re-firing on messages already moved to custom folders
          2. New emails being immediately swept out of inbox before the FE
             can display them (which was causing the "notifications show but
             inbox is empty" bug)

        msg_vals: plain dict with the same keys as the create() vals dict.
        """
        # Guard: only run rules on messages landing in inbox.
        # Messages imported into sent, custom folders, etc. should not
        # trigger move rules — they are already where they belong.
        current_folder = (msg_vals.get('folder') or '').lower().strip()
        if current_folder not in _RULE_SOURCE_FOLDERS:
            return

        account_id = msg_vals.get('account_id')
        if not account_id:
            return

        acc = self.env['lugal.email.account'].sudo().browse(account_id)
        if not acc.exists():
            return
        owner_uid = acc.user_id.id

        # Augment vals with a real attachment sentinel.  This must not default
        # to False blindly, otherwise attachment rules never match during IMAP
        # import or retroactive apply-all.
        msg_vals_aug = dict(
            msg_vals,
            has_attachments=self._message_has_attachments(msg_record, msg_vals),
        )

        rules = self.sudo().search([
            ('is_active', '=', True),
            ('user_id',   '=', owner_uid),
            '|',
            ('account_id', '=', account_id),
            ('account_id', '=', False),
        ], order='sequence asc, id asc')

        for rule in rules:
            try:
                if rule._matches(msg_vals_aug):
                    should_stop = rule._apply_actions(msg_record)
                    if should_stop:
                        break
            except Exception as _e:
                _logger.warning('Email rule %s evaluation error: %s', rule.id, _e)
# TODO: remove - cherry-pick marker

end of file email_rule.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of email_quick_step.py
email_quick_step.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_quick_step.py
"""
lugal.email.quick.step — named action bundles applied in one click.

A quick step bundles several actions (same schema as email rules) under a
user-defined name and optional keyboard shortcut.

Steps JSON schema (list):
  [{"action": "mark_read"}, {"action": "move_folder", "value": "archive"}]

Supported actions (same set as email rules):
  mark_read | mark_important | mark_unimportant | mark_starred
  move_folder (value = logical or IMAP path) | forward_to (value = email)
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalEmailQuickStep(models.Model):
    _name        = 'lugal.email.quick.step'
    _description = 'Email Quick Step'
    _order       = 'sequence asc, id asc'

    name        = fields.Char(string='Quick Step Name', required=True)
    description = fields.Char(string='Description')
    user_id     = fields.Many2one('res.users', string='Owner', required=True,
                                  default=lambda self: self.env.user, ondelete='cascade', index=True)
    sequence    = fields.Integer(string='Display Order', default=10)
    icon        = fields.Char(string='Icon (optional)', help='Icon name hint for FE (e.g. "archive", "star").')
    steps_json  = fields.Text(
        string='Steps (JSON)', default='[]',
        help='Ordered list of {action, value} dicts to execute in sequence.',
    )
    # How many times the user has applied this quick step
    use_count   = fields.Integer(string='Use Count', default=0, readonly=True)

    def _get_steps(self):
        try:
            return json.loads(self.steps_json or '[]') or []
        except Exception:
            return []

    def apply_to_message(self, msg_record):
        """Apply the quick step's actions to a lugal.email.message record."""
        write_vals = {}
        imap_moves = []
        LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        for step in self._get_steps():
            action = step.get('action', '')
            value  = (step.get('value') or '').strip()
            try:
                if action == 'mark_read':
                    write_vals['is_read'] = True
                elif action == 'mark_important':
                    write_vals['is_important'] = True
                elif action == 'mark_unimportant':
                    write_vals['is_important'] = False
                elif action == 'mark_starred':
                    write_vals['is_starred'] = True
                elif action == 'move_folder':
                    if not value:
                        continue
                    if value.replace('/', '.').split('.')[-1].lower() == 'important':
                        write_vals['is_important'] = True
                    target_folder = value.lower() if value.lower() in LOGICAL else value
                    write_vals['folder'] = target_folder
                    if msg_record.imap_uid and msg_record.account_id:
                        acc = msg_record.account_id
                        cur = msg_record.folder or 'inbox'
                        if cur.lower() == 'inbox':
                            from_imap = 'INBOX'
                        elif cur.lower() in LOGICAL:
                            try:
                                from_imap = acc._get_server_folder_name(cur.lower())
                            except Exception:
                                from_imap = cur.lower()
                        else:
                            from_imap = cur
                        imap_moves.append((value.lower() in LOGICAL, msg_record.imap_uid, from_imap, value))
            except Exception as _e:
                _logger.warning('Quick step action %r failed: %s', action, _e)

        if write_vals:
            msg_record.write(write_vals)
            if msg_record.account_id and (
                'folder' in write_vals or 'is_read' in write_vals
            ):
                unread_count = self.env['lugal.email.message'].sudo().search_count([
                    ('account_id', '=', msg_record.account_id.id),
                    ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])
                msg_record.account_id.sudo().write({'unread_count': unread_count})

        for is_logical, imap_uid, from_imap, dest in imap_moves:
            try:
                if is_logical:
                    msg_record.account_id._imap_move_async(imap_uid, from_imap, dest.lower())
                else:
                    msg_record.account_id._imap_move_to_raw_path_async(imap_uid, from_imap, dest)
            except Exception as _e:
                _logger.warning('Quick step IMAP move failed: %s', _e)

        try:
            self.write({'use_count': self.use_count + 1})
        except Exception:
            pass
# TODO: remove - cherry-pick marker

end of file email_quick_step.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of email_controller.py
email_controller.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/email_controller.py
# Component: Lugal Email — REST API controller for /api/lugal/email/* (email_controller.py)
"""
Layer 1 — /api/lugal/email/*

Pure email engine REST endpoints (plain HTTP, Bearer JWT auth).
No CRM-specific logic. All endpoints return JSON directly (not JSON-RPC envelope).
"""

import json
import logging
import threading
from datetime import timedelta, timezone
from odoo import http, fields
from odoo.http import request, Response
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

# Saudi Arabia timezone — UTC+3, no DST
_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')

ALLOWED_LINK_MODELS = {
    'lugal.crm.customer',
    'lugal.crm.ticket',
    'lugal.crm.interaction',
}

# HTML signatures may include inline data: URLs; keep a generous cap.
_MAX_EMAIL_SIGNATURE_LEN = 5 * 1024 * 1024


def _norm_addr_list(raw):
    """Normalize to a flat list of email address strings.
    Accepts: ["a@b.com", ...] or [{"email": "a@b.com"}, ...] or a bare string."""
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    result = []
    for item in raw:
        addr = item['email'] if isinstance(item, dict) else item
        if addr and isinstance(addr, str) and addr.strip():
            result.append(addr.strip())
    return result

def _imap_quote_mailbox(path):
    """Return an IMAP-safe quoted mailbox name for use in raw imaplib commands.

    Python's imaplib does NOT quote mailbox names automatically.  Folder names
    that contain spaces, parentheses, or other IMAP atom-special characters MUST
    be wrapped in double-quotes before being sent to the server.  Without quoting,
    ``conn.create("INBOX.MailsFrom Weird guy")`` sends::

        C: TAG CREATE INBOX.MailsFrom Weird guy

    …and the server sees ``INBOX.MailsFrom`` as the mailbox name, truncating at
    the first space.  Quoting fixes this::

        C: TAG CREATE "INBOX.MailsFrom Weird guy"

    Only characters that require quoting trigger the wrapper; plain names are
    returned as-is so there is no regression for existing clean folder paths.
    """
    # IMAP atom-specials that force quoting (RFC 3501 §9)
    _NEEDS_QUOTE = set(' \t()\\"[]%*\x00\r\n')
    if any(c in _NEEDS_QUOTE for c in path):
        escaped = path.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return path


# ── Background IMAP sync state ────────────────────────────────────────────────
# Per-account lock: prevents the same account running two syncs simultaneously.
_sync_lock = threading.Lock()
_syncing_accounts: set = set()

# Per-credential lock: prevents multiple accounts sharing the same IMAP login
# (same imap_host + username) from opening concurrent IMAP connections.
# Without this lock, logging in with 15 accounts that share one IMAP username
# fires 15 simultaneous connections → server limit exceeded → IDLE crashes.
_cred_sync_lock = threading.Lock()
_syncing_credentials: set = set()   # set of (imap_host, imap_port, username)
_cred_wait_timeout = 25.0

# Throttle mirrors (kept here so the controller doesn't import from the model).
_IMAP_THROTTLE_SECONDS = 30        # min gap between syncs when inbox has messages
_IMAP_THROTTLE_EMPTY_SECONDS = 20  # min gap when inbox is empty


def _truthy(v):
    return str(v or '').lower() in ('1', 'true', 'yes', 'on')


def _needs_imap_sync(acc, force=False):
    """
    Return True if this account is overdue for an IMAP sync.
    Fast path: only reads already-loaded ORM fields + one indexed search_count.
    """
    if not (acc.password or '').strip():
        return False
    if force:
        return True
    if not acc.last_sync_date:
        return True
    from odoo import fields as odoo_fields
    delta = (odoo_fields.Datetime.now() - acc.last_sync_date).total_seconds()
    inbox_count = acc.env['lugal.email.message'].sudo().search_count([
        ('account_id', '=', acc.id),
        ('folder', '=', 'inbox'),
        ('is_deleted', '=', False),
    ])
    limit = _IMAP_THROTTLE_EMPTY_SECONDS if inbox_count == 0 else _IMAP_THROTTLE_SECONDS
    return delta >= limit


def _run_imap_sync_bg(acc_id, db_name, force=False):
    """
    Spawn a one-shot daemon thread to run IMAP inbox sync for a single account.

    Two-level de-duplication:
      1. Per account_id  — prevents the same account syncing twice in parallel.
      2. Per IMAP credential (host + username) — prevents multiple accounts that
         share one IMAP login from opening concurrent connections to the mail
         server, which would hit the server's max-connections-per-user limit and
         cause the IDLE watcher's persistent connection to be force-closed.

    force=True bypasses the 30-second throttle (use on login / WS connect).

    Returns the Thread object, or None if a sync is already running.
    """
    with _sync_lock:
        if acc_id in _syncing_accounts:
            return None
        _syncing_accounts.add(acc_id)

    def _do():
        cred_key = None
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                acc = env['lugal.email.account'].browse(acc_id)
                if not acc.exists() or not acc.is_active or not (acc.password or '').strip():
                    return

                # Build the credential key
                imap_host = (acc.imap_host or '').strip()
                imap_port = int(acc.imap_port or 993)
                username  = (acc.username or acc.email_address or '').strip()
                cred_key  = (imap_host, imap_port, username)

                # Credential-level gate: wait briefly instead of dropping the
                # sync request. Under load, silently skipping here makes the FE
                # depend on a later manual resync even though a notification was
                # already delivered.
                import time as _time
                wait_started = _time.monotonic()
                while True:
                    with _cred_sync_lock:
                        if cred_key not in _syncing_credentials:
                            _syncing_credentials.add(cred_key)
                            break
                    if _time.monotonic() - wait_started >= _cred_wait_timeout:
                        _logger.warning(
                            'Timed out waiting for IMAP credential sync gate '
                            'acc=%s credential=%s',
                            acc_id, cred_key,
                        )
                        cred_key = None
                        return
                    _time.sleep(0.25)

                if force:
                    acc.action_sync()
                else:
                    acc.action_sync_if_stale()
                cr.commit()

        except Exception:
            _logger.exception('Background IMAP sync failed account_id=%s', acc_id)
        finally:
            with _sync_lock:
                _syncing_accounts.discard(acc_id)
            if cred_key:
                with _cred_sync_lock:
                    _syncing_credentials.discard(cred_key)

    t = threading.Thread(target=_do, daemon=True, name=f'imap-bg-{acc_id}')
    t.start()
    return t


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_response(data, status=200):
    """Return a plain JSON HTTP response with permissive CORS headers.

    CORS headers are set unconditionally so any FE origin (any port, any host)
    can consume these endpoints without needing a dev-proxy workaround.
    """
    resp = Response(
        json.dumps(data, default=str),
        status=status,
        mimetype='application/json',
    )
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Odoo-Database'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    return resp


def _unauthorized():
    return _json_response({'success': False, 'error': 'Unauthorized'}, status=401)


def _not_found(msg='Not found'):
    return _json_response({'success': False, 'error': msg}, status=404)


def _format_imap_error(exc):
    """Turn imaplib errors (often bytes in .args[0]) into a clean API string."""
    args = getattr(exc, 'args', None)
    if args and isinstance(args[0], bytes):
        return args[0].decode('utf-8', errors='replace')
    return str(exc)


def _is_imap_connection_limit_error(text: str) -> bool:
    t = (text or '').lower()
    return any(k in t for k in ('limit', 'maximum', 'too many', '[limit]', 'mail_max_userip'))


def _resolve_imap_folder(account, local_folder):
    """Map a local folder label to the real IMAP server folder name.

    Logical names ('inbox', 'sent', 'trash', …) are resolved through the
    account's cached per-server mapping so Gmail/Dovecot/cPanel differences
    are handled transparently.

    Custom IMAP paths (anything not in _LOGICAL_FOLDERS, e.g.
    'INBOX.syed_naqvi.Important') are returned AS-IS — they are already the
    correct server-side path and must NEVER be passed to _get_server_folder_name
    which would `capitalize()` them and produce a wrong name like
    'Inbox.syed_naqvi.important', causing silent IMAP flag-push failures.
    """
    _LOGICAL_FOLDERS = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    if local_folder.lower() == 'inbox':
        return 'INBOX'
    if local_folder.lower() in _LOGICAL_FOLDERS:
        try:
            return account.sudo()._get_server_folder_name(local_folder.lower())
        except Exception:
            return local_folder.capitalize()
    # Custom folder — the raw IMAP path is stored verbatim in the DB; use it directly.
    return local_folder


def _account_to_dict(acc):
    unread_count = acc.unread_count
    try:
        unread_count = acc.env['lugal.email.message'].sudo().search_count([
            ('account_id', '=', acc.id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
    except Exception:
        pass
    return {
        'id':                  acc.id,
        'name':                acc.name,
        'email_address':       acc.email_address,
        'username':            acc.username or acc.email_address or '',
        'display_name_field':  acc.display_name_field or '',
        'imap_host':           acc.imap_host or '',
        'imap_port':           acc.imap_port,
        'imap_use_ssl':        acc.imap_use_ssl,
        'smtp_host':           acc.smtp_host or '',
        'smtp_port':           acc.smtp_port,
        'smtp_use_tls':        acc.smtp_use_tls,
        'is_default':          acc.is_default,
        'is_active':           acc.is_active,
        'sync_status':         acc.sync_status or 'never',
        'last_sync_date':      _to_riyadh_iso(acc.last_sync_date),
        'unread_count':        unread_count,
        # password_set lets the FE know whether the app password has been entered
        # without ever exposing the actual credential value.
        'password_set':        bool(acc.password),
    }


def _refresh_account_unread_count(account):
    """Keep cached account unread_count aligned after read/unread actions."""
    if not account:
        return 0
    unread_count = account.env['lugal.email.message'].sudo().search_count([
        ('account_id', '=', account.id),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('is_read', '=', False),
        ('is_deleted', '=', False),
    ])
    account.sudo().write({'unread_count': unread_count})
    return unread_count


def _propagate_read_to_sent_copies(env, message_id, read_at):
    """
    When a recipient marks an inbox message as read, find the matching sent-folder
    copy (same RFC 2822 Message-ID) in any Lugal account and mark it read too.

    This is what drives is_read/read_at on *sent* messages — they track whether the
    recipient has read the message, not whether the sender opened their own copy.
    """
    if not message_id:
        return
    try:
        sent_copies = env['lugal.email.message'].sudo().search([
            ('message_id', '=', message_id),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        sent_copies = sent_copies.filtered(lambda msg: _is_sent_folder(msg.folder))
        if sent_copies:
            sent_copies.with_context(lugal_recipient_read=True).write({
                'is_read': True,
                'read_at': read_at,
            })
            _logger.info(
                '_propagate_read_to_sent_copies: marked %d sent copy(s) read '
                'for message_id=%s', len(sent_copies), message_id,
            )
    except Exception as exc:
        _logger.warning(
            '_propagate_read_to_sent_copies failed message_id=%s: %s', message_id, exc,
        )


def _folder_tail(folder_path):
    return (folder_path or '').replace('/', '.').split('.')[-1].lower()


def _folder_move_vals(folder_path):
    vals = {'folder': folder_path}
    if _folder_tail(folder_path) == 'important':
        vals['is_important'] = True
    return vals


def _extract_email_address(raw):
    try:
        from email.utils import parseaddr
        return (parseaddr(raw or '')[1] or raw or '').strip().lower()
    except Exception:
        return (raw or '').strip().lower()


def _rewrite_folder_references(env, account_id, old_path, new_path):
    """Rewrite DB message folders and rule destinations after an IMAP rename."""
    Msg = env['lugal.email.message'].sudo()
    Rule = env['lugal.email.rule'].sudo()
    renamed_msgs = 0
    rules_updated = 0
    seen_msg_ids = set()
    seps = []
    for sep in ('.', '/', '/' if '.' in old_path else '.'):
        if sep not in seps:
            seps.append(sep)

    exact_msgs = Msg.search([
        ('account_id', '=', account_id),
        ('folder', '=', old_path),
    ])
    if exact_msgs:
        seen_msg_ids.update(exact_msgs.ids)
        exact_msgs.write(_folder_move_vals(new_path))

    for sep in seps:
        old_prefix = old_path + sep
        new_prefix = new_path + sep
        child_msgs = Msg.search([
            ('account_id', '=', account_id),
            ('folder', 'like', old_prefix + '%'),
        ])
        for child_msg in child_msgs:
            if child_msg.id in seen_msg_ids:
                continue
            child_msg.write(_folder_move_vals(new_prefix + child_msg.folder[len(old_prefix):]))
            seen_msg_ids.add(child_msg.id)

    renamed_msgs = len(seen_msg_ids)

    for rule in Rule.search([('account_id', '=', account_id)]):
        try:
            actions = json.loads(rule.actions_json or '[]')
        except Exception:
            continue
        changed = False
        for act in actions:
            if act.get('action') != 'move_folder':
                continue
            value = (act.get('value') or '').strip()
            if value == old_path:
                act['value'] = new_path
                changed = True
            else:
                for sep in seps:
                    old_prefix = old_path + sep
                    if value.startswith(old_prefix):
                        act['value'] = new_path + sep + value[len(old_prefix):]
                        changed = True
                        break
        if changed:
            rule.write({'actions_json': json.dumps(actions)})
            rules_updated += 1

    return {'messages_updated': renamed_msgs, 'rules_updated': rules_updated}


def _find_or_create_sender_move_rule(msg, target_folder):
    """Manual custom-folder moves become sender rules for future mail."""
    sender_addr = _extract_email_address(msg.from_address)
    if not sender_addr or not msg.account_id:
        return None
    Rule = msg.env['lugal.email.rule'].sudo()
    conditions = [{'field': 'from_address', 'operator': 'contains', 'value': sender_addr}]
    actions = [{'action': 'move_folder', 'value': target_folder}]
    for rule in Rule.search([
        ('user_id', '=', msg.account_id.user_id.id),
        ('account_id', '=', msg.account_id.id),
        ('is_active', '=', True),
    ], order='sequence asc, id asc'):
        try:
            if (
                json.loads(rule.conditions_json or '[]') == conditions
                and json.loads(rule.actions_json or '[]') == actions
            ):
                return rule
        except Exception:
            continue
    return Rule.create({
        'name':            f'Move all emails from {sender_addr} to {target_folder}',
        'user_id':         msg.account_id.user_id.id,
        'account_id':      msg.account_id.id,
        'is_active':       True,
        'sequence':        90,
        'match_mode':      'all',
        'conditions_json': json.dumps(conditions),
        'actions_json':    json.dumps(actions),
        'stop_processing': True,
    })


def _apply_sender_move_to_existing(msg, target_folder):
    """Move historical inbound messages from the same sender into target_folder."""
    sender_addr = _extract_email_address(msg.from_address)
    if not sender_addr or not msg.account_id:
        return {'rule_id': None, 'applied_existing': 0}

    rule = _find_or_create_sender_move_rule(msg, target_folder)
    mirrored_rules = []
    try:
        from odoo.addons.lugal_email.controllers.rules_controller import (
            _mirror_sender_move_rule_to_user_accounts,
        )
        if rule:
            mirrored_rules = _mirror_sender_move_rule_to_user_accounts(
                rule, msg.account_id.user_id.id, msg.account_id.id)
    except Exception:
        _logger.warning('manual sender move rule mirror failed msg=%s', msg.id, exc_info=True)
    Msg = msg.env['lugal.email.message'].sudo()
    LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    matches = Msg.search([
        ('account_id', '=', msg.account_id.id),
        ('from_address', 'ilike', sender_addr),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('folder', '!=', target_folder),
        ('is_deleted', '=', False),
    ], limit=5000)

    imap_tasks = [(m.imap_uid, m.folder) for m in matches if m.imap_uid]
    if matches:
        matches.write(_folder_move_vals(target_folder))

    if imap_tasks and (msg.account_id.password or '').strip():
        db_name = msg.env.cr.dbname
        acc_id = msg.account_id.id

        def _bg_bulk_sender_move():
            try:
                from collections import defaultdict
                from odoo.modules.registry import Registry as _Registry
                from odoo.api import Environment as _Env
                by_src = defaultdict(list)
                for uid_val, src_folder in imap_tasks:
                    by_src[src_folder].append(str(uid_val))
                with _Registry(db_name).cursor() as _cr:
                    _env = _Env(_cr, 1, {})
                    _acc = _env['lugal.email.account'].browse(acc_id)
                    with _acc._imap_session() as conn:
                        for src_folder, uid_list in by_src.items():
                            try:
                                if (src_folder or '').lower() == 'inbox':
                                    imap_src = 'INBOX'
                                elif (src_folder or '').lower() in LOGICAL:
                                    imap_src = _acc._get_server_folder_name(src_folder.lower(), existing_conn=conn)
                                else:
                                    imap_src = src_folder
                                conn.select(_imap_quote_mailbox(imap_src), readonly=False)
                                uid_set = ','.join(uid_list)
                                dest = _imap_quote_mailbox(target_folder)
                                res = conn.uid('move', uid_set, dest)
                                if res[0] != 'OK':
                                    conn.uid('copy', uid_set, dest)
                                    conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                    conn.expunge()
                            except Exception as exc:
                                _logger.warning(
                                    'manual move rule IMAP batch failed src=%s dest=%s: %s',
                                    src_folder, target_folder, exc,
                                )
            except Exception as exc:
                _logger.warning('manual move rule background thread failed: %s', exc)

        threading.Thread(
            target=_bg_bulk_sender_move,
            daemon=True,
            name=f'imap-sender-rule-{msg.account_id.id}',
        ).start()

    unread_count = _refresh_account_unread_count(msg.account_id)
    return {
        'rule_id': rule.id if rule else None,
        'applied_existing': len(matches),
        'unread_count': unread_count,
        'mirrored_rules': mirrored_rules,
    }


def _sync_unread_custom_folders(accounts, max_folders=12):
    """Refresh IMAP flags for custom folders that currently have unread badges."""
    if not accounts:
        return []
    Msg = accounts.env['lugal.email.message'].sudo()
    ICP = accounts.env['ir.config_parameter'].sudo()
    rows = Msg.search([
        ('account_id', 'in', accounts.ids),
        ('folder', 'not in', ['inbox', 'sent', 'drafts', 'trash', 'archive', 'spam']),
        ('is_read', '=', False),
        ('is_deleted', '=', False),
    ], order='write_date desc', limit=500)
    pairs = []
    seen = set()
    for row in rows:
        key = (row.account_id.id, row.folder)
        if key not in seen:
            seen.add(key)
            pairs.append((row.account_id, row.folder))
        if len(pairs) >= max_folders:
            break

    synced = []
    import time as _time
    now = int(_time.time())
    for acc, folder in pairs:
        if not (acc.password or '').strip():
            continue
        throttle_key = f'lugal_email.custom_unread_sync.{acc.id}.{folder}'
        try:
            last = int(ICP.get_param(throttle_key, '0') or '0')
        except Exception:
            last = 0
        if now - last < 45:
            continue
        try:
            ICP.set_param(throttle_key, str(now))
            res = acc.sudo().sync_custom_imap_folder(folder, headers_only=True)
            _refresh_account_unread_count(acc)
            synced.append({'account_id': acc.id, 'folder': folder, 'result': res})
        except Exception:
            _logger.warning(
                'notifications custom unread sync failed acc=%s folder=%s',
                acc.id, folder, exc_info=True,
            )
    return synced


def _folder_role(folder):
    """Canonical role name the client can use across list/detail/realtime rows."""
    value = (folder or 'inbox').strip()
    low = value.lower()
    logical = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    return low if low in logical else 'custom'


def _is_sent_folder(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent',
        'sent items',
        'sent messages',
    }


def _attachment_payload(att, inline=False, cid_value=None):
    url = (
        f'/web/content/{att.id}?access_token={att.access_token}'
        if att.access_token
        else f'/web/content/{att.id}?download=true'
    )
    data = {
        'id':       att.id,
        'name':     att.name or 'attachment',
        'mimetype': att.mimetype or 'application/octet-stream',
        'size':     att.file_size or 0,
        'url':      url,
        'inline':   bool(inline),
    }
    if cid_value:
        data['cid'] = f'cid:{cid_value}'
        data['content_id'] = cid_value
    return data


def _message_attachment_buckets(msg):
    """Return (regular_attachments, inline_attachments) with CID metadata."""
    _CID_PREFIX = '__inline_cid__:'
    att_list = []
    inline_list = []
    try:
        atts = msg.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', msg.id),
        ])
        for att in atts:
            desc = att.description or ''
            if desc.startswith(_CID_PREFIX):
                cid_value = desc[len(_CID_PREFIX):].strip()
                inline_list.append(_attachment_payload(att, inline=True, cid_value=cid_value))
            else:
                att_list.append(_attachment_payload(att, inline=False))
    except Exception:
        pass
    return att_list, inline_list


def _message_to_dict(msg, full=False):
    data = {
        'id':             msg.id,
        'account_id':     msg.account_id.id,
        'folder':         msg.folder,
        'folder_role':    _folder_role(msg.folder),
        'subject':        msg.subject or '(no subject)',
        'from_name':      msg.from_name or '',
        'from_address':   msg.from_address or '',
        'to_addresses':   msg.to_addresses or '[]',
        'cc_addresses':   msg.cc_addresses or '[]',
        'date':           _to_riyadh_iso(msg.date),
        # received_at: when Odoo first imported this message (create_date = Saudi TZ)
        'received_at':    _to_riyadh_iso(msg.create_date),
        # read_at: first time the message was opened/marked-read (null if never read)
        'read_at':        _to_riyadh_iso(msg.read_at) if msg.read_at else None,
        'is_read':        msg.is_read,
        'is_starred':     msg.is_starred,
        'is_flagged':     msg.is_flagged,    # IMAP \Flagged — independent of is_starred
        'is_important':   msg.is_important,
        'is_draft':       msg.is_draft,
        'is_mentioned':   msg.is_mentioned,
        'written_in_arabic': bool(getattr(msg, 'written_in_arabic', False)),
        'message_size':   msg.message_size or 0,
        'smtp_delivered': msg.smtp_delivered,
        'smtp_error':     msg.smtp_error or None,
        'smtp_status':    msg.smtp_status or 'pending',
        'thread_id':      msg.thread_id or None,
        'in_reply_to':    msg.in_reply_to or None,
        'version':        _to_riyadh_iso(msg.write_date),
        'write_date':     _to_riyadh_iso(msg.write_date),
        # Read receipt tracking fields
        'request_read_receipt': bool(msg.request_read_receipt),
        'recipient_read_at':    _to_riyadh_iso(msg.recipient_read_at) if msg.recipient_read_at else None,
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket':   {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                        if msg.linked_ticket_id else None,
        },
    }
    att_list, inline_list = _message_attachment_buckets(msg)

    # These counters are always in the response (list view needs them for icons)
    data['has_attachments']         = bool(att_list)
    data['attachment_count']        = len(att_list)
    data['has_inline_attachments']  = bool(inline_list)
    data['inline_attachment_count'] = len(inline_list)

    if full:
        data['body_html']          = msg.body_html or ''
        data['body_text']          = msg.body_text or ''
        data['body_fetched']       = bool(msg.body_fetched)
        data['attachments']        = att_list      # paperclip-added files only
        data['inline_attachments'] = inline_list   # pasted / dropped / inserted images
    return data


def _build_quoted_html(msg):
    """Return an HTML block with the original message quoted below the reply area."""
    date_str = _to_riyadh_iso(msg.date) or ''
    sender   = msg.from_name or msg.from_address or 'Unknown'
    addr     = msg.from_address or ''
    header   = (
        f'<div style="color:#555;font-size:0.9em;margin-top:16px;border-top:1px solid #e0e0e0;padding-top:8px;">'
        f'<b>On {date_str}, {sender}'
        f'{(" &lt;" + addr + "&gt;") if addr else ""} wrote:</b>'
        f'</div>'
    )
    original = msg.body_html or (msg.body_text or '').replace('\n', '<br>')
    return (
        f'<br><br>{header}'
        f'<blockquote style="margin:8px 0 0 8px;padding-left:12px;'
        f'border-left:3px solid #ccc;color:#333;">'
        f'{original}'
        f'</blockquote>'
    )


def _build_quoted_text(msg):
    """Return a plain-text block with the original message quoted (> prefix)."""
    date_str = _to_riyadh_iso(msg.date) or ''
    sender   = msg.from_name or msg.from_address or 'Unknown'
    addr     = msg.from_address or ''
    header   = f'On {date_str}, {sender}{(" <" + addr + ">") if addr else ""} wrote:'
    original = (msg.body_text or '').strip()
    quoted   = '\n'.join('> ' + line for line in original.splitlines()) if original else ''
    return f'\n\n{header}\n{quoted}'


def _thread_vals_for_reply(orig):
    """Return the thread_id / references / in_reply_to values for a reply or reply-all.

    Thread-ID is the root of the conversation — the very first message's
    Message-ID.  The References chain grows with each reply so email clients
    can reconstruct the full conversation tree.

    RFC 2822 rules:
    - in_reply_to  = Message-ID of the immediate parent
    - references   = parent.references + parent.message_id (space-joined)
    - thread_id    = first entry in the final references list (= root msg-id)
    """
    parent_msg_id  = (orig.message_id or '').strip()
    parent_refs    = (orig.references or '').strip()
    parent_tid     = (orig.thread_id or '').strip()

    # Build the new References chain
    if parent_refs:
        new_refs = f'{parent_refs} {parent_msg_id}'.strip() if parent_msg_id else parent_refs
    elif parent_msg_id:
        new_refs = parent_msg_id
    else:
        new_refs = ''

    # thread_id is inherited from the parent, falling back to the parent's
    # own Message-ID (making it the implicit root).
    new_thread_id = parent_tid or parent_msg_id or ''

    return {
        'in_reply_to': parent_msg_id or False,
        'references':  new_refs or False,
        'thread_id':   new_thread_id or False,
    }


def _thread_vals_for_forward(orig):
    """Return thread values for a forward.

    Forwards start a NEW thread in the recipient's mailbox — the forward
    itself is the root.  The original thread_id is NOT propagated.
    We still carry a References header pointing to the original so that
    mail servers can link them loosely.
    """
    parent_msg_id = (orig.message_id or '').strip()
    new_refs      = parent_msg_id if parent_msg_id else ''
    return {
        'in_reply_to': parent_msg_id or False,
        'references':  new_refs or False,
        'thread_id':   False,   # will be set to the new message's own Message-ID after create
    }


def _get_user_accounts(uid):
    return request.env['lugal.email.account'].sudo().search([
        ('user_id', '=', uid),
        ('is_deleted', '=', False),
        ('is_active', '=', True),
    ])


class LugalEmailController(http.Controller):

    # ── Accounts ─────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def accounts(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            if request.httprequest.method == 'GET':
                accs = _get_user_accounts(uid)

                # Auto-provision: existing employees who were created before the
                # auto-create logic existed will have no accounts. Build one from
                # their res.users profile so the FE always has something to show.
                if not accs:
                    user = request.env['res.users'].sudo().browse(uid)
                    if user.exists():
                        user_email = user.partner_id.email or user.login or ''
                        user_name  = user.partner_id.name or user.login or ''
                        if user_email:
                            try:
                                new_acc = request.env['lugal.email.account'].sudo().create({
                                    'user_id':       uid,
                                    'name':          user_name,
                                    'email_address': user_email,
                                    'username':      user_email,
                                    'password':      '',       # admin must enter the app password
                                    'imap_host':     'mail.nooralnibras.com',
                                    'imap_port':     993,
                                    'imap_use_ssl':  True,
                                    'smtp_host':     'mail.nooralnibras.com',
                                    'smtp_port':     465,
                                    'smtp_use_tls':  False,
                                    'is_default':    True,
                                    'is_active':     True,
                                    'sync_status':   'never',
                                })
                                accs = new_acc
                            except Exception:
                                _logger.warning(
                                    'accounts GET: auto-provision failed for uid=%s', uid,
                                    exc_info=True,
                                )
                                accs = request.env['lugal.email.account'].sudo().browse()

                return _json_response({
                    'success': True,
                    'data': [_account_to_dict(a) for a in accs],
                })
            # POST — create account
            body = json.loads(request.httprequest.data or '{}')
            vals = {
                'user_id':          uid,
                'name':             body.get('name', ''),
                'email_address':    body.get('email_address', ''),
                'display_name_field': body.get('display_name_field', ''),
                'username':         body.get('username', ''),
                'password':         body.get('password', ''),
                'imap_host':        body.get('imap_host', 'imap.gmail.com'),
                'imap_port':        body.get('imap_port', 993),
                'imap_use_ssl':     body.get('imap_use_ssl', True),
                'smtp_host':        body.get('smtp_host', 'smtp.gmail.com'),
                'smtp_port':        body.get('smtp_port', 587),
                'smtp_use_tls':     body.get('smtp_use_tls', True),
                'is_default':       body.get('is_default', False),
            }
            if not vals['email_address'] or not vals['name']:
                return _json_response({'success': False, 'error': 'name and email_address required'}, 400)
            acc = request.env['lugal.email.account'].sudo().create(vals)
            if vals['is_default']:
                acc.action_set_default()
            return _json_response({'success': True, 'data': _account_to_dict(acc)}, 201)
        except Exception as exc:
            _logger.exception('email accounts error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'DELETE', 'OPTIONS'])
    def account_detail(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid or acc.is_deleted:
                return _not_found('Account not found')

            method = request.httprequest.method
            if method == 'GET':
                return _json_response({'success': True, 'data': _account_to_dict(acc)})

            if method == 'DELETE':
                acc.write({'is_deleted': True, 'active': False})
                return _json_response({'success': True})

            # PATCH — partial update
            body = json.loads(request.httprequest.data or '{}')
            allowed = {
                'name', 'email_address', 'display_name_field', 'username', 'password',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls',
                'is_active',
            }
            vals = {k: v for k, v in body.items() if k in allowed}
            if vals:
                acc.write(vals)
            return _json_response({'success': True, 'data': _account_to_dict(acc)})
        except Exception as exc:
            _logger.exception('account_detail error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/test', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_test(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            result = acc.action_test_connection()
            return _json_response({'success': result.get('status') == 'ok', **result})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/sync/all', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def sync_all_accounts(self, **kwargs):
        """Kick off a background IMAP sync for every active account owned by the current user."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            accs = _get_user_accounts(uid)
            notification_folder_domain = [
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ]
            db_name = request.env.cr.dbname
            results = []
            for acc in accs:
                try:
                    t = _run_imap_sync_bg(acc.id, db_name)
                    results.append({'account_id': acc.id, 'sync_started': t is not None})
                except Exception as exc:
                    results.append({'account_id': acc.id, 'sync_started': False, 'error': str(exc)})
            return _json_response({
                'success': True,
                'message': 'Sync started in background',
                'synced': len(results),
                'data': results,
            })
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/sync', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_sync(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            t = _run_imap_sync_bg(acc.id, request.env.cr.dbname)
            return _json_response({
                'success': True,
                'sync_started': t is not None,
                'message': 'Sync started in background' if t is not None else 'Sync already running for this account',
            })
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/set_default', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_set_default(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            acc.action_set_default()
            return _json_response({'success': True, 'data': _account_to_dict(acc)})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/signature', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'PUT', 'OPTIONS'])
    def user_email_signature(self, **kwargs):
        """Read or replace the JWT user's HTML email signature (``res.users.signature``)."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return _not_found('User not found')

            method = request.httprequest.method
            if method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {'signature': user.signature or ''},
                })

            raw = request.httprequest.data or b'{}'
            body = json.loads(raw)
            if 'signature' not in body:
                return _json_response(
                    {'success': False, 'error': 'signature field is required'},
                    400,
                )
            sig = body.get('signature')
            if sig is not None and not isinstance(sig, str):
                return _json_response(
                    {'success': False, 'error': 'signature must be a string or null'},
                    400,
                )
            sig = '' if sig is None else sig
            if len(sig) > _MAX_EMAIL_SIGNATURE_LEN:
                return _json_response(
                    {'success': False, 'error': 'signature exceeds maximum length'},
                    400,
                )
            user.write({'signature': sig})
            return _json_response({
                'success': True,
                'data': {'signature': user.signature or ''},
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('user_email_signature error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Push-webhook: instant notify without waiting for cron ─────────────────
    #
    # External services (Microsoft Graph, Gmail Pub/Sub, Mailgun, custom SMTP
    # forwarders, etc.) can POST to this endpoint the moment a new email lands
    # in a mailbox.  The sync runs synchronously inside the current request so
    # no extra DB connections are opened and the WS push event fires before
    # this response is returned.
    #
    # Authentication: callers MUST send a shared secret in the
    # X-Lugal-Webhook-Token header OR as a `token` query / body parameter.
    # Set the secret once via System Parameters:
    #   lugal.email.webhook.token = <random-string>
    # If the parameter is missing or empty the endpoint is disabled (401).
    #
    # Request body (JSON, all fields optional):
    #   { "email": "user@domain.com",   # narrow sync to one account
    #     "account_id": 3 }             # OR by internal account id
    # If neither is provided all active accounts are synced sequentially.

    @http.route('/api/lugal/email/webhook/notify',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def email_push_notify(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        # Validate shared secret
        cfg_secret = request.env['ir.config_parameter'].sudo().get_param(
            'lugal.email.webhook.token', ''
        ).strip()
        if not cfg_secret:
            return _json_response({'success': False, 'error': 'Webhook not configured'}, 401)

        incoming_token = (
            request.httprequest.headers.get('X-Lugal-Webhook-Token', '')
            or kwargs.get('token', '')
        ).strip()
        if incoming_token != cfg_secret:
            return _json_response({'success': False, 'error': 'Invalid token'}, 401)

        try:
            import json as _json_mod
            body_bytes = request.httprequest.get_data(cache=False)
            payload = {}
            if body_bytes:
                try:
                    payload = _json_mod.loads(body_bytes)
                except Exception:
                    pass

            email_addr = payload.get('email', '').strip().lower()
            account_id = payload.get('account_id')

            Acc = request.env['lugal.email.account'].sudo()
            if account_id:
                accs = Acc.browse(int(account_id)).filtered(
                    lambda a: a.exists() and (a.password or '').strip()
                )
            elif email_addr:
                accs = Acc.search([
                    ('email_address', '=ilike', email_addr),
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ])
            else:
                accs = Acc.search([
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ])

            synced = []
            for acc in accs:
                if not (acc.password or '').strip():
                    continue
                # Run synchronously inside this request's existing DB cursor —
                # no extra pool connections are opened, and the WS bus event
                # fires (and commits) before we return the response.
                try:
                    result = acc.action_sync()
                    request.env.cr.commit()
                    synced.append({
                        'account_id': acc.id,
                        'sync_ok': True,
                        'imported': (result or {}).get('imported', 0),
                    })
                except Exception as exc_inner:
                    _logger.exception('email_push_notify: sync failed for account %s', acc.id)
                    synced.append({'account_id': acc.id, 'sync_ok': False, 'error': str(exc_inner)})

            return _json_response({
                'success': True,
                'message': 'Sync complete',
                'accounts': synced,
            })
        except Exception as exc:
            _logger.exception('email_push_notify failed')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Manual Force-Sync ─────────────────────────────────────────────────────
    #
    # FE can call this endpoint to immediately (re)sync one or all of the
    # logged-in user's email accounts.  Runs synchronously and waits for
    # completion so the response already contains the fresh message counts.
    #
    # POST /api/lugal/email/sync
    # Body (JSON, all optional):
    #   { "account_id": 55 }     // sync a specific account
    #   {}                       // sync all of this user's accounts
    #
    # Response:
    #   { "success": true, "accounts": [{ "id":55, "sync_ok":true, "imported":12,
    #     "unread":5, "sync_status":"ok", "sync_error": null }] }

    @http.route('/api/lugal/email/sync',
                type='http', auth='none', csrf=False, methods=['GET', 'POST', 'OPTIONS'])
    def force_sync(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        # GET /api/lugal/email/sync?account_id=&folder=&limit=&offset= →
        # acts as an alias for GET /api/lugal/email/messages with the same params.
        # Some FE builds use /sync as the message-list endpoint.
        if request.httprequest.method == 'GET':
            return self.messages_list(**kwargs)
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = {}
            raw = request.httprequest.get_data(cache=False)
            if raw:
                try:
                    body = json.loads(raw)
                except Exception:
                    pass

            account_id = body.get('account_id')
            Acc = request.env['lugal.email.account'].sudo()

            if account_id:
                accs = Acc.browse(int(account_id))
                if not accs.exists() or accs.user_id.id != uid:
                    return _not_found('Email account not found')
            else:
                accs = _get_user_accounts(uid)

            if not accs:
                return _json_response({'success': False, 'error': 'No email accounts configured'}, 400)

            results = []
            for acc in accs:
                if not (acc.password or '').strip():
                    results.append({
                        'id':          acc.id,
                        'sync_ok':     False,
                        'error':       'No app password configured on this account',
                        'sync_status': acc.sync_status or 'never',
                        'imported':    0,
                        'unread':      0,
                    })
                    continue

                try:
                    sync_result = acc.action_sync()
                    request.env.cr.commit()
                    unread = request.env['lugal.email.message'].sudo().search_count([
                        ('account_id', '=', acc.id),
                        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ])
                    results.append({
                        'id':          acc.id,
                        'name':        acc.name,
                        'email':       acc.email_address,
                        'sync_ok':     (sync_result or {}).get('sync_status') == 'ok',
                        'imported':    (sync_result or {}).get('imported', 0),
                        'unread':      unread,
                        'sync_status': acc.sync_status or 'never',
                        'sync_error':  acc.sync_error_msg or None,
                    })
                except Exception as exc:
                    _logger.exception('force_sync failed for account %s', acc.id)
                    results.append({
                        'id':          acc.id,
                        'sync_ok':     False,
                        'error':       str(exc),
                        'sync_status': 'error',
                        'imported':    0,
                        'unread':      0,
                    })

            return _json_response({'success': True, 'accounts': results})
        except Exception as exc:
            _logger.exception('force_sync endpoint error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Messages / Mailbox ────────────────────────────────────────────────────

    @http.route([
        '/api/lugal/email/messages',
        '/api/lugal/email/mailbox/inbox',
        '/api/lugal/email/mailbox/<string:folder_name>',
    ], type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def messages_list(self, folder_name='inbox', **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            params      = request.httprequest.args
            folder_raw  = (params.get('folder', folder_name) or 'inbox').strip()
            folder_q    = folder_raw   # canonical path for DB queries (may change after IMAP resolve)
            account_id  = params.get('account_id')
            query       = (
                params.get('query')
                or params.get('q')
                or params.get('search')
                or ''
            ).strip()
            linked_model = params.get('linked_model')
            linked_id   = params.get('linked_id')
            limit       = int(params.get('limit', 50))
            offset      = int(params.get('offset', 0))
            auto_sync   = params.get('auto_sync', '1') != '0'
            force_sync  = params.get('force_sync', '0') == '1'
            # since_id: when provided, NEW messages (id > since_id) are fetched
            # first and prepended before the paginated list.  Use this after
            # receiving a crm.email.message.new WS event to guarantee the newly
            # arrived email appears at the top even if its Date header is old.
            since_id    = int(params.get('since_id', 0) or 0)
            focus_raw   = params.get('message_id') or params.get('focus_message_id')
            focus_message_id = 0
            if focus_raw:
                try:
                    focus_message_id = int(str(focus_raw).strip())
                except (TypeError, ValueError):
                    return _json_response({'success': False, 'error': 'message_id must be an integer'}, 400)

            def _first_param(*names):
                for name in names:
                    if name in params:
                        return params.get(name)
                return None

            # Optional server-side filter params.  Support both legacy short
            # names and FE contract names (`filter_*`) used by ConversationsEmail.
            filter_unread         = _first_param('filter_unread', 'unread')
            filter_flagged        = _first_param('filter_flagged', 'flagged')
            filter_starred        = _first_param('filter_starred', 'starred')
            filter_important      = _first_param('filter_important', 'important')
            filter_has_attachment = _first_param(
                'filter_has_attachment', 'filter_has_attachments', 'has_attachments',
            )
            filter_mentioned      = _first_param('filter_mentioned', 'mentioned')
            filter_sent_to_me     = _first_param('filter_sent_to_me', 'sent_to_me')

            # scope to this user's accounts
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids
            try:
                requested_account_id = int(str(account_id).strip()) if account_id else None
            except (TypeError, ValueError):
                return _json_response({'success': False, 'error': 'account_id must be an integer'}, 400)
            if requested_account_id and requested_account_id not in account_ids:
                return _json_response({'success': False, 'error': 'Account not found'}, 404)

            _LOGICAL_MAILBOX = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            is_custom_mailbox = folder_raw.lower() not in _LOGICAL_MAILBOX
            imap_folder_sync = None
            folder_branch_expand = False

            # Kick off IMAP sync if the account is stale, then wait for completion.
            # For accounts that have NEVER been synced (sync_status='never') we use
            # force=True and a longer 15-second timeout so the first inbox load
            # always shows real emails rather than an empty list.
            # For routine syncs a 7-second timeout is sufficient.
            if auto_sync and folder_raw == 'inbox':
                db_name = request.env.cr.dbname
                sync_threads = []
                has_never_synced = False
                for acc in user_accounts:
                    try:
                        acc_never = not acc.last_sync_date or acc.sync_status == 'never'
                        effective_force = force_sync or acc_never
                        if effective_force or _needs_imap_sync(acc, force=False):
                            t = _run_imap_sync_bg(acc.id, db_name, force=effective_force)
                            if t:
                                sync_threads.append(t)
                                if acc_never:
                                    has_never_synced = True
                                    _logger.info(
                                        'mailbox: first-time sync triggered for account %s',
                                        acc.id,
                                    )
                    except Exception:
                        _logger.exception('mailbox auto-sync kick failed for account %s', acc.id)
                # Wait longer for first-time syncs (cold start from mail server).
                wait_secs = 15.0 if has_never_synced else 7.0
                for t in sync_threads:
                    t.join(timeout=wait_secs)

            # User-created IMAP folders (rule destinations) are not part of action_sync
            # (INBOX+Sent only).  Pull them on-demand so list/sync APIs return messages.
            if auto_sync and is_custom_mailbox:
                imap_folder_sync = []
                aid = requested_account_id
                targets = user_accounts.filtered(lambda a: a.id == aid) if aid else user_accounts
                folder_branch_expand = False

                for acc in targets:
                    if not (acc.password or '').strip():
                        imap_folder_sync.append({
                            'account_id': acc.id,
                            'imported': 0,
                            'error': 'no password',
                            'resolved_path': folder_raw,
                        })
                        continue
                    # Determine if this is a namespace parent using the DB only —
                    # no IMAP call needed and avoids connection limit issues.
                    # A folder is a namespace parent when child folders exist,
                    # regardless of whether the parent also has direct messages.
                    # Example:
                    #   INBOX.syed_naqvi              -> all Syed mail
                    #   INBOX.syed_naqvi.Important    -> only important Syed mail
                    Msg = request.env['lugal.email.message'].sudo()
                    has_child_messages = Msg.search_count([
                        ('account_id', '=', acc.id),
                        ('folder',     'like', folder_raw + '.%'),
                        ('is_deleted', '=', False),
                    ]) > 0
                    is_namespace_parent = has_child_messages
                    children_paths = []  # only used for imap_folder_sync reporting

                    try:
                        # Keep custom-folder sync isolated.  IMAP/body import can
                        # hit uniqueness or server-state errors; if that happens,
                        # the list endpoint must still return cached DB rows
                        # instead of leaving the request cursor aborted.
                        with request.env.cr.savepoint():
                            if is_namespace_parent:
                                # Namespace parent — expand query to all children.
                                # No IMAP sync needed; messages already in DB from leaf syncs.
                                folder_branch_expand = True
                                folder_q = folder_raw
                                imap_folder_sync.append({
                                    'account_id':      acc.id,
                                    'branch':          True,
                                    'child_mailboxes': [],
                                    'imported':        0,
                                    'error':           None,
                                    'resolved_path':   folder_raw,
                                    'per_mailbox':     [],
                                })
                            else:
                                # Leaf folder or folder with its own messages — exact match only
                                res = acc.sudo().sync_custom_imap_folder(folder_raw)
                                imap_folder_sync.append({'account_id': acc.id, **res})
                                # Only accept resolved_path if it matches the requested folder
                                # exactly (case differences only). Never allow it to become a
                                # parent path which would expand the query to sibling folders.
                                resolved = (res.get('resolved_path') or '').strip()
                                if resolved and resolved.lower() == folder_raw.lower():
                                    folder_q = resolved
                    except Exception:
                        try:
                            request.env.cr.rollback()
                        except Exception:
                            pass
                        _logger.exception(
                            'mailbox custom-folder sync failed acc=%s folder=%s',
                            acc.id, folder_raw,
                        )
                        imap_folder_sync.append({
                            'account_id': acc.id,
                            'imported': 0,
                            'error': 'exception',
                            'resolved_path': folder_raw,
                        })

            # Namespace parent (e.g. INBOX.syednaqvi): include messages stored under
            # child folders (INBOX.syednaqvi.Important) in the same list response.
            _folder_domain = [('folder', '=', folder_q)]
            if is_custom_mailbox and folder_branch_expand:
                _folder_domain = [
                    '|', '|',
                    ('folder', '=', folder_q),
                    ('folder', 'like', folder_q + '.%'),
                    ('folder', 'like', folder_q + '/%'),
                ]

            base_domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
            ] + _folder_domain
            if account_id:
                base_domain.append(('account_id', '=', requested_account_id))
            if query:
                base_domain += ['|', ('subject', 'ilike', query), ('body_text', 'ilike', query)]
            if linked_model and linked_id:
                base_domain += [('linked_model', '=', linked_model), ('linked_record_id', '=', int(linked_id))]

            # Optional server-side filters
            filter_domain = []
            if _truthy(filter_unread):
                filter_domain.append(('is_read', '=', False))
            if _truthy(filter_flagged):
                filter_domain.append(('is_flagged', '=', True))
            if _truthy(filter_starred):
                filter_domain.append(('is_starred', '=', True))
            if _truthy(filter_important):
                filter_domain.append(('is_important', '=', True))
            # Folder paths created by the "important from sender" template must
            # not display stale/non-important duplicates.  This keeps
            # INBOX.<sender>.Important semantically consistent even if older
            # rows were imported before the rule/move hardening landed.
            if is_custom_mailbox:
                _folder_tail = (folder_q or '').replace('/', '.').split('.')[-1].lower()
                if _folder_tail == 'important':
                    filter_domain.append(('is_important', '=', True))
            if _truthy(filter_mentioned):
                filter_domain.append(('is_mentioned', '=', True))
            if _truthy(filter_has_attachment):
                attachment_account_ids = (
                    [requested_account_id] if requested_account_id else account_ids
                )
                request.env.cr.execute(
                    """
                    SELECT DISTINCT a.res_id
                    FROM ir_attachment a
                    JOIN lugal_email_message m ON m.id = a.res_id
                    WHERE a.res_model = 'lugal.email.message'
                      AND COALESCE(a.description, '') NOT LIKE '__inline_cid__:%'
                      AND m.account_id = ANY(%s)
                      AND m.is_deleted = FALSE
                    """,
                    (attachment_account_ids,),
                )
                att_msg_ids = [row[0] for row in request.env.cr.fetchall()]
                filter_domain.append(('id', 'in', att_msg_ids))
            if _truthy(filter_sent_to_me):
                user_emails = [a.email_address for a in user_accounts if a.email_address]
                if user_emails:
                    to_clauses = [('to_addresses', 'ilike', e) for e in user_emails]
                    if len(to_clauses) == 1:
                        filter_domain += to_clauses
                    else:
                        or_clause = ['|'] * (len(to_clauses) - 1) + to_clauses
                        filter_domain += or_clause

            base_domain += filter_domain

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(base_domain)

            # Default inbox sorting uses create_date so brand-new arrivals appear
            # first even if a sender has a bad clock.  Custom rule folders are
            # different: historical/stale DB rows may be re-used during IMAP
            # custom-folder sync, so create_date can be old while the email Date
            # is current.  For custom folders, sort by the email Date first.
            sort_order = (
                'date desc, create_date desc, id desc'
                if is_custom_mailbox
                else 'create_date desc, id desc'
            )

            new_msgs = Msg.browse()
            if since_id:
                since_account_ids = [requested_account_id] if requested_account_id else account_ids
                all_accs_domain = [
                    ('account_id', 'in', since_account_ids),
                    ('is_deleted', '=', False),
                ] + _folder_domain + [
                    ('id',         '>',  since_id),
                ]
                new_msgs = Msg.search(all_accs_domain, order='id desc')

            page_msgs = Msg.search(base_domain, limit=limit, offset=offset, order=sort_order)
            focus_msg = Msg.browse()
            if focus_message_id:
                focus_domain = [
                    ('id',         '=',  focus_message_id),
                    ('account_id', 'in', [requested_account_id] if requested_account_id else account_ids),
                    ('is_deleted', '=',  False),
                ] + _folder_domain
                focus_msg = Msg.search(focus_domain, limit=1)

            include_thread = params.get('include_thread', '0') == '1'

            pinned_msgs = list(new_msgs)
            if focus_msg and focus_msg.id not in {m.id for m in pinned_msgs}:
                # Notification/open-from-link safety net: pin the exact requested
                # message for this mailbox even if optional filters like unread=1
                # or pagination would otherwise hide it after it is opened/read.
                pinned_msgs.insert(0, focus_msg)

            if pinned_msgs:
                pinned_ids = {m.id for m in pinned_msgs}
                combined = pinned_msgs + [m for m in page_msgs if m.id not in pinned_ids]
                display_msgs = combined[:limit]
            else:
                display_msgs = list(page_msgs)

            # ── Thread enrichment ─────────────────────────────────────────────
            # Collect unique thread_ids from this page so we can batch-count
            # (and optionally batch-fetch) thread messages in one DB round-trip.
            thread_ids_on_page = list({
                m.thread_id for m in display_msgs if m.thread_id
            })

            # thread_count per thread_id (across all user accounts, all folders)
            thread_count_map: dict = {}
            thread_msgs_map: dict = {}   # populated only when include_thread=1

            if thread_ids_on_page:
                # Batch fetch all thread members across all folders in one query.
                all_thread_members = Msg.search([
                    ('account_id', 'in', account_ids),
                    ('is_deleted', '=', False),
                    ('thread_id',  'in', thread_ids_on_page),
                ] + filter_domain, order='date asc, id asc')

                # Group by thread_id in Python — O(n) over thread members
                from collections import defaultdict as _defaultdict
                _groups: dict = _defaultdict(list)
                for tm in all_thread_members:
                    _groups[tm.thread_id].append(tm)

                for tid, members in _groups.items():
                    thread_count_map[tid] = len(members)
                    if include_thread:
                        thread_msgs_map[tid] = [_message_to_dict(tm, full=False) for tm in members]

            def _enrich(m):
                d = _message_to_dict(m)
                tid = m.thread_id or None
                d['thread_count'] = thread_count_map.get(tid, 1) if tid else 1
                if include_thread and tid and tid in thread_msgs_map:
                    d['thread_messages'] = thread_msgs_map[tid]
                return d

            items = [_enrich(m) for m in display_msgs]

            # Include the highest message ID in the current account scope so
            # account-scoped sent/inbox requests never receive cross-account rows.
            all_max = Msg.search([
                ('account_id', 'in', [requested_account_id] if requested_account_id else account_ids),
                ('is_deleted', '=', False),
            ] + _folder_domain, order='id desc', limit=1)
            max_id = all_max[0].id if all_max else 0

            return _json_response({
                'success': True,
                'data': {
                    'folder':           folder_q,
                    'total':            total,
                    'limit':            limit,
                    'offset':           offset,
                    'max_id':           max_id,
                    'items':            items,
                    'focused_message_id': focus_message_id or None,
                    'focused_message_found': bool(focus_msg),
                    'imap_folder_sync': imap_folder_sync,
                    'includes_descendant_folders': bool(
                        is_custom_mailbox and folder_branch_expand
                    ),
                },
            })
        except Exception as exc:
            _logger.exception('messages_list error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'DELETE', 'OPTIONS'])
    def message_detail(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        # ?preview=true → return message data without marking it as read.
        # Used by notification handlers that need the payload without side-effects.
        preview_mode = str(kwargs.get('preview', '')).lower() in ('1', 'true', 'yes')
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            if request.httprequest.method == 'PATCH':
                body = json.loads(request.httprequest.data or '{}')
                vals = {}
                imap_uid    = msg.imap_uid
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)

                if 'is_flagged' in body:
                    is_flagged = bool(body['is_flagged'])
                    vals['is_flagged'] = is_flagged   # independent field from is_starred
                    if imap_uid:
                        if is_flagged:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, add_flags=['\\Flagged']
                            )
                        else:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, remove_flags=['\\Flagged']
                            )

                if 'is_starred' in body:
                    vals['is_starred'] = bool(body['is_starred'])

                if 'is_important' in body:
                    vals['is_important'] = bool(body['is_important'])

                sent_read_noop = False
                if 'is_read' in body:
                    is_read = bool(body['is_read'])
                    if _is_sent_folder(msg.folder):
                        # Sent-folder: is_read/read_at track RECIPIENT read status.
                        # Sender patching their own sent copy is cosmetic-only; push
                        # \Seen to IMAP but do not alter DB is_read/read_at.
                        sent_read_noop = True
                        if imap_uid and is_read:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, add_flags=['\\Seen']
                            )
                    else:
                        was_already_read = bool(msg.read_at)
                        vals['is_read'] = is_read
                        if is_read and not msg.read_at:
                            from datetime import datetime
                            vals['read_at'] = datetime.utcnow()
                        if imap_uid:
                            if is_read:
                                msg.account_id.sudo()._imap_store_async(
                                    imap_uid, imap_folder, add_flags=['\\Seen']
                                )
                            else:
                                msg.account_id.sudo()._imap_store_async(
                                    imap_uid, imap_folder, remove_flags=['\\Seen']
                                )
                        # Propagate read confirmation to the sender's sent copy.
                        if is_read and not was_already_read and msg.message_id:
                            _propagate_read_to_sent_copies(
                                request.env, msg.message_id,
                                msg.read_at or fields.Datetime.now()
                            )
                        # Send MDN if marking inbox message as read for the first time
                        # and sender requested a read receipt.
                        if (is_read and not was_already_read
                                and msg.request_read_receipt
                                and msg.folder in ('inbox',)
                                and msg.from_address
                                and msg.message_id):
                            try:
                                _send_mdn_async(
                                    acc=msg.account_id,
                                    to_address=msg.from_address,
                                    original_message_id=msg.message_id,
                                    original_subject=msg.subject or '',
                                    recipient_email=msg.account_id.email_address,
                                )
                            except Exception as _mdn_exc:
                                _logger.warning('MDN trigger failed (patch): %s', _mdn_exc)

                if not vals:
                    if sent_read_noop:
                        return _json_response({'success': True, 'data': _message_to_dict(msg)})
                    return _json_response(
                        {'success': False, 'error': 'Provide at least one of: is_flagged, is_starred, is_important, is_read'},
                        400,
                    )
                msg.write(vals)
                if 'is_read' in vals:
                    _refresh_account_unread_count(msg.account_id)
                return _json_response({'success': True, 'data': _message_to_dict(msg)})

            if request.httprequest.method == 'DELETE':
                prev_folder = msg.folder
                msg.write({'folder': 'trash'})
                _refresh_account_unread_count(msg.account_id)
                # Push move to IMAP server (fire-and-forget)
                if msg.imap_uid:
                    imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                    msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'trash')
                return _json_response({'success': True})
            # Lazy-fetch full body if this message was imported headers-only.
            if not msg.body_fetched and msg.imap_uid:
                try:
                    msg.account_id.sudo().fetch_message_body(msg.id)
                    msg.invalidate_recordset()  # reload from DB
                except Exception:
                    _logger.exception('Lazy body fetch failed for message %s', msg.id)
            # GET does NOT auto-mark as read.
            # To mark a message as read, use: POST /api/lugal/email/messages/<id>/read
            return _json_response({'success': True, 'data': _message_to_dict(msg, full=True)})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/thread', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def message_thread(self, message_id, **kwargs):
        """Return all messages in the same email thread, ordered oldest → newest.

        A thread is the full conversation: the original email plus all replies,
        reply-alls that share the same root Message-ID (thread_id).

        The requesting message itself is always included.  Messages from all
        folders (inbox, sent) are included so the user sees both sides of the
        conversation.  Deleted messages are excluded.

        Query params:
          include_body=1   — include body_html / body_text for each message
                             (default: 0, returns headers only to keep response small)
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            anchor = request.env['lugal.email.message'].sudo().browse(message_id)
            if not anchor.exists() or anchor.account_id.user_id.id != uid:
                return _not_found()

            thread_id = anchor.thread_id or anchor.message_id
            account_ids = _get_user_accounts(uid).ids
            include_body = request.httprequest.args.get('include_body', '0') == '1'

            Msg = request.env['lugal.email.message'].sudo()
            if thread_id:
                thread_msgs = Msg.search([
                    ('account_id', 'in', account_ids),
                    ('is_deleted', '=', False),
                    ('thread_id',  '=', thread_id),
                ], order='date asc, id asc')
            else:
                # Fallback: no thread_id — return just this message
                thread_msgs = anchor

            # Always ensure the anchor itself is in the list even if thread_id is missing
            if anchor.id not in thread_msgs.ids:
                thread_msgs = anchor | thread_msgs

            items = [_message_to_dict(m, full=include_body) for m in thread_msgs]
            return _json_response({
                'success': True,
                'data': {
                    'thread_id':    thread_id or None,
                    'total':        len(items),
                    'messages':     items,
                },
            })
        except Exception as exc:
            _logger.exception('message_thread error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/details', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def message_details_bulk(self, **kwargs):
        """Return full body + attachments for a batch of message IDs in one call.

        Request body (JSON):
          { "message_ids": [1337, 1338, 1339] }   — max 50 IDs per call.

        Response:
          {
            "success": true,
            "data": {
              "items": [
                { "id": 1337, "body_html": "...", "body_text": "...", "attachments": [] }
              ],
              "missing_ids": [1339]   // IDs not found / not owned by caller / deleted
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            message_ids = body.get('message_ids')
            if not isinstance(message_ids, list) or not message_ids:
                return _json_response(
                    {'success': False, 'error': 'message_ids must be a non-empty array'},
                    400,
                )
            if len(message_ids) > 50:
                return _json_response(
                    {'success': False, 'error': 'message_ids may not exceed 50 items per request'},
                    400,
                )
            if not all(isinstance(i, int) for i in message_ids):
                return _json_response(
                    {'success': False, 'error': 'message_ids must be an array of integers'},
                    400,
                )

            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            Msg  = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids).filtered(
                lambda m: m.exists() and not m.is_deleted and m.account_id.id in account_ids
            )
            found_ids = set(msgs.ids)
            missing_ids = [i for i in message_ids if i not in found_ids]

            # If we have missing IDs it likely means the inbox hasn't synced yet.
            # Kick off a background sync for every account that is overdue so
            # subsequent requests pick up the messages. Non-blocking / non-fatal.
            if missing_ids:
                try:
                    db_name = request.env.cr.dbname
                    for acc in user_accounts:
                        if (acc.password or '').strip() and _needs_imap_sync(acc):
                            _run_imap_sync_bg(acc.id, db_name)
                except Exception:
                    pass

            # Lazy-fetch bodies that were imported as headers-only (any folder)
            for msg in msgs:
                if not msg.body_fetched and msg.imap_uid:
                    try:
                        msg.account_id.sudo().fetch_message_body(msg.id)
                        msg.invalidate_recordset()
                    except Exception:
                        _logger.exception('Bulk lazy body fetch failed for message %s', msg.id)

            items = []
            for msg in msgs:
                attachments, inline_attachments = _message_attachment_buckets(msg)
                items.append({
                    'id':                  msg.id,
                    'account_id':          msg.account_id.id,
                    'folder':              msg.folder,
                    'folder_role':         _folder_role(msg.folder),
                    'is_read':             msg.is_read,
                    'read_at':             _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                    'version':             _to_riyadh_iso(msg.write_date),
                    'write_date':          _to_riyadh_iso(msg.write_date),
                    'body_html':           msg.body_html or '',
                    'body_text':           msg.body_text or '',
                    'attachments':         attachments,
                    'inline_attachments':  inline_attachments,
                })

            return _json_response({
                'success': True,
                'data': {
                    'items':       items,
                    'missing_ids': missing_ids,
                },
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('message_details_bulk error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Notifications & Unread ────────────────────────────────────────────────

    @http.route(['/api/lugal/email/notifications', '/api/lugal/email/unread'],
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def notifications(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            params = request.httprequest.args
            # Optional ISO datetime: only return new_messages received after this timestamp.
            # Pass the `data.checked_at` value from the previous poll response.
            since_str = params.get('since', '')
            # Optional integer: only return messages with id > last_seen_id.
            # Complements since= for browsers that missed a push notification
            # (e.g. second browser session that connected after the push was sent).
            last_seen_id = int(params.get('last_seen_id', 0) or 0)

            accs = _get_user_accounts(uid)
            notification_folder_domain = [
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ]

            # ── Auto-sync for accounts that are stale/never synced/errored ─
            # The notifications endpoint is often called before the inbox is opened.
            # Without this, notifications can show stale counts/messages until
            # the user manually hits resync.
            db_name = request.env.cr.dbname
            sync_threads = []
            for acc in accs:
                needs_urgent_sync = (
                    (acc.password or '').strip() and
                    (
                        acc.sync_status in ('never', 'error')
                        or not acc.last_sync_date
                        or _needs_imap_sync(acc)
                    )
                )
                if needs_urgent_sync:
                    try:
                        force_now = acc.sync_status in ('never', 'error') or not acc.last_sync_date
                        t = _run_imap_sync_bg(acc.id, db_name, force=force_now)
                        if t:
                            sync_threads.append(t)
                            _logger.info(
                                'notifications: triggered freshness sync for account %s '
                                '(sync_status=%s)', acc.id, acc.sync_status,
                            )
                    except Exception:
                        _logger.exception(
                            'notifications: urgent sync kick failed for account %s', acc.id,
                        )

            # Wait briefly for syncs so the response contains fresh counts.
            # If the sync takes longer the FE will get the cached (possibly stale) counts
            # and the sync will complete in the background.
            has_cold_sync = any(
                a.sync_status in ('never', 'error') or not a.last_sync_date
                for a in accs
            )
            wait_timeout = 8.0 if has_cold_sync else 3.0
            for t in sync_threads:
                t.join(timeout=wait_timeout)

            # Re-read accounts after sync to pick up updated unread_count / sync_status.
            accs = _get_user_accounts(uid)
            custom_folder_sync = _sync_unread_custom_folders(accs)

            per_account = []
            total_unread = 0
            for acc in accs:
                # Count unread inbound messages from DB (source of truth).
                # Includes custom rule folders such as INBOX.syed_naqvi and
                # INBOX.syed_naqvi.Important, not only literal inbox.
                unread = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', '=', acc.id),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ] + notification_folder_domain)
                total_unread += unread
                has_pw     = bool((acc.password or '').strip())
                err_msg    = acc.sync_error_msg or ''
                is_auth    = 'AUTHENTICATIONFAILED' in err_msg.upper() or 'INVALID CREDENTIALS' in err_msg.upper()
                needs_setup = not has_pw or is_auth
                per_account.append({
                    'id':             acc.id,
                    'name':           acc.name,
                    'unread_count':   unread,
                    'sync_status':    acc.sync_status or 'never',
                    'last_sync_date': _to_riyadh_iso(acc.last_sync_date),
                    'sync_error':     err_msg or None,
                    'password_set':   has_pw,
                    # needs_setup=true means inbox will remain empty until
                    # the user (or admin) configures valid credentials.
                    'needs_setup':    needs_setup,
                    'setup_reason':   ('invalid_credentials' if is_auth
                                       else ('no_password' if not has_pw else None)),
                })

            # Per-folder unread totals across all accounts
            account_ids = accs.ids
            per_folder = {}
            for folder in ('inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'):
                per_folder[folder] = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', 'in', account_ids),
                    ('folder', '=', folder),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])
            per_folder['inbound'] = request.env['lugal.email.message'].sudo().search_count([
                ('account_id', 'in', account_ids),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ] + notification_folder_domain)

            last_sync = None
            if accs:
                dates = [a.last_sync_date for a in accs if a.last_sync_date]
                if dates:
                    last_sync = _to_riyadh_iso(max(dates))

            Msg = request.env['lugal.email.message'].sudo()

            # ── New inbound messages (for browser/in-app notifications) ────────
            # Returns up to 10 most recent UNREAD inbound messages, including
            # custom rule folders.
            # If `?since=<ISO datetime>` is supplied only messages received after
            # that timestamp are returned, so the FE can detect new arrivals
            # without comparing counts.
            new_msg_domain = [
                ('account_id', 'in', account_ids),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ] + notification_folder_domain
            if since_str:
                try:
                    from odoo.fields import Datetime as OdooDatetime
                    since_dt = OdooDatetime.from_string(since_str.replace('T', ' ')[:19])
                    new_msg_domain.append(('date', '>', since_dt))
                except Exception:
                    pass  # ignore bad since value
            # last_seen_id allows the FE to detect messages it missed (e.g. if the
            # WebSocket push was lost because the browser wasn't subscribed yet).
            # On each poll, send the highest message id seen so far; the server
            # returns any inbox messages with id > last_seen_id.
            if last_seen_id:
                new_msg_domain.append(('id', '>', last_seen_id))
            new_inbox = Msg.search(new_msg_domain, order='date desc', limit=10)
            new_messages = [
                {
                    'id':           m.id,
                    'account_id':   m.account_id.id,
                    'account_name': m.account_id.name or m.account_id.email_address,
                    'subject':      m.subject or '(no subject)',
                    'from_name':    m.from_name or '',
                    'from_address': m.from_address or '',
                    'date':         _to_riyadh_iso(m.date),
                    'is_read':      m.is_read,
                    'folder':       m.folder or 'inbox',
                }
                for m in new_inbox
            ]

            # ── Recently sent messages and their SMTP delivery status ──────────
            # FE polls this to show ✓ (sent) / ✓✓ (delivered) indicators.
            recent_sent = Msg.search([
                ('account_id', 'in', account_ids),
                ('folder', '=', 'sent'),
                ('is_deleted', '=', False),
            ], order='date desc', limit=20)
            sent_status = [
                {
                    'id':             m.id,
                    'subject':        m.subject or '',
                    'date':           _to_riyadh_iso(m.date),
                    'to_addresses':   m.to_addresses or '[]',
                    'smtp_delivered': m.smtp_delivered,
                    'smtp_error':     m.smtp_error or None,
                    'smtp_status':    m.smtp_status or 'pending',
                }
                for m in recent_sent
            ]

            from datetime import datetime as _nowdt
            return _json_response({
                'success': True,
                'data': {
                    'inbox':              per_folder.get('inbox', 0),
                    'total':              total_unread,
                    'per_folder':         per_folder,
                    # account_configured=true only when at least one account
                    # has a password set AND is NOT in an auth-failure state.
                    'account_configured': any(
                        not a.get('needs_setup') for a in per_account
                    ),
                    'accounts':           per_account,
                    'sync_status':        accs[0].sync_status if accs else 'never',
                    'last_sync_date':     last_sync,
                    # Use this value as the `?since=` param on your next poll.
                    'checked_at':         _nowdt.now(tz=_RIYADH_TZ).strftime('%Y-%m-%dT%H:%M:%S+03:00'),
                    'new_messages':       new_messages,
                    'custom_folder_sync': custom_folder_sync,
                    'recently_sent':      sent_status,
                },
            })
        except Exception as exc:
            _logger.exception('notifications error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Compose: Send / Reply / Forward ──────────────────────────────────────

    @http.route('/api/lugal/email/send', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def send_email(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            account_id = body.get('account_id')
            to         = body.get('to', [])
            if isinstance(to, str):
                to = [to]
            # Normalize: FE may send [{"email": "..."}, ...] or ["email@...", ...]
            to_emails  = _norm_addr_list(to)
            subject    = body.get('subject', '')
            body_html  = body.get('body_html', body.get('body', ''))
            body_text  = body.get('body_text', '')
            written_in_arabic = _truthy(body.get('written_in_arabic'))
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))

            if not to_emails:
                return _json_response({'success': False, 'error': "'to' is required"}, 400)

            attachment_ids = body.get('attachment_ids', [])

            # Resolve account
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _not_found('Email account not found')
            else:
                accs = _get_user_accounts(uid).filtered('is_default')
                acc  = accs[0] if accs else _get_user_accounts(uid)[:1]
                if not acc:
                    return _json_response({'success': False, 'error': 'No email account configured'}, 400)

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))

            # Store in sent folder
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses':        json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':           body_html,
                'body_text':           body_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
            })
            # New compose: this message IS the root of its own thread.
            if msg.message_id and not msg.thread_id:
                msg.write({'thread_id': msg.message_id})

            # Link uploaded attachments to this message so they appear in
            # message details APIs and are preserved for thread display.
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass

            # Commit NOW so the background SMTP thread can see the message row
            # and attachments immediately via its own fresh cursor.
            request.env.cr.commit()

            # Fire SMTP in background — all file I/O + network happens in daemon
            # thread; the HTTP response is returned without waiting.
            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text, cc_emails, bcc_emails,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
            )

            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True  # SMTP running in background
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            _logger.exception('send_email error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/reply', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def reply(self, message_id, **kwargs):
        """GET → returns compose prefill (to, subject, quoted_body_html, quoted_body_text).
           POST → sends the reply immediately.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()

            acc       = orig.account_id
            own_email = (acc.email_address or '').strip().lower()

            # Reply-To takes precedence over From per RFC 5322
            reply_addr = (orig.reply_to or '').strip() or (orig.from_address or '').strip()
            reply_name = orig.from_name or orig.from_address or ''
            to_addr    = [reply_addr] if reply_addr else []

            subject = (orig.subject or '') if (orig.subject or '').startswith('Re:') \
                      else f"Re: {orig.subject or ''}"

            if request.httprequest.method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {
                        'to':  [{'name': reply_name, 'email': reply_addr}] if reply_addr else [],
                        'cc':  [],
                        'bcc': [],
                        'subject':          subject,
                        'in_reply_to':      orig.message_id or '',
                        # body_html/body_text: initialize the compose box to empty.
                        # The user types their reply here; the backend appends the
                        # quoted block automatically on POST so raw HTML never appears
                        # in the editor.
                        'body_html':        '',
                        'body_text':        '',
                        # quoted_body_html/text: the formatted quote block (for display
                        # as a read-only preview below the editor if the FE wishes).
                        # Do NOT insert these into the editable composer.
                        'quoted_body_html': _build_quoted_html(orig),
                        'quoted_body_text': _build_quoted_text(orig),
                    },
                })

            body = json.loads(request.httprequest.data or '{}')

            # Build complete email body: user's content + quoted original.
            # The FE compose box only collects the user's new reply text;
            # the quoted block is assembled here so raw HTML never appears in the editor.
            user_html   = (body.get('body_html', '') or '').strip()
            user_text   = (body.get('body_text', '') or '').strip()
            written_in_arabic = _truthy(body.get('written_in_arabic'))

            # skip_auto_quote=true → FE has already embedded the quoted block
            # inside body_html itself.  In that case, don't append it a second
            # time or the email will contain double quoted sections and double
            # signatures.  FE should set this flag whenever it places the
            # quoted_body_html from the GET prefill directly into the editable
            # composer field that it sends back on POST.
            skip_auto_quote = bool(body.get('skip_auto_quote', False))

            # Heuristic safety-net: even without the explicit flag, if the
            # submitted body_html already contains a blockquote we assume the
            # FE included the quote and skip appending it again.
            if not skip_auto_quote and user_html:
                skip_auto_quote = '</blockquote>' in user_html.lower()

            if skip_auto_quote:
                final_html = user_html
                final_text = user_text
            else:
                quoted_html = _build_quoted_html(orig)
                quoted_text = _build_quoted_text(orig)
                final_html  = (user_html + quoted_html) if user_html else quoted_html
                final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            thread_vals = _thread_vals_for_reply(orig)
            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            vals = {
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_addr]),
                'cc_addresses':        json.dumps([{'email': e} for e in _norm_addr_list(body.get('cc', []))]),
                'bcc_addresses':       json.dumps([{'email': e} for e in _norm_addr_list(body.get('bcc', []))]),
                'body_html':           final_html,
                'body_text':           final_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
                **thread_vals,
            }
            if orig.linked_customer_id:
                vals['linked_customer_id'] = orig.linked_customer_id
            if orig.linked_ticket_id:
                vals['linked_ticket_id'] = orig.linked_ticket_id
            msg = request.env['lugal.email.message'].sudo().create(vals)
            attachment_ids = body.get('attachment_ids', [])
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass
            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_addr, subject, final_html, final_text,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/reply_all', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def reply_all(self, message_id, **kwargs):
        """GET  → returns compose prefill (to, cc, subject, quoted body).
           POST → sends the reply-all immediately.

        To field rules (RFC 5322):
          - If original has Reply-To, that goes in To (primary).
          - Plus all original To addresses excluding the sender's own address.
          - Original From is added to To only when Reply-To is absent.
        Cc  = all original Cc addresses, excluding the sender's own address.
        Bcc = never copied from original (not transmitted in received emails).
              POST body may include extra bcc:[...] addresses.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()

            acc       = orig.account_id
            own_email = (acc.email_address or '').strip().lower()

            # ── Build To list (RFC 5322 §3.6.2) ──────────────────────────────
            # If Reply-To is set, it replaces From as the primary reply target.
            # All original To recipients are still included (Reply All = everyone).
            orig_to_parsed = []
            try:
                orig_to_parsed = json.loads(orig.to_addresses or '[]')
            except Exception:
                pass

            reply_to_override = (orig.reply_to or '').strip()
            to_entries: list[dict] = []   # {'name': ..., 'email': ...}
            seen_emails: set[str] = set()

            def _add_to(name: str, email: str, target: list):
                """Append to target list, skipping own address and duplicates."""
                e = email.strip()
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    target.append({'name': name, 'email': e})

            if reply_to_override:
                # Reply-To takes precedence as the primary reply address
                _add_to('', reply_to_override, to_entries)
            else:
                # No Reply-To: use the original From
                _add_to(orig.from_name or '', orig.from_address or '', to_entries)

            # Add remaining original To recipients (they're already part of "all")
            for entry in orig_to_parsed:
                _add_to(
                    entry.get('name') or '',
                    entry.get('email') or '',
                    to_entries,
                )

            # ── Build Cc list ──────────────────────────────────────────────────
            orig_cc_parsed = []
            try:
                orig_cc_parsed = json.loads(orig.cc_addresses or '[]')
            except Exception:
                pass

            cc_entries: list[dict] = []
            for entry in orig_cc_parsed:
                e  = (entry.get('email') or '').strip()
                el = e.lower()
                # Skip own address AND addresses already in To (no duplicates)
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    cc_entries.append({'name': entry.get('name') or '', 'email': e})

            subject = (orig.subject or '') if (orig.subject or '').startswith('Re:') \
                      else f"Re: {orig.subject or ''}"

            if request.httprequest.method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {
                        'to':      to_entries,
                        'cc':      cc_entries,
                        'bcc':     [],
                        'subject': subject,
                        'in_reply_to':      orig.message_id or '',
                        # body_html/body_text: initialize the compose box to empty.
                        'body_html':        '',
                        'body_text':        '',
                        # quoted_body_html/text: read-only preview below the editor.
                        # Do NOT insert these into the editable composer.
                        'quoted_body_html': _build_quoted_html(orig),
                        'quoted_body_text': _build_quoted_text(orig),
                    },
                })

            # ── POST: send the reply ───────────────────────────────────────────
            body = json.loads(request.httprequest.data or '{}')

            # Merge any extra addresses the FE added in the compose window
            for e in _norm_addr_list(body.get('to', [])):
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    to_entries.append({'name': '', 'email': e})
            for e in _norm_addr_list(body.get('cc', [])):
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    cc_entries.append({'name': '', 'email': e})

            to_addrs  = [entry['email'] for entry in to_entries]
            cc_addrs  = [entry['email'] for entry in cc_entries]
            bcc_addrs = _norm_addr_list(body.get('bcc', []))

            if not to_addrs:
                return _json_response(
                    {'success': False, 'error': 'No recipients to reply to'}, 400
                )

            # Build complete email body: user's content + quoted original.
            user_html   = (body.get('body_html', '') or '').strip()
            user_text   = (body.get('body_text', '') or '').strip()
            written_in_arabic = _truthy(body.get('written_in_arabic'))

            skip_auto_quote = bool(body.get('skip_auto_quote', False))
            if not skip_auto_quote and user_html:
                skip_auto_quote = '</blockquote>' in user_html.lower()

            if skip_auto_quote:
                final_html = user_html
                final_text = user_text
            else:
                quoted_html = _build_quoted_html(orig)
                quoted_text = _build_quoted_text(orig)
                final_html  = (user_html + quoted_html) if user_html else quoted_html
                final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            thread_vals = _thread_vals_for_reply(orig)
            vals = {
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps(to_entries),
                'cc_addresses':        json.dumps(cc_entries),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_addrs]),
                'body_html':           final_html,
                'body_text':           final_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
                **thread_vals,
            }
            if orig.linked_customer_id:
                vals['linked_customer_id'] = orig.linked_customer_id
            if orig.linked_ticket_id:
                vals['linked_ticket_id'] = orig.linked_ticket_id

            msg = request.env['lugal.email.message'].sudo().create(vals)
            attachment_ids = body.get('attachment_ids', [])
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass

            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_addrs, subject,
                final_html, final_text,
                cc=cc_addrs, bcc=bcc_addrs,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            _logger.exception('reply_all error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/forward', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def forward(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()
            body    = json.loads(request.httprequest.data or '{}')
            acc     = orig.account_id
            to      = body.get('to', [])
            to_fwd   = _norm_addr_list(to)
            cc_fwd   = _norm_addr_list(body.get('cc', []))
            bcc_fwd  = _norm_addr_list(body.get('bcc', []))
            subject = f"Fwd: {orig.subject or ''}"
            importance_raw = (body.get('importance') or 'normal').lower()
            written_in_arabic = _truthy(body.get('written_in_arabic'))
            # Combine the user's intro text (if any) with the properly formatted
            # quoted original message.  Using _build_quoted_html gives a consistent
            # "---------- Forwarded message ----------" style header.
            fwd_user_html = (body.get('body_html', '') or '').strip()
            fwd_quoted    = _build_quoted_html(orig)
            fwd_body      = (fwd_user_html + fwd_quoted) if fwd_user_html else fwd_quoted
            fwd_thread = _thread_vals_for_forward(orig)
            fwd_attachment_ids   = body.get('attachment_ids', [])
            request_read_receipt = bool(body.get('request_read_receipt', False))
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_fwd]),
                'cc_addresses':        json.dumps([{'email': e} for e in cc_fwd]),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_fwd]),
                'body_html':           fwd_body,
                'body_text':           body.get('body_text', ''),
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
                **fwd_thread,
            })
            # Forward is the root of a new thread on OUR side — use its own msg-id
            if not msg.thread_id and msg.message_id:
                msg.write({'thread_id': msg.message_id})
            if fwd_attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in fwd_attachment_ids]
                    ).write({'res_id': msg.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass
            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_fwd, subject, fwd_body, body.get('body_text', ''),
                cc=cc_fwd, bcc=bcc_fwd,
                msg_id=msg.id, attachment_ids=fwd_attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Status Actions ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/read', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def toggle_read(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg  = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            body     = json.loads(request.httprequest.data or '{}')
            is_read  = body.get('is_read', True)

            # ── Sent-folder messages: is_read/read_at track RECIPIENT read status ──
            # The sender viewing their own sent copy must NOT update is_read/read_at.
            # We still push \Seen to IMAP so the sender's client clears the unread
            # badge, but the DB fields remain driven solely by recipient activity
            # (_propagate_read_to_sent_copies, MDN handler).
            if _is_sent_folder(msg.folder):
                if msg.imap_uid and is_read:
                    imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Seen']
                    )
                unread_count = _refresh_account_unread_count(msg.account_id)
                return _json_response({'success': True, 'data': {
                    'is_read': msg.is_read,
                    'read_at': _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                    'unread_count': unread_count,
                }})

            # ── Inbox / custom-folder messages: normal read handling ──────────────
            # Capture pre-write state before the write() override may stamp read_at
            was_already_read = bool(msg.read_at)
            msg.write({'is_read': is_read})
            unread_count = _refresh_account_unread_count(msg.account_id)
            # Push \Seen / -\Seen flag to IMAP server
            if msg.imap_uid:
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
                if is_read:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Seen']
                    )
                else:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, remove_flags=['\\Seen']
                    )
            # Propagate read confirmation to the sender's sent-folder copy so the
            # sender sees is_read=True once any recipient actually reads the message.
            if is_read and not was_already_read and msg.message_id:
                _propagate_read_to_sent_copies(
                    request.env, msg.message_id, msg.read_at or fields.Datetime.now()
                )
            # Send MDN if: marking as read for the first time, the original
            # sender requested a receipt, and this is an inbox message.
            if (is_read and not was_already_read
                    and msg.request_read_receipt
                    and msg.folder in ('inbox',)
                    and msg.from_address
                    and msg.message_id):
                try:
                    _send_mdn_async(
                        acc=msg.account_id,
                        to_address=msg.from_address,
                        original_message_id=msg.message_id,
                        original_subject=msg.subject or '',
                        recipient_email=msg.account_id.email_address,
                    )
                except Exception as _mdn_exc:
                    _logger.warning('MDN trigger failed (toggle_read): %s', _mdn_exc)
            return _json_response({'success': True, 'data': {
                'is_read': is_read,
                'read_at': _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                'unread_count': unread_count,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/star', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def toggle_star(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            new_starred = not msg.is_starred
            msg.write({'is_starred': new_starred})
            # Push \Flagged / -\Flagged to IMAP server
            if msg.imap_uid:
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
                if new_starred:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Flagged']
                    )
                else:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, remove_flags=['\\Flagged']
                    )
            return _json_response({'success': True, 'data': {'is_starred': msg.is_starred}})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/restore', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def restore(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            prev_folder = msg.folder
            msg.write({'folder': 'inbox'})
            unread_count = _refresh_account_unread_count(msg.account_id)
            # Move back to INBOX on the IMAP server
            if msg.imap_uid:
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'inbox')
            return _json_response({'success': True, 'unread_count': unread_count})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/archive', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def archive_msg(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            prev_folder = msg.folder
            msg.write({'folder': 'archive'})
            unread_count = _refresh_account_unread_count(msg.account_id)
            # Move to Archive folder on the IMAP server
            if msg.imap_uid:
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'archive')
            return _json_response({'success': True, 'unread_count': unread_count})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/unarchive', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def unarchive_msg(self, message_id, **kwargs):
        """Move a message from the archive folder back to the inbox."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            if msg.folder != 'archive':
                return _json_response(
                    {'success': False, 'error': 'Message is not in the archive folder'},
                    409,
                )
            msg.write({'folder': 'inbox'})
            unread_count = _refresh_account_unread_count(msg.account_id)
            if msg.imap_uid:
                imap_archive = _resolve_imap_folder(msg.account_id, 'archive')
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_archive, 'inbox')
            return _json_response({'success': True, 'unread_count': unread_count})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/permanent', type='http', auth='none', csrf=False,
                methods=['DELETE', 'OPTIONS'])
    def message_permanent_delete(self, message_id, **kwargs):
        """Hard-delete a single message from the DB.

        The message MUST be in the 'trash' folder; attempting to permanently
        delete a message that is still in any other folder returns 409 so the
        FE can show a "move to trash first" hint.

        On success the record is gone from the DB — no recovery possible.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            if msg.folder != 'trash':
                return _json_response(
                    {'success': False, 'error': 'Message must be in trash before permanent deletion'},
                    409,
                )
            imap_uid = msg.imap_uid
            acc      = msg.account_id.sudo()
            msg.sudo().unlink()
            unread_count = _refresh_account_unread_count(acc)
            # Expunge from IMAP Trash folder so webmail also removes it permanently
            if imap_uid:
                trash_folder = acc._get_server_folder_name('trash')
                acc._imap_expunge_async(imap_uid, trash_folder)
            return _json_response({'success': True, 'deleted_id': message_id, 'unread_count': unread_count})
        except Exception as exc:
            _logger.exception('message_permanent_delete error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/bulk_delete', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def message_bulk_permanent_delete(self, **kwargs):
        """Hard-delete multiple messages in one call.

        All messages must be in the 'trash' folder and owned by the caller.
        Messages that are not in trash, not found, or belong to another user
        are silently skipped and reported in 'skipped_ids'.

        Request body (JSON):
          { "message_ids": [1, 2, 3] }   — max 1000 IDs per call.

        Response:
          {
            "success": true,
            "data": {
              "deleted_ids": [1, 2],
              "skipped_ids": [3]
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            message_ids = body.get('message_ids')
            if not isinstance(message_ids, list) or not message_ids:
                return _json_response(
                    {'success': False, 'error': 'message_ids must be a non-empty array'},
                    400,
                )
            if len(message_ids) > 1000:
                return _json_response(
                    {'success': False, 'error': 'message_ids may not exceed 1000 per request'},
                    400,
                )
            if not all(isinstance(i, int) for i in message_ids):
                return _json_response(
                    {'success': False, 'error': 'message_ids must be an array of integers'},
                    400,
                )

            user_account_ids = _get_user_accounts(uid).ids
            Msg = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids)

            to_delete = msgs.filtered(
                lambda m: m.exists()
                and not m.is_deleted
                and m.account_id.id in user_account_ids
                and m.folder == 'trash'
            )
            deleted_ids  = to_delete.ids
            skipped_ids  = [i for i in message_ids if i not in deleted_ids]
            affected_accounts = to_delete.mapped('account_id')
            to_delete.unlink()
            unread_counts = {
                str(acc.id): _refresh_account_unread_count(acc)
                for acc in affected_accounts
            }

            return _json_response({
                'success': True,
                'data': {
                    'deleted_ids': deleted_ids,
                    'skipped_ids': skipped_ids,
                    'unread_counts': unread_counts,
                },
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('message_bulk_permanent_delete error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Record Linking ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/link', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def link_message(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg  = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            body      = json.loads(request.httprequest.data or '{}')
            model     = body.get('model', '')
            record_id = body.get('record_id')
            if model not in ALLOWED_LINK_MODELS:
                return _json_response({'success': False, 'error': f'Model {model} not allowed'}, 400)
            vals = {
                'linked_model':       model,
                'linked_record_id':   record_id,
                'linked_record_name': body.get('record_name', ''),
            }
            if model == 'lugal.crm.customer':
                vals['linked_customer_id'] = record_id
                vals['linked_customer_name'] = body.get('record_name', '')
            elif model == 'lugal.crm.ticket':
                vals['linked_ticket_id'] = record_id
                vals['linked_ticket_name'] = body.get('record_name', '')
            msg.write(vals)
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/unlink', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def unlink_message(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            msg.write({
                'linked_model': False, 'linked_record_id': False,
                'linked_record_name': False,
                'linked_customer_id': False, 'linked_customer_name': False,
                'linked_ticket_id': False, 'linked_ticket_name': False,
            })
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)


    # ── Draft Emails ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/drafts', type='http', auth='none', csrf=False,
                methods=['POST', 'GET', 'OPTIONS'])
    def drafts(self, **kwargs):
        """
        GET  /api/lugal/email/drafts
             List all drafts for the authenticated user.
             Query params: limit (int, default 50), offset (int, default 0)

        POST /api/lugal/email/drafts
             Create a new draft (or auto-save an existing one by passing "id").
             Body (JSON):
               {
                 "account_id":    4,           // required
                 "to":            ["a@b.com"],  // optional
                 "cc":            [],
                 "bcc":           [],
                 "subject":       "...",
                 "body_html":     "<p>...</p>",
                 "body_text":     "...",
                 "attachment_ids": [42, 43],    // already-uploaded ir.attachment IDs
                 "id":            123           // if present: UPDATE existing draft
               }
             Response: { "success": true, "data": { <draft message dict> } }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        # ── GET: list drafts ──────────────────────────────────────────────────
        if request.httprequest.method == 'GET':
            try:
                args = request.httprequest.args
                limit  = int(args.get('limit', 50))
                offset = int(args.get('offset', 0))
                account_ids = [a.id for a in _get_user_accounts(uid)]
                if not account_ids:
                    return _json_response({'success': True, 'data': {'total': 0, 'items': []}})
                Msg   = request.env['lugal.email.message'].sudo()
                domain = [
                    ('account_id', 'in', account_ids),
                    ('is_draft',   '=', True),
                    ('is_deleted', '=', False),
                ]
                total = Msg.search_count(domain)
                msgs  = Msg.search(domain, limit=limit, offset=offset, order='write_date desc')
                return _json_response({
                    'success': True,
                    'data': {
                        'total':  total,
                        'limit':  limit,
                        'offset': offset,
                        'items':  [_message_to_dict(m, full=True) for m in msgs],
                    },
                })
            except Exception as exc:
                _logger.exception('drafts GET error')
                return _json_response({'success': False, 'error': str(exc)}, 500)

        # ── POST: create / update draft ───────────────────────────────────────
        try:
            body       = json.loads(request.httprequest.data or '{}')
            draft_id   = body.get('id')
            account_id = body.get('account_id')
            to_emails  = _norm_addr_list(body.get('to', []))
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))
            subject    = body.get('subject', '')
            body_html  = body.get('body_html', body.get('body', ''))
            body_text  = body.get('body_text', '')
            written_in_arabic = _truthy(body.get('written_in_arabic'))
            att_ids    = body.get('attachment_ids', [])

            # Resolve account
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _not_found('Email account not found')
            else:
                accs = _get_user_accounts(uid).filtered('is_default')
                acc  = accs[0] if accs else _get_user_accounts(uid)[:1]
                if not acc:
                    return _json_response({'success': False, 'error': 'No email account configured'}, 400)

            vals = {
                'account_id':   acc.id,
                'folder':       'drafts',
                'is_draft':     True,
                'is_read':      True,
                'body_fetched': True,
                'from_name':    acc.display_name_field or acc.email_address,
                'from_address': acc.email_address,
                'to_addresses': json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses': json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_emails]),
                'subject':      subject,
                'body_html':    body_html,
                'body_text':    body_text,
                'written_in_arabic': written_in_arabic,
                'date':         __import__('odoo').fields.Datetime.now(),
            }

            Msg = request.env['lugal.email.message'].sudo()
            if draft_id:
                # Update existing draft
                draft = Msg.browse(int(draft_id))
                if not draft.exists() or not draft.is_draft or draft.account_id.user_id.id != uid:
                    return _not_found('Draft not found')
                draft.write(vals)
                msg = draft
            else:
                msg = Msg.create(vals)

            # Link attachments to this draft
            if att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in att_ids]
                    ).write({'res_id': msg.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass

            return _json_response({'success': True, 'data': _message_to_dict(msg, full=True)},
                                  200 if draft_id else 201)
        except Exception as exc:
            _logger.exception('drafts POST error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/drafts/<int:draft_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    def draft_detail(self, draft_id, **kwargs):
        """
        GET    /api/lugal/email/drafts/<id>  — fetch a single draft with full body + attachments
        PUT    /api/lugal/email/drafts/<id>  — replace draft content (same body as POST /drafts)
        PATCH  /api/lugal/email/drafts/<id>  — partial update (same body, only provided fields updated)
        DELETE /api/lugal/email/drafts/<id>  — permanently discard the draft
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        try:
            draft = request.env['lugal.email.message'].sudo().browse(draft_id)
            if not draft.exists() or not draft.is_draft \
                    or draft.is_deleted or draft.account_id.user_id.id != uid:
                return _not_found('Draft not found')

            method = request.httprequest.method

            if method == 'GET':
                return _json_response({'success': True, 'data': _message_to_dict(draft, full=True)})

            if method == 'DELETE':
                draft.write({'is_deleted': True, 'active': False})
                return _json_response({'success': True})

            # PUT / PATCH — update fields
            body       = json.loads(request.httprequest.data or '{}')
            to_emails  = _norm_addr_list(body.get('to', []))
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))
            att_ids    = body.get('attachment_ids', [])

            vals = {}
            if 'to'        in body: vals['to_addresses']  = json.dumps([{'email': e} for e in to_emails])
            if 'cc'        in body: vals['cc_addresses']  = json.dumps([{'email': e} for e in cc_emails])
            if 'bcc'       in body: vals['bcc_addresses'] = json.dumps([{'email': e} for e in bcc_emails])
            if 'subject'   in body: vals['subject']    = body['subject']
            if 'body_html' in body: vals['body_html']  = body.get('body_html', '')
            if 'body_text' in body: vals['body_text']  = body.get('body_text', '')
            if 'body'      in body: vals['body_html']  = body.get('body', '')
            if 'written_in_arabic' in body:
                vals['written_in_arabic'] = _truthy(body.get('written_in_arabic'))

            if vals:
                draft.write(vals)
            if att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in att_ids]
                    ).write({'res_id': draft.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass

            return _json_response({'success': True, 'data': _message_to_dict(draft, full=True)})
        except Exception as exc:
            _logger.exception('draft_detail error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/drafts/<int:draft_id>/send', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def send_draft(self, draft_id, **kwargs):
        """
        POST /api/lugal/email/drafts/<id>/send

        Sends an existing draft via SMTP (async — returns immediately).
        Optionally accepts a body to make final edits before sending:
          {
            "to":             [...],   // override recipients
            "subject":        "...",   // override subject
            "body_html":      "...",   // override body
            "attachment_ids": [...]    // additional attachment IDs
          }
        The draft is moved to the sent folder on success.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            draft = request.env['lugal.email.message'].sudo().browse(draft_id)
            if not draft.exists() or not draft.is_draft \
                    or draft.is_deleted or draft.account_id.user_id.id != uid:
                return _not_found('Draft not found')

            # Idempotency guard: atomically claim the draft send with a row-level
            # lock so double-clicks or concurrent requests only trigger one SMTP send.
            try:
                request.env.cr.execute(
                    "SELECT id FROM lugal_email_message "
                    "WHERE id = %s AND is_draft = TRUE FOR UPDATE NOWAIT",
                    (draft_id,),
                )
                if not request.env.cr.fetchone():
                    return _json_response(
                        {'success': False, 'error': 'Draft already sent or is being sent'},
                        409,
                    )
            except Exception:
                # Lock contention: another request is already sending this draft.
                return _json_response(
                    {'success': False, 'error': 'Draft send already in progress'},
                    409,
                )

            body = json.loads(request.httprequest.data or '{}')
            requested_account_id = body.get('account_id')
            if requested_account_id not in (None, '', False):
                try:
                    requested_account_id = int(requested_account_id)
                except (TypeError, ValueError):
                    return _json_response(
                        {'success': False, 'error': 'account_id must be an integer'},
                        400,
                    )
                if requested_account_id != draft.account_id.id:
                    return _json_response(
                        {
                            'success': False,
                            'error': (
                                'Draft account_id mismatch: this draft belongs to '
                                f'account {draft.account_id.id}'
                            ),
                        },
                        409,
                    )

            # Apply any last-minute overrides
            to_emails  = _norm_addr_list(body['to']) if 'to' in body \
                         else _norm_addr_list(json.loads(draft.to_addresses or '[]'))
            cc_emails  = _norm_addr_list(body['cc']) if 'cc' in body \
                         else _norm_addr_list(json.loads(draft.cc_addresses or '[]'))
            bcc_emails = _norm_addr_list(body.get('bcc', [])) \
                         if 'bcc' in body \
                         else _norm_addr_list(json.loads(draft.bcc_addresses or '[]'))
            subject        = body.get('subject', draft.subject or '')
            body_html      = body.get('body_html', body.get('body', draft.body_html or ''))
            body_text      = body.get('body_text', draft.body_text or '')
            written_in_arabic = (
                _truthy(body.get('written_in_arabic'))
                if 'written_in_arabic' in body
                else bool(draft.written_in_arabic)
            )
            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))

            if not to_emails:
                return _json_response({'success': False, 'error': "'to' is required to send"}, 400)

            # Merge attachment IDs: already linked + any extras passed now
            existing_att_ids = [
                a.id for a in request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'lugal.email.message'),
                    ('res_id',    '=', draft.id),
                ])
            ]
            extra_att_ids = [int(i) for i in body.get('attachment_ids', [])]
            all_att_ids = list({*existing_att_ids, *extra_att_ids})

            # Move draft → sent
            import odoo as _odoo
            acc = draft.account_id
            draft.write({
                'folder':                'sent',
                'is_draft':              False,
                'is_read':               False,
                'read_at':               False,
                'subject':               subject,
                'from_name':             acc.display_name_field or acc.email_address,
                'from_address':          acc.email_address,
                'to_addresses':          json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses':          json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses':         json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':             body_html,
                'body_text':             body_text,
                'written_in_arabic':     written_in_arabic,
                'is_important':          importance_raw == 'high',
                'date':                  _odoo.fields.Datetime.now(),
                'request_read_receipt':  request_read_receipt,
            })
            # Link any extra attachments
            if extra_att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(extra_att_ids).write({
                        'res_id': draft.id, 'res_model': 'lugal.email.message',
                    })
                except Exception:
                    pass

            request.env.cr.commit()

            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text,
                cc=cc_emails, bcc=bcc_emails,
                msg_id=draft.id, attachment_ids=all_att_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
            )

            resp_data = _message_to_dict(draft)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 200)
        except Exception as exc:
            _logger.exception('send_draft error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Mailbox folders ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def account_folders(self, account_id, **kwargs):
        """List all IMAP folders for an account (including user-created ones).

        Returns stable folder objects:
          { "name": "INBOX", "path": "INBOX", "role": "inbox",
            "message_count": 42, "unread_count": 5 }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            import imaplib
            try:
                with acc._imap_session() as conn:
                    typ, raw_list = conn.list()
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP / per-user limit). '
                            'Wait a few seconds and retry; the app now queues IMAP access so this should be rare.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            if typ != 'OK':
                return _json_response({'success': False, 'error': 'IMAP LIST failed'}, 502)

            import re
            _LIST_RE = re.compile(r'\((?P<flags>[^)]*)\)\s+"(?P<delim>[^"]*)"\s+(?P<name>.+)')

            # Map common folder names to semantic roles (checked against full path
            # AND the last path segment so "INBOX.Sent", "INBOX/Sent", "Sent" all → "sent")
            _ROLE_MAP = {
                'inbox':          'inbox',
                'sent':           'sent', 'sent items': 'sent', 'sent messages': 'sent',
                'drafts':         'drafts', 'draft': 'drafts',
                'trash':          'trash', 'deleted': 'trash', 'deleted items': 'trash',
                'spam':           'spam', 'junk':  'spam', 'junk e-mail': 'spam',
                'archive':        'archive', 'archives': 'archive',
            }

            # IMAP special-use flags → role (RFC 6154)
            _FLAG_ROLE = {
                '\\sent':    'sent',
                '\\drafts':  'drafts',
                '\\trash':   'trash',
                '\\junk':    'spam',
                '\\spam':    'spam',
                '\\archive': 'archive',
                '\\all':     'archive',
                '\\inbox':   'inbox',
                # Some servers use bare names without backslash
                'sent':      'sent',
                'drafts':    'drafts',
                'trash':     'trash',
                'junk':      'spam',
                'spam':      'spam',
                'archive':   'archive',
            }

            def _resolve_role(raw_name, flags_str):
                """Determine semantic role from IMAP flags first, then folder name."""
                # 1. Check IMAP special-use flags (most reliable)
                for flag in flags_str.split():
                    role = _FLAG_ROLE.get(flag.lower())
                    if role:
                        return role
                # 2. Check full path
                role = _ROLE_MAP.get(raw_name.lower())
                if role:
                    return role
                # 3. Check last path segment (handles INBOX.Sent, INBOX/Trash, etc.)
                last_seg = raw_name.replace('/', '.').rsplit('.', 1)[-1].lower()
                return _ROLE_MAP.get(last_seg, 'custom')

            Msg = request.env['lugal.email.message'].sudo()

            # Detect the hierarchy delimiter from the first folder entry.
            delimiter = '.'
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                dm = _LIST_RE.match(line.strip())
                if dm:
                    delimiter = dm.group('delim') or '.'
                    break

            _STANDARD_ROLES = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

            folders = []
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = _LIST_RE.match(line.strip())
                if not m:
                    continue
                flags    = m.group('flags').lower()
                raw_name = m.group('name').strip().strip('"')
                if '\\noselect' in flags:
                    continue
                _INTERNAL_KEYWORDS = {'dovecot', 'sieve', 'courier', 'cyrus', '.subscriptions'}
                if any(kw in raw_name.lower() for kw in _INTERNAL_KEYWORDS):
                    continue
                role = _resolve_role(raw_name, m.group('flags'))

                # ── Count messages ──────────────────────────────────────────────
                # Standard folders: DB stores logical key ('inbox', 'sent', …)
                # Custom folders:   DB stores the raw IMAP path ('INBOX.omar.Important').
                # Namespace parents (e.g. INBOX.syed_naqvi) represent the whole
                # sender folder, so their counts include child folders.  Important
                # child folders only count important rows.
                local_folder_key = role if role in _STANDARD_ROLES else raw_name
                folder_domain = [('folder', '=', local_folder_key)]
                if role == 'custom':
                    child_count = Msg.search_count([
                        ('account_id', '=', acc.id),
                        ('is_deleted', '=', False),
                        '|',
                        ('folder', 'like', raw_name + delimiter + '%'),
                        ('folder', 'like', raw_name + ('/' if delimiter != '/' else '.') + '%'),
                    ])
                    if child_count:
                        folder_domain = [
                            '|', '|',
                            ('folder', '=', local_folder_key),
                            ('folder', 'like', raw_name + delimiter + '%'),
                            ('folder', 'like', raw_name + ('/' if delimiter != '/' else '.') + '%'),
                        ]
                    if raw_name.replace('/', '.').split('.')[-1].lower() == 'important':
                        folder_domain = [('folder', '=', local_folder_key), ('is_important', '=', True)]

                total  = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('is_deleted', '=', False),
                ] + folder_domain)
                unread = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('is_read',    '=', False),
                    ('is_deleted', '=', False),
                ] + folder_domain)

                # ── Tree metadata ───────────────────────────────────────────────
                # Split by the detected delimiter to compute depth and parent.
                parts = raw_name.split(delimiter)
                depth = len(parts) - 1   # INBOX → 0, INBOX.Sent → 1, INBOX.omar.Important → 2
                parent_path = delimiter.join(parts[:-1]) if depth > 0 else None

                folders.append({
                    'path':          raw_name,
                    'name':          parts[-1] or raw_name,
                    'parent_path':   parent_path,
                    'depth':         depth,
                    'role':          role,
                    'flags':         [f.strip().lstrip('\\') for f in m.group('flags').split() if f.strip()],
                    'message_count': total,
                    'unread_count':  unread,
                })

            # ── Build nested tree ───────────────────────────────────────────────
            # Index folders by path for O(1) child insertion.
            by_path = {f['path']: dict(f, children=[]) for f in folders}
            roots   = []
            for f in folders:
                node = by_path[f['path']]
                pp   = f['parent_path']
                if pp and pp in by_path:
                    by_path[pp]['children'].append(node)
                else:
                    roots.append(node)

            return _json_response({'success': True, 'data': {
                'total':     len(folders),
                'items':     folders,   # flat list (unchanged — FE may already use this)
                'tree':      roots,     # nested tree (new — use for sidebar rendering)
                'delimiter': delimiter,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Create folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/create',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_create(self, account_id, **kwargs):
        """Create a new IMAP folder for an account.

        Body:
          {
            "name":   "From Umar",   // required — display name (no separators)
            "parent": "INBOX"        // optional — parent path.
                                     //   Pass "" or omit → top-level folder.
                                     //   The server's hierarchy delimiter is
                                     //   detected automatically (. or /).
          }

        Returns:
          { "path": "INBOX.From Umar", "name": "From Umar",
            "parent": "INBOX", "delimiter": "." }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body   = json.loads(request.httprequest.data or '{}')
            name   = (body.get('name') or '').strip()
            # parent=None / "" / missing → top-level folder (no parent prefix)
            parent_raw = body.get('parent')
            parent = (parent_raw or '').strip() if parent_raw is not None else None

            if not name:
                return _json_response({'success': False, 'error': 'name is required'}, 400)
            if '"' in name:
                return _json_response({'success': False, 'error': 'name must not contain double-quotes'}, 400)

            import imaplib, re as _re, time as _time
            try:
                with acc._imap_session() as conn:
                    # ── Detect the server's hierarchy delimiter ──────────────────
                    delimiter = '.'   # safe default for most corporate IMAP servers
                    try:
                        _t, _l = conn.list('', '')
                        if _t == 'OK' and _l:
                            _dl = _l[0]
                            if isinstance(_dl, bytes):
                                _dl = _dl.decode('utf-8', errors='replace')
                            _dm = _re.search(r'\)\s+"([^"]+)"', _dl)
                            if _dm:
                                delimiter = _dm.group(1)
                    except Exception:
                        pass   # fallback to '.'

                    # Reject names that contain the delimiter (would create sub-levels)
                    if delimiter in name:
                        return _json_response(
                            {'success': False,
                             'error': f'name must not contain the hierarchy delimiter "{delimiter}"'},
                            400,
                        )

                    # Build full IMAP path
                    if parent:
                        folder_path = f'{parent}{delimiter}{name}'
                    else:
                        folder_path = name   # top-level folder

                    typ, data = conn.create(_imap_quote_mailbox(folder_path))
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            if typ != 'OK':
                err = data[0].decode('utf-8', errors='replace') if data else 'CREATE failed'
                return _json_response({'success': False, 'error': err}, 502)

            return _json_response({'success': True, 'data': {
                'path':      folder_path,
                'name':      name,
                'parent':    parent or '',
                'delimiter': delimiter,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Rename folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/rename',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_rename(self, account_id, **kwargs):
        """Rename (or move) an IMAP folder.

        Body: { "old_path": "INBOX/Projects", "new_path": "INBOX/Active Projects" }
          old_path (required) — current full IMAP folder path
          new_path (required) — desired full IMAP folder path

        Note: renaming INBOX itself is not allowed by IMAP spec.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body     = json.loads(request.httprequest.data or '{}')
            old_path = (body.get('old_path') or '').strip()
            new_path = (body.get('new_path') or '').strip()

            if not old_path or not new_path:
                return _json_response({'success': False, 'error': 'old_path and new_path are required'}, 400)
            if old_path.upper() == 'INBOX':
                return _json_response({'success': False, 'error': 'Cannot rename INBOX'}, 400)

            import imaplib, time as _time, re as _re
            rename_status = 'renamed'
            try:
                with acc._imap_session() as conn:
                    def _list_names():
                        names = {}
                        typ_l, raw_l = conn.list()
                        if typ_l != 'OK' or not raw_l:
                            return names
                        lr = _re.compile(
                            r'^\((?P<flags>[^)]*)\)\s+'
                            r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                            r'(?P<name>.+?)\s*$'
                        )
                        for item in raw_l:
                            if not item:
                                continue
                            line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                            m = lr.match(line.strip())
                            if not m:
                                continue
                            name = m.group('name').strip().strip('"')
                            if name:
                                names[name.lower()] = name
                        return names

                    names_before = _list_names()
                    old_exists = old_path.lower() in names_before
                    new_existing = names_before.get(new_path.lower())
                    if not old_exists and new_existing:
                        # The user may have renamed the folder directly in
                        # webmail.  Treat this as success and reconcile DB/rules.
                        new_path = new_existing
                        typ, data = 'OK', []
                        rename_status = 'already_renamed_on_server'
                    else:
                        typ, data = conn.rename(
                            _imap_quote_mailbox(old_path),
                            _imap_quote_mailbox(new_path),
                        )
                        if typ != 'OK':
                            names_after = _list_names()
                            new_existing = names_after.get(new_path.lower())
                            if new_existing:
                                new_path = new_existing
                                typ, data = 'OK', []
                                rename_status = 'server_renamed_despite_non_ok_response'
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            if typ != 'OK':
                msg = data[0].decode('utf-8', errors='replace') if data else 'RENAME failed'
                return _json_response({'success': False, 'error': msg}, 502)

            rewrite = _rewrite_folder_references(request.env, account_id, old_path, new_path)
            _refresh_account_unread_count(acc)
            request.env.cr.commit()

            return _json_response({'success': True, 'data': {
                'old_path': old_path,
                'new_path': new_path,
                'rename_status': rename_status,
                'messages_updated': rewrite['messages_updated'],
                'rules_updated': rewrite['rules_updated'],
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Delete folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/delete',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_delete(self, account_id, **kwargs):
        """Permanently delete an IMAP folder and all its messages.

        Body: { "path": "INBOX/OldProjects" }
          path (required) — full IMAP folder path to delete

        Protected folders (INBOX, Sent, Drafts, Trash, Spam/Junk) cannot be deleted.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body = json.loads(request.httprequest.data or '{}')
            path = (body.get('path') or '').strip()

            if not path:
                return _json_response({'success': False, 'error': 'path is required'}, 400)

            # Protected by full path match, last segment, OR any segment containing
            # known system/server-internal names (e.g. Dovecot internal folders).
            _PROTECTED_NAMES = {
                'inbox', 'sent', 'sent items', 'sent messages',
                'drafts', 'draft', 'trash', 'deleted', 'deleted items',
                'spam', 'junk', 'junk e-mail', 'archive', 'archives',
            }
            # Server-internal prefixes/substrings — protect entire path if any segment matches
            _INTERNAL_KEYWORDS = {'dovecot', 'sieve', 'courier', 'cyrus', '.subscriptions'}
            path_lower = path.lower()
            segments   = [s.lower() for s in path.replace('/', '.').split('.')]
            if (path_lower in _PROTECTED_NAMES
                    or segments[-1] in _PROTECTED_NAMES
                    or any(kw in path_lower for kw in _INTERNAL_KEYWORDS)):
                return _json_response(
                    {'success': False, 'error': f'Cannot delete protected/system folder: {path}'},
                    400,
                )

            import imaplib, re as _re, time as _time
            deleted_paths = []
            try:
                with acc._imap_session() as conn:
                    # List ALL folders once — we need this both for flag checks and to
                    # discover children.  Avoids pattern-based LIST which fails on many
                    # servers when the path contains dots.
                    _SYSTEM_FLAGS = {'\\sent', '\\drafts', '\\trash', '\\junk',
                                     '\\spam', '\\archive', '\\all', '\\inbox'}
                    _LR = _re.compile(r'\((?P<flags>[^)]*)\)\s+"(?P<delim>[^"]*)"\s+"?(?P<name>.+?)"?\s*$')
                    typ_all, all_raw = conn.list()

                    all_folder_names = []   # [(name, flags_set)]
                    delimiter = '.'
                    if typ_all == 'OK' and all_raw:
                        for item in all_raw:
                            if not item:
                                continue
                            line = item.decode('utf-8', errors='replace') \
                                   if isinstance(item, bytes) else item
                            fm = _LR.search(line.strip())
                            if not fm:
                                continue
                            fname  = fm.group('name').strip().strip('"')
                            fdelim = fm.group('delim') or '.'
                            fflags = {f.lower() for f in fm.group('flags').split()}
                            all_folder_names.append((fname, fflags))
                            delimiter = fdelim   # use last seen delimiter

                    # Locate the target folder and check for system flags
                    target_flags = set()
                    for fname, fflags in all_folder_names:
                        if fname.lower() == path.lower():
                            target_flags = fflags
                            break

                    if target_flags & _SYSTEM_FLAGS:
                        return _json_response(
                            {'success': False,
                             'error': f'Cannot delete system folder: {path}'},
                            400,
                        )

                    # Collect all folders to delete: the target itself + any descendants.
                    # Children are any folders whose path starts with "<path><delimiter>".
                    prefix_lower = path.lower() + delimiter
                    to_delete = [
                        fname for fname, _ in all_folder_names
                        if fname.lower() == path.lower()
                        or fname.lower().startswith(prefix_lower)
                    ]

                    # Sort deepest first so children are deleted before their parent.
                    # Depth = number of delimiter occurrences.
                    to_delete.sort(key=lambda p: p.count(delimiter), reverse=True)

                    for folder_path in to_delete:
                        try:
                            conn.unsubscribe(_imap_quote_mailbox(folder_path))
                        except Exception:
                            pass
                        typ_d, data_d = conn.delete(_imap_quote_mailbox(folder_path))
                        if typ_d == 'OK':
                            deleted_paths.append(folder_path)
                            # Remove DB records for this folder so they stop appearing in
                            # the messages list.
                            try:
                                # Restore messages to inbox instead of marking deleted.
                                # Messages only get is_deleted when the user explicitly
                                # deletes them — not when a folder container is removed.
                                orphaned = request.env['lugal.email.message'].sudo().search([
                                    ('account_id', '=', account_id),
                                    ('folder',     '=', folder_path),
                                    ('is_deleted', '=', False),
                                ])
                                if orphaned:
                                    orphaned.write({'folder': 'inbox'})
                                request.env.cr.commit()
                            except Exception:
                                pass
                        else:
                            # If a virtual parent doesn't physically exist on the server,
                            # the server returns NONEXISTENT — that's fine, just skip it.
                            err_str = (data_d[0].decode('utf-8', errors='replace')
                                       if data_d else '')
                            if 'nonexistent' not in err_str.lower():
                                _logger.warning(
                                    'IMAP DELETE %r returned %s: %s', folder_path, typ_d, err_str)

            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            # ── Cleanup: delete rules + restore messages when folder deleted ──
            # Rules pointing at a deleted folder silently drop future emails.
            # Delete them now and fire async IMAP to put orphaned messages back.
            rules_deleted = 0
            msgs_restored = 0
            if deleted_paths:
                deleted_set = set(p.lower() for p in deleted_paths)

                # 1. Delete rules whose move_folder destination is now gone
                Rule = request.env['lugal.email.rule'].sudo()
                rules_to_del = Rule.browse()
                for rule in Rule.search([('account_id', '=', account_id)]):
                    try:
                        actions = json.loads(rule.actions_json or '[]')
                        for act in actions:
                            if act.get('action') == 'move_folder':
                                if (act.get('value') or '').lower() in deleted_set:
                                    rules_to_del |= rule
                                    break
                    except Exception:
                        pass
                if rules_to_del:
                    rules_deleted = len(rules_to_del)
                    _logger.info(
                        'folder_delete: removing %d rule(s) targeting deleted path(s): %s',
                        rules_deleted, [r.id for r in rules_to_del],
                    )
                    rules_to_del.unlink()

                # 2. Any messages still under deleted paths → restore to inbox
                Msg = request.env['lugal.email.message'].sudo()
                still_orphaned = Msg.search([
                    ('account_id', '=', account_id),
                    ('folder',     'in', deleted_paths),
                    ('is_deleted', '=', False),
                ])
                if still_orphaned:
                    msgs_restored = len(still_orphaned)
                    to_imap = [(m.imap_uid, m.folder) for m in still_orphaned if m.imap_uid]
                    still_orphaned.write({'folder': 'inbox'})
                    _refresh_account_unread_count(acc)

                    # Async IMAP: physically move messages back to INBOX on server
                    import collections as _col, threading as _thr
                    _db  = request.env.cr.dbname
                    _aid = account_id
                    by_src = _col.defaultdict(list)
                    for uid, src in to_imap:
                        by_src[src].append(uid)

                    def _bg(_by_src=by_src, _db=_db, _aid=_aid):
                        try:
                            from odoo.modules.registry import Registry as _Reg
                            import odoo as _odoo
                            with _Reg(_db).cursor() as _cr:
                                _env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                                _acc = _env['lugal.email.account'].browse(_aid)
                                with _acc._imap_session() as _conn:
                                    for _src, _uids in _by_src.items():
                                        try:
                                            _conn.select(_src, readonly=False)
                                            _uid_set = ','.join(str(u) for u in _uids)
                                            _t, _ = _conn.uid('move', _uid_set, 'INBOX')
                                            if _t != 'OK':
                                                _conn.uid('copy', _uid_set, 'INBOX')
                                                _conn.uid('store', _uid_set, '+FLAGS', '(\\Deleted)')
                                                _conn.expunge()
                                            _logger.info(
                                                'folder_delete restore: %d msgs %s→INBOX', len(_uids), _src)
                                        except Exception as _me:
                                            _logger.warning('folder_delete restore %s: %s', _src, _me)
                        except Exception as _e:
                            _logger.warning('folder_delete restore thread: %s', _e)

                    if to_imap:
                        _thr.Thread(target=_bg, daemon=True,
                                    name=f'imap-restore-{_aid}').start()

                try:
                    _refresh_account_unread_count(acc)
                    request.env.cr.commit()
                except Exception:
                    pass

            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
                'rules_deleted': rules_deleted,
                'msgs_restored': msgs_restored,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Move to custom folder ──────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/move',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def message_move(self, message_id, **kwargs):
        """Move a message to any folder — including user-created custom ones.

        Body: { "folder": "INBOX/Projects" }
          folder may be a logical name (inbox, sent, drafts, trash, archive, spam)
          or a raw IMAP folder path (e.g. "INBOX/Work/2026").
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            body       = json.loads(request.httprequest.data or '{}')
            target_raw = (body.get('folder') or '').strip()
            if not target_raw:
                return _json_response({'success': False, 'error': 'folder is required'}, 400)

            # Map logical names → IMAP folder via account helper, otherwise use raw path
            LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            if target_raw.lower() in LOGICAL:
                target_logical = target_raw.lower()
                imap_dest = msg.account_id.sudo()._get_server_folder_name(target_logical)
            else:
                target_logical = 'custom'
                imap_dest = target_raw
                if (msg.account_id.password or '').strip():
                    try:
                        with msg.account_id.sudo()._imap_session(connect_attempts=6, retry_delay=2.0) as _conn:
                            msg.account_id.sudo()._imap_ensure_folder(imap_dest, existing_conn=_conn)
                    except Exception:
                        _logger.warning(
                            'message_move: could not ensure destination folder %s',
                            imap_dest, exc_info=True,
                        )

            prev_folder = msg.folder
            imap_from   = _resolve_imap_folder(msg.account_id, prev_folder)

            # Update local DB record
            # For logical folders store the logical key; for custom IMAP paths
            # store the raw path so the messages_list query can find them.
            new_folder = target_logical if target_logical != 'custom' else target_raw
            write_vals = {'folder': new_folder}
            if new_folder.replace('/', '.').split('.')[-1].lower() == 'important':
                write_vals['is_important'] = True
            msg.write(write_vals)
            rule_info = {'rule_id': None, 'applied_existing': 0}
            if target_logical == 'custom':
                rule_info = _apply_sender_move_to_existing(msg, new_folder)
                unread_count = rule_info.get('unread_count', _refresh_account_unread_count(msg.account_id))
            else:
                unread_count = _refresh_account_unread_count(msg.account_id)

            # Push IMAP move asynchronously
            if msg.imap_uid:
                import threading
                acc        = msg.account_id
                imap_uid   = msg.imap_uid
                db_name    = request.env.cr.dbname
                acc_id     = acc.id

                def _bg_move():
                    try:
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as _cr:
                            from odoo.api import Environment
                            _env = Environment(_cr, 1, {})
                            _acc = _env['lugal.email.account'].browse(acc_id)
                            with _acc._imap_session() as conn:
                                conn.select(_imap_quote_mailbox(imap_from))
                                result = conn.uid(
                                    'move', str(imap_uid),
                                    _imap_quote_mailbox(imap_dest),
                                )
                                if result[0] != 'OK':
                                    conn.uid('copy', str(imap_uid),
                                             _imap_quote_mailbox(imap_dest))
                                    conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                                    conn.expunge()
                    except Exception as _e:
                        _logger.warning('message_move IMAP failed uid=%s: %s', imap_uid, _e)

                threading.Thread(target=_bg_move, daemon=True, name=f'imap-move-{message_id}').start()

            return _json_response({'success': True, 'data': {
                'id': msg.id,
                'folder': target_raw,
                'is_important': msg.is_important,
                'unread_count': unread_count,
                'rule_id': rule_info.get('rule_id'),
                'applied_existing': rule_info.get('applied_existing', 0),
                'mirrored_rules': rule_info.get('mirrored_rules', []),
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Bulk move by sender ────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/bulk_move_by_sender',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def bulk_move_by_sender(self, **kwargs):
        """Move ALL messages from one or more senders into a target folder.

        Body (JSON):
          {
            "account_id":    22,                           // required
            "senders":       ["foo@bar.com", "baz@x.com"], // required, 1–50 addresses
            "target_folder": "INBOX.MailsFrom Weird guy",  // required — raw IMAP path
                                                           // OR logical name (inbox/sent/…)
            "source_folder": "inbox"                       // optional — restrict to one folder
                                                           //   (default: all non-deleted msgs)
          }

        Returns:
          { "success": true, "data": { "moved": 42, "senders": [...], "target_folder": "..." } }

        The DB is updated synchronously; IMAP moves are executed asynchronously
        in a background thread (fire-and-forget, best-effort).
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')

            account_id    = body.get('account_id')
            senders_raw   = body.get('senders') or []
            target_folder = (body.get('target_folder') or '').strip()
            source_folder = (body.get('source_folder') or '').strip() or None

            # ── Validate inputs ──────────────────────────────────────────────
            if not account_id:
                return _json_response({'success': False, 'error': 'account_id is required'}, 400)
            if not isinstance(senders_raw, list) or not senders_raw:
                return _json_response({'success': False, 'error': 'senders must be a non-empty array'}, 400)
            if len(senders_raw) > 50:
                return _json_response({'success': False, 'error': 'senders may not exceed 50 per request'}, 400)
            if not target_folder:
                return _json_response({'success': False, 'error': 'target_folder is required'}, 400)

            senders = [s.strip().lower() for s in senders_raw if isinstance(s, str) and s.strip()]
            if not senders:
                return _json_response({'success': False, 'error': 'senders contains no valid email addresses'}, 400)

            # ── Authorise account ────────────────────────────────────────────
            try:
                aid = int(account_id)
            except (TypeError, ValueError):
                return _json_response({'success': False, 'error': 'account_id must be an integer'}, 400)

            acc = request.env['lugal.email.account'].sudo().browse(aid)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')

            # ── Resolve logical → IMAP folder name ──────────────────────────
            _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            if target_folder.lower() in _LOGICAL:
                target_logical = target_folder.lower()
                imap_dest      = acc.sudo()._get_server_folder_name(target_logical)
                db_folder      = target_logical
            else:
                target_logical = 'custom'
                imap_dest      = target_folder
                db_folder      = target_folder   # raw IMAP path stored in DB
                # Be forgiving for FE flows that create a rule/folder and then
                # immediately bulk-move.  Ensure the destination exists before
                # the DB move so async IMAP MOVE has a valid target.
                if (acc.password or '').strip():
                    try:
                        with acc.sudo()._imap_session(connect_attempts=6, retry_delay=2.0) as _conn:
                            acc.sudo()._imap_ensure_folder(imap_dest, existing_conn=_conn)
                    except Exception as _ensure_exc:
                        _logger.warning(
                            'bulk_move_by_sender: could not ensure IMAP folder %s: %s',
                            imap_dest, _ensure_exc,
                        )

            # ── Find messages matching any of the senders ────────────────────
            Msg = request.env['lugal.email.message'].sudo()

            # Build OR domain: ('from_address', 'ilike', s1) OR ('from_address', 'ilike', s2) …
            sender_clauses = [('from_address', 'ilike', s) for s in senders]
            if len(sender_clauses) == 1:
                sender_domain = sender_clauses
            else:
                or_prefix     = ['|'] * (len(sender_clauses) - 1)
                sender_domain = or_prefix + sender_clauses

            base = [
                ('account_id', '=', aid),
                ('is_deleted', '=', False),
            ]
            if source_folder:
                base.append(('folder', '=', source_folder))

            msgs = Msg.search(base + sender_domain)

            if not msgs:
                return _json_response({'success': True, 'data': {
                    'moved': 0, 'senders': senders, 'target_folder': target_folder,
                }})

            # ── Capture per-message IMAP state before writing ────────────────
            # Store (imap_uid, current_imap_folder_key) pairs for IMAP moves.
            imap_tasks = []
            for m in msgs:
                if m.imap_uid:
                    imap_tasks.append((m.imap_uid, m.folder))

            # ── Update DB atomically ──────────────────────────────────────────
            write_vals = {'folder': db_folder}
            if db_folder.replace('/', '.').split('.')[-1].lower() == 'important':
                write_vals['is_important'] = True
            msgs.write(write_vals)
            unread_count = _refresh_account_unread_count(acc)

            moved_count = len(msgs)

            # ── Async IMAP moves (best-effort, fire-and-forget) ───────────────
            if imap_tasks and (acc.password or '').strip():
                db_name = request.env.cr.dbname

                def _bg_bulk_move():
                    try:
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as _cr:
                            from odoo.api import Environment as _Env
                            _env = _Env(_cr, 1, {})
                            _acc = _env['lugal.email.account'].browse(aid)
                            with _acc._imap_session() as conn:
                                # Group UIDs by source folder so we do one SELECT per folder
                                from collections import defaultdict as _dd
                                by_src = _dd(list)
                                for uid_val, src_folder in imap_tasks:
                                    # Resolve logical folder key → IMAP path
                                    if src_folder in _LOGICAL:
                                        imap_src = _acc._get_server_folder_name(src_folder)
                                    else:
                                        imap_src = src_folder
                                    by_src[imap_src].append(str(uid_val))

                                _quoted_dest = _imap_quote_mailbox(imap_dest)
                                for imap_src, uid_list in by_src.items():
                                    try:
                                        conn.select(_imap_quote_mailbox(imap_src))
                                        uid_set = ','.join(uid_list)
                                        res = conn.uid('move', uid_set, _quoted_dest)
                                        if res[0] != 'OK':
                                            # Fallback: COPY + DELETE
                                            conn.uid('copy', uid_set, _quoted_dest)
                                            conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                            conn.expunge()
                                    except Exception as _se:
                                        _logger.warning(
                                            'bulk_move_by_sender IMAP src=%s: %s', imap_src, _se)
                    except Exception as _e:
                        _logger.warning('bulk_move_by_sender IMAP thread error: %s', _e)

                import threading as _thr
                _thr.Thread(
                    target=_bg_bulk_move, daemon=True,
                    name=f'imap-bulk-move-{aid}',
                ).start()

            return _json_response({'success': True, 'data': {
                'moved':         moved_count,
                'senders':       senders,
                'target_folder': target_folder,
                'db_folder':     db_folder,
                'unread_count':  unread_count,
            }})
        except Exception as exc:
            _logger.exception('bulk_move_by_sender error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Related messages ───────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/related',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def message_related(self, message_id, **kwargs):
        """Return messages related to a given message.

        Query params:
          type   = "sender"       → all messages from the same from_address
                 | "conversation" → all messages in the same thread (by subject / thread_id)
          scope  = "inbox"        → only inbox folder (default)
                 | "all"          → all folders the user owns
          limit  = int (default 50, max 500)
          offset = int (default 0)

        Always excludes the source message itself and soft-deleted rows.
        Results ordered: newest first.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found('Message not found')

            args      = request.httprequest.args
            rel_type  = (args.get('type') or 'sender').lower()     # sender | conversation
            scope     = (args.get('scope') or 'inbox').lower()     # inbox  | all
            limit     = min(int(args.get('limit') or 50), 500)
            offset    = max(int(args.get('offset') or 0), 0)

            # Base domain — restrict to accounts owned by this user
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
                ('id',         '!=', message_id),
            ]

            if scope == 'inbox':
                domain.append(('folder', '=', 'inbox'))

            if rel_type == 'sender':
                sender = (msg.from_address or '').strip().lower()
                if not sender:
                    return _json_response({'success': False, 'error': 'Source message has no sender'}, 400)
                # Case-insensitive match on from_address
                domain.append(('from_address', 'ilike', sender))

            elif rel_type == 'conversation':
                # Match by thread_id first (most reliable), then fall back to
                # normalised subject scan so threaded replies without proper
                # References headers are still grouped.
                thread_id  = (msg.thread_id or '').strip()
                raw_subject = (msg.subject or '').strip()

                # Strip common prefixes: Re:, Fwd:, Fw:, AW:, ... (case-insensitive)
                import re as _re
                _PREFIX = _re.compile(r'^(?:(?:re|fwd?|aw|tr|rép|sv)\s*:\s*)+', _re.IGNORECASE)
                norm_subject = _PREFIX.sub('', raw_subject).strip()

                if thread_id:
                    # Prefer thread_id — exact match OR subject fallback via OR
                    if norm_subject:
                        domain += ['|',
                            ('thread_id', '=', thread_id),
                            ('subject',   'ilike', norm_subject),
                        ]
                    else:
                        domain.append(('thread_id', '=', thread_id))
                elif norm_subject:
                    domain.append(('subject', 'ilike', norm_subject))
                else:
                    return _json_response({'success': False, 'error': 'Cannot determine conversation — no thread_id or subject'}, 400)

            else:
                return _json_response({'success': False, 'error': f'Unknown type "{rel_type}". Use sender or conversation'}, 400)

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            msgs  = Msg.search(domain, limit=limit, offset=offset, order='create_date desc, id desc')

            return _json_response({
                'success': True,
                'data': {
                    'type':   rel_type,
                    'scope':  scope,
                    'total':  total,
                    'limit':  limit,
                    'offset': offset,
                    'items':  [_message_to_dict(m) for m in msgs],
                },
            })
        except Exception as exc:
            _logger.exception('message_related error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Sender contact resolve ─────────────────────────────────────────────────

    @http.route('/api/lugal/email/senders/resolve',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def sender_resolve(self, **kwargs):
        """Resolve a sender email address → contact info (phone, mobile, social links).

        Query param: ?email=someone@example.com

        Looks up res.partner, then lugal.crm.employee (by work email / email).
        Returns the first match.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            email = (request.httprequest.args.get('email') or '').strip().lower()
            if not email:
                return _json_response({'success': False, 'error': 'email param required'}, 400)

            result = {'email': email, 'found': False}

            # 1. Try res.partner
            partner = request.env['res.partner'].sudo().search(
                [('email', '=ilike', email)], limit=1,
            )
            if partner:
                result.update({
                    'found':   True,
                    'source':  'partner',
                    'name':    partner.name or '',
                    'phone':   partner.phone or '',
                    'mobile':  partner.mobile or '',
                    'website': partner.website or '',
                })

            # 2. Try res.users (internal employee)
            if not result['found']:
                user = request.env['res.users'].sudo().search(
                    [('email', '=ilike', email)], limit=1,
                )
                if user:
                    result.update({
                        'found':   True,
                        'source':  'user',
                        'name':    user.name or '',
                        'phone':   getattr(user.partner_id, 'phone', '') or '',
                        'mobile':  getattr(user.partner_id, 'mobile', '') or '',
                        'website': '',
                    })

            return _json_response({'success': True, 'data': result})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Email attachment upload ────────────────────────────────────────────────

    @http.route('/api/lugal/email/attachments/upload', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def email_attachment_upload(self, **kwargs):
        """
        Multipart file upload for email compose.

        Form fields:
          - file | files | files[]  – one or more binary parts
          - account_id (optional)   – link attachment to this email account
          - inline (optional, "true") – mark as inline image; returns a `cid` for use
            in body HTML as <img src="cid:…">  Inline images are excluded from the
            attachments[] list returned by message detail APIs.

        Response:
          {
            "success": true,
            "data": {
              "attachments": [
                { "id": 42, "name": "invoice.pdf", "mimetype": "application/pdf",
                  "size": 102400, "url": "/web/content/42?download=true",
                  "inline": false }
              ]
            }
          }

        For inline images the response also includes:
          "cid": "cid:img-<uuid>@lugal.mail"
        Embed this value in the HTML body as <img src="cid:img-<uuid>@lugal.mail">.

        Pass ALL returned "id" values (inline + regular) in send/reply/forward as:
          { "attachment_ids": [42, 43] }
        The backend automatically separates inline from regular when building the email.
        """
        import base64
        import mimetypes as _mimetypes
        import uuid as _uuid

        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        try:
            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json_response({'success': False, 'error': 'No files provided'}, 400)

            is_inline = str(kwargs.get('inline') or request.httprequest.form.get('inline', '')).lower() == 'true'

            MAX_MB = 1024  # 1 GB
            max_bytes = MAX_MB * 1024 * 1024

            results = []
            Attachment = request.env['ir.attachment'].sudo()

            for f in files:
                data = f.read()
                if len(data) > max_bytes:
                    return _json_response(
                        {'success': False, 'error': f'{f.filename or "file"}: exceeds {MAX_MB} MB'},
                        400,
                    )
                mime = f.mimetype or _mimetypes.guess_type(f.filename or '')[0] or 'application/octet-stream'
                filename = f.filename or 'attachment'

                att_token = _uuid.uuid4().hex

                # For inline images: generate a Content-ID and store it in `description`
                # so the MIME builder can embed the image as multipart/related.
                cid_value = None
                description = None
                if is_inline:
                    cid_value = f'img-{_uuid.uuid4().hex}@lugal.mail'
                    description = f'__inline_cid__:{cid_value}'

                att = Attachment.create({
                    'name': filename,
                    'mimetype': mime,
                    'datas': base64.b64encode(data).decode('utf-8'),
                    'type': 'binary',
                    'res_model': 'lugal.email.message',
                    'access_token': att_token,
                    **(({'description': description}) if description else {}),
                })
                att.flush_recordset(['access_token'])

                att_url = f"/web/content/{att.id}?access_token={att_token}"
                entry = {
                    'id': att.id,
                    'name': att.name or filename,
                    'mimetype': mime,
                    'size': len(data),
                    'url': att_url,
                    'file_url': att_url,
                    'inline': is_inline,
                }
                if cid_value:
                    entry['cid'] = f'cid:{cid_value}'
                results.append(entry)

            return _json_response({'success': True, 'data': {'attachments': results}})

        except Exception as exc:
            _logger.exception('email_attachment_upload')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _json_response({'success': False, 'error': str(exc)}, 500)


# ── SMTP helper ───────────────────────────────────────────────────────────────

_SMTP_RECIPIENT_ERROR_CODES = {
    550: 'Mailbox not found or recipient does not exist',
    551: 'User is not local',
    552: 'Mailbox storage quota exceeded',
    553: 'Mailbox name not allowed',
    554: 'Transaction failed / message rejected',
}


def _read_att_parts(attachment_ids, cr, db_name):
    """
    Read raw binary data for each attachment from filestore or DB.

    Returns (regular_parts, inline_parts):
      regular_parts – list of (filename, mimetype, raw_bytes)   → Content-Disposition: attachment
      inline_parts  – list of (cid, filename, mimetype, raw_bytes) → multipart/related embed

    Inline images are identified by a description field starting with
    ``__inline_cid__:<cid_value>`` — set by the upload endpoint when
    ``inline=true`` is passed.

    Uses direct SQL — avoids ir.attachment.datas ORM computed field which in
    Odoo 17+ returns raw bytes (not base64), causing silent corruption when
    base64.b64decode() is applied.
    """
    import os as _os
    import odoo as _odoo_mod

    regular_parts = []
    inline_parts  = []
    if not attachment_ids:
        return regular_parts, inline_parts

    ids_int = [int(i) for i in attachment_ids]
    cr.execute(
        "SELECT id, name, mimetype, store_fname, description FROM ir_attachment WHERE id = ANY(%s)",
        (ids_int,),
    )
    att_meta = {row[0]: row for row in cr.fetchall()}
    filestore_base = _os.path.join(
        _odoo_mod.tools.config['data_dir'], 'filestore', db_name
    )

    for att_id in ids_int:
        if att_id not in att_meta:
            _logger.warning('_read_att_parts: attachment %s not found — skipping', att_id)
            continue
        _, att_name, att_mime, store_fname, description = att_meta[att_id]
        att_name = att_name or 'attachment'
        att_mime = att_mime or 'application/octet-stream'
        data = b''

        if store_fname:
            file_path = _os.path.join(filestore_base, store_fname)
            try:
                with open(file_path, 'rb') as fh:
                    data = fh.read()
            except Exception as exc:
                _logger.warning(
                    '_read_att_parts: filestore read failed for att %s at %s: %s',
                    att_id, file_path, exc,
                )
        else:
            cr.execute("SELECT db_datas FROM ir_attachment WHERE id = %s", (att_id,))
            row = cr.fetchone()
            if row and row[0]:
                raw = row[0]
                data = bytes(raw) if not isinstance(raw, bytes) else raw

        if not data:
            _logger.warning('_read_att_parts: no binary data for att %s (%s)', att_id, att_name)
            continue

        _logger.debug('_read_att_parts: loaded %s (%s, %d bytes)', att_name, att_mime, len(data))

        # Inline images: description = "__inline_cid__:<cid_value>"
        cid_prefix = '__inline_cid__:'
        if description and description.startswith(cid_prefix):
            cid_value = description[len(cid_prefix):]
            inline_parts.append((cid_value, att_name, att_mime, data))
        else:
            regular_parts.append((att_name, att_mime, data))

    return regular_parts, inline_parts


def _build_mime_message(from_header, to_list, subject, body_html, body_text,
                        cc, att_parts, from_address, importance='normal',
                        inline_parts=None, request_read_receipt=False,
                        written_in_arabic=False):
    """
    Build a MIME message from pre-loaded data.

    Returns a tuple (raw_rfc2822_string, generated_message_id) so callers can
    persist the Message-ID back to the DB record and enable IMAP deduplication.

    att_parts     – list of (filename, mimetype, raw_bytes) for regular attachments
    inline_parts  – list of (cid, filename, mimetype, raw_bytes) for CID-embedded images.
                    These are wrapped in multipart/related so <img src="cid:…"> renders.
    request_read_receipt – when True, adds Disposition-Notification-To header (read receipt).
    """
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.encoders import encode_base64
    from email.utils import formatdate, make_msgid

    inline_parts = inline_parts or []

    # ── Build the text/alternative part ─────────────────────────────────────
    alt_part = MIMEMultipart('alternative')
    if body_text:
        alt_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
    if body_html:
        alt_part.attach(MIMEText(body_html, 'html', 'utf-8'))

    # ── Wrap in multipart/related when inline (CID) images are present ──────
    # Structure:  multipart/related
    #               multipart/alternative (text + html)
    #               image/png (Content-ID: <cid>, Content-Disposition: inline)
    if inline_parts:
        related_part = MIMEMultipart('related')
        related_part.attach(alt_part)
        for cid_value, img_name, img_mime, img_data in inline_parts:
            try:
                mime_type = img_mime.split('/')
                main_type = mime_type[0]
                sub_type  = mime_type[1] if len(mime_type) > 1 else 'octet-stream'
                img_part = MIMEBase(main_type, sub_type)
                img_part.set_payload(img_data)
                encode_base64(img_part)
                img_part.add_header('Content-ID', f'<{cid_value}>')
                img_part.add_header('Content-Disposition', 'inline', filename=img_name)
                related_part.attach(img_part)
                _logger.debug('_build_mime_message: inline image %s cid=%s', img_name, cid_value)
            except Exception as exc:
                _logger.warning('_build_mime_message: inline image failed %s: %s', img_name, exc)
        body_part = related_part
    else:
        body_part = alt_part

    # ── Wrap in multipart/mixed when regular attachments are present ─────────
    if att_parts:
        mime_msg = MIMEMultipart('mixed')
        mime_msg.attach(body_part)
        for att_name, att_mime, data in att_parts:
            try:
                mime_type = att_mime.split('/')
                main_type = mime_type[0]
                sub_type  = mime_type[1] if len(mime_type) > 1 else 'octet-stream'
                part = MIMEBase(main_type, sub_type)
                part.set_payload(data)
                encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=att_name)
                mime_msg.attach(part)
                _logger.debug('_build_mime_message: attached %s (%s, %d bytes)',
                              att_name, att_mime, len(data))
            except Exception as att_exc:
                _logger.warning('_build_mime_message: MIME build failed for %s: %s',
                                att_name, att_exc)
    else:
        mime_msg = body_part

    generated_msg_id = make_msgid(
        domain=from_address.split('@')[-1] if '@' in from_address else 'mail'
    )
    mime_msg['Subject']    = subject
    mime_msg['From']       = from_header
    mime_msg['To']         = ', '.join(to_list)
    mime_msg['Date']       = formatdate(localtime=True)
    mime_msg['Message-ID'] = generated_msg_id
    if cc:
        mime_msg['Cc'] = ', '.join(cc)

    # High-importance headers (honoured by Outlook, Apple Mail, Gmail)
    if (importance or 'normal').lower() == 'high':
        mime_msg['X-Priority']        = '1'
        mime_msg['X-MSMail-Priority'] = 'High'
        mime_msg['Importance']        = 'High'

    # Read/Delivery receipt — asks the recipient's mail client to send a notification
    # when the message is read (RFC 3798).  Not all clients honour this.
    if request_read_receipt:
        mime_msg['Disposition-Notification-To'] = from_address
        mime_msg['Return-Receipt-To']           = from_address

    # Propagate Arabic-compose flag to the recipient's inbox so the FE can
    # render the body RTL.  This is a private Lugal extension header; non-Lugal
    # clients silently ignore it.
    if written_in_arabic:
        mime_msg['X-Written-In-Arabic'] = 'true'

    return mime_msg.as_string(), generated_msg_id


def _do_smtp_send(smtp_host, smtp_port, smtp_use_tls, username, password,
                  from_address, all_recipients, raw_message, msg_id, db_name,
                  generated_msg_id=None):
    """
    Perform the actual SMTP send and write result back to lugal.email.message.
    Safe to call from a background thread — uses its own Registry cursor for
    the write-back so it never touches the HTTP request cursor.

    generated_msg_id – the RFC-2822 Message-ID that was embedded in the outgoing
                       MIME message.  Written back to the DB record so that when
                       the IMAP Sent folder is synced the upsert logic can match
                       on message_id and update the existing row instead of
                       creating a duplicate.

    Returns (delivered: bool, error_msg: str|None, refused: dict).
    """
    import smtplib
    import socket
    import time

    delivered = False
    error_msg = None
    refused   = {}

    def _connect_and_send(host, port, use_tls):
        # Port 465 = implicit TLS (SMTP_SSL).
        # smtp_use_tls + other ports = STARTTLS (explicit TLS, common on 587).
        # No TLS + non-465 = plain SMTP (port 25 or custom relay).
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
            server.ehlo()
        elif use_tls:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()

        try:
            server.login(username, password)
            return server.sendmail(from_address, all_recipients, raw_message)
        finally:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass

    transient_errors = (
        ConnectionResetError,
        ConnectionAbortedError,
        BrokenPipeError,
        TimeoutError,
        socket.timeout,
        OSError,
        smtplib.SMTPServerDisconnected,
    )

    attempts = [(int(smtp_port or 587), bool(smtp_use_tls))]
    if attempts[0][0] == 465:
        attempts.append((587, True))
    elif attempts[0][0] == 587:
        attempts.append((465, False))

    try:
        last_exc = None
        partial_refused = {}
        sent_ok = False
        for idx, (attempt_port, attempt_tls) in enumerate(attempts, start=1):
            for retry in range(1, 3):
                try:
                    partial_refused = _connect_and_send(
                        smtp_host, attempt_port, attempt_tls,
                    )
                    if attempt_port != int(smtp_port or 587):
                        _logger.warning(
                            'SMTP delivered via fallback route: from=%s to=%s '
                            'primary=%s:%s fallback=%s:%s',
                            from_address, all_recipients, smtp_host, smtp_port,
                            smtp_host, attempt_port,
                        )
                    last_exc = None
                    sent_ok = True
                    break
                except smtplib.SMTPRecipientsRefused:
                    raise
                except smtplib.SMTPAuthenticationError:
                    raise
                except transient_errors as exc:
                    last_exc = exc
                    _logger.warning(
                        'SMTP transient failure attempt=%s.%s from=%s to=%s '
                        'host=%s:%s tls=%s error=%s',
                        idx, retry, from_address, all_recipients,
                        smtp_host, attempt_port, attempt_tls, exc,
                    )
                    if retry < 2:
                        time.sleep(0.75)
                        continue
                    break
            if sent_ok:
                break
        if not sent_ok and last_exc:
            raise last_exc

        if partial_refused:
            delivered = True
            parts = []
            for addr, (code, reason) in partial_refused.items():
                hint = _SMTP_RECIPIENT_ERROR_CODES.get(code, 'Delivery failed')
                parts.append(f'{addr}: {hint} (code {code})')
            error_msg = 'Partial delivery — refused: ' + '; '.join(parts)
            refused   = partial_refused
        else:
            delivered = True

        _logger.info(
            'SMTP delivered: from=%s to=%s subject=(see msg %s) host=%s:%s',
            from_address, all_recipients, msg_id, smtp_host, smtp_port,
        )

    except smtplib.SMTPRecipientsRefused as exc:
        refused = exc.recipients
        parts   = []
        for addr, (code, reason) in refused.items():
            if isinstance(reason, bytes):
                reason = reason.decode('utf-8', errors='replace')
            hint = _SMTP_RECIPIENT_ERROR_CODES.get(code, 'Delivery failed')
            parts.append(f'{addr}: {hint} (code {code})')
        error_msg = 'Recipient(s) not found or rejected: ' + '; '.join(parts)
        _logger.warning('SMTP rejected all recipients: %s', error_msg)

    except Exception as exc:
        error_msg = str(exc)
        _logger.error(
            'SMTP FAILED: from=%s to=%s host=%s:%s tls=%s error=%s',
            from_address, all_recipients, smtp_host, smtp_port, smtp_use_tls, exc,
        )

    # Write delivery result back via a fresh cursor (safe from any thread).
    final_delivered = delivered and not refused
    if msg_id:
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as _cr:
                env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                record = env['lugal.email.message'].browse(msg_id)
                if record.exists():
                    write_vals = {
                        'smtp_delivered': final_delivered,
                        'smtp_error':     error_msg or False,
                        'smtp_status':    'delivered' if final_delivered else 'failed',
                    }
                    # Persist the generated RFC-2822 Message-ID so the IMAP Sent
                    # folder sync can find this exact row by message_id and update
                    # it (stamping imap_uid) instead of creating a duplicate record.
                    if generated_msg_id and not record.message_id:
                        write_vals['message_id'] = generated_msg_id
                        # Bootstrap thread_id from message_id if not yet set.
                        if not record.thread_id:
                            write_vals['thread_id'] = generated_msg_id
                    record.write(write_vals)
                    # Push a real-time failure notification so the FE can show a
                    # "delivery failed" banner without waiting for the next poll.
                    if not final_delivered:
                        try:
                            user_id = record.account_id.user_id.id
                            env['bus.bus']._sendone(
                                f'supply_user.{user_id}',
                                'crm.email.smtp.failed',
                                {
                                    'msg_id':  msg_id,
                                    'subject': record.subject or '',
                                    'error':   error_msg or 'Delivery failed',
                                },
                            )
                        except Exception as bus_exc:
                            _logger.debug('smtp.failed bus push error: %s', bus_exc)
        except Exception as write_exc:
            _logger.warning('_do_smtp_send: write-back failed for msg %s: %s', msg_id, write_exc)

    return delivered, error_msg, refused


def _send_mdn_async(acc, to_address, original_message_id, original_subject, recipient_email):
    """
    Send a Message Disposition Notification (MDN / read receipt) asynchronously.

    Called when a user marks an inbox message as read and the original sender
    requested a receipt (Disposition-Notification-To header, RFC 3798).

    acc                  – lugal.email.account (sender's / recipient's account)
    to_address           – RFC-2822 address to deliver the MDN to (original From / DNT)
    original_message_id  – Message-ID of the email being acknowledged
    original_subject     – Subject of the original email
    recipient_email      – Email address of the person who read the message
    """
    import threading

    db_name      = acc.env.cr.dbname
    acc_id       = acc.id
    smtp_host    = acc.smtp_host
    smtp_port    = acc.smtp_port
    smtp_use_tls = acc.smtp_use_tls
    username     = acc.username or acc.email_address
    password     = acc.password or ''
    from_address = acc.email_address
    display_name = (acc.display_name_field or '').strip()

    def _bg():
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email.utils import formatdate, make_msgid

        try:
            # RFC 3798 MDN structure:
            #   multipart/report; report-type=disposition-notification
            #     ├── text/plain            (human-readable notice)
            #     └── message/disposition-notification  (machine-readable fields)
            mdn = MIMEMultipart('report', report_type='disposition-notification')
            from_hdr = f'{display_name} <{from_address}>' if display_name else from_address
            mdn['From']       = from_hdr
            mdn['To']         = to_address
            mdn['Subject']    = f'Read: {original_subject}' if original_subject else 'Read: (no subject)'
            mdn['Date']       = formatdate(localtime=True)
            mdn['Message-ID'] = make_msgid(
                domain=from_address.split('@')[-1] if '@' in from_address else 'mail'
            )

            # Part 1: Human-readable text (required by RFC 3798)
            human_text = (
                f'Your message "{original_subject}" was read by {recipient_email}.'
            )
            mdn.attach(MIMEText(human_text, 'plain', 'utf-8'))

            # Part 2: Machine-readable notification
            notif_body = (
                f'Reporting-UA: LugalAI Mail Server\r\n'
                f'Final-Recipient: rfc822; {recipient_email}\r\n'
                f'Original-Recipient: rfc822; {recipient_email}\r\n'
                f'Original-Message-ID: {original_message_id}\r\n'
                f'Disposition: manual-action/MDN-sent-automatically; displayed\r\n'
            )
            notif_part = MIMEBase('message', 'disposition-notification')
            notif_part.set_payload(notif_body)
            mdn.attach(notif_part)

            raw_mdn = mdn.as_string()

            # Send via SMTP (same credentials as the receiver's outbound SMTP)
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
                server.ehlo()
            elif smtp_use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.ehlo()

            server.login(username, password)
            server.sendmail(from_address, [to_address], raw_mdn)
            server.quit()
            _logger.info(
                'MDN sent: from=%s to=%s orig_mid=%s',
                from_address, to_address, original_message_id,
            )
        except Exception as exc:
            _logger.warning(
                'MDN send failed: from=%s to=%s orig_mid=%s error=%s',
                from_address, to_address, original_message_id, exc,
            )

    threading.Thread(target=_bg, daemon=True, name=f'mdn-acc{acc_id}').start()


def _send_via_smtp_async(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                         msg_id=None, attachment_ids=None, importance='normal',
                         request_read_receipt=False, written_in_arabic=False):
    """
    Fire-and-forget SMTP send.

    Captures SMTP credentials and other primitives from the Odoo record objects
    (which must not be accessed from another thread), then hands all work —
    file reading, MIME building, SMTP network I/O — to a daemon thread.

    The HTTP handler calls this AFTER committing the message row to the DB and
    returns immediately; the background thread writes smtp_delivered/smtp_error
    back via its own Registry cursor.
    """
    import threading

    # Capture all credentials and config as plain Python primitives before the
    # thread starts — Odoo ORM objects are NOT thread-safe across threads.
    db_name       = acc.env.cr.dbname
    acc_id        = acc.id
    smtp_host     = acc.smtp_host
    smtp_port     = acc.smtp_port
    smtp_use_tls  = acc.smtp_use_tls
    imap_host     = acc.imap_host
    imap_port     = int(acc.imap_port or 993)
    imap_use_ssl  = bool(acc.imap_use_ssl)
    username      = acc.username or acc.email_address
    password      = acc.password or ''
    from_address  = acc.email_address
    display_name  = (acc.display_name_field or '').strip()
    from_header   = f'{display_name} <{from_address}>' if display_name else from_address
    att_ids          = [int(i) for i in (attachment_ids or [])]
    all_recipients   = list(to_list) + list(cc or []) + list(bcc or [])
    _written_arabic  = bool(written_in_arabic)   # capture primitive before thread

    _logger.info(
        'SMTP async queued: from=%s to=%s attachments=%s msg_id=%s written_in_arabic=%s',
        from_address, all_recipients, att_ids, msg_id, _written_arabic,
    )

    def _bg():
        """Background worker: reads files, builds MIME, sends, then appends to IMAP Sent."""
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo

            # Open a fresh cursor to read attachment binary data.
            with _Registry(db_name).cursor() as _cr:
                att_parts, inline_parts = _read_att_parts(att_ids, _cr, db_name)

            raw_message, generated_msg_id = _build_mime_message(
                from_header, to_list, subject, body_html, body_text, cc, att_parts,
                from_address, importance=importance,
                inline_parts=inline_parts,
                request_read_receipt=request_read_receipt,
                written_in_arabic=_written_arabic,
            )

            delivered, error_msg, refused = _do_smtp_send(
                smtp_host, smtp_port, smtp_use_tls, username, password,
                from_address, all_recipients, raw_message, msg_id, db_name,
                generated_msg_id=generated_msg_id,
            )

            # ── IMAP APPEND ───────────────────────────────────────────────────
            # After successful SMTP delivery, upload a copy to the IMAP Sent
            # folder so the message appears in webmail, Outlook, etc.
            if delivered:
                try:
                    with _Registry(db_name).cursor() as _cr2:
                        env2 = _odoo.api.Environment(_cr2, _odoo.SUPERUSER_ID, {})
                        acc_rec = env2['lugal.email.account'].browse(acc_id)
                        if not acc_rec.exists():
                            raise RuntimeError('account missing')
                        msg_bytes = (
                            raw_message.encode('utf-8')
                            if isinstance(raw_message, str)
                            else raw_message
                        )
                        with acc_rec._imap_session() as _append_conn:
                            sent_folder = acc_rec._get_server_folder_name('sent', existing_conn=_append_conn)
                            typ, data = _append_conn.append(
                                sent_folder, '(\\Seen)', None, msg_bytes,
                            )
                    if typ == 'OK':
                        _logger.info(
                            'SMTP+APPEND: msg=%s appended to %s folder=%s',
                            msg_id, imap_host, sent_folder,
                        )
                    else:
                        _logger.warning(
                            'IMAP APPEND returned %s for msg=%s folder=%s: %s',
                            typ, msg_id, sent_folder, data,
                        )
                except Exception as append_exc:
                    _logger.warning(
                        'IMAP APPEND to Sent failed for msg=%s acc=%s: %s',
                        msg_id, acc_id, append_exc,
                    )

        except Exception as exc:
            _logger.error('SMTP background worker crashed for msg %s: %s', msg_id, exc, exc_info=True)

    threading.Thread(target=_bg, daemon=True, name=f'smtp-{msg_id}').start()


def _send_via_smtp(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                   msg_id=None, attachment_ids=None):
    """
    Synchronous SMTP send — kept for backward compatibility / direct callers.
    New callers should prefer _send_via_smtp_async.
    """
    db_name      = acc.env.cr.dbname
    smtp_host    = acc.smtp_host
    smtp_port    = acc.smtp_port
    smtp_use_tls = acc.smtp_use_tls
    username     = acc.username or acc.email_address
    password     = acc.password or ''
    from_address = acc.email_address
    display_name = (acc.display_name_field or '').strip()
    from_header  = f'{display_name} <{from_address}>' if display_name else from_address

    att_parts, inline_parts = _read_att_parts(attachment_ids or [], acc.env.cr, db_name)
    all_recipients = list(to_list) + list(cc or []) + list(bcc or [])
    raw_message, generated_msg_id = _build_mime_message(
        from_header, to_list, subject, body_html, body_text, cc, att_parts, from_address,
        inline_parts=inline_parts,
    )
    return _do_smtp_send(
        smtp_host, smtp_port, smtp_use_tls, username, password,
        from_address, all_recipients, raw_message, msg_id, db_name,
        generated_msg_id=generated_msg_id,
    )
# TODO: remove - cherry-pick marker

end of file email_controller.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of crm_email_controller.py
crm_email_controller.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/crm_email_controller.py
"""
Layer 2 — /api/crm/email/*
CRM-context wrappers around the email engine (JSON-RPC format).
"""

import logging
from datetime import timedelta, timezone
from odoo import http, fields
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields, so we guard for both."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _folder_role(folder):
    value = (folder or 'inbox').strip().lower()
    return value if value in {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'} else 'custom'


def _is_sent_folder(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent',
        'sent items',
        'sent messages',
    }


def _crm_error(exc, handler=''):
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass
    return {'success': False, 'error': str(exc)}


def _msg_to_dict(msg, full=False):
    import json as _json
    data = {
        'id':           msg.id,
        'account_id':   msg.account_id.id,
        'folder':       msg.folder,
        'folder_role':  _folder_role(msg.folder),
        'subject':      msg.subject or '(no subject)',
        'from_name':    msg.from_name or '',
        'from_address': msg.from_address or '',
        'to_addresses': msg.to_addresses or '[]',
        'date':         _to_riyadh_iso(msg.date),
        'read_at':      _to_riyadh_iso(msg.read_at) if msg.read_at else None,
        'is_read':      msg.is_read,
        'is_starred':   msg.is_starred,
        'version':      _to_riyadh_iso(msg.write_date),
        'write_date':   _to_riyadh_iso(msg.write_date),
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket': {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                      if msg.linked_ticket_id else None,
        },
    }
    if full:
        data['body_html']   = msg.body_html or ''
        data['body_text']   = msg.body_text or ''
        data['attachments'] = []
    return data


class CrmEmailController(http.Controller):

    # ── Customer-scoped inbox ─────────────────────────────────────────────────

    @http.route('/api/crm/email/customer/<int:customer_id>/messages',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_messages(self, customer_id, folder=None, page=1, per_page=30, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [
                ('linked_customer_id', '=', customer_id),
                ('is_deleted', '=', False),
            ]
            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            if folder:
                domain.append(('folder', '=', folder))
            offset = (int(page) - 1) * int(per_page)
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='create_date desc, id desc')
            # Try to resolve customer name from CRM model if available
            customer_name = ''
            try:
                customer = request.env['lugal.crm.customer'].browse(customer_id)
                customer_name = customer.name if customer.exists() else ''
            except Exception:
                pass
            return {
                'success':       True,
                'data': {
                    'customer_id':   customer_id,
                    'customer_name': customer_name,
                    'total':         total,
                    'page':          int(page),
                    'per_page':      int(per_page),
                    'items':         [_msg_to_dict(m) for m in msgs],
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'customer_messages')

    @http.route('/api/crm/email/customer/<int:customer_id>/thread',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_thread(self, customer_id, subject_contains=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('linked_customer_id', '=', customer_id), ('is_deleted', '=', False)]
            if subject_contains:
                domain.append(('subject', 'ilike', subject_contains))
            msgs = request.env['lugal.email.message'].sudo().search(domain, order='subject, date desc')
            # Group by subject
            threads = {}
            for m in msgs:
                key = (m.subject or '').strip()
                threads.setdefault(key, []).append(_msg_to_dict(m))
            thread_list = [{'subject': k, 'count': len(v), 'messages': v} for k, v in threads.items()]
            return {
                'success': True,
                'data': {
                    'customer_id': customer_id,
                    'total_threads': len(thread_list),
                    'threads': thread_list,
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'customer_thread')

    # ── Personal CRM inbox ────────────────────────────────────────────────────

    @http.route('/api/crm/email/messages/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_list(self, folder='inbox', page=1, per_page=30,
                      customer_id=None, ticket_id=None, is_read=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            accs = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid), ('is_deleted', '=', False),
            ])
            domain = [
                ('account_id', 'in', accs.ids),
                ('folder', '=', folder),
                ('is_deleted', '=', False),
            ]
            if customer_id:
                domain.append(('linked_customer_id', '=', int(customer_id)))
            if ticket_id:
                domain.append(('linked_ticket_id', '=', int(ticket_id)))
            if is_read is not None:
                domain.append(('is_read', '=', bool(is_read)))
            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            offset = (int(page) - 1) * int(per_page)
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='create_date desc, id desc')
            return {
                'success': True,
                'data': {
                    'total': total, 'page': int(page), 'per_page': int(per_page),
                    'items': [_msg_to_dict(m) for m in msgs],
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'messages_list')

    @http.route('/api/crm/email/messages/<int:message_id>',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_detail(self, message_id, preview=False, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid or msg.is_deleted:
                return {'success': False, 'error': 'Not found'}
            if not preview and not msg.is_read and not _is_sent_folder(msg.folder):
                was_already_read = bool(msg.read_at)
                read_at = fields.Datetime.now()
                msg.write({'is_read': True, 'read_at': read_at})
                try:
                    from odoo.addons.lugal_email.controllers.email_controller import (
                        _propagate_read_to_sent_copies,
                        _refresh_account_unread_count,
                        _resolve_imap_folder,
                        _send_mdn_async,
                    )
                    if not was_already_read and msg.message_id:
                        _propagate_read_to_sent_copies(request.env, msg.message_id, msg.read_at or read_at)
                    _refresh_account_unread_count(msg.account_id)
                    if msg.imap_uid:
                        msg.account_id.sudo()._imap_store_async(
                            msg.imap_uid,
                            _resolve_imap_folder(msg.account_id, msg.folder),
                            add_flags=['\\Seen'],
                        )
                    if (not was_already_read
                            and msg.request_read_receipt
                            and msg.from_address
                            and msg.message_id):
                        _send_mdn_async(
                            acc=msg.account_id,
                            to_address=msg.from_address,
                            original_message_id=msg.message_id,
                            original_subject=msg.subject or '',
                            recipient_email=msg.account_id.email_address,
                        )
                except Exception:
                    _logger.warning('CRM email detail read sync failed msg=%s', msg.id)
            return {'success': True, 'data': _msg_to_dict(msg, full=True)}
        except Exception as exc:
            return _crm_error(exc, 'message_detail')

    # ── Templates ─────────────────────────────────────────────────────────────

    @http.route('/api/crm/email/templates/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def templates_list(self, branch_id=None, category=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('channel', '=', 'email'), ('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', int(branch_id)))
            if category:
                domain.append(('category', '=', category))
            templates = request.env['lugal.crm.message.template'].search(domain)
            items = [{
                'id':       t.id, 'name': t.name, 'name_ar': t.name_ar or '',
                'channel':  t.channel, 'category': t.category,
                'body':     t.body, 'body_ar': t.body_ar or '',
                'branch_id': t.branch_id.id if t.branch_id else None,
            } for t in templates]
            return {'success': True, 'data': {'total': len(items), 'items': items}}
        except Exception as exc:
            return _crm_error(exc, 'templates_list')

    @http.route('/api/crm/email/templates/<int:template_id>/apply',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_apply(self, template_id, customer_id=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            t = request.env['lugal.crm.message.template'].browse(template_id)
            if not t.exists():
                return {'success': False, 'error': 'Template not found'}
            customer_name = ''
            if customer_id:
                c = request.env['lugal.crm.customer'].browse(int(customer_id))
                if c.exists():
                    customer_name = c.name
            user = request.env.user
            vars_ = {
                'customer_name': customer_name,
                'agent_name':    user.name or '',
                'branch_name':   t.branch_id.name if t.branch_id else '',
            }
            rendered    = t.body or ''
            rendered_ar = t.body_ar or ''
            for k, v in vars_.items():
                rendered    = rendered.replace(f'{{{k}}}', v)
                rendered_ar = rendered_ar.replace(f'{{{k}}}', v)
            return {'success': True, 'data': {'rendered': rendered, 'rendered_ar': rendered_ar}}
        except Exception as exc:
            return _crm_error(exc, 'template_apply')

    # ── Bulk actions ──────────────────────────────────────────────────────────

    @http.route('/api/crm/email/bulk/read',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_read(self, message_ids=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids:
                return {'success': False, 'error': 'message_ids required'}
            msgs = request.env['lugal.email.message'].sudo().browse(message_ids).filtered(
                lambda msg: msg.exists() and msg.account_id.user_id.id == uid and not msg.is_deleted
            )
            readable_msgs = msgs.filtered(lambda msg: not _is_sent_folder(msg.folder))
            unread_msgs = readable_msgs.filtered(lambda msg: not msg.is_read or not msg.read_at)
            read_at = fields.Datetime.now()
            if unread_msgs:
                unread_msgs.write({'is_read': True, 'read_at': read_at})
                try:
                    from odoo.addons.lugal_email.controllers.email_controller import (
                        _propagate_read_to_sent_copies,
                        _refresh_account_unread_count,
                        _resolve_imap_folder,
                        _send_mdn_async,
                    )
                    for msg in unread_msgs:
                        if msg.message_id:
                            _propagate_read_to_sent_copies(request.env, msg.message_id, msg.read_at or read_at)
                        _refresh_account_unread_count(msg.account_id)
                        if msg.imap_uid:
                            msg.account_id.sudo()._imap_store_async(
                                msg.imap_uid,
                                _resolve_imap_folder(msg.account_id, msg.folder),
                                add_flags=['\\Seen'],
                            )
                        if msg.request_read_receipt and msg.from_address and msg.message_id:
                            _send_mdn_async(
                                acc=msg.account_id,
                                to_address=msg.from_address,
                                original_message_id=msg.message_id,
                                original_subject=msg.subject or '',
                                recipient_email=msg.account_id.email_address,
                            )
                except Exception:
                    _logger.warning('CRM email bulk read sync failed ids=%s', unread_msgs.ids)
            return {
                'success': True,
                'updated': len(unread_msgs),
                'skipped_sent_ids': msgs.filtered(lambda msg: _is_sent_folder(msg.folder)).ids,
            }
        except Exception as exc:
            return _crm_error(exc, 'bulk_read')

    @http.route('/api/crm/email/bulk/trash',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_trash(self, message_ids=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids:
                return {'success': False, 'error': 'message_ids required'}
            msgs = request.env['lugal.email.message'].sudo().browse(message_ids)
            msgs.write({'folder': 'trash'})
            return {'success': True, 'updated': len(msgs)}
        except Exception as exc:
            return _crm_error(exc, 'bulk_trash')

    @http.route('/api/crm/email/subscribe',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def subscribe(self, **kwargs):
        """Ensure the IMAP IDLE worker is running for all of this user's accounts.

        The FE calls this once after the WebSocket connects (fire-and-forget).
        It is idempotent — calling it multiple times has no side-effect.

        Response:
          {
            "subscribed": true,
            "accounts": ["user@domain.com", ...],
            "polling_interval_seconds": 30
          }

        The IMAP IDLE threads are persistent daemons owned by a single Odoo worker
        process. This endpoint wakes the supervisor immediately (instead of waiting
        up to 5 s for the background watchdog) so notifications start instantly.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            # Wake the IDLE supervisor immediately.
            # We trigger the dedicated cron job instead of calling start_all()
            # directly so that the IMAP threads are always owned by the
            # long-lived cron worker (SNl process) rather than a short-lived
            # HTTP worker that gets recycled after ~N requests.  The cron
            # trigger wakes the cron worker within seconds.
            try:
                cron = request.env.ref(
                    'lugal_email.ir_cron_lugal_email_idle_supervisor',
                    raise_if_not_found=False,
                )
                if cron:
                    cron.sudo()._trigger()
                else:
                    # Fallback if the cron ref is not found
                    request.env['lugal.email.idle.watcher'].sudo().start_all()
            except Exception as exc:
                _logger.warning('subscribe: cron trigger failed: %s', exc)

            # Return which accounts are being monitored for this user.
            accounts = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid),
                ('is_active', '=', True),
                ('is_deleted', '=', False),
            ])
            monitored = [
                acc.email_address
                for acc in accounts
                if (acc.password or '').strip()
            ]

            # Trigger one background IMAP sync per credential group on connect.
            # Force=True bypasses the 30-second throttle so the user always gets
            # fresh emails immediately when they open the app or reconnect.
            try:
                db_name = request.env.cr.dbname
                from odoo.addons.lugal_email.controllers.email_controller import (
                    _run_imap_sync_bg,
                )
                seen_creds: set = set()
                for acc in accounts:
                    if not (acc.password or '').strip():
                        continue
                    cred = (
                        (acc.imap_host or '').strip(),
                        int(acc.imap_port or 993),
                        (acc.username or acc.email_address or '').strip(),
                    )
                    if cred in seen_creds:
                        continue
                    seen_creds.add(cred)
                    # Always force a sync on WS connect — user expects fresh data
                    _run_imap_sync_bg(acc.id, db_name, force=True)
            except Exception as exc_sync:
                _logger.warning('subscribe: immediate email sync failed: %s', exc_sync)

            # Return current unread count so the FE can reconcile immediately on
            # connect without waiting for the next IMAP sync or push event.
            # This closes the race where an email arrives between page load and
            # WebSocket subscription.
            total_unread = 0
            try:
                total_unread = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', 'in', accounts.ids),
                    ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])
            except Exception:
                pass

            return {
                'success': True,
                'subscribed': True,
                'accounts': monitored,
                'polling_interval_seconds': 30,
                'unread_count': total_unread,
            }
        except Exception as exc:
            return _crm_error(exc, 'subscribe')

    @http.route('/api/crm/email/messages/bulk_delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_permanent_delete(self, message_ids=None, **kwargs):
        """Hard-delete messages that are already in the trash folder.

        Only messages owned by the caller that are in the 'trash' folder are
        deleted. Messages in any other folder, or belonging to another user,
        are skipped (reported in skipped_ids) without raising an error.

        Params (JSON-RPC):
          message_ids: list[int]  — max 1000 per call, required.

        Response:
          { "success": true, "data": { "deleted_ids": [...], "skipped_ids": [...] } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids or not isinstance(message_ids, list):
                return {'success': False, 'error': 'message_ids must be a non-empty list'}
            if len(message_ids) > 1000:
                return {'success': False, 'error': 'message_ids may not exceed 1000 per request'}

            user_accounts = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid),
                ('is_deleted', '=', False),
                ('is_active', '=', True),
            ])
            user_account_ids = user_accounts.ids

            Msg = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids)

            to_delete = msgs.filtered(
                lambda m: m.exists()
                and not m.is_deleted
                and m.account_id.id in user_account_ids
                and m.folder == 'trash'
            )
            deleted_ids = to_delete.ids
            skipped_ids = [i for i in message_ids if i not in deleted_ids]
            to_delete.unlink()

            return {
                'success': True,
                'data': {
                    'deleted_ids': deleted_ids,
                    'skipped_ids': skipped_ids,
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'bulk_permanent_delete')

    # ── Stats ─────────────────────────────────────────────────────────────────

    @http.route('/api/crm/email/stats',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stats(self, customer_id=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if customer_id:
                domain.append(('linked_customer_id', '=', int(customer_id)))
            Msg = request.env['lugal.email.message'].sudo()
            return {
                'success': True,
                'data': {
                    'total':    Msg.search_count(domain),
                    'unread':   Msg.search_count(domain + [('is_read', '=', False)]),
                    'starred':  Msg.search_count(domain + [('is_starred', '=', True)]),
                    'by_folder': {
                        f: Msg.search_count(domain + [('folder', '=', f)])
                        for f in ('inbox', 'sent', 'drafts', 'trash', 'archive', 'spam')
                    },
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'stats')
# TODO: remove - cherry-pick marker

end of file crm_email_controller.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of settings_email_controller.py
settings_email_controller.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/settings_email_controller.py
"""
Layer 3 — /api/crm/settings/email/*
User-facing CRUD for email account configuration (JSON-RPC).
"""

import logging
from datetime import timedelta, timezone
from odoo import http
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _crm_error(exc, handler=''):
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass
    return {'success': False, 'error': str(exc)}


def _acc_to_dict(acc):
    return {
        'id':             acc.id,
        'name':           acc.name,
        'email_address':  acc.email_address,
        'display_name':   acc.display_name_field or '',
        'imap_host':      acc.imap_host or '',
        'imap_port':      acc.imap_port,
        'imap_use_ssl':   acc.imap_use_ssl,
        'smtp_host':      acc.smtp_host or '',
        'smtp_port':      acc.smtp_port,
        'smtp_use_tls':   acc.smtp_use_tls,
        'is_default':     acc.is_default,
        'is_active':      acc.is_active,
        'sync_status':    acc.sync_status or 'never',
        'last_sync_date': _to_riyadh_iso(acc.last_sync_date),
        'unread_count':   acc.unread_count,
    }


class SettingsEmailController(http.Controller):

    @http.route('/api/crm/settings/email/accounts',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_accounts(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            accs = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid), ('is_deleted', '=', False),
            ])
            return {'success': True, 'data': [_acc_to_dict(a) for a in accs]}
        except Exception as exc:
            return _crm_error(exc, 'list_accounts')

    @http.route('/api/crm/settings/email/accounts/add',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def add_account(self, name, email_address, username=None, password=None,
                    imap_host='imap.gmail.com', imap_port=993, imap_use_ssl=True,
                    smtp_host='smtp.gmail.com', smtp_port=587, smtp_use_tls=True,
                    display_name=None, is_default=False, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().create({
                'user_id':           uid,
                'name':              name,
                'email_address':     email_address,
                'display_name_field': display_name or '',
                'username':          username or email_address,
                'password':          password or '',
                'imap_host':         imap_host,
                'imap_port':         int(imap_port),
                'imap_use_ssl':      imap_use_ssl,
                'smtp_host':         smtp_host,
                'smtp_port':         int(smtp_port),
                'smtp_use_tls':      smtp_use_tls,
                'is_default':        is_default,
            })
            if is_default:
                acc.action_set_default()
            # Trigger IDLE watcher immediately so the new account does not have
            # to wait up to 1 minute for the next supervisor cron run.
            # Also do an initial IMAP sync right now so existing inbox messages
            # are imported and the WS notification fires without delay.
            if (password or '').strip():
                try:
                    acc.action_sync()
                except Exception:
                    _logger.warning('add_account: initial sync failed for account %s', acc.id, exc_info=True)
                acc._schedule_idle_start()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'add_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid or acc.is_deleted:
                return {'success': False, 'error': 'Account not found'}
            allowed = {
                'name', 'email_address', 'display_name_field', 'username', 'password',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls', 'is_active',
            }
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                acc.write(vals)
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'update_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as exc:
            return _crm_error(exc, 'delete_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/test',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def test_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_test_connection()
        except Exception as exc:
            return _crm_error(exc, 'test_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/sync',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def sync_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_sync()
        except Exception as exc:
            return _crm_error(exc, 'sync_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/set_default',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def set_default(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.action_set_default()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'set_default')
# TODO: remove - cherry-pick marker

end of file settings_email_controller.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of rules_controller.py
rules_controller.py

# -*- coding: utf-8 -*-
# Component: Lugal Email — rules & quick steps REST API (rules_controller.py)
"""
Email Rules  &  Quick Steps REST API
=====================================

Rules endpoints:
  GET    /api/lugal/email/rules            — list current user's rules
  POST   /api/lugal/email/rules            — create a rule
  GET    /api/lugal/email/rules/<id>       — get one rule
  PUT    /api/lugal/email/rules/<id>       — full update
  PATCH  /api/lugal/email/rules/<id>       — partial update
  DELETE /api/lugal/email/rules/<id>       — delete
  POST   /api/lugal/email/rules/<id>/test  — dry-run a rule against a message

Quick Steps endpoints:
  GET    /api/lugal/email/quick_steps            — list
  POST   /api/lugal/email/quick_steps            — create
  GET    /api/lugal/email/quick_steps/<id>       — get one
  PUT    /api/lugal/email/quick_steps/<id>       — update
  DELETE /api/lugal/email/quick_steps/<id>       — delete
  POST   /api/lugal/email/messages/<id>/apply_quick_step — apply to a message
"""
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _imap_exc_text(exc):
    parts = []
    for a in getattr(exc, 'args', ()) or ():
        if isinstance(a, bytes):
            parts.append(a.decode('utf-8', errors='replace'))
        else:
            parts.append(str(a))
    return ' '.join(parts) if parts else str(exc)


def _is_imap_userip_limit(exc) -> bool:
    t = _imap_exc_text(exc).lower()
    return any(
        k in t
        for k in (
            '[limit]', 'mail_max_userip', 'maximum number of connections',
            'too many connections',
        )
    )


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _ensure_jwt():
    """Return user_id from JWT or None."""
    from .email_controller import ensure_jwt_user_id
    return ensure_jwt_user_id()


def _json_ok(data, status=200):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': True, 'data': data})
    return request.make_response(body, headers=headers, status=status)


def _json_err(msg, status=400):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': False, 'error': msg})
    return request.make_response(body, headers=headers, status=status)


def _rule_dict(rule):
    return {
        'id':                 rule.id,
        'name':               rule.name,
        'is_active':          rule.is_active,
        'sequence':           rule.sequence,
        'match_mode':         rule.match_mode,
        'account_id':         rule.account_id.id if rule.account_id else None,
        'conditions':         json.loads(rule.conditions_json or '[]'),
        'actions':            json.loads(rule.actions_json or '[]'),
        'stop_processing':    rule.stop_processing,
        'last_triggered_at':  rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        'trigger_count':      rule.trigger_count,
    }


def _message_has_attachments(msg) -> bool:
    if not msg or not msg.exists():
        return False
    return bool(msg.env['ir.attachment'].sudo().search_count([
        ('res_model', '=', 'lugal.email.message'),
        ('res_id', '=', msg.id),
    ]))


def _message_rule_vals(msg) -> dict:
    return {
        'from_address':    msg.from_address or '',
        'to_addresses':    msg.to_addresses or '',
        'cc_addresses':    msg.cc_addresses or '',
        'bcc_addresses':   msg.bcc_addresses or '',
        'subject':         msg.subject or '',
        'body_text':       msg.body_text or '',
        'has_attachments': _message_has_attachments(msg),
        'is_important':    msg.is_important,
        'is_read':         msg.is_read,
        'is_starred':      msg.is_starred,
        'folder':          msg.folder or '',
    }


def _rule_matches_shape(rule, conditions, actions) -> bool:
    try:
        return (
            json.loads(rule.conditions_json or '[]') == conditions
            and json.loads(rule.actions_json or '[]') == actions
        )
    except Exception:
        return False


def _find_existing_move_rule(uid, account_id, conditions, actions, env=None):
    Rule = (env or request.env)['lugal.email.rule'].sudo()
    for rule in Rule.search([
        ('user_id', '=', uid),
        ('account_id', '=', int(account_id)),
        ('is_active', '=', True),
    ], order='sequence asc, id asc'):
        if _rule_matches_shape(rule, conditions, actions):
            return rule
    return Rule.browse()


def _rule_move_destinations(rule):
    try:
        actions = json.loads(rule.actions_json or '[]') or []
    except Exception:
        return []
    return [
        (act.get('value') or '').strip()
        for act in actions
        if act.get('action') == 'move_folder' and (act.get('value') or '').strip()
    ]


def _message_already_in_destination_branch(msg, rule):
    current = (msg.folder or '').strip()
    if not current:
        return False
    for dest in _rule_move_destinations(rule):
        if current == dest or current.startswith(dest + '.') or current.startswith(dest + '/'):
            return True
    return False


def _apply_move_rule_to_existing(rule, uid, account_id=None, limit=5000):
    """Move existing inbound mail for a newly created move rule."""
    if not _rule_move_destinations(rule):
        return {'matched': 0, 'applied': 0, 'skipped': 0}

    Msg = rule.env['lugal.email.message'].sudo()
    domain = [
        ('account_id.user_id', '=', uid),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('is_deleted', '=', False),
    ]
    if account_id:
        domain.append(('account_id', '=', int(account_id)))

    matched = applied = skipped = 0
    affected_accounts = rule.env['lugal.email.account'].sudo().browse()
    for msg in Msg.search(domain, order='date desc, id desc', limit=limit):
        msg_vals = _message_rule_vals(msg)
        if not rule._matches(msg_vals):
            continue
        if _message_already_in_destination_branch(msg, rule):
            continue
        matched += 1
        try:
            affected_accounts |= msg.account_id
            rule._apply_actions(msg)
            applied += 1
        except Exception:
            skipped += 1
            _logger.warning('apply move rule to existing failed rule=%s msg=%s', rule.id, msg.id)

    for acc in affected_accounts:
        unread = Msg.search_count([
            ('account_id', '=', acc.id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        acc.sudo().write({'unread_count': unread})

    return {'matched': matched, 'applied': applied, 'skipped': skipped}


def _apply_account_move_rules_to_existing(rule, uid, account_id=None, limit=10000):
    """Re-run all active move rules in sequence for existing inbound mail.

    This preserves parent/child rule semantics: specific child rules such as
    Important/Attachments run first and stop processing, then the parent sender
    catch-all handles the remaining mail. Applying only the parent or child rule
    in isolation can leave old inbox rows behind or pull child matches back to
    the parent folder.
    """
    Rule = rule.env['lugal.email.rule'].sudo()
    Msg = rule.env['lugal.email.message'].sudo()
    domain = [
        ('account_id.user_id', '=', uid),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('is_deleted', '=', False),
    ]
    rule_domain = [('user_id', '=', uid), ('is_active', '=', True)]
    if account_id:
        aid = int(account_id)
        domain.append(('account_id', '=', aid))
        rule_domain.append(('account_id', '=', aid))

    rules = Rule.search(rule_domain, order='sequence asc, id asc')
    move_rules = rules.filtered(lambda r: bool(_rule_move_destinations(r)))
    if not move_rules:
        return {'matched': 0, 'applied': 0, 'skipped': 0, 'rules_considered': 0}

    matched = applied = skipped = 0
    affected_accounts = rule.env['lugal.email.account'].sudo().browse()
    for msg in Msg.search(domain, order='date desc, id desc', limit=limit):
        msg_vals = _message_rule_vals(msg)
        for candidate in move_rules:
            try:
                if not candidate._matches(msg_vals):
                    continue
                if _message_already_in_destination_branch(msg, candidate):
                    if candidate.stop_processing:
                        break
                    continue
                matched += 1
                before_folder = msg.folder
                affected_accounts |= msg.account_id
                candidate._apply_actions(msg)
                msg.invalidate_recordset()
                if msg.folder != before_folder:
                    applied += 1
                if candidate.stop_processing:
                    break
            except Exception:
                skipped += 1
                _logger.warning(
                    'apply account move rules failed rule=%s msg=%s',
                    candidate.id, msg.id,
                )
                break

    for acc in affected_accounts:
        unread = Msg.search_count([
            ('account_id', '=', acc.id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        acc.sudo().write({'unread_count': unread})

    return {
        'matched': matched,
        'applied': applied,
        'skipped': skipped,
        'rules_considered': len(move_rules),
    }


def _sender_values_from_conditions(conditions):
    return [
        (c.get('value') or '').strip().lower()
        for c in (conditions or [])
        if c.get('field') == 'from_address'
        and c.get('operator') == 'contains'
        and (c.get('value') or '').strip()
    ]


def _mirror_sender_move_rule_to_user_accounts(rule, uid, source_account_id=None):
    """Keep sender move rules consistent across all of a user's mail accounts.

    Users expect "move all from this sender" to follow the sender, not only the
    mailbox where the rule was first created.  If the same sender later emails a
    second account for the same user, that account must also have the destination
    folder/rule and historical mail moved.
    """
    try:
        conditions = json.loads(rule.conditions_json or '[]') or []
        actions = json.loads(rule.actions_json or '[]') or []
    except Exception:
        return []
    if not _sender_values_from_conditions(conditions):
        return []
    move_destinations = [
        (a.get('value') or '').strip()
        for a in actions
        if a.get('action') == 'move_folder' and (a.get('value') or '').strip()
    ]
    if not move_destinations:
        return []

    Acc = rule.env['lugal.email.account'].sudo()
    Rule = rule.env['lugal.email.rule'].sudo()
    accounts = Acc.search([
        ('user_id', '=', uid),
        ('is_active', '=', True),
        ('is_deleted', '=', False),
    ])
    mirrored = []
    for acc in accounts:
        if source_account_id and acc.id == int(source_account_id):
            continue

        # Ensure IMAP folders exist per account; creating a folder on one mailbox
        # does not create it on the user's other mailboxes.
        if (acc.password or '').strip():
            try:
                with acc._imap_session(connect_attempts=4, retry_delay=1.5) as conn:
                    for dest in move_destinations:
                        if dest.lower() not in {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}:
                            acc._imap_ensure_folder(dest, existing_conn=conn)
            except Exception:
                _logger.warning(
                    'mirror sender rule: could not ensure folders for acc=%s rule=%s',
                    acc.id, rule.id, exc_info=True,
                )

        existing = _find_existing_move_rule(uid, acc.id, conditions, actions, env=rule.env)
        if existing:
            mirrored_rule = existing
            created = False
        else:
            mirrored_rule = Rule.create({
                'name':            rule.name,
                'user_id':         uid,
                'account_id':      acc.id,
                'is_active':       True,
                'sequence':        rule.sequence,
                'match_mode':      rule.match_mode,
                'conditions_json': json.dumps(conditions),
                'actions_json':    json.dumps(actions),
                'stop_processing': rule.stop_processing,
            })
            created = True

        applied = _apply_account_move_rules_to_existing(mirrored_rule, uid, acc.id)
        mirrored.append({
            'account_id': acc.id,
            'rule_id': mirrored_rule.id,
            'created': created,
            'auto_applied_existing': applied,
        })
    return mirrored


def _qs_dict(qs):
    return {
        'id':          qs.id,
        'name':        qs.name,
        'description': qs.description or '',
        'sequence':    qs.sequence,
        'icon':        qs.icon or '',
        'steps':       json.loads(qs.steps_json or '[]'),
        'use_count':   qs.use_count,
    }


# ── Rules controller ───────────────────────────────────────────────────────────

class EmailRulesController(http.Controller):

    # ── List ──────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rules = request.env['lugal.email.rule'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_rule_dict(r) for r in rules])
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Create ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['POST'])
    def rules_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            account_id = body.get('account_id')
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _json_err('Account not found', 404)
            rule = request.env['lugal.email.rule'].sudo().create({
                'name':             name,
                'user_id':          uid,
                'account_id':       int(account_id) if account_id else False,
                'is_active':        body.get('is_active', True),
                'sequence':         int(body.get('sequence', 10)),
                'match_mode':       body.get('match_mode', 'all'),
                'conditions_json':  json.dumps(body.get('conditions', [])),
                'actions_json':     json.dumps(body.get('actions', [])),
                'stop_processing':  bool(body.get('stop_processing', False)),
            })
            auto_applied = _apply_account_move_rules_to_existing(rule, uid, account_id)
            mirrored_rules = _mirror_sender_move_rule_to_user_accounts(rule, uid, account_id)
            request.env.cr.commit()
            data = _rule_dict(rule)
            data['auto_applied_existing'] = auto_applied
            data['mirrored_rules'] = mirrored_rules
            return _json_ok(data, status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Get one ───────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_get(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Update (PUT / PATCH) ──────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def rules_update(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'            in body: write_vals['name']             = (body['name'] or '').strip()
            if 'is_active'       in body: write_vals['is_active']        = bool(body['is_active'])
            if 'sequence'        in body: write_vals['sequence']         = int(body['sequence'])
            if 'match_mode'      in body: write_vals['match_mode']       = body['match_mode']
            if 'conditions'      in body: write_vals['conditions_json']  = json.dumps(body['conditions'])
            if 'actions'         in body: write_vals['actions_json']     = json.dumps(body['actions'])
            if 'stop_processing' in body: write_vals['stop_processing']  = bool(body['stop_processing'])
            if 'account_id'      in body:
                account_id = body['account_id']
                if account_id:
                    acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                    if not acc.exists() or acc.user_id.id != uid:
                        return _json_err('Account not found', 404)
                write_vals['account_id'] = int(account_id) if account_id else False
            if write_vals:
                rule.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Delete ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def rules_delete(self, rule_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            rule.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': rule_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Apply rule to all existing messages ───────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>/apply_all', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_apply_all(self, rule_id, **kwargs):
        """Apply a rule retroactively to all existing inbox messages for the user."""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)

            body       = json.loads(request.httprequest.data or '{}')
            account_id = body.get('account_id')
            folder     = (body.get('folder') or 'inbox').strip()

            domain = [('account_id.user_id', '=', uid), ('is_deleted', '=', False)]
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _json_err('Account not found', 404)
                domain.append(('account_id', '=', int(account_id)))
            if folder:
                domain.append(('folder', '=', folder))

            messages  = request.env['lugal.email.message'].sudo().search(domain, order='id desc', limit=5000)
            matched = applied = skipped = 0
            for msg in messages:
                msg_vals = _message_rule_vals(msg)
                if rule._matches(msg_vals):
                    matched += 1
                    try:
                        rule._apply_actions(msg)
                        applied += 1
                    except Exception:
                        skipped += 1
                        _logger.warning('rules_apply_all: failed to apply rule %s to msg %s', rule_id, msg.id)

            request.env.cr.commit()
            return _json_ok({'matched': matched, 'applied': applied, 'skipped': skipped})
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Dry-run test ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>/test', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_test(self, rule_id, **kwargs):
        """Dry-run: return whether the rule would match a given message_id (no side effects)."""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body       = json.loads(request.httprequest.data or '{}')
            message_id = body.get('message_id')
            if not message_id:
                return _json_err('message_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(int(message_id))
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            msg_vals = _message_rule_vals(msg)
            matched     = rule._matches(msg_vals)
            would_apply = []
            if matched:
                for act in rule._get_actions():
                    would_apply.append(act)
            return _json_ok({
                'rule_id':      rule_id,
                'message_id':   int(message_id),
                'matched':      matched,
                'would_apply':  would_apply,
                'stop_after':   rule.stop_processing and matched,
            })
        except Exception as exc:
            return _json_err(str(exc), 500)


    # ── Create rule from template (auto-creates IMAP folders) ─────────────────

    @http.route('/api/lugal/email/rules/from_template', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_from_template(self, **kwargs):
        """Create a rule from a predefined template.

        Automatically creates the IMAP folder structure and immediately moves
        any existing matching messages into the destination folder (both in the
        DB and on the IMAP server synchronously — no fire-and-forget).

        Body:
          {
            "template_key":  "move_important_from_sender",
            "sender_email":  "omar@nooralnibras.com",
            "sender_name":   "Omar",
            "account_id":    4
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})

        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)

        try:
            body         = json.loads(request.httprequest.data or '{}')
            template_key = (body.get('template_key') or '').strip()
            sender_email = (
                (body.get('sender_email') or body.get('senderEmail') or '')
            ).strip()
            sender_name = (
                (body.get('sender_name') or body.get('senderName') or sender_email or '')
            ).strip()
            account_id   = body.get('account_id')

            if not template_key:
                return _json_err('template_key is required', 400)
            if not account_id:
                return _json_err('account_id is required', 400)

            acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
            if not acc.exists() or acc.user_id.id != uid:
                return _json_err('Account not found or access denied', 404)

            # Canonical address for rule conditions + folder slug
            sender_addr = sender_email
            if not sender_addr and sender_name and '@' in sender_name:
                sender_addr = sender_name.strip()
            if not sender_addr:
                return _json_err(
                    'sender_email is required (JSON key sender_email or senderEmail; '
                    'or pass sender_name as a full address containing @)',
                    400,
                )

            # ── Folder slug: always from email local-part, dots → underscores ──
            import re as _re

            def _folder_slug_from_email(addr: str) -> str:
                addr = (addr or '').strip().lower()
                if not addr:
                    return 'sender'
                local, _, domain = addr.partition('@')
                local = (local or (domain.split('.')[0] if domain else '') or 'sender')
                # Dots in local-part become '_' so the slug is one IMAP hierarchy segment
                local = local.replace('.', '_')
                slug = _re.sub(r'[^\w\-]+', '_', local, flags=_re.ASCII).strip('_') or 'sender'
                return slug[:60].rstrip('_')

            folder_slug = _folder_slug_from_email(sender_addr)

            slug_override = (body.get('folder_slug') or '').strip()
            if slug_override:
                folder_slug = _re.sub(r'[^\w\-]+', '', slug_override, flags=_re.ASCII)[:60] or folder_slug

            # Human-readable rule label
            if sender_name and '@' not in sender_name and sender_name.strip():
                sender_label = f'{sender_name.strip()} ({sender_addr})'
            else:
                sender_label = sender_addr

            # ── Template catalogue ─────────────────────────────────────────────
            TEMPLATES = {
                'move_all_from_sender': {
                    'label':       f'Move all emails from {sender_label} to sender parent folder',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_important_from_sender': {
                    'label':       f'Move all important emails from {sender_label} to Important child folder',
                    'child_name':  'Important',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                        {'field': 'is_important', 'operator': 'equals', 'value': 'true'},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_attachments_from_sender': {
                    'label':       f'Move all emails with attachments from {sender_label} to Attachments child folder',
                    'child_name':  'Attachments',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',    'operator': 'contains', 'value': sender_addr},
                        {'field': 'has_attachments', 'operator': 'equals',   'value': 'true'},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_cc_bcc_from_sender': {
                    'label':       f'Move all emails with CC and BCC from {sender_label} to CC and BCC child folder',
                    'child_name':  'CC and BCC',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',  'operator': 'contains',     'value': sender_addr},
                        {'field': 'cc_addresses',  'operator': 'is_not_empty', 'value': ''},
                        {'field': 'bcc_addresses', 'operator': 'is_not_empty', 'value': ''},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
            }

            tpl = TEMPLATES.get(template_key)
            if not tpl:
                return _json_err(
                    f'Unknown template_key. Valid keys: {list(TEMPLATES)}', 400)

            # ── Build IMAP folder paths ────────────────────────────────────────
            import time as _time_mod

            delimiter = '.'
            child_name = tpl['child_name']
            folders_created = []
            is_move_template = bool(child_name) or template_key.startswith('move_')

            parent_path = f'INBOX{delimiter}{folder_slug}'
            dest_path = (f'{parent_path}{delimiter}{child_name}'
                         if child_name else parent_path)

            for outer_attempt in range(6):
                folders_created = []
                try:
                    with acc._imap_session(connect_attempts=14, retry_delay=3.5) as conn_probe:
                        # Detect delimiter by listing all folders.
                        # Do NOT use conn.list('', '') — some servers (cPanel/Dovecot)
                        # reject an empty reference string with "Invalid reference".
                        typ_d, listing_d = conn_probe.list()
                        if typ_d == 'OK' and listing_d:
                            first = listing_d[0]
                            if isinstance(first, bytes):
                                first = first.decode('utf-8', errors='replace')
                            import re as _re2
                            m = _re2.search(r'"([./])"', first)
                            if m:
                                delimiter = m.group(1)

                        parent_path = f'INBOX{delimiter}{folder_slug}'
                        dest_path = (f'{parent_path}{delimiter}{child_name}'
                                     if child_name else parent_path)

                        if is_move_template:
                            acc._imap_ensure_folder(parent_path, existing_conn=conn_probe)
                            folders_created.append(parent_path)
                            if child_name:
                                acc._imap_ensure_folder(dest_path, existing_conn=conn_probe)
                                folders_created.append(dest_path)
                    break
                except Exception as fe:
                    if outer_attempt < 5 and _is_imap_userip_limit(fe):
                        _time_mod.sleep(3.0 * (outer_attempt + 1))
                        continue
                    fe_disp = _imap_exc_text(fe)
                    st = 503 if _is_imap_userip_limit(fe) else 500
                    return _json_err(
                        f'Could not prepare IMAP folders under "{parent_path}": {fe_disp}',
                        st,
                    )

            # ── Build actions list ─────────────────────────────────────────────
            actions = list(tpl['mark_actions'])
            if is_move_template:
                actions.append({'action': 'move_folder', 'value': dest_path})

            Rule = request.env['lugal.email.rule'].sudo()
            parent_rule = Rule.browse()
            parent_conditions = [
                {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
            ]
            parent_actions = [{'action': 'move_folder', 'value': parent_path}]

            # ── Create/reuse rules ────────────────────────────────────────────
            # Any nested sender rule must have exactly one parent rule:
            #   INBOX.<sender>            -> all mail from sender
            #   INBOX.<sender>.Important  -> important subset
            #   INBOX.<sender>.<Sibling>  -> another subset
            # Child subset rules run first and stop.  The parent catch-all runs
            # later so non-matching sender mail still lands in the parent.
            if is_move_template and child_name:
                parent_rule = _find_existing_move_rule(
                    uid, account_id, parent_conditions, parent_actions)
                if not parent_rule:
                    parent_rule = Rule.create({
                        'name':             f'Move all emails from {sender_label}',
                        'user_id':          uid,
                        'account_id':       int(account_id),
                        'is_active':        True,
                        'sequence':         90,
                        'match_mode':       'all',
                        'conditions_json':  json.dumps(parent_conditions),
                        'actions_json':     json.dumps(parent_actions),
                        'stop_processing':  True,
                    })

            existing_child_rule = _find_existing_move_rule(uid, account_id, tpl['conditions'], actions)
            if existing_child_rule:
                rule = existing_child_rule
            else:
                rule = Rule.create({
                    'name':             tpl['label'],
                    'user_id':          uid,
                    'account_id':       int(account_id),
                    'is_active':        True,
                    'sequence':         10 if child_name else 90,
                    'match_mode':       tpl['match_mode'],
                    'conditions_json':  json.dumps(tpl['conditions']),
                    'actions_json':     json.dumps(actions),
                    'stop_processing':  tpl['stop_processing'],
                })
            request.env.cr.commit()

            # ── Auto-apply: update DB immediately, move on IMAP in background ──
            # Moving 100+ messages via individual IMAP round-trips inside an HTTP
            # request reliably times out. Instead:
            #   1. Update the DB folder field for all matching messages RIGHT NOW
            #      so the FE sees them in the correct folder instantly.
            #   2. Fire a single background thread that opens one IMAP connection
            #      and moves all messages using UID MOVE in batches.
            applied_count = 0
            skipped_count = 0

            if is_move_template:
                Msg = request.env['lugal.email.message'].sudo()
                existing = Msg.search([
                    ('account_id', '=', int(account_id)),
                    ('is_deleted', '=', False),
                ], order='id desc', limit=2000)

                # Find matching messages and collect (msg_id, imap_uid, from_folder, dest)
                to_move_db  = []   # ORM records for DB update
                to_move_imap = []  # (imap_uid, from_imap_path, dest_path) for background thread
                _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

                for msg in existing:
                    msg_vals = _message_rule_vals(msg)
                    try:
                        target_path = None
                        if child_name and parent_rule and parent_rule._matches(msg_vals):
                            target_path = dest_path if rule._matches(msg_vals) else parent_path
                        elif rule._matches(msg_vals):
                            target_path = dest_path

                        if target_path:
                            to_move_db.append((msg, target_path))
                            # Determine IMAP source path for this message
                            cur = msg.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                imap_from = 'INBOX'
                            elif cur.lower() in _LOGICAL:
                                # We'll resolve the actual server name in the bg thread
                                imap_from = cur.lower()
                            else:
                                imap_from = cur
                            if msg.imap_uid:
                                to_move_imap.append((msg.imap_uid, imap_from, target_path))
                    except Exception:
                        skipped_count += 1

                # Step 1: update DB immediately so FE sees messages in new folder
                if to_move_db:
                    try:
                        import collections as _collections
                        by_dest = _collections.defaultdict(list)
                        for m, target_path in to_move_db:
                            by_dest[target_path].append(m.id)
                        for target_path, ids in by_dest.items():
                            write_vals = {'folder': target_path}
                            if target_path.replace('/', '.').split('.')[-1].lower() == 'important':
                                write_vals['is_important'] = True
                            Msg.browse(ids).write(write_vals)
                        unread_count = Msg.search_count([
                            ('account_id', '=', int(account_id)),
                            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                            ('is_read', '=', False),
                            ('is_deleted', '=', False),
                        ])
                        acc.sudo().write({'unread_count': unread_count})
                        request.env.cr.commit()
                        applied_count = len(to_move_db)
                    except Exception as dbe:
                        _logger.warning('from_template DB batch update failed: %s', dbe)
                        for msg, target_path in to_move_db:
                            try:
                                write_vals = {'folder': target_path}
                                if target_path.replace('/', '.').split('.')[-1].lower() == 'important':
                                    write_vals['is_important'] = True
                                msg.write(write_vals)
                                applied_count += 1
                            except Exception:
                                skipped_count += 1
                        try:
                            unread_count = Msg.search_count([
                                ('account_id', '=', int(account_id)),
                                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                                ('is_read', '=', False),
                                ('is_deleted', '=', False),
                            ])
                            acc.sudo().write({'unread_count': unread_count})
                            request.env.cr.commit()
                        except Exception:
                            pass

                # Step 2: fire background thread for IMAP moves
                # Groups UIDs by source folder so we only SELECT each mailbox once.
                if to_move_imap:
                    import threading as _threading
                    import collections as _collections
                    db_name = request.env.cr.dbname
                    acc_id  = acc.id

                    # Group by source folder for efficiency
                    by_folder = _collections.defaultdict(list)
                    for uid, from_folder, target_path in to_move_imap:
                        by_folder[(from_folder, target_path)].append(uid)

                    def _bg_imap_move():
                        try:
                            from odoo.modules.registry import Registry as _Reg
                            import odoo as _odoo
                            with _Reg(db_name).cursor() as _cr:
                                _env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                                _acc = _env['lugal.email.account'].browse(acc_id)
                                with _acc._imap_session() as conn:
                                    for (src_folder, target_path), uids in by_folder.items():
                                        # Resolve logical names to real IMAP paths
                                        if src_folder.lower() == 'inbox':
                                            imap_src = 'INBOX'
                                        elif src_folder.lower() in _LOGICAL:
                                            imap_src = _acc._get_server_folder_name(
                                                src_folder.lower(), existing_conn=conn)
                                        else:
                                            imap_src = src_folder

                                        try:
                                            conn.select(imap_src, readonly=False)
                                        except Exception as se:
                                            _logger.warning(
                                                'bg_imap_move: SELECT %s failed: %s', imap_src, se)
                                            continue

                                        # Move in batches of 50 UIDs at a time
                                        _BATCH = 50
                                        for i in range(0, len(uids), _BATCH):
                                            batch = uids[i:i + _BATCH]
                                            uid_set = ','.join(str(u) for u in batch)
                                            try:
                                                typ_m, _ = conn.uid('move', uid_set, target_path)
                                                if typ_m != 'OK':
                                                    # Fallback: COPY + mark deleted + expunge
                                                    conn.uid('copy', uid_set, target_path)
                                                    conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                                    conn.expunge()
                                                _logger.info(
                                                    'bg_imap_move: moved %d uids from %s → %s',
                                                    len(batch), imap_src, target_path,
                                                )
                                            except Exception as me:
                                                _logger.warning(
                                                    'bg_imap_move: batch move failed %s → %s: %s',
                                                    imap_src, target_path, me,
                                                )
                        except Exception as exc:
                            _logger.warning('bg_imap_move thread failed acc=%s: %s', acc_id, exc)

                    _threading.Thread(
                        target=_bg_imap_move, daemon=True,
                        name=f'imap-bulk-move-{acc_id}',
                    ).start()

            mirrored_rules = []
            if is_move_template:
                if parent_rule:
                    mirrored_rules.extend(
                        _mirror_sender_move_rule_to_user_accounts(parent_rule, uid, account_id)
                    )
                mirrored_rules.extend(
                    _mirror_sender_move_rule_to_user_accounts(rule, uid, account_id)
                )

            return _json_ok({
                'rule':            _rule_dict(rule),
                'parent_rule':     _rule_dict(parent_rule) if parent_rule else None,
                'folder_slug':     folder_slug,
                'sender_label':    sender_label,
                'sender_address':  sender_addr,
                'parent_folder':   parent_path if is_move_template else None,
                'dest_folder':     dest_path   if is_move_template else None,
                'folders_created': folders_created,
                'client_guidance': (
                    'Move templates create IMAP folders on the server in this request. '
                    'You do not need to call POST …/folders/create first unless the UI '
                    'builds a custom path or name outside the template.'
                ),
                'auto_applied': {
                    'applied':          applied_count,
                    'skipped':          skipped_count,
                    'imap_move_queued': bool(to_move_imap) if is_move_template else False,
                },
                'mirrored_rules':   mirrored_rules,
            }, status=201)

        except Exception as exc:
            _logger.exception('rules_from_template error')
            return _json_err(str(exc), 500)

    # ── Rule Templates ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/templates', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_templates(self, **kwargs):
        """Return predefined rule templates for the 'Create Rule' dropdown."""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])

        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)

        sender_email = (kwargs.get('sender_email') or '').strip()
        sender_name  = (kwargs.get('sender_name')  or sender_email or 'sender').strip()
        folder       = (kwargs.get('folder')        or '').strip()

        import re as _re

        def _folder_slug_from_email(addr: str) -> str:
            addr = (addr or '').strip().lower()
            if not addr:
                return 'sender'
            local, _, domain = addr.partition('@')
            local = (local or (domain.split('.')[0] if domain else '') or 'sender')
            local = local.replace('.', '_')
            return _re.sub(r'[^\w\-]+', '_', local, flags=_re.ASCII).strip('_')[:60] or 'sender'

        folder_slug = _folder_slug_from_email(sender_email)
        parent_folder = folder or f'INBOX.{folder_slug}'

        def move_action_for(child_name=None):
            target = parent_folder if not child_name else f'{parent_folder}.{child_name}'
            return [{'action': 'move_folder', 'value': target}]

        def sender_cond():
            return [{
                'field':    'from_address',
                'operator': 'contains',
                'value':    sender_email,
            }] if sender_email else []

        def template_item(key, label, description, conditions, child_name=None):
            destination = parent_folder if not child_name else f'{parent_folder}.{child_name}'
            return {
                'key':                     key,
                'label':                   label,
                'description':             description,
                'match_mode':              'all',
                'conditions':              conditions,
                'actions':                 move_action_for(child_name),
                'stop_processing':         True,
                'creates_folder':          True,
                'parent_folder':           parent_folder,
                'child_folder':            child_name,
                'destination_folder':      destination,
                'destination_description': (
                    'Sender parent folder' if not child_name else f'{child_name} child folder'
                ),
            }

        templates = [
            template_item(
                'move_all_from_sender',
                f'Move all emails from {sender_name} to sender parent folder' if sender_email
                else 'Move all emails from a sender to sender parent folder',
                'Create/reuse the sender parent folder and move every email from this sender into it.',
                sender_cond() or [{'field': 'from_address', 'operator': 'contains', 'value': ''}],
            ),
            template_item(
                'move_important_from_sender',
                f'Move all important emails from {sender_name} to Important child folder' if sender_email
                else 'Move all important emails from a sender to Important child folder',
                'Create/reuse the sender parent folder plus its Important child folder, then move only important emails from this sender into that child folder.',
                (sender_cond() + [
                    {'field': 'is_important', 'operator': 'equals', 'value': 'true'},
                ]) if sender_email else [
                    {'field': 'from_address', 'operator': 'contains', 'value': ''},
                    {'field': 'is_important', 'operator': 'equals', 'value': 'true'},
                ],
                child_name='Important',
            ),
            template_item(
                'move_with_attachments_from_sender',
                f'Move all emails with attachments from {sender_name} to Attachments child folder' if sender_email
                else 'Move all emails with attachments from a sender to Attachments child folder',
                'Create/reuse the sender parent folder plus its Attachments child folder, then move only emails with attachments from this sender into that child folder.',
                sender_cond() + [{'field': 'has_attachments', 'operator': 'equals', 'value': 'true'}],
                child_name='Attachments',
            ),
            template_item(
                'move_with_cc_bcc_from_sender',
                f'Move all emails with CC and BCC from {sender_name} to CC and BCC child folder' if sender_email
                else 'Move all emails with CC and BCC from a sender to CC and BCC child folder',
                'Create/reuse the sender parent folder plus its CC and BCC child folder, then move only emails with both CC and BCC values into that child folder.',
                sender_cond() + [
                    {'field': 'cc_addresses',  'operator': 'is_not_empty', 'value': ''},
                    {'field': 'bcc_addresses', 'operator': 'is_not_empty', 'value': ''},
                ],
                child_name='CC and BCC',
            ),
        ]

        return _json_ok(templates)


# ── Quick Steps controller ─────────────────────────────────────────────────────

class EmailQuickStepsController(http.Controller):

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            items = request.env['lugal.email.quick.step'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_qs_dict(q) for q in items])
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['POST'])
    def qs_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            qs = request.env['lugal.email.quick.step'].sudo().create({
                'name':        name,
                'description': body.get('description', ''),
                'user_id':     uid,
                'sequence':    int(body.get('sequence', 10)),
                'icon':        body.get('icon', ''),
                'steps_json':  json.dumps(body.get('steps', [])),
            })
            request.env.cr.commit()
            return _json_ok(_qs_dict(qs), status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_get(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def qs_update(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'        in body: write_vals['name']        = body['name']
            if 'description' in body: write_vals['description'] = body['description']
            if 'sequence'    in body: write_vals['sequence']    = int(body['sequence'])
            if 'icon'        in body: write_vals['icon']        = body['icon']
            if 'steps'       in body: write_vals['steps_json']  = json.dumps(body['steps'])
            if write_vals:
                qs.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def qs_delete(self, qs_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            qs.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/apply_quick_step',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def apply_quick_step(self, message_id, **kwargs):
        """Apply a quick step to a message. Body: { "quick_step_id": 5 }"""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body    = json.loads(request.httprequest.data or '{}')
            qs_id   = body.get('quick_step_id')
            if not qs_id:
                return _json_err('quick_step_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            qs = request.env['lugal.email.quick.step'].sudo().browse(int(qs_id))
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Quick step not found', 404)
            qs.apply_to_message(msg)
            request.env.cr.commit()
            return _json_ok({'applied': True, 'message_id': message_id, 'quick_step_id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)
# TODO: remove - cherry-pick marker

end of file rules_controller.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __manifest__.py
__manifest__.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/__manifest__.py
# Component: Lugal Email — module manifest (lugal_email / __manifest__.py)
{
    'name': 'Lugal Email',
    'version': '1.1.3',
    'category': 'Communication',
    'summary': 'IMAP/SMTP email engine for the Lugal suite — accounts, inbox, send, notifications',
    'description': """
Lugal Email
===========
Full email management module for the Lugal suite.

Features
--------
- lugal.email.account  — IMAP/SMTP account configuration per user
- lugal.email.message  — Stored/cached email messages
- /api/lugal/email/*   — REST HTTP API (Bearer-JWT auth)
- /api/crm/email/*     — CRM-context wrappers (JSON-RPC)
- /api/crm/settings/email/* — Settings CRUD (JSON-RPC)
""",
    'depends': ['base', 'mail', 'lugal_auth'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# TODO: remove - cherry-pick marker

end of file __manifest__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __init__.py
__init__.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/__init__.py
from . import email_account
from . import email_message
from . import email_idle_watcher
from . import email_rule
from . import email_quick_step
# TODO: remove - cherry-pick marker

end of file __init__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __init__.py
__init__.py

# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/__init__.py
from . import email_controller
from . import crm_email_controller
from . import settings_email_controller
from . import rules_controller
# TODO: remove - cherry-pick marker

end of file __init__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

## Module: lugal_ws_migration

start of lugal_email_ws.py
lugal_email_ws.py

import logging
import time
from datetime import timedelta, timezone

from odoo import api, models

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _folder_role(folder):
    value = (folder or 'inbox').strip().lower()
    return value if value in {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'} else 'custom'


def _build_message_preview(record):
    """
    Build a complete inbox-ready message dict from an ORM record.

    This mirrors the shape of _message_to_dict() in email_controller so the FE
    can immediately prepend the new message to the inbox list without a
    follow-up /api/lugal/email/messages call.  Attachments are omitted from
    the preview (body_fetched=False for IMAP-synced headers-only messages) and
    can be fetched lazily via message_detail when the user opens the email.
    """
    try:
        atts = record.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', record.id),
        ])
        attachments = []
        inline_attachments = []
        cid_prefix = '__inline_cid__:'
        for a in atts:
            item = {
                'id':       a.id,
                'name':     a.name or 'attachment',
                'mimetype': a.mimetype or 'application/octet-stream',
                'size':     a.file_size or 0,
                'inline':   False,
            }
            desc = a.description or ''
            if desc.startswith(cid_prefix):
                cid_value = desc[len(cid_prefix):].strip()
                item['inline'] = True
                item['cid'] = f'cid:{cid_value}'
                item['content_id'] = cid_value
                inline_attachments.append(item)
            else:
                attachments.append(item)
    except Exception:
        attachments = []
        inline_attachments = []

    return {
        'id':             record.id,
        'account_id':     record.account_id.id,
        'folder':         record.folder,
        'folder_role':    _folder_role(record.folder),
        'subject':        record.subject or '(no subject)',
        'from_name':      record.from_name or '',
        'from_address':   record.from_address or '',
        'to_addresses':   record.to_addresses or '[]',
        'cc_addresses':   record.cc_addresses or '[]',
        'date':           _to_riyadh_iso(record.date),
        'received_at':    _to_riyadh_iso(record.create_date),
        'read_at':        _to_riyadh_iso(record.read_at) if record.read_at else None,
        'is_read':        record.is_read,
        'is_starred':     record.is_starred,
        'is_flagged':     record.is_flagged,
        'is_important':   record.is_important,
        'written_in_arabic': bool(getattr(record, 'written_in_arabic', False)),
        'is_draft':       record.is_draft,
        'smtp_delivered': record.smtp_delivered,
        'smtp_error':     record.smtp_error or None,
        'smtp_status':    record.smtp_status or 'pending',
        'version':        _to_riyadh_iso(record.write_date),
        'write_date':     _to_riyadh_iso(record.write_date),
        'body_fetched':   bool(getattr(record, 'body_fetched', False)),
        'attachments':    attachments,
        'inline_attachments': inline_attachments,
        'crm_links': {
            'customer': None,
            'ticket':   None,
        },
    }


def _notification_folder_domain():
    """Unread mail that should affect email badges/notifications.

    Includes inbox and custom rule folders such as INBOX.syed_naqvi and
    INBOX.syed_naqvi.Important.  Excludes outbound/system folders that should
    not increment the "new email" bell count.
    """
    return [
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
    ]


class LugalEmailMessageWs(models.Model):
    """
    Wire new inbox email arrivals to the Odoo bus so the FE WebSocket client
    receives a real-time push with the FULL message payload.

    The payload now includes a `message_data` key with the complete inbox-row
    dict so the FE can immediately prepend the new message to the inbox list
    without a follow-up /api/lugal/email/messages call.  This eliminates the
    race condition where the inbox API was called before the DB committed the
    new message, causing the FE to show stale (old) inbox data.
    """
    _inherit = 'lugal.email.message'

    def _lugal_send_new_email_notification(self):
        """Push realtime notification after the message reaches its final folder."""
        for record in self:
            try:
                record.invalidate_recordset()
            except Exception:
                pass
            record = record.sudo().exists()
            if not record or record.is_deleted or not record.active:
                continue

            if (
                not record.is_read
                and (record.folder or '') not in ('sent', 'drafts', 'trash', 'spam')
            ):
                uid = (
                    record.account_id.user_id.id
                    if record.account_id and record.account_id.user_id
                    else None
                )
                if uid:
                    try:
                        unread_count = self.sudo().search_count([
                            ('account_id', '=', record.account_id.id),
                            ('is_read',    '=', False),
                            ('is_deleted', '=', False),
                        ] + _notification_folder_domain())
                        # Full message dict so the FE can update the inbox list
                        # immediately without calling messages_list again.
                        message_data = _build_message_preview(record)
                        payload = {
                            'message_id':   record.id,
                            'account_id':   record.account_id.id,
                            'mailbox':      record.folder or 'inbox',
                            'folder':       record.folder or 'inbox',
                            'folder_role':  _folder_role(record.folder),
                            'subject':      record.subject or '(no subject)',
                            'from_name':    record.from_name or '',
                            'from_address': record.from_address or '',
                            'from':         record.from_address or '',
                            'received_at':  _to_riyadh_iso(record.date),
                            'unread_count': unread_count,
                            'uid':          uid,
                            'version':      _to_riyadh_iso(record.write_date),
                            # Full row — FE should prepend this to the correct
                            # mailbox/folder using message_data.folder.
                            'message_data': message_data,
                        }
                        _logger.info(
                            '[EmailWS] bus._sendone uid=%s channel=supply_user.%s '
                            'message_id=%s folder=%s at %.3f',
                            uid, uid, record.id, record.folder, time.time(),
                        )
                        self.env['bus.bus'].sudo()._sendone(
                            f'supply_user.{uid}',
                            'crm.email.message.new',
                            payload,
                        )
                    except Exception as exc:
                        _logger.debug(
                            'lugal_email_ws: bus notify error uid=%s: %s', uid, exc,
                        )
                    # Web Push — deliver even when browser tab is closed
                    try:
                        sender_label = record.from_name or record.from_address or 'New Email'
                        subject = record.subject or '(no subject)'
                        self.env['lugal.push.subscription'].sudo().send_push_to_user(
                            uid,
                            title=sender_label,
                            body=subject,
                            data={
                                'type':       'email',
                                'message_id': record.id,
                                'account_id': record.account_id.id,
                                'folder':     record.folder or 'inbox',
                                'url':        '/emails',
                            },
                        )
                    except Exception:
                        pass

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('lugal_email_defer_new_message_ws'):
            records._lugal_send_new_email_notification()
        return records
# TODO: remove - cherry-pick marker

end of file lugal_email_ws.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of lugal_ir_websocket.py
lugal_ir_websocket.py

import logging
import time

from odoo import api, models
from odoo.http import SessionExpiredException
from odoo.service import security
from odoo.addons.bus.websocket import wsrequest

_logger = logging.getLogger(__name__)


class LugalIrWebsocket(models.AbstractModel):
    """
    Extends Odoo's native ir.websocket to:
      1. Override _authenticate to gracefully handle stale WS sessions
         (session_token=None) so the subscribe frame is never silently dropped.
         A TypeError from check_session now raises SessionExpiredException
         (WS close code 4001) so the frontend refreshes the session and reconnects.
      2. Detect mid-connection uid changes (login/logout of different user on the
         same browser session) and force SessionExpiredException so the WS
         reconnects with fresh channel subscriptions for the new user.
      3. Automatically subscribe each authenticated user to their supply chat,
         per-user, per-session, and stories channels when the WebSocket opens.
    """
    _name = 'ir.websocket'
    _inherit = 'ir.websocket'

    @classmethod
    def _authenticate(cls):
        """
        Override Odoo's WebSocket authentication to handle three cases:

        Case 1 — Stale session (session_token=None):
          TypeError from check_session → log + raise SessionExpiredException (4001)
          → FE calls _ensureSession() and reconnects.

        Case 2 — UID changed mid-connection (e.g. different user logged in on
          the same browser session, or logout then login):
          The session store shows a different uid than when this WS connection
          first authenticated. Raise SessionExpiredException (4001) so the WS
          closes and the FE reconnects — the new connection's _build_bus_channel_list
          subscribes to the correct channels for the new user.

        Case 3 — Logout (uid becomes None on a previously authenticated connection):
          The WS was open for uid=X. The HTTP logout endpoint set session.uid=None.
          Raise SessionExpiredException (4001) so the WS closes cleanly.
          FE's _handleClose(4001) calls _ensureSession() → gets 401 (JWT revoked)
          → shows login screen.
        """
        # ws_obj persists for the lifetime of this WebSocket connection.
        # We attach _authenticated_uid to track the uid at first authentication.
        ws_obj = getattr(wsrequest, 'ws', None)

        current_uid = wsrequest.session.uid

        if current_uid is not None:
            session_valid = False
            try:
                session_valid = security.check_session(
                    wsrequest.session, wsrequest.env, wsrequest
                )
            except TypeError:
                _logger.info(
                    '[WS] Stale session (session_token=None) for uid=%s — forcing re-auth',
                    current_uid,
                )
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()

            if not session_valid:
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()

            # ── UID-change detection ───────────────────────────────────────
            # Store the uid on first successful authentication for this WS
            # connection.  If it changes on a later frame (e.g. different user
            # logged in using the same browser session cookie) we force close.
            if ws_obj is not None:
                initial_uid = getattr(ws_obj, '_authenticated_uid', None)
                if initial_uid is None:
                    # First successful auth — record it.
                    ws_obj._authenticated_uid = current_uid
                    _logger.info(
                        '[WS] Connection authenticated: uid=%s session=%s',
                        current_uid, wsrequest.session.sid[:8],
                    )
                elif initial_uid != current_uid:
                    # UID changed (different user re-used this session cookie).
                    # Close the stale connection so the new session opens a fresh
                    # WS with correct channel subscriptions.
                    _logger.info(
                        '[WS] UID changed %s → %s on session %s — forcing reconnect '
                        '(channels would be stale)',
                        initial_uid, current_uid, wsrequest.session.sid[:8],
                    )
                    raise SessionExpiredException()

        else:
            # uid is None — either anonymous connection or a logged-out session.
            if ws_obj is not None and getattr(ws_obj, '_authenticated_uid', None) is not None:
                # This connection WAS authenticated (uid was recorded).  Now the
                # session shows uid=None → the HTTP logout endpoint was called.
                # Force close so the FE can handle the logout state.
                _logger.info(
                    '[WS] Session logged out for uid=%s — closing WS (code 4001)',
                    ws_obj._authenticated_uid,
                )
                raise SessionExpiredException()

            # Genuinely anonymous or never-authenticated connection — allow as public.
            public_user = wsrequest.env.ref('base.public_user')
            wsrequest.update_env(user=public_user.id)

    def _build_bus_channel_list(self, channels):
        result = super()._build_bus_channel_list(channels)
        uid = self.env.uid

        # Only add custom channels for real authenticated users
        try:
            public_uid = self.env.ref('base.public_user').id
        except Exception:
            public_uid = None

        if not uid or uid == public_uid:
            return result

        # All active supply chat conversations this user participates in
        try:
            Conv = self.env['lugal.supply.conversation'].sudo()
            convs = Conv.search([
                ('is_archived', '=', False),
                ('participant_ids', 'in', [uid]),
            ])
            for conv in convs:
                result.append(f'supply_chat.{conv.id}')
        except Exception as exc:
            _logger.warning(
                '_build_bus_channel_list: failed to fetch conversations for uid=%s: %s',
                uid, exc
            )

        # Per-user private channel (email notifications, delivery receipts, etc.)
        result.append(f'supply_user.{uid}')

        # Per-session channel: used for session-specific signals (force_close,
        # reconnect_required) so only THIS browser's WS receives them and not
        # every tab that the same user has open.
        try:
            session_sid = wsrequest.session.sid
            result.append(f'supply_session.{session_sid}')
        except Exception:
            pass

        # Global stories broadcast channel
        result.append('supply_stories')

        _logger.debug(
            '[WS] Channel list built for uid=%s at %.3f (%d channels)',
            uid, time.time(), len(result),
        )
        return result
# TODO: remove - cherry-pick marker

end of file lugal_ir_websocket.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of lugal_ir_http.py
lugal_ir_http.py

import logging

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request, SessionExpiredException
from odoo.service import security
import werkzeug.exceptions

_logger = logging.getLogger(__name__)


class LugalIrHttp(models.AbstractModel):
    """
    Override ir.http._authenticate_explicit to handle stale WS session cookies
    that were created before the session_token fix in ws_session.py.

    The old WS session bridge set session.uid but forgot session.session_token,
    leaving it as None.  Odoo's check_session calls consteq(expected_str, None)
    which raises TypeError.  Without this patch, that TypeError bubbles up as
    AccessDenied → HTTP 403 for every HTTP-type route (notifications, ws/config,
    WebSocket) until the browser clears its cookies.

    With this patch we catch the TypeError and treat it like a failed session
    check: log out the stale session and continue — the JWT Bearer token in the
    Authorization header will still authenticate the request normally.
    """
    _name = 'ir.http'
    _inherit = 'ir.http'

    @classmethod
    def _authenticate_explicit(cls, auth):
        try:
            if request.session.uid is not None:
                session_valid = False
                try:
                    session_valid = security.check_session(
                        request.session, request.env, request
                    )
                except TypeError:
                    # session_token is None — stale session from old WS bridge.
                    # Treat as failed check: clear session and fall through to
                    # JWT Bearer auth below.
                    _logger.info(
                        'lugal_ws_migration: stale session (session_token=None) '
                        'for uid=%s — clearing and continuing',
                        request.session.uid,
                    )

                if not session_valid:
                    request.session.logout(keep_db=True)
                    request.env = api.Environment(
                        request.env.cr, None, request.session.context
                    )

            getattr(cls, f'_auth_method_{auth}')()

        except (AccessDenied, SessionExpiredException, werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info(
                'lugal_ws_migration: exception during authentication',
                exc_info=True,
            )
            raise AccessDenied()
# TODO: remove - cherry-pick marker

end of file lugal_ir_http.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of lugal_push_notification.py
lugal_push_notification.py

# -*- coding: utf-8 -*-
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LugalPushSubscription(models.Model):
    _name = 'lugal.push.subscription'
    _description = 'Browser Web Push Subscription'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        ondelete='cascade',
        index=True,
    )
    endpoint = fields.Char(required=True, index=True)
    auth_key = fields.Char(string='Auth Key')
    p256dh_key = fields.Char(string='P256DH Key')
    user_agent = fields.Char()
    active = fields.Boolean(default=True)
    created_at = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('endpoint_unique', 'unique(endpoint)', 'Push endpoint must be unique.'),
    ]

    @api.model
    def send_push_to_user(self, user_id, title, body, data=None):
        """Send a Web Push notification to every active browser subscription for a user.

        Called from bus event publishers (new chat message, new email, etc.) so that
        users with a closed/backgrounded browser tab still receive a system notification.
        """
        subscriptions = self.search([
            ('user_id', '=', user_id),
            ('active', '=', True),
        ])
        if not subscriptions:
            return
        for sub in subscriptions:
            try:
                sub._do_send(title, body, data or {})
            except Exception as exc:
                _logger.warning(
                    'Push send failed uid=%s endpoint=%s: %s',
                    user_id, (sub.endpoint or '')[:60], exc,
                )

    def _do_send(self, title, body, data):
        """Low-level: send a single push notification to this subscription."""
        self.ensure_one()
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            _logger.warning(
                'pywebpush is not installed — push notifications disabled. '
                'Install it with: pip install pywebpush'
            )
            return

        ICP = self.env['ir.config_parameter'].sudo()
        private_key = ICP.get_param('lugal.push.vapid.private_key', '').strip()
        vapid_email = ICP.get_param('lugal.push.vapid.email', 'admin@example.com').strip()

        if not private_key:
            _logger.warning(
                'VAPID private key not configured. '
                'Run the "Generate VAPID Keys" server action or set '
                'lugal.push.vapid.private_key in ir.config_parameter.'
            )
            return

        payload = json.dumps({
            'title': title,
            'body': body,
            'data': data,
        })

        subscription_info = {
            'endpoint': self.endpoint,
            'keys': {
                'auth': self.auth_key or '',
                'p256dh': self.p256dh_key or '',
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={'sub': f'mailto:{vapid_email}'},
                content_encoding='aes128gcm',
            )
        except WebPushException as exc:
            response = getattr(exc, 'response', None)
            status = response.status_code if response is not None else None
            if status in (404, 410):
                # The subscription is gone (browser cleared it) — deactivate
                self.sudo().write({'active': False})
                _logger.info(
                    'Push subscription expired (HTTP %s) for uid=%s — deactivated',
                    status, self.user_id.id,
                )
            else:
                raise
# TODO: remove - cherry-pick marker

end of file lugal_push_notification.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of ws_session.py
ws_session.py

import json
import logging

from odoo import http
from odoo.http import request, Response, root
from odoo.service.security import compute_session_token
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

# Keep the WebSocket session bridge valid across long inactive browser sessions.
# Product requirement: do not drop an inactive tab merely because the user works
# elsewhere; explicit logout/user switch still invalidates the session.
SESSION_TTL = 60 * 60 * 24 * 365


class WsSessionController(http.Controller):

    # ------------------------------------------------------------------
    # POST /api/crm/ws/session
    # Exchange a valid JWT Bearer token for a short-lived Odoo session_id.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/ws/session',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def get_ws_session(self, **kwargs):
        """
        Exchange a valid JWT Bearer token for an Odoo session_id cookie.

        The response includes Set-Cookie: session_id=... so the browser
        automatically stores it. The FE does NOT need to parse the JSON body
        and manually call document.cookie — just make the request and the
        browser handles the rest.

        The cookie is then forwarded by the Vite proxy when the FE opens
        the WebSocket: ws://<vite-host>/websocket → ws://192.168.116.204:8076

        Authorization: Bearer <jwt>    ← JWT read from header
        Body: {}                       ← body ignored
        """
        def _json(payload, status=200, extra_headers=None):
            headers = [('Content-Type', 'application/json')]
            if extra_headers:
                headers.extend(extra_headers)
            return Response(json.dumps(payload), status=status, headers=headers)

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        # Validate JWT — reads Authorization: Bearer <token> from header
        uid = ensure_jwt_user_id()
        if not uid:
            return _json({'success': False, 'error': 'Unauthorized'}, 401)

        try:
            session = request.session
            old_uid = session.uid  # capture before overwriting

            session.uid = uid
            session.db = request.db
            session.login = (
                request.env['res.users'].sudo().browse(uid).login
            )

            if old_uid and old_uid != uid:
                # Different user taking over this session — keep old token so
                # check_session() fails on the next WS dispatch and the stale
                # connection closes with code 4001.  See auth_controller.py's
                # _attach_ws_session for the full explanation.
                pass
            else:
                # Compute and store the session token so Odoo's check_session()
                # can verify it.  Without this, check_session calls
                # consteq(str, None) → TypeError → AccessDenied → 403 for every
                # HTTP-type route (notifications, ws/config, WebSocket).
                session.session_token = compute_session_token(session, request.env)

            # Force-save the session.  Odoo normally sets can_save=False when
            # the X-Odoo-Database header is present (stateless mode), which
            # prevents the Set-Cookie from being emitted in post_dispatch.
            # We need the cookie in the browser so the WS upgrade (which goes
            # through the Vite proxy) carries it automatically.
            session.can_save = True
            request.session.touch()
            root.session_store.save(session)

            # When a DIFFERENT user is taking over this session, push a bus signal
            # so any open WS connection for the old user can close immediately.
            # The _authenticate() override in lugal_ir_websocket.py will also detect
            # the uid change and raise SessionExpiredException (close 4001) on the
            # next WS frame, but the bus push provides an immediate fast-path close.
            if old_uid and old_uid != uid:
                try:
                    session_sid = session.sid
                    bus = request.env['bus.bus'].sudo()
                    bus._sendone(
                        f'supply_session.{session_sid}',
                        'session.reconnect_required',
                        {'reason': 'user_changed', 'old_uid': old_uid, 'new_uid': uid},
                    )
                    bus._sendone(
                        f'supply_user.{old_uid}',
                        'session.reconnect_required',
                        {'reason': 'user_changed', 'session_id': session_sid},
                    )
                    _logger.info(
                        'ws_session: pushed reconnect — session %s uid %s → %s',
                        session_sid[:8], old_uid, uid,
                    )
                except Exception as be:
                    _logger.debug('ws_session: bus signal failed: %s', be)

            # Build the Set-Cookie header manually so it works regardless of
            # which Odoo post_dispatch path is taken.
            # Use SameSite=Lax so the session cookie is sent when the browser
            # opens the WebSocket through the Vite proxy on the same origin.
            # Also set a Max-Age so the session persists across tabs/reopens.
            cookie_header = (
                f'session_id={session.sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL}'
            )

            return _json(
                {
                    'success': True,
                    'data': {
                        'session_id': session.sid,
                        'expires_in': SESSION_TTL,
                    },
                },
                extra_headers=[('Set-Cookie', cookie_header)],
            )
        except Exception as exc:
            _logger.exception('ws_session: session creation failed: %s', exc)
            return _json({'success': False, 'error': 'Session creation failed'}, 500)

    # ------------------------------------------------------------------
    # GET /api/crm/ws/config
    # Returns whether WebSocket mode is enabled for this user.
    # Controls the FE startup router (BusClient vs long-poll fallback).
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/ws/config',
        type='http',
        auth='none',
        methods=['GET', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def ws_config(self, **kwargs):
        """
        Returns the current WebSocket rollout flag.
        FE calls this once on startup to decide WS vs long-poll.
        Safe to call even without authentication — returns use_websocket: false
        on any auth failure so the FE always has a safe fallback.
        """
        def _json(payload):
            return Response(
                json.dumps(payload),
                headers=[('Content-Type', 'application/json')],
            )

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json({'use_websocket': False, 'fallback_on_error': True, 'ws_version': None})

            ICP = request.env['ir.config_parameter'].sudo()
            enabled = ICP.get_param('ws.rollout.enabled', 'False').lower() == 'true'

            # Return the required WS version so the FE can include it in the
            # connection URL: ws://.../websocket?version=<ws_version>
            # Odoo immediately closes connections whose version param doesn't
            # match _VERSION (close code 1000, reason "OUTDATED_VERSION").
            from odoo.addons.bus.websocket import WebsocketConnectionHandler
            ws_version = WebsocketConnectionHandler._VERSION

            # Build the WebSocket URL using X-Forwarded-Host (set by our proxy)
            # so the returned URL reflects the client-facing host:port (e.g.
            # 192.168.116.228:3003) rather than the internal Odoo address.
            # The proxy already routes /websocket → gevent worker.
            forwarded_host = request.httprequest.headers.get('X-Forwarded-Host', '')
            raw_host = forwarded_host or request.httprequest.host or ''
            scheme   = 'wss' if request.httprequest.is_secure else 'ws'
            ws_url   = f"{scheme}://{raw_host}/websocket?version={ws_version}"

            return _json({
                'use_websocket': enabled,
                'fallback_on_error': True,
                'ws_version': ws_version,
                'ws_url': ws_url,
            })
        except Exception as _exc:
            _logger.exception('ws_config error: %s', _exc)
            return _json({'use_websocket': False, 'fallback_on_error': True})
# TODO: remove - cherry-pick marker

end of file ws_session.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of push_controller.py
push_controller.py

# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, Response

from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class PushNotificationController(http.Controller):

    # ------------------------------------------------------------------
    # GET /api/crm/push/vapid-public-key
    # Returns the VAPID public key so the browser can subscribe.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/vapid-public-key',
        type='http',
        auth='none',
        methods=['GET', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def push_vapid_public_key(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        ICP = request.env['ir.config_parameter'].sudo()
        public_key = ICP.get_param('lugal.push.vapid.public_key', '').strip()

        return Response(
            json.dumps({'public_key': public_key}),
            headers=[
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ],
        )

    # ------------------------------------------------------------------
    # POST /api/crm/push/subscribe
    # Register or refresh a browser push subscription for the current user.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/subscribe',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def push_subscribe(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            endpoint = (kwargs.get('endpoint') or '').strip()
            auth_key = (kwargs.get('auth') or '').strip()
            p256dh_key = (kwargs.get('p256dh') or '').strip()
            user_agent = (kwargs.get('user_agent') or '').strip()[:200]

            if not endpoint:
                return {'success': False, 'error': 'endpoint is required'}

            Sub = request.env['lugal.push.subscription'].sudo()
            existing = Sub.search([('endpoint', '=', endpoint)], limit=1)
            if existing:
                existing.write({
                    'user_id': uid,
                    'auth_key': auth_key,
                    'p256dh_key': p256dh_key,
                    'user_agent': user_agent,
                    'active': True,
                })
            else:
                Sub.create({
                    'user_id': uid,
                    'endpoint': endpoint,
                    'auth_key': auth_key,
                    'p256dh_key': p256dh_key,
                    'user_agent': user_agent,
                })
            return {'success': True, 'data': {'subscribed': True}}
        except Exception as exc:
            _logger.exception('push_subscribe failed')
            return {'success': False, 'error': str(exc)}

    # ------------------------------------------------------------------
    # POST /api/crm/push/unsubscribe
    # Deactivate a push subscription (e.g. user revokes permission).
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/unsubscribe',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def push_unsubscribe(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            endpoint = (kwargs.get('endpoint') or '').strip()
            if not endpoint:
                return {'success': False, 'error': 'endpoint is required'}

            Sub = request.env['lugal.push.subscription'].sudo()
            sub = Sub.search([('endpoint', '=', endpoint), ('user_id', '=', uid)], limit=1)
            if sub:
                sub.write({'active': False})
            return {'success': True, 'data': {'unsubscribed': True}}
        except Exception as exc:
            _logger.exception('push_unsubscribe failed')
            return {'success': False, 'error': str(exc)}
# TODO: remove - cherry-pick marker

end of file push_controller.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __manifest__.py
__manifest__.py

{
    'name': 'Lugal WS Migration',
    'version': '1.0.2',
    'summary': 'WebSocket migration layer — sandbox/migration branch only',
    'description': """
        Provides:
          - Session bridge: POST /api/crm/ws/session (JWT → Odoo session)
          - Feature flag:   GET  /api/crm/ws/config
          - _build_bus_channel_list() override for supply chat/stories/email channels
          - Phase 4: lugal.email.message create hook → crm.email.message.new bus event

        NEVER install on lugal_local. Sandbox (lugal_ws_sandbox) only.
        Completely inert unless installed — does not affect dev or production.
    """,
    'depends': ['bus', 'lugal_crm', 'lugal_auth'],
    'data': [
        'security/ir.model.access.csv',
        'data/ws_config.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
# TODO: remove - cherry-pick marker

end of file __manifest__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __init__.py
__init__.py

from . import lugal_ir_websocket
from . import lugal_email_ws
from . import lugal_ir_http
from . import lugal_push_notification
# TODO: remove - cherry-pick marker

end of file __init__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

start of __init__.py
__init__.py

from . import ws_session
from . import push_controller
# TODO: remove - cherry-pick marker

end of file __init__.py
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------


---

## Issue History & Full Debug Context: `is_read` / `read_at` / `recipient_read_at`

---

### 1. The Problem — What Was Observed

These three fields on `lugal.email.message` were behaving incorrectly:

| Field | Expected Behavior | What Was Happening |
|---|---|---|
| `is_read` | `false` until the **recipient** opens the email | Was being set to `true` immediately when the message was created (for sent mail) or when IMAP sync detected `\Seen` flag |
| `read_at` | `null` until the **recipient** explicitly opens the message | Was being stamped to the IMAP message date (delivery time) or to the sync timestamp — identical to `received_at` |
| `recipient_read_at` | Set only when an **MDN (read receipt)** is received from the recipient | Mostly unused / not connected to the main `is_read` flow |

**Key symptom reported by user:** In the sent folder, `read_at == received_at` and `is_read == true` even when the recipient had never opened the mail. The sender opening their own sent folder was the trigger.

---

### 2. Root Cause Analysis

There were **multiple overlapping bugs** creating this behavior. In order of discovery:

#### Bug A — IMAP sync stamping `read_at` with delivery date

**Location:** `email_account.py` → `_upsert_inbox_message()`

The original code contained:
```python
# WRONG: sets read_at to the IMAP message date
if is_read:
    vals['read_at'] = dt   # dt = parsed Date: header (delivery time)
```

This meant: any message that arrived at the IMAP server already with `\Seen` flag got `read_at = delivery_timestamp`, making it look "read" at the moment it was received.

**Fix:** Remove this line entirely. `read_at` must only be set when the user explicitly opens the mail inside the Lugal app.

---

#### Bug B — Model `create()` auto-stamping `read_at` during IMAP sync

**Location:** `email_message.py` → `create()`

The model's `create()` had auto-stamp logic:
```python
if vals.get('is_read') and not vals.get('read_at'):
    vals['read_at'] = now
```

This ran even during IMAP sync, so the moment `_upsert_inbox_message` created a row with `is_read=True` (from `\Seen` flag), `create()` would add `read_at=now`.

**Fix:** Added `lugal_imap_sync=True` context flag. All calls from `_upsert_inbox_message` use `Message.sudo().with_context(lugal_imap_sync=True)`. The `create()` and `write()` overrides skip auto-stamping when this context is set.

---

#### Bug C — Sent messages created with `is_read=True` by the send endpoints

**Location:** `email_controller.py` → `compose_send()`, `reply_email()`, `forward_email()`, `draft_to_sent()`

When the user sent an email, the controller created the local "sent copy" with `is_read=True`:
```python
# WRONG
{'folder': 'sent', 'is_read': True, ...}
```

This immediately made the sent message appear as "read" from the sender's perspective, even though no recipient had read it yet.

**Fix:** Removed `'is_read': True` from all sent-message creation calls. Sent messages start with `is_read=False`.

---

#### Bug D — Model-level: no guard preventing `is_read`/`read_at` from being overwritten on sent rows

**Location:** `email_message.py`

Even after fixing the controller, any `write({'is_read': True})` on a sent message (e.g. when the sender clicked "Mark as Read" in their sent folder) would update `is_read`/`read_at` — reflecting the sender's action, not the recipient's.

**Fix:** Added `_is_sent_folder_value()` helper and model-level guards in `create()` and `write()`:
```python
def _is_sent_folder_value(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent', 'sent items', 'sent messages',
    }

def write(self, vals):
    allow_recipient_read = bool(self.env.context.get('lugal_recipient_read'))
    read_fields = {'is_read', 'read_at'} & set(vals)
    if read_fields and not allow_recipient_read:
        sent_records = self.filtered(lambda rec: _is_sent_folder_value(rec.folder))
        if sent_records:
            # Strip is_read/read_at from the write for sent records
            sent_vals = {k: v for k, v in vals.items() if k not in read_fields}
            other_records = self - sent_records
            if other_records:
                super().write(vals)   # normal records get full update
            if sent_vals:
                super().write(sent_vals)   # sent records get update MINUS is_read/read_at
            return True
    return super().write(vals)
```

The **only** way to update `is_read`/`read_at` on a sent message is to pass `context={'lugal_recipient_read': True}`.

---

#### Bug E — Controller toggle_read / PATCH updating sender's view for sent messages

**Location:** `email_controller.py` → `toggle_read()`, `update_message()`

When the user marked their own sent message as read (via the toggle or PATCH), the code was directly setting `is_read=True` and `read_at=now` on the DB row.

**Fix:** Added `_is_sent_folder()` helper to both controllers. For sent messages:
- Push `\Seen` flag to IMAP (cosmetic — keeps the webmail in sync)
- **Do NOT** modify DB `is_read` or `read_at`
- Return the current DB state unchanged

```python
def _is_sent_folder(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent', 'sent items', 'sent messages',
    }

# In toggle_read:
if _is_sent_folder(msg.folder):
    # Push IMAP \Seen for cosmetic purposes ONLY
    # DO NOT update DB is_read / read_at
    return {'is_read': msg.is_read, 'read_at': _to_riyadh_iso(msg.read_at)}
```

---

#### Bug F — No propagation from inbox-read to sender's sent copy

**Problem:** When the recipient marked their inbox copy as read, the sender's sent copy was never updated.

**Fix:** Added `_propagate_read_to_sent_copies()` helper in both `email_controller.py` and `crm_email_controller.py`:

```python
def _propagate_read_to_sent_copies(env, message_id, read_at):
    """When an inbox message is marked read, find and update the matching sent copy."""
    if not message_id:
        return
    try:
        sent_copies = env['lugal.email.message'].sudo().search([
            ('message_id', '=', message_id),
            ('folder', '=', 'sent'),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        sent_copies = sent_copies.filtered(lambda m: _is_sent_folder(m.folder))
        if sent_copies:
            sent_copies.with_context(lugal_recipient_read=True).write({
                'is_read': True,
                'read_at': read_at,
            })
    except Exception as exc:
        _logger.warning('_propagate_read_to_sent_copies failed: %s', exc)
```

This is called after **every successful inbox read** (in `toggle_read`, PATCH endpoint, `message_detail`, `bulk_read`).

---

#### Bug G — MDN handler not updating `is_read`/`read_at`

**Location:** `email_account.py` → `_upsert_inbox_message()` MDN section

The original MDN handler was setting `recipient_read_at` but NOT updating `is_read` or `read_at` on the sent message:
```python
# OLD (incomplete)
_sent.write({'recipient_read_at': _read_ts})
```

**Fix:** Now uses `lugal_recipient_read=True` context and updates all three fields:
```python
_sent.with_context(lugal_recipient_read=True).write({
    'recipient_read_at': _read_ts,
    'is_read':           True,
    'read_at':           _read_ts,
})
```

---

#### Bug H — IMAP `\Seen` flag being interpreted for sent folder during sync

**Location:** `email_account.py` → `_upsert_inbox_message()`

When syncing the sent folder via IMAP, a message with `\Seen` would have `is_read=True` from `_parse_flags_from_fetch_response()`. This overwrote the correct DB state.

**Fix:** Added explicit reset after flag parsing:
```python
is_read = self._parse_flags_from_fetch_response(flags_meta)
# For sent folder: \Seen means the SENDER viewed their own copy.
# It has nothing to do with whether the RECIPIENT read it.
# is_read/read_at on sent messages are ONLY updated by:
#   1. _propagate_read_to_sent_copies (internal recipient read)
#   2. MDN receipt (external confirmation)
if folder_key == 'sent':
    is_read = False
```

---

#### Bug I — `_sync_sent_folder` creating sent rows with `is_read=True`

**Location:** `email_account.py` → `_sync_sent_folder()`

When importing sent messages from IMAP Sent folder, rows were created with `is_read=True`:
```python
# Note: this is STILL in the code at line ~1659
Msg.create({
    ...
    'is_read': True,   # ← This bypasses the model guard because it's in Sent folder
    ...
})
```

**IMPORTANT NOTE for the fixing agent:** The `_sync_sent_folder()` method at line ~1648–1663 still creates rows with `is_read=True`. The model guard in `create()` will catch this and strip it (since `lugal_recipient_read` is not in context), so it should be safe. But it's worth verifying — the model's `create()` guard should normalize `is_read=False` for sent rows.

---

### 3. The Full Data Flow (Correct Architecture)

```
OUTBOUND (Sender's perspective):
─────────────────────────────────
1. Sender composes + sends email
   → DB sent row created: is_read=False, read_at=NULL
   → IMAP APPEND to Sent folder (with \Seen to prevent "new email" badge in webmail)

2. Recipient opens email in their inbox
   → Their inbox copy: is_read=True, read_at=NOW
   → _propagate_read_to_sent_copies() called:
       → Finds sender's sent row by message_id
       → Writes is_read=True, read_at=NOW with lugal_recipient_read=True context
   → If sender requested read receipt: MDN sent to sender

3. MDN arrives at sender's IMAP inbox
   → _upsert_inbox_message() detects multipart/report + disposition-notification
   → Finds sent row by Original-Message-ID
   → Writes recipient_read_at, is_read=True, read_at with lugal_recipient_read=True
   → MDN is discarded (not stored as regular inbox message)

INBOUND (Recipient's perspective):
───────────────────────────────────
1. Email arrives on IMAP server
   → _upsert_inbox_message() imports it with is_read=False, read_at=NULL
   → IMAP \Seen flag is parsed but only applied to inbox (never to sent folder)
   → lugal_imap_sync=True prevents auto-stamping

2. Recipient opens email
   → message_detail or toggle_read sets is_read=True, read_at=NOW
   → _propagate_read_to_sent_copies() updates sender's sent copy
   → IMAP \Seen flag pushed async
   → If request_read_receipt=True: MDN sent to sender

SENT FOLDER GUARD (model level):
──────────────────────────────────
   Any write of {is_read, read_at} on a sent-folder row is STRIPPED
   unless context['lugal_recipient_read'] = True.
   This is the hard invariant: sent folder read state = recipient read state.
```

---

### 4. Files Modified and What Was Changed

| File | Change |
|---|---|
| `email_message.py` | Added `_is_sent_folder_value()` helper; model-level guard in `create()` and `write()` to block `is_read`/`read_at` updates on sent rows without `lugal_recipient_read` context; added `lugal_imap_sync` context check to prevent auto-stamping during IMAP sync |
| `email_account.py` | Removed `vals['read_at'] = dt` from `_upsert_inbox_message()`; all `Message` env calls use `with_context(lugal_imap_sync=True)`; added `if folder_key == 'sent': is_read = False` to ignore IMAP `\Seen` flag for sent folder; MDN handler updated to also write `is_read=True` + `read_at` with `lugal_recipient_read=True` |
| `email_controller.py` | Removed `'is_read': True` from all sent-message creation calls; added `_is_sent_folder()` helper; refactored `toggle_read` and PATCH to block DB updates for sent folder; added `_propagate_read_to_sent_copies()` helper; all inbox read actions call propagation |
| `crm_email_controller.py` | Added `_is_sent_folder()` helper; `message_detail` now skips read-stamping for sent folder; `bulk_read` filters out sent messages; all inbox reads call `_propagate_read_to_sent_copies()` |

---

### 5. Context Flags Reference

| Context Key | Set By | Effect |
|---|---|---|
| `lugal_imap_sync=True` | `_upsert_inbox_message()` | Disables auto-stamping of `read_at` in `create()` and `write()` during IMAP import |
| `lugal_recipient_read=True` | `_propagate_read_to_sent_copies()`, MDN handler | Allows `is_read`/`read_at` to be written on sent-folder rows |
| `lugal_email_defer_new_message_ws=True` | `_upsert_inbox_message()` create path | Defers WebSocket notification until after inbox rules run (prevents premature push before folder is assigned) |

---

### 6. Known Remaining Issues / What to Verify

1. **`_sync_sent_folder()` still passes `is_read=True`** (line ~1659 in `email_account.py`). The model guard should strip it, but verify the model `create()` guard is active before the `_sync_sent_folder()` code path. If the sent folder is being synced with `lugal_imap_sync=True` context AND `_is_sent_folder_value` catches it, the `is_read=False` should win. Trace: `_sync_sent_folder` → `Msg.create({..., 'is_read': True})` — `Msg` here is `self.env['lugal.email.message'].sudo()` without `lugal_imap_sync`. So the model's `create()` guard (`allow_recipient_read = False`, `_is_sent_folder_value('sent') = True`) should strip `is_read`. Should be safe but confirm.

2. **Internal-only propagation** — `_propagate_read_to_sent_copies()` only works when both sender and recipient use the **same Lugal system** (same `message_id` in DB). For external recipients (Gmail, Outlook users), MDN is the only mechanism. MDN requires the sender to have set `request_read_receipt=True`.

3. **`recipient_read_at` vs `read_at`** — These two fields now serve distinct roles:
   - `read_at` = canonical "was this message read by the intended audience?" — updated by both internal propagation AND MDN
   - `recipient_read_at` = specifically "timestamp from an MDN receipt" — only updated by MDN handler
   - The frontend should use `read_at` as the primary signal and `recipient_read_at` as MDN provenance.

4. **Historical data** — After the fixes were deployed, a cleanup script was run:
   - 42 incorrectly-read sent rows were reset to `is_read=False, read_at=NULL`
   - 412 sent rows were updated to reflect actual recipient read state (where the recipient's inbox copy had `is_read=True`)
   This cleanup ran once. Any rows created before the fix that were not in those 42/412 may still have stale data.

5. **WebSocket delivery** — The `_lugal_send_new_email_notification()` in `lugal_email_ws.py` pushes to `supply_user.{uid}` channel with event type `crm.email.message.new`. The `is_read` and `read_at` fields in the WebSocket payload reflect the DB state at push time. Since sent messages now start with `is_read=False`, this payload should now be correct.

---

### 7. What to Test

**Test Case 1 — Sender sends to internal recipient:**
1. Sender (user A) composes and sends to recipient (user B) — both on same system
2. **Assert sent message state:** `is_read=false`, `read_at=null`
3. Recipient (user B) opens the email
4. **Assert sent message state:** `is_read=true`, `read_at=<time B opened it>`

**Test Case 2 — Sender sends with read receipt to external recipient:**
1. Sender (user A) composes with `request_read_receipt=true`, sends to external Gmail
2. **Assert sent message:** `is_read=false`, `read_at=null`, `request_read_receipt=true`
3. Recipient opens email in Gmail, Gmail sends MDN back
4. MDN arrives in sender's IMAP inbox
5. **Assert sent message:** `is_read=true`, `read_at=<MDN timestamp>`, `recipient_read_at=<MDN timestamp>`
6. **Assert MDN is NOT in inbox** (should be silently discarded)

**Test Case 3 — Sender views own sent folder:**
1. Sender opens their sent folder, clicks a sent message
2. **Assert:** `is_read` and `read_at` do NOT change in DB (sender viewing own copy must not trigger read)
3. `\Seen` flag may be pushed to IMAP (cosmetic) but DB state unchanged

**Test Case 4 — Bulk mark as read:**
1. User marks multiple inbox messages as read via `/api/crm/email/bulk/read`
2. **Assert:** All inbox messages → `is_read=true`, `read_at=now`
3. **Assert:** For each inbox message, the corresponding sender's sent copy → `is_read=true`
4. **Assert:** Any sent-folder message IDs in the request are returned in `skipped_sent_ids`

