# -*- coding: utf-8 -*-
from odoo import models, fields


class PerfumeTag(models.Model):
    _name = 'perfume.tag'
    _description = 'Perfume Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=False)
    code = fields.Char(
        string='Tag Code',
        required=True,
        help='Unique identifier for URLs and API (e.g., woody, fresh).',
    )
    active = fields.Boolean(string='Active', default=True)

    perfume_ids = fields.Many2many(
        'perfume.perfume',
        'perfume_perfume_tag_rel',
        'tag_id',
        'perfume_id',
        string='Perfumes',
        readonly=True,
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Tag code must be unique!'),
    ]


