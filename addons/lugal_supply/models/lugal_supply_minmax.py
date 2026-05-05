# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LugalSupplyMinmax(models.Model):
    """Min/max inventory rule per product and branch."""
    _name = 'lugal.supply.minmax'
    _description = 'Lugal Supply Min/Max Rule'
    _order = 'product_id asc, branch_id asc'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product',
        string='Product / المنتج',
        required=True,
        ondelete='cascade',
        index=True,
    )
    branch_id = fields.Integer(string='Branch ID / معرّف الفرع', default=0, index=True)
    min_qty = fields.Float(string='Min Qty / الحد الأدنى', digits=(16, 4), default=0.0)
    max_qty = fields.Float(string='Max Qty / الحد الأقصى', digits=(16, 4), default=0.0)

    _sql_constraints = [
        (
            'product_branch_unique',
            'UNIQUE(product_id, branch_id)',
            'A min/max rule already exists for this product and branch.',
        )
    ]

    @api.constrains('min_qty', 'max_qty')
    def _check_qty(self):
        for rec in self:
            if rec.max_qty > 0 and rec.min_qty > rec.max_qty:
                raise ValidationError('Min qty cannot exceed max qty.')
