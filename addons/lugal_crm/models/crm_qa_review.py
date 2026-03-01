# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CrmQaReview(models.Model):
    """QA Review — QA auditors score calls and/or messages for quality assurance."""
    _name = 'lugal.crm.qa.review'
    _description = 'CRM QA Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reviewed_at desc, id desc'
    _rec_name = 'review_number'

    review_number = fields.Char(
        string='Review # / رقم المراجعة',
        readonly=True,
        copy=False,
        index=True,
        default='New',
        tracking=True,
    )

    review_type = fields.Selection([
        ('call', 'Call Recording / تسجيل مكالمة'),
        ('message', 'Message Thread / محادثة رسائل'),
    ], string='Review Type / نوع المراجعة', required=True, index=True, tracking=True)

    # --- Subject being reviewed ---
    call_id = fields.Many2one(
        'lugal.crm.call',
        string='Call / المكالمة',
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    conversation_id = fields.Char(
        string='Conversation ID / معرف المحادثة',
        index=True,
        tracking=True,
        help='Omnichannel conversation_id from lugal.crm.omnichannel.message',
    )
    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.users',
        string='Agent Reviewed / الموظف المُقيَّم',
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

    # --- Review metadata ---
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer (QA) / المدقق',
        default=lambda self: self.env.uid,
        ondelete='restrict',
        required=True,
        index=True,
        tracking=True,
    )
    reviewed_at = fields.Datetime(
        string='Reviewed At / وقت المراجعة',
        default=fields.Datetime.now,
        required=True,
        index=True,
        tracking=True,
    )
    listen_duration_seconds = fields.Integer(
        string='Listen Duration (sec) / مدة الاستماع',
        default=0,
        tracking=True,
        help='How many seconds the QA reviewer actually listened to the recording.',
    )

    # --- Scoring ---
    score = fields.Float(
        string='Score (0–100) / التقييم',
        digits=(5, 2),
        default=0.0,
        tracking=True,
    )
    greeting_score = fields.Float(string='Greeting / التحية', digits=(5, 2), default=0.0, tracking=True)
    product_knowledge_score = fields.Float(string='Product Knowledge / معرفة المنتج', digits=(5, 2), default=0.0, tracking=True)
    problem_solving_score = fields.Float(string='Problem Solving / حل المشكلات', digits=(5, 2), default=0.0, tracking=True)
    professionalism_score = fields.Float(string='Professionalism / الاحترافية', digits=(5, 2), default=0.0, tracking=True)
    compliance_score = fields.Float(string='Compliance / الامتثال', digits=(5, 2), default=0.0, tracking=True)

    # --- Feedback ---
    issues_found = fields.Text(string='Issues Found / المشكلات المُكتشفة', tracking=True)
    qa_notes = fields.Text(string='QA Notes / ملاحظات المدقق', tracking=True)
    feedback_to_agent = fields.Text(string='Feedback to Agent / ملاحظات للموظف', tracking=True)

    status = fields.Selection([
        ('draft', 'Draft / مسودة'),
        ('submitted', 'Submitted / مُرسَل'),
        ('acknowledged', 'Acknowledged / تم الاطلاع'),
    ], string='Status / الحالة', default='draft', index=True, tracking=True)

    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-assign review number from ir.sequence on creation."""
        for vals in vals_list:
            if vals.get('review_number', 'New') == 'New':
                vals['review_number'] = self.env['ir.sequence'].next_by_code('lugal.crm.qa.review') or 'New'
        return super().create(vals_list)

    @api.constrains('score')
    def _check_score_range(self):
        """Ensure score is between 0 and 100."""
        for rec in self:
            if not (0.0 <= rec.score <= 100.0):
                raise ValidationError('Score must be between 0 and 100.')

    @api.onchange('greeting_score', 'product_knowledge_score', 'problem_solving_score',
                  'professionalism_score', 'compliance_score')
    def _onchange_compute_score(self):
        """Auto-compute average score from sub-scores when any sub-score changes."""
        for rec in self:
            sub_scores = [
                rec.greeting_score,
                rec.product_knowledge_score,
                rec.problem_solving_score,
                rec.professionalism_score,
                rec.compliance_score,
            ]
            non_zero = [s for s in sub_scores if s > 0]
            rec.score = sum(non_zero) / len(non_zero) if non_zero else 0.0
