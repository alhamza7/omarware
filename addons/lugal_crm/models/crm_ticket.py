# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmTicket(models.Model):
    """Complaint / ticket — auto-numbered, SLA, first response, resolution for KPIs."""
    _name = 'lugal.crm.ticket'
    _description = 'CRM Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    ticket_number = fields.Char(
        string='Ticket # / رقم التذكرة',
        readonly=True,
        copy=False,
        index=True,
        default='New',
        tracking=True,
    )

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        required=True,
        ondelete='cascade',
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
    assigned_to_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    escalated_to_id = fields.Many2one(
        'res.users',
        string='Escalated To / تصعيد لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    description = fields.Text(string='Description / الوصف', tracking=True)
    ticket_type = fields.Char(string='Type / النوع', tracking=True)
    channel = fields.Char(string='Channel / القناة', tracking=True)
    status = fields.Selection([
        ('open', 'Open / مفتوح'),
        ('in_progress', 'In Progress / قيد التنفيذ'),
        ('resolved', 'Resolved / محلول'),
        ('closed', 'Closed / مغلق'),
        ('stale', 'Stale / متأخر'),
    ], string='Status / الحالة', default='open', required=True, index=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority / الأولوية', default='medium', index=True, tracking=True)
    sla_deadline = fields.Datetime(string='SLA Deadline / موعد SLA', tracking=True)
    first_response_at = fields.Datetime(string='First Response At / أول رد', readonly=True, tracking=True)
    resolved_at = fields.Datetime(string='Resolved At / تم الحل في', readonly=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-assign ticket number from ir.sequence on creation."""
        for vals in vals_list:
            if vals.get('ticket_number', 'New') == 'New':
                vals['ticket_number'] = self.env['ir.sequence'].next_by_code('lugal.crm.ticket') or 'New'
        return super().create(vals_list)
