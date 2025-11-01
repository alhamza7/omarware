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


class SaleOrderLine(models.Model):
    """Extend sale order line to support packaging-based pricing"""
    _inherit = 'sale.order.line'

    product_packaging_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Packaging',
        help="Select a specific product packaging (UoM). If a pricelist item exists "
             "for this packaging, its price will be applied automatically.",
        ondelete='set null',
    )

    @api.onchange('product_id')
    def _onchange_product_id_packaging(self):
        """Update domain and clear packaging when product changes"""
        if self.product_id:
            product_tmpl = self.product_id.product_tmpl_id
            packaging_ids = product_tmpl.uom_ids.ids if product_tmpl.uom_ids else []
            domain = [('id', 'in', packaging_ids)] if packaging_ids else [('id', '=', False)]
            return {
                'domain': {'product_packaging_id': domain},
                'value': {'product_packaging_id': False}
            }
        else:
            self.product_packaging_id = False
            return {'domain': {'product_packaging_id': [('id', '=', False)]}}

    @api.onchange('product_packaging_id')
    def _onchange_product_packaging_id(self):
        """Update quantity and price when packaging changes"""
        if self.product_packaging_id and self.product_id:
            packaging_uom = self.product_packaging_id
            product_uom = self.product_id.uom_id

            self.product_uom_id = packaging_uom

            if packaging_uom and product_uom:
                qty_in_product_uom = packaging_uom._compute_quantity(1.0, product_uom)
                if qty_in_product_uom and qty_in_product_uom > 0:
                    if not self.product_uom_qty or self.product_uom_qty == 1.0:
                        self.product_uom_qty = qty_in_product_uom
        
        # Don't call _reset_price_unit() here, let the depends trigger it
        # when product_uom_id changes

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_pricelist_item_id(self):
        """Override to ensure packaging rules are excluded from standard matching"""
        for line in self:
            if not line.product_id or line.display_type or not line.order_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                # Get product base UoM
                product_uom = line.product_id.uom_id
                current_uom = line.product_uom_id
                
                # Always search using product base UoM to avoid matching packaging rules
                line.pricelist_item_id = line.order_id.pricelist_id._get_product_rule(
                    product=line.product_id,
                    quantity=1.0,  # Use 1 for unit price
                    uom=product_uom,  # Always use product base UoM
                    date=line._get_order_date(),
                    currency=line.currency_id,
                )

    def _get_pricelist_price(self):
        """Override to check for packaging-specific pricing"""
        self.ensure_one()
        if not self.product_id:
            return 0.0

        # Check if current UoM is a packaging (different from product's base UoM)
        # We use product_uom_id since product_packaging_id might not be set in onchange context
        product_uom = self.product_id.uom_id
        current_uom = self.product_uom_id
        
        # Determine if we're using packaging based on UoM
        is_packaging = current_uom and product_uom and current_uom.id != product_uom.id
        
        if is_packaging and self.order_id and self.order_id.pricelist_id:
            PricelistItem = self.env['product.pricelist.item']
            pricelist_id = self.order_id.pricelist_id.id
            packaging_uom_id = current_uom.id
            
            # Search for packaging-specific rule
            packaging_rule = PricelistItem.search([
                ('pricelist_id', '=', pricelist_id),
                ('product_packaging_id', '=', packaging_uom_id),
                '|', ('product_id', '=', self.product_id.id),
                '|', ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                '&', ('product_id', '=', False), ('product_tmpl_id', '=', False),
            ], limit=1, order='applied_on DESC, min_quantity DESC, id DESC')

            # If packaging rule found, use it directly (NO multiplication)
            if packaging_rule:
                if packaging_rule.compute_price == 'fixed':
                    return packaging_rule.fixed_price
                
                price = packaging_rule._compute_price(
                    self.product_id,
                    quantity=1.0,
                    uom=current_uom,
                    date=self.order_id.date_order or fields.Datetime.now(),
                    currency=self.order_id.currency_id
                )
                return price
            
            # No packaging rule - get product base price and multiply by packaging factor
            packaging_uom = current_uom
            
            # Search for product rule (WITHOUT packaging)
            product_rule = PricelistItem.search([
                ('pricelist_id', '=', pricelist_id),
                ('product_packaging_id', '=', False),
                '|', ('product_id', '=', self.product_id.id),
                '|', ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                     ('categ_id', 'parent_of', self.product_id.categ_id.id),
            ], limit=1, order='applied_on DESC, min_quantity DESC, id DESC')
            
            if product_rule and product_rule._is_applicable_for(self.product_id, 1.0):
                base_price = product_rule._compute_price(
                    self.product_id,
                    quantity=1.0,
                    uom=product_uom,
                    date=self.order_id.date_order or fields.Datetime.now(),
                    currency=self.order_id.currency_id
                )
            else:
                # Use product list price as fallback
                base_price = self.product_id.lst_price
            
            # Multiply by packaging factor
            qty_in_product_uom = packaging_uom._compute_quantity(1.0, product_uom)
            return base_price * qty_in_product_uom
        
        # No packaging specified - use standard Odoo logic
        return super()._get_pricelist_price()
