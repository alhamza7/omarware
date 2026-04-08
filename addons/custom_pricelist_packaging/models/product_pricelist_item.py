# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    """Extend pricelist item to support UoM-based pricing"""
    _inherit = 'product.pricelist.item'

    # Available UoMs for current product/template
    available_uom_ids = fields.Many2many(
        comodel_name='uom.uom',
        compute='_compute_available_uom_ids',
        string='Available UoMs',
        store=False,
        help='Computed list of UoMs allowed for this rule based on the selected product/template.'
    )

    product_packaging_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product UoM',
        domain="[('id', 'in', available_uom_ids)]",
        help="Select a specific UoM. "
             "If set, the fixed price will apply when this UoM is used in sales orders.",
        ondelete='set null',
    )

    @api.depends('product_id', 'product_tmpl_id')
    def _compute_available_uom_ids(self):
        """Populate available UoMs from the product's UoM category."""
        for item in self:
            uoms = self.env['uom.uom']
            if item.product_id and item.product_id.uom_id:
                # Get all UoMs
                uoms = self.env['uom.uom'].search([])
            elif item.product_tmpl_id and item.product_tmpl_id.uom_id:
                uoms = self.env['uom.uom'].search([])
            item.available_uom_ids = uoms

    @api.onchange('product_id', 'product_tmpl_id')
    def _onchange_product_packaging_domain(self):
        """Clear packaging when the product or template changes."""
        if self.product_packaging_id:
            self.product_packaging_id = False
