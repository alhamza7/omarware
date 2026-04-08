# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmTask(models.Model):
    """Task / follow-up / reminder — assignable by supervisors to agents."""
    _name = 'lugal.crm.task'
    _description = 'CRM Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc, priority desc, id asc'
    _rec_name = 'title'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        ondelete='cascade',
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
    created_by_id = fields.Many2one(
        'res.users',
        string='Created By / أنشأه',
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
    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    description = fields.Text(string='Description / الوصف', tracking=True)
    due_date = fields.Datetime(string='Due Date / تاريخ الاستحقاق', index=True, tracking=True)
    reminder_date = fields.Datetime(string='Reminder / تذكير', tracking=True)
    priority = fields.Selection([
        ('low', 'Low / منخفض'),
        ('medium', 'Medium / متوسط'),
        ('high', 'High / عالي'),
        ('urgent', 'Urgent / عاجل'),
    ], string='Priority / الأولوية', default='medium', index=True, tracking=True)
    status = fields.Selection([
        ('open', 'Open / مفتوح'),
        ('in_progress', 'In Progress / قيد التنفيذ'),
        ('done', 'Done / منجز'),
        ('overdue', 'Overdue / متأخر'),
    ], string='Status / الحالة', default='open', required=True, index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
