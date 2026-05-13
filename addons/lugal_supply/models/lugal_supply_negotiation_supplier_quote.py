# -*- coding: utf-8 -*-
"""Additional supplier price points for the same item request negotiation (comparison)."""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LugalSupplyNegotiationSupplierQuote(models.Model):
    _name = 'lugal.supply.negotiation.supplier.quote'
    _description = 'Negotiation Supplier Comparison Quote'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    negotiation_id = fields.Many2one(
        'lugal.supply.negotiation',
        string='Negotiation',
        required=True,
        ondelete='cascade',
        index=True,
    )
    vendor_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Supplier',
        required=True,
        ondelete='restrict',
        index=True,
    )
    offered_price = fields.Float(string='Quoted price', digits=(16, 4), default=0.0)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        ondelete='set null',
    )
    lead_time_days = fields.Integer(
        string='Lead time (days)',
        help='Supplier-indicative production or shipping lead time.',
    )
    notes = fields.Text(string='Notes')
    is_recommended = fields.Boolean(
        string='Recommended',
        help='Mark preferred quote among alternatives (informational).',
    )

    @api.constrains('negotiation_id', 'vendor_id')
    def _check_unique_vendor_per_negotiation(self):
        for rec in self:
            dup = self.search([
                ('negotiation_id', '=', rec.negotiation_id.id),
                ('vendor_id', '=', rec.vendor_id.id),
                ('id', '!=', rec.id),
            ], limit=1)
            if dup:
                raise ValidationError(
                    _('Each supplier can only appear once in the comparison list for a negotiation.')
                )


class LugalSupplyNegotiationComparison(models.Model):
    _inherit = 'lugal.supply.negotiation'

    supplier_quote_ids = fields.One2many(
        'lugal.supply.negotiation.supplier.quote',
        'negotiation_id',
        string='Supplier comparison',
        help='Optional additional supplier quotes; primary supplier remains on the main Supplier field.',
    )
