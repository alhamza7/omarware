# -*- coding: utf-8 -*-
##############################################################################
#
#    Custom Pricelist Packaging
#    Copyright (C) 2024
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
##############################################################################

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    """Extend pricelist item to support packaging-based pricing"""
    _inherit = 'product.pricelist.item'

    # Available packaging units for current product/template (computed for reliable domain)
    available_packaging_uom_ids = fields.Many2many(
        comodel_name='uom.uom',
        compute='_compute_available_packaging_uom_ids',
        string='Available Packaging UoMs',
        store=False,
        help='Computed list of packaging UoMs allowed for this rule based on the selected product/template.'
    )

    product_packaging_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Packaging',
        domain="[('id', 'in', available_packaging_uom_ids)]",
        help="Select a specific product packaging (UoM). "
             "If set, the fixed price will apply when this packaging is used in sales orders.",
        ondelete='set null',
    )

    @api.depends('product_id', 'product_tmpl_id')
    def _compute_available_packaging_uom_ids(self):
        """Populate available packaging UoMs from the product template's uom_ids."""
        for item in self:
            uoms = self.env['uom.uom']
            if item.product_id:
                uoms = item.product_id.product_tmpl_id.uom_ids
            elif item.product_tmpl_id:
                uoms = item.product_tmpl_id.uom_ids
            item.available_packaging_uom_ids = uoms

    @api.onchange('product_id', 'product_tmpl_id')
    def _onchange_product_packaging_domain(self):
        """Clear packaging when the product or template changes; domain uses computed field."""
        if self.product_packaging_id:
            self.product_packaging_id = False
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update domain and clear packaging when product changes"""
        # Call parent's onchange first
        result = super()._onchange_product_id()
        
        # Update packaging domain
        packaging_result = self._onchange_product_packaging_domain()
        
        # Merge results
        if result:
            result.setdefault('domain', {}).update(packaging_result.get('domain', {}))
            result.setdefault('value', {}).update(packaging_result.get('value', {}))
        else:
            result = packaging_result
        
        return result
    
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Update domain and clear packaging when product template changes"""
        # Call parent's onchange first
        result = super()._onchange_product_tmpl_id()
        
        # Update packaging domain
        packaging_result = self._onchange_product_packaging_domain()
        
        # Merge results
        if result:
            result.setdefault('domain', {}).update(packaging_result.get('domain', {}))
            result.setdefault('value', {}).update(packaging_result.get('value', {}))
        else:
            result = packaging_result
        
        return result

    @api.model
    def _get_packaging_domain(self, product_id=None, product_tmpl_id=None):
        """Get domain for packaging field based on product or template"""
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.exists():
                product_tmpl = product.product_tmpl_id
                packaging_ids = product_tmpl.uom_ids.ids if product_tmpl.uom_ids else []
                return [('id', 'in', packaging_ids)] if packaging_ids else [('id', '=', False)]
        elif product_tmpl_id:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            if product_tmpl.exists():
                packaging_ids = product_tmpl.uom_ids.ids if product_tmpl.uom_ids else []
                return [('id', 'in', packaging_ids)] if packaging_ids else [('id', '=', False)]
        return [('id', '=', False)]
    
    @api.onchange('product_packaging_id')
    def _onchange_product_packaging_id(self):
        """Set compute_price to fixed when packaging is selected"""
        if self.product_packaging_id and not self.compute_price:
            self.compute_price = 'fixed'
            # Optionally set fixed_price based on packaging if a price exists
            # This can be customized based on business requirements
    

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Override to check packaging applicability"""
        res = super()._is_applicable_for(product, qty_in_product_uom)
        
        # If this rule has packaging_id set, it should NOT match
        # unless we're specifically looking for packaging rules
        # (packaging rules are handled separately in sale_order_line)
        if res and self.product_packaging_id:
            # Return False to prevent packaging rules from matching in standard flow
            return False
        
        return res

