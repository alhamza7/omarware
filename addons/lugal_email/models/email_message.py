# -*- coding: utf-8 -*-

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
    folder = fields.Selection([
        ('inbox',   'Inbox'),
        ('sent',    'Sent'),
        ('drafts',  'Drafts'),
        ('trash',   'Trash'),
        ('archive', 'Archive'),
        ('spam',    'Spam'),
    ], string='Folder', default='inbox', index=True)

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
    date           = fields.Datetime(string='Date', index=True)

    # ── Body ──────────────────────────────────────────────────────────────────
    body_html = fields.Html(string='Body HTML', sanitize=False)
    body_text = fields.Text(string='Body Text')

    # ── Status ────────────────────────────────────────────────────────────────
    is_read    = fields.Boolean(string='Read',    default=False, index=True)
    is_starred = fields.Boolean(string='Starred', default=False)
    is_draft   = fields.Boolean(string='Draft',   default=False)

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

    # True for messages we created locally (sent/reply/forward) or once the full
    # IMAP body has been downloaded on-demand. False for inbox rows that were
    # imported with headers only (body_html/body_text may be blank).
    body_fetched = fields.Boolean(
        string='Full Body Fetched', default=False,
        help='False = only headers synced; body fetched on first open.',
    )

    # ── Soft delete ───────────────────────────────────────────────────────────
    active     = fields.Boolean(default=True)
    is_deleted = fields.Boolean(default=False, index=True)
