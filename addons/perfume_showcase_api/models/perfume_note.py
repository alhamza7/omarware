# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PerfumeNote(models.Model):
    _name = 'perfume.note'
    _description = 'Perfume Note'
    _order = 'name'

    name = fields.Char(string='Note Name', required=True, translate=False)
    category = fields.Selection([
        ('top', 'Top Notes'),
        ('middle', 'Middle Notes'),
        ('base', 'Base Notes'),
    ], string='Category', required=True)
    active = fields.Boolean(string='Active', default=True)
    perfumes = fields.Many2many(
        'perfume.perfume',
        'perfume_perfume_note_rel',
        'note_id',
        'perfume_id',
        string='Perfumes',
        readonly=True
    )

