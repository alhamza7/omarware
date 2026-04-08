# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmChannelConfig(models.Model):
    """Channel configuration per branch — display name, color, assigned users, free-for-all."""
    _name = 'lugal.crm.channel.config'
    _description = 'CRM Channel Config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'channel asc, branch_id asc, id asc'
    _rec_name = 'display_name'

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
    display_name = fields.Char(string='Display Name / الاسم المعروض', tracking=True)
    color_hex = fields.Char(string='Color (hex) / اللون', tracking=True)
    icon = fields.Char(string='Icon / الأيقونة', tracking=True)
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    assigned_user_ids = fields.Many2many(
        'res.users',
        'lugal_crm_channel_config_user_rel',
        'config_id', 'user_id',
        string='Assigned Users / المستخدمون المعينون',
        help='Users who can handle this channel. Empty = all (when is_free_for_all).',
    )
    is_free_for_all = fields.Boolean(
        string='Free for All / متاح للجميع',
        default=False,
        help='If set, any user can take chats; otherwise only assigned_user_ids.',
        tracking=True,
    )

    # SLA settings — threshold in seconds before a chat is flagged as breached
    sla_threshold_seconds = fields.Integer(
        string='SLA Threshold (sec) / مدة SLA بالثواني',
        default=300,
        tracking=True,
        help='Seconds before an unanswered message is flagged as SLA breached. Default 5 min.',
    )

    # Work hours — used for AI bot takeover outside these hours
    work_hours_start = fields.Float(
        string='Work Hours Start / بداية الدوام',
        default=8.0,
        tracking=True,
        help='Hour of day (24h, decimal). E.g. 8.5 = 08:30.',
    )
    work_hours_end = fields.Float(
        string='Work Hours End / نهاية الدوام',
        default=18.0,
        tracking=True,
        help='Hour of day (24h, decimal). E.g. 17.0 = 17:00.',
    )

    is_active = fields.Boolean(string='Is Active / نشط', default=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
