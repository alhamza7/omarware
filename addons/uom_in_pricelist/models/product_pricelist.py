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
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    """Inherits the Product Pricelist to update the _compute_price_rule
     function for adding the product uom in price rule."""
    _inherit = "product.pricelist"

    def _compute_price_rule(
            self, products, quantity, currency=None, uom=None, date=False,
            compute_price=True,
            **kwargs
    ):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given price list}
        
        Enhanced for Odoo 19 with UoM-specific pricing support using product_packaging_id.
        """
        self.ensure_one()
        if not products:
            return {}
        if not date:
            date = fields.Datetime.now()
        
        # Get all applicable rules
        rules = self._get_applicable_rules(products, date, **kwargs)
        results = {}
        
        for product in products:
            suitable_rule = self.env['product.pricelist.item']
            target_uom = uom or product.uom_id
            
            # Convert quantity to product's base UoM
            qty_in_product_uom = quantity
            if uom and uom != product.uom_id:
                try:
                    qty_in_product_uom = uom._compute_quantity(
                        quantity, product.uom_id, raise_if_failure=False
                    ) or quantity
                except:
                    qty_in_product_uom = quantity
            
            _logger.info(f"🔍 Looking for rules for {product.display_name} with UoM {uom.name if uom else 'None'} (ID: {uom.id if uom else None})")
            
            # Search for the best matching rule
            # Priority: exact UoM match > base rule (no UoM)
            exact_match_rule = None
            base_rule = None
            
            for rule in rules:
                # Check basic rule applicability
                if not rule._is_applicable_for(product, qty_in_product_uom):
                    continue
                
                # Check if rule has product_packaging_id (which points to uom.uom)
                if rule.product_packaging_id:
                    # Rule has a specific UoM
                    if uom and rule.product_packaging_id.id == uom.id:
                        # Exact match!
                        _logger.info(f"✅ Found EXACT UoM match: Rule {rule.id}, Price {rule.fixed_price}")
                        exact_match_rule = rule
                        break  # Perfect match, stop searching
                    else:
                        # UoM doesn't match - skip this rule
                        continue
                else:
                    # Rule has no specific UoM - use as fallback
                    if not base_rule:
                        base_rule = rule
                        _logger.info(f"📋 Found base rule: Rule {rule.id}, Price {rule.fixed_price}")
            
            # Use exact match if found, otherwise use base rule
            suitable_rule = exact_match_rule or base_rule
            
            if suitable_rule:
                _logger.info(f"✅ Selected rule {suitable_rule.id} for {product.display_name}")
            else:
                _logger.warning(f"⚠️ No suitable rule found for {product.display_name}")
            
            # Calculate final price
            if compute_price and suitable_rule:
                try:
                    # _compute_price in pricelist_item will handle UoM
                    price = suitable_rule._compute_price(
                        product, quantity, target_uom, date=date, currency=currency
                    )
                    _logger.info(f"💰 Final price for {product.display_name}: ${price}")
                except Exception as e:
                    _logger.error(f"❌ Error computing price: {e}")
                    price = 0.0
            else:
                price = 0.0
            
            results[product.id] = (price, suitable_rule.id if suitable_rule else False)
        
        return results
