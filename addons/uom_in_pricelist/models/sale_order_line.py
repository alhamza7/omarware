# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Enhanced for Odoo 19 - Complete UoM Pricing Support
#
#############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """Override Sale Order Line to properly handle UoM-specific pricing"""
    _inherit = 'sale.order.line'

    def _get_display_price(self):
        """
        Override to handle UoM-specific pricing from pricelist items
        This is the REAL method that Odoo calls to get prices!
        """
        _logger.info("🚀 Custom _get_display_price called!")
        
        if not self.product_id or not self.order_id.pricelist_id:
            return super()._get_display_price()
        
        # Get pricelist and UoM
        pricelist = self.order_id.pricelist_id
        uom = self.product_uom_id or self.product_id.uom_id
        
        _logger.info(f"🔍 Getting price for {self.product_id.display_name} with UoM {uom.name} (ID: {uom.id})")
        
        # Search for exact UoM match in pricelist items
        pricelist_items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', uom.id),
            ('compute_price', '=', 'fixed'),
        ], limit=1, order='id DESC')
        
        if pricelist_items:
            # Found exact UoM match - use it!
            price = pricelist_items[0].fixed_price
            _logger.info(f"✅ Found exact UoM match! Price: ${price}")
            return price
        
        # No exact match - try base price (without packaging)
        _logger.info(f"⚠️ No exact UoM match, looking for base price")
        base_items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', False),
            ('compute_price', '=', 'fixed'),
        ], limit=1, order='id DESC')
        
        if base_items:
            price = base_items[0].fixed_price
            _logger.info(f"✅ Found base price: ${price}")
            
            # Convert price to selected UoM
            if uom != self.product_id.uom_id:
                factor = uom.factor_inv / self.product_id.uom_id.factor_inv
                price = price * factor
                _logger.info(f"🔄 Converted price by factor {factor}: ${price}")
            
            return price
        
        # No match at all - use standard Odoo logic
        _logger.info(f"⚠️ No price found, using standard pricing")
        return super()._get_display_price()


