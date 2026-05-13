# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LugalSupplyInventoryMinmax(models.Model):
    """Min/max stock level configuration per product (and optionally branch)."""
    _name = 'lugal.supply.inventory.minmax'
    _description = 'Supply Inventory Min/Max'
    _order = 'product_id asc, id asc'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch',
        ondelete='set null',
        index=True,
    )
    min_qty = fields.Float(string='Minimum Qty', default=0.0, digits=(16, 4), required=True)
    max_qty = fields.Float(string='Maximum Qty', default=0.0, digits=(16, 4), required=True)

    current_stock = fields.Float(
        string='Current Stock',
        compute='_compute_current_stock',
        digits=(16, 4),
    )

    needs_reorder = fields.Boolean(
        string='Needs Reorder',
        compute='_compute_needs_reorder',
    )

    @api.depends('product_id')
    def _compute_current_stock(self):
        for rec in self:
            if not rec.product_id:
                rec.current_stock = 0.0
                continue
            quants = self.env['stock.quant'].sudo().search(
                [('product_id', '=', rec.product_id.id), ('location_id.usage', '=', 'internal')]
            )
            rec.current_stock = sum(quants.mapped('quantity'))

    @api.depends('current_stock', 'min_qty')
    def _compute_needs_reorder(self):
        for rec in self:
            rec.needs_reorder = rec.current_stock < rec.min_qty

    _sql_constraints = [
        (
            'unique_product_branch',
            'UNIQUE(product_id, branch_id)',
            'A min/max rule already exists for this product and branch combination.',
        ),
    ]
