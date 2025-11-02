# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from . import product_pricelist
from . import product_pricelist_item
from . import product_pricelist_item_compatible  # حل مشكلة التوافق
from . import sale_order_line  # استخدم للتسعير البسيط المباشر
# Smart pricing system - نظام التسعير الذكي (معطل مؤقتاً)
# from . import product_pricelist_smart
# from . import sale_order_line_smart
from . import pos_order_line_smart

# Apply monkey patch for UoM pricing
# This must be done AFTER all imports to ensure it overrides other modules
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.sale.models.sale_order_line import SaleOrderLine
    
    # Store original
    _original_get_display_price = SaleOrderLine._get_display_price
    
    def _get_display_price_uom(self):
        """UoM-aware pricing"""
        if not self.product_id or not self.order_id.pricelist_id:
            return _original_get_display_price(self)
        
        pricelist = self.order_id.pricelist_id
        uom = self.product_uom_id or self.product_id.uom_id
        
        # Exact UoM match
        items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', uom.id),
            ('compute_price', '=', 'fixed'),
        ], limit=1)
        
        if items:
            _logger.info(f"✅ UoM price: {items[0].fixed_price}")
            return items[0].fixed_price
        
        # Base price
        base = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            ('product_packaging_id', '=', False),
        ], limit=1)
        
        if base:
            price = base[0].fixed_price
            if uom != self.product_id.uom_id:
                price *= uom.factor_inv / self.product_id.uom_id.factor_inv
            return price
        
        return _original_get_display_price(self)
    
    # Patch
    SaleOrderLine._get_display_price = _get_display_price_uom
    _logger.info("✅ UoM pricing patch applied!")
    
except Exception as e:
    _logger.error(f"❌ Failed to patch UoM pricing: {e}")

