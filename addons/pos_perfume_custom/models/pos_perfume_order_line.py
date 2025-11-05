# -*- coding: utf-8 -*-
from odoo import models, api, fields

class PosPerfumeOrderLineTemp(models.TransientModel):
    """
    POS Perfume Order Line TEMP - Works exactly like sale.order.line
    Uses Odoo's onchange mechanism for price calculation
    This is a temporary model used ONLY for onchange calculations
    """
    _name = 'pos.perfume.order.line.temp'
    _description = 'POS Perfume Order Line Temporary (for onchange)'
    
    # Basic fields
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    
    # Quantities and prices
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    discount = fields.Float(string='Discount %')
    
    # Computed
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_amount')
    available_qty = fields.Float(string='Available', compute='_compute_available_qty')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """When product changes - set default UoM and get price"""
        if not self.product_id:
            self.product_uom_id = False
            self.price_unit = 0.0
            return
        
        # Set default UoM
        self.product_uom_id = self.product_id.uom_id
        
        # Get price from pricelist
        self._get_pricelist_price()
    
    @api.onchange('product_uom_id')
    def _onchange_product_uom(self):
        """When UoM changes - recalculate price"""
        if self.product_id and self.product_uom_id:
            self._get_pricelist_price()
    
    @api.onchange('pricelist_id')
    def _onchange_pricelist(self):
        """When pricelist changes - recalculate price"""
        if self.product_id:
            self._get_pricelist_price()
    
    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        """When warehouse changes - update available qty"""
        self._compute_available_qty()
    
    def _get_pricelist_price(self):
        """Get price from pricelist - same logic as sale.order.line"""
        if not self.product_id:
            self.price_unit = 0.0
            return
        
        product = self.product_id
        pricelist = self.pricelist_id
        uom = self.product_uom_id or product.uom_id
        
        if pricelist:
            # Get price from pricelist (exactly like sale.order.line)
            price = pricelist._get_product_price(
                product=product,
                quantity=self.product_uom_qty or 1.0,
                uom=uom,
            )
        else:
            # No pricelist - use list price
            price = product.list_price
            # Convert to target UoM if needed
            if uom and uom != product.uom_id:
                price = product.uom_id._compute_price(price, uom)
        
        self.price_unit = price
    
    @api.depends('product_id', 'warehouse_id')
    def _compute_available_qty(self):
        """Compute available quantity in selected warehouse"""
        for line in self:
            if not line.product_id:
                line.available_qty = 0.0
                continue
            
            if not line.warehouse_id:
                # Get total available
                line.available_qty = line.product_id.qty_available
            else:
                # Get available in specific warehouse
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id.warehouse_id', '=', line.warehouse_id.id),
                    ('location_id.usage', '=', 'internal'),
                ])
                line.available_qty = sum(quants.mapped(lambda q: q.quantity - q.reserved_quantity))
    
    @api.depends('product_uom_qty', 'price_unit', 'discount')
    def _compute_amount(self):
        """Compute line amounts"""
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = price * line.product_uom_qty

