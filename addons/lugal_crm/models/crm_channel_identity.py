# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmChannelIdentity(models.Model):
    """Customer identity per channel — WhatsApp, Instagram, etc. Enables omnichannel resolution."""
    _name = 'lugal.crm.channel.identity'
    _description = 'CRM Channel Identity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'channel asc, id asc'
    _rec_name = 'handle'

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
        ('tiktok', 'TikTok'),
        ('telegram', 'Telegram'),
        ('x', 'X (Twitter)'),
        ('snapchat', 'Snapchat'),
        ('email', 'Email'),
        ('store', 'Store / فرع'),
        ('website', 'Website'),
    ], string='Channel / القناة', required=True, index=True, tracking=True)
    handle = fields.Char(string='Handle / المعرف', required=True, index=True, tracking=True)
    is_verified = fields.Boolean(string='Verified / موثق', default=False, tracking=True)
    is_primary = fields.Boolean(string='Primary / أساسي', default=False, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
