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

    def _compute_price_unit(self):
        """
        Enhanced price computation to handle UoM-specific pricelist items
        This is the KEY to making UoM pricing work without touching Core!
        """
        _logger.info("🚀 Custom _compute_price_unit called!")
        
        for line in self:
            if not line.product_id or not line.order_id.pricelist_id:
                super(SaleOrderLine, line)._compute_price_unit()
                continue
            
            # Get pricelist and UoM
            pricelist = line.order_id.pricelist_id
            uom = line.product_uom_id or line.product_id.uom_id
            
            _logger.info(f"🔍 Computing price for {line.product_id.display_name} with UoM {uom.name} (ID: {uom.id})")
            
            # Search for exact UoM match in pricelist items
            # استخدام product_tmpl_id وليس product_id (متوافق مع SAP - الأسعار مرتبطة بالمنتج الأساسي ووحدة القياس)
            pricelist_items = self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('product_uom_id', '=', uom.id),  # Exact UoM match!
                ('compute_price', '=', 'fixed'),
            ], limit=1, order='id DESC')
            
            if pricelist_items:
                # Found exact UoM match - use it!
                price = pricelist_items[0].fixed_price
                _logger.info(f"✅ Found exact UoM match! Price: ${price}")
                
                # Handle currency conversion if needed
                if pricelist.currency_id != line.currency_id:
                    price = pricelist.currency_id._convert(
                        price,
                        line.currency_id,
                        line.company_id,
                        line.order_id.date_order or fields.Date.today()
                    )
                
                line.price_unit = price
                _logger.info(f"💰 Set price_unit to ${line.price_unit}")
            else:
                # No exact match - use standard Odoo logic
                _logger.info(f"⚠️ No exact UoM match, using standard pricing")
                super(SaleOrderLine, line)._compute_price_unit()

