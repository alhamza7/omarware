# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def post_load_hook(env):
    """
    Hook to monkey-patch sale.order.line._get_display_price after all modules are loaded
    This ensures our UoM pricing works regardless of module loading order
    
    Args:
        env: Odoo environment
    """
    _logger.info("🚀 Installing UoM pricing monkey patch...")
    
    # Import after all modules loaded
    from odoo.addons.sale.models.sale_order_line import SaleOrderLine
    
    # Store original method
    original_get_display_price = SaleOrderLine._get_display_price
    
    def _get_display_price_with_uom(self):
        """
        Enhanced _get_display_price that supports UoM-specific pricing
        """
        if not self.product_id or not self.order_id.pricelist_id:
            return original_get_display_price(self)
        
        # Get pricelist and UoM
        pricelist = self.order_id.pricelist_id
        uom = self.product_uom_id or self.product_id.uom_id
        
        # Search for exact UoM match in pricelist items
        pricelist_items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', uom.id),
            ('compute_price', '=', 'fixed'),
        ], limit=1, order='id DESC')
        
        if pricelist_items:
            # Found exact UoM match!
            _logger.info(f"✅ UoM match for {self.product_id.display_name} @ {uom.name}: ${pricelist_items[0].fixed_price}")
            return pricelist_items[0].fixed_price
        
        # Try base price (without packaging)
        base_items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', False),
            ('compute_price', '=', 'fixed'),
        ], limit=1, order='id DESC')
        
        if base_items:
            price = base_items[0].fixed_price
            
            # Convert price to selected UoM
            if uom != self.product_id.uom_id:
                factor = uom.factor_inv / self.product_id.uom_id.factor_inv
                price = price * factor
                _logger.info(f"🔄 Converted base price for {uom.name}: ${price}")
            
            return price
        
        # No custom pricing - use original logic
        return original_get_display_price(self)
    
    # Apply monkey patch
    SaleOrderLine._get_display_price = _get_display_price_with_uom
    
    _logger.info("✅ UoM pricing monkey patch installed successfully!")


def uninstall_hook(env):
    """
    Hook called when module is uninstalled
    
    Args:
        env: Odoo environment
    """
    _logger.info("🔄 Removing UoM pricing customizations...")

