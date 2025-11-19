# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PerfumeBrand(models.Model):
    _name = 'perfume.brand'
    _description = 'Perfume Brand'
    _order = 'name'

    # NOTE: translate=False to avoid JSONB translation features that require
    # PostgreSQL jsonpath functions in some environments.
    name = fields.Char(string='Brand Name', required=True, translate=False)
    code = fields.Char(string='Brand Code', required=True, help='Unique identifier for API (e.g., louis-vuitton)')
    country = fields.Char(string='Country', required=True, translate=False)
    active = fields.Boolean(string='Active', default=True)
    perfumes = fields.One2many('perfume.perfume', 'brand_id', string='Perfumes')
    perfume_count = fields.Integer(string='Perfume Count', compute='_compute_perfume_count', store=False)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Brand code must be unique!'),
    ]

    @api.depends('perfumes')
    def _compute_perfume_count(self):
        for brand in self:
            brand.perfume_count = len(brand.perfumes)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.country})"
            result.append((record.id, name))
        return result

