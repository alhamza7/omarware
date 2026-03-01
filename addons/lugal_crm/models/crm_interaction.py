# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmInteraction(models.Model):
    """Activity timeline entry — call, message, email, visit, note."""
    _name = 'lugal.crm.interaction'
    _description = 'CRM Interaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'interaction_date desc, id desc'
    _rec_name = 'subject'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User / المستخدم',
        default=lambda self: self.env.user,
        ondelete='set null',
        index=True,
        tracking=True,
    )
    interaction_type = fields.Selection([
        ('call', 'Call / مكالمة'),
        ('message', 'Message / رسالة'),
        ('email', 'Email'),
        ('visit', 'Visit / زيارة'),
        ('note', 'Note / ملاحظة'),
    ], string='Type / النوع', required=True, index=True, tracking=True)
    channel = fields.Char(string='Channel / القناة', tracking=True)
    subject = fields.Char(string='Subject / الموضوع', index=True, tracking=True)
    body = fields.Text(string='Body / المحتوى', tracking=True)
    outcome = fields.Char(string='Outcome / النتيجة', tracking=True)
    duration_seconds = fields.Integer(string='Duration (sec) / المدة (ثانية)', tracking=True)
    interaction_date = fields.Datetime(
        string='Date / التاريخ',
        default=fields.Datetime.now,
        required=True,
        index=True,
        tracking=True,
    )
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
