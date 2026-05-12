# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_message.py
# Component: Lugal Email — lugal.email.message model (email_message.py)

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


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
        now = fields.Datetime.now()
        for vals in vals_list:
            # Auto-stamp read_at when a new message is created already marked as
            # read (e.g. outgoing sent/reply messages composed by the user).
            if vals.get('is_read') and not vals.get('read_at'):
                vals['read_at'] = now
        return super().create(vals_list)

    def write(self, vals):
        # Auto-stamp read_at the first time is_read transitions to True.
        if (
            vals.get('is_read')
            and not vals.get('read_at')
            and any(not rec.is_read and not rec.read_at for rec in self)
        ):
            vals = dict(vals, read_at=fields.Datetime.now())
        return super().write(vals)
# TODO: remove - cherry-pick marker
