# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmOmnichannelMessage(models.Model):
    """Omnichannel message — inbox entry from WhatsApp, Instagram, etc."""
    _name = 'lugal.crm.omnichannel.message'
    _description = 'CRM Omnichannel Message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sent_at desc, id desc'
    _rec_name = 'content'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    channel = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('tiktok', 'TikTok'),
        ('x', 'X'),
        ('snapchat', 'Snapchat'),
        ('email', 'Email'),
        ('website', 'Website'),
    ], string='Channel / القناة', required=True, index=True, tracking=True)
    direction = fields.Selection([
        ('inbound', 'Inbound / وارد'),
        ('outbound', 'Outbound / صادر'),
    ], string='Direction / الاتجاه', required=True, index=True, tracking=True)
    channel_identity_id = fields.Many2one(
        'lugal.crm.channel.identity',
        string='Channel Identity / هوية القناة',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    content = fields.Text(string='Content / المحتوى', tracking=True)
    media_url = fields.Char(string='Media URL', tracking=True)
    sent_at = fields.Datetime(string='Sent At / وقت الإرسال', required=True, index=True, tracking=True)
    read_at = fields.Datetime(string='Read At / وقت القراءة', tracking=True)
    assigned_to_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    conversation_id = fields.Char(string='Conversation ID / معرف المحادثة', index=True, tracking=True)
    status = fields.Selection([
        ('pending', 'Pending / قيد الانتظار'),
        ('assigned', 'Assigned / مُعيَّن'),
        ('resolved', 'Resolved / محلول'),
    ], string='Status / الحالة', default='pending', index=True, tracking=True)

    # Agent reply tracking — "opened" only counts when agent actually replies
    replied_by_agent_at = fields.Datetime(
        string='First Reply At / وقت أول رد من الموظف',
        tracking=True,
        help='Timestamp of the first outbound reply by the agent. Used to compute FRT.',
    )

    # Conversation ownership — auto-assigned when agent first replies
    owner_id = fields.Many2one(
        'res.users',
        string='Owner / المالك',
        ondelete='set null',
        index=True,
        tracking=True,
        help='Agent who owns this conversation (auto-set on first reply).',
    )

    # SLA breach flag — set by a scheduler or on write if threshold exceeded
    sla_breached = fields.Boolean(
        string='SLA Breached / تجاوز SLA',
        default=False,
        index=True,
        tracking=True,
    )

    # Waiting for customer response after agent reply
    waiting_customer_response = fields.Boolean(
        string='Waiting Customer Response / ننتظر رد العميل',
        default=False,
        index=True,
        tracking=True,
    )

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.model
    def _cron_flag_sla_breaches(self):
        """
        Every 5 min: flag inbound messages that have not been replied to
        within the SLA threshold defined in the channel config.
        """
        Config = self.env['lugal.crm.channel.config']
        now = datetime.now()

        # Group pending messages by channel+branch and check their SLA
        pending = self.search([
            ('direction', '=', 'inbound'),
            ('status', '=', 'pending'),
            ('sla_breached', '=', False),
            ('is_deleted', '=', False),
        ])
        for msg in pending:
            try:
                # Lookup channel config for this channel+branch
                config = Config.search([
                    ('channel', '=', msg.channel),
                    ('branch_id', '=', msg.branch_id.id if msg.branch_id else False),
                ], limit=1)
                threshold = config.sla_threshold_seconds if config else 300
                if msg.sent_at:
                    elapsed = (now - msg.sent_at).total_seconds()
                    if elapsed > threshold:
                        msg.write({'sla_breached': True})
            except Exception:
                _logger.exception('SLA cron error for message %s', msg.id)
