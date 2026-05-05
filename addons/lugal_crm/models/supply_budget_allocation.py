# -*- coding: utf-8 -*-
"""Budget envelope for supply POs — structure only; enforcement gated by config."""

from odoo import fields, models


class LugalSupplyBudgetAllocation(models.Model):
    _name = 'lugal.supply.budget.allocation'
    _description = 'Supply Budget Allocation (structure)'
    _order = 'company_id, name'

    name = fields.Char(string='Label', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount_limit = fields.Monetary(
        string='Amount limit',
        currency_field='currency_id',
        help='When budget control is enabled in settings, PO total must not exceed this.',
    )
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notes')
