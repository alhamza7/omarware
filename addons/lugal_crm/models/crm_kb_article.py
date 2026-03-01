# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmKbArticle(models.Model):
    """Knowledge base article — policies, journals, events, FAQ, ideas, circulars, training."""
    _name = 'lugal.crm.kb.article'
    _description = 'CRM Knowledge Base Article'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'title'

    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    title_ar = fields.Char(string='العنوان بالعربي', tracking=True)
    category = fields.Selection([
        ('policy', 'Policy / سياسة'),
        ('journal', 'Journal / مجلة'),
        ('event', 'Event / حدث'),
        ('faq', 'FAQ / الأسئلة الشائعة'),
        ('idea', 'Idea / فكرة'),
        ('circular', 'Circular / منشور'),
        ('training', 'Training / تدريب'),
        ('document', 'Document / مستند'),
    ], string='Category / التصنيف', default='document', index=True, tracking=True)
    content = fields.Html(string='Content / المحتوى', tracking=True)
    content_ar = fields.Html(string='المحتوى بالعربي', tracking=True)
    author_id = fields.Many2one(
        'res.users',
        string='Author / الكاتب',
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
        help='Leave empty for company-wide article.',
    )
    is_published = fields.Boolean(string='Published / منشور', default=False, tracking=True)
    published_at = fields.Datetime(string='Published At / تاريخ النشر', readonly=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
