# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmCallScript(models.Model):
    """Script / FAQ for agents — guided workflow, objection handling."""
    _name = 'lugal.crm.call.script'
    _description = 'CRM Call Script'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, category asc, id asc'
    _rec_name = 'title'

    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    category = fields.Selection([
        ('faq', 'FAQ / الأسئلة الشائعة'),
        ('guided_workflow', 'Guided Workflow / سير العمل'),
        ('objection_handling', 'Objection Handling / التعامل مع الاعتراضات'),
    ], string='Category / التصنيف', default='faq', index=True, tracking=True)
    question = fields.Char(string='Question / السؤال', index=True, tracking=True)
    answer = fields.Text(string='Answer / الإجابة', tracking=True)
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        help='Leave empty for company-wide script.',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    is_active = fields.Boolean(string='Is Active / نشط', default=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
