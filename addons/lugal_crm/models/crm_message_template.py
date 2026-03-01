# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmMessageTemplate(models.Model):
    """
    Reusable message templates for WhatsApp, Telegram, Email.
    Agents select templates to reply quickly. Supports variable placeholders: {customer_name}, {agent_name}, etc.
    """
    _name = 'lugal.crm.message.template'
    _description = 'CRM Message Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'channel asc, name asc, id asc'
    _rec_name = 'name'

    name = fields.Char(string='Template Name / اسم القالب', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='اسم القالب بالعربي', tracking=True)

    channel = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('any', 'Any / أي قناة'),
    ], string='Channel / القناة', default='any', required=True, index=True, tracking=True)

    category = fields.Selection([
        ('greeting', 'Greeting / ترحيب'),
        ('followup', 'Follow-up / متابعة'),
        ('catalogue', 'Catalogue / كتالوج'),
        ('pricing', 'Pricing / أسعار'),
        ('support', 'Support / دعم'),
        ('closing', 'Closing / إغلاق'),
        ('other', 'Other / أخرى'),
    ], string='Category / التصنيف', default='other', index=True, tracking=True)

    body = fields.Text(
        string='Template Body / نص القالب',
        required=True,
        tracking=True,
        help='Use {customer_name}, {agent_name}, {branch_name} as placeholders.',
    )
    body_ar = fields.Text(
        string='النص بالعربي',
        tracking=True,
        help='Arabic version of the template body.',
    )

    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        help='Leave empty for all branches.',
        tracking=True,
    )

    # For WhatsApp — template may require pre-approval by channel
    requires_approval = fields.Boolean(
        string='Requires Channel Approval / يتطلب موافقة القناة',
        default=False,
        tracking=True,
    )
    approval_status = fields.Selection([
        ('draft', 'Draft / مسودة'),
        ('pending', 'Pending Approval / بانتظار الموافقة'),
        ('approved', 'Approved / موافق عليه'),
        ('rejected', 'Rejected / مرفوض'),
    ], string='Approval Status / حالة الموافقة', default='draft', index=True, tracking=True)

    is_active = fields.Boolean(string='Active / نشط', default=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
