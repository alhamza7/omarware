# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmCall(models.Model):
    """Call record — full dialog window spec: outcome, notes, financial snapshot, POS order link."""
    _name = 'lugal.crm.call'
    _description = 'CRM Call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'started_at desc, id desc'
    _rec_name = 'caller_number'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.users',
        string='Agent / الموظف',
        default=lambda self: self.env.user,
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
    call_type = fields.Selection([
        ('inbound', 'Inbound / وارد'),
        ('outbound', 'Outbound / صادر'),
    ], string='Call Type / نوع المكالمة', required=True, index=True, tracking=True)
    channel = fields.Char(string='Channel / القناة', tracking=True)
    caller_number = fields.Char(string='Caller Number / رقم المتصل', index=True, tracking=True)
    duration_seconds = fields.Integer(string='Duration (sec) / المدة (ثانية)', tracking=True)
    started_at = fields.Datetime(string='Started At / بدء', required=True, index=True, tracking=True)
    ended_at = fields.Datetime(string='Ended At / انتهاء', tracking=True)
    outcome = fields.Selection([
        ('resolved', 'Resolved / محلول'),
        ('callback', 'Callback / معاودة'),
        ('escalated', 'Escalated / تصعيد'),
        ('no_answer', 'No Answer / لا رد'),
    ], string='Outcome / النتيجة', index=True, tracking=True)
    notes = fields.Text(string='Notes / ملاحظات', tracking=True)
    ai_summary = fields.Text(string='AI Summary / ملخص الذكاء الاصطناعي', tracking=True)
    qa_score = fields.Float(string='QA Score / تقييم الجودة', digits=(5, 2), tracking=True)
    issues_found = fields.Text(string='Issues Found / ملاحظات الجودة', tracking=True)

    # Financial snapshot at call time
    balance_at_call = fields.Float(string='Balance at Call / الرصيد وقت المكالمة', digits=(16, 2), tracking=True)
    outstanding_at_call = fields.Float(string='Outstanding at Call / المستحق وقت المكالمة', digits=(16, 2), tracking=True)
    credit_limit_at_call = fields.Float(string='Credit Limit at Call / حد الائتمان وقت المكالمة', digits=(16, 2), tracking=True)

    # Actions taken during call
    invoice_created_id = fields.Integer(string='Invoice Created ID (POS)', readonly=True, tracking=True)
    ticket_created_id = fields.Many2one(
        'lugal.crm.ticket',
        string='Ticket Created / التذكرة المنشأة',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    catalogue_sent = fields.Boolean(string='Catalogue Sent / تم إرسال الكتالوج', default=False, tracking=True)
    catalogue_sent_via = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('telegram', 'Telegram'),
    ], string='Catalogue Sent Via / طريقة الإرسال', tracking=True)

    # Call recording — URL/path for audio file stored externally
    recording_url = fields.Char(
        string='Recording URL / رابط التسجيل',
        tracking=True,
        help='External URL or file path for the call recording. Restricted to authorized users.',
    )

    # POS order link (from pos.perfume.order)
    pos_order_id = fields.Integer(string='POS Order ID', readonly=True, index=True, tracking=True)
    pos_order_name = fields.Char(string='POS Order Name', readonly=True, tracking=True)
    pos_order_total = fields.Float(string='POS Order Total (USD)', digits=(16, 2), readonly=True, tracking=True)
    pos_order_total_iqd = fields.Float(string='POS Order Total (IQD)', digits=(16, 2), readonly=True, tracking=True)
    pos_order_state = fields.Char(string='POS Order State', readonly=True, tracking=True)
    pos_sale_order_name = fields.Char(string='POS Sale Order Name', readonly=True, tracking=True)
    pos_sap_synced = fields.Boolean(string='POS SAP Synced', readonly=True, tracking=True)

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
