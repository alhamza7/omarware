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
            
            # Use the raw quantity (not converted) for _is_applicable_for.
            # Conversion would cause sub-unit rules to fail the min_quantity check:
            # e.g., 1 "100 غم" → 0.1 kg which is < min_quantity=1 (kg), wrongly rejecting the rule.
            # Since all rules here have min_quantity=1 (meaning "at least 1 of this unit"),
            # we pass the original quantity to avoid false rejections.
            qty_for_applicability = quantity

            _logger.info(f"[Price Rule] Looking for rules for {product.display_name} with UoM {uom.name if uom else 'None'} (ID: {uom.id if uom else None})")
            
            # Search for the best matching rule
            # Priority: exact UoM match > base rule (no UoM)
            exact_match_rule = None
            base_rule = None
            
            for rule in rules:
                # Check basic rule applicability using raw quantity to avoid UoM conversion issues
                if not rule._is_applicable_for(product, qty_for_applicability):
                    continue
                
                # Check UoM match - PRIORITY SYSTEM:
                # 1. HIGHEST: UoM match WITHOUT packaging (base price)
                # 2. MEDIUM: UoM match WITH packaging (packaging price)
                # 3. LOWEST: No UoM specified (fallback)
                
                rule_uom = None
                has_packaging = False

                # PRIORITY: product_packaging_id stores the specific sub-unit UoM in this
                # system (it is a Many2one to uom.uom, not product.packaging).
                # A rule that has product_packaging_id set is a sub-unit price rule;
                # its effective UoM IS product_packaging_id itself.
                # A rule without product_packaging_id is the base-UoM price rule,
                # matched via product_uom_id.
                if rule.product_packaging_id:
                    # Sub-unit rule — product_packaging_id is the specific UoM
                    rule_uom = rule.product_packaging_id  # uom.uom record
                    has_packaging = True
                elif rule.product_uom_id:
                    # Base-UoM rule
                    rule_uom = rule.product_uom_id
                    has_packaging = False

                if rule_uom:
                    # Rule has a specific UoM — check if it matches the requested UoM
                    if uom and rule_uom.id == uom.id:
                        if not has_packaging:
                            _logger.info(f"[Price Rule] Found EXACT UoM match (NO packaging - BASE PRICE): Rule {rule.id}, Price {rule.fixed_price}")
                            exact_match_rule = rule
                            break  # Perfect match — stop searching
                        elif not exact_match_rule or (exact_match_rule and exact_match_rule.product_packaging_id):
                            _logger.info(f"[Price Rule] Found UoM match (WITH packaging): Rule {rule.id}, Price {rule.fixed_price}")
                            exact_match_rule = rule
                    else:
                        # UoM doesn't match — skip
                        continue
                else:
                    # Rule has no specific UoM — use as fallback
                    if not base_rule:
                        base_rule = rule
                        _logger.info(f"[Price Rule] Found base rule: Rule {rule.id}, Price {rule.fixed_price}")
            
            # Use exact match if found, otherwise use base rule
            suitable_rule = exact_match_rule or base_rule
            
            if suitable_rule:
                _logger.info(f"[Price Rule] Selected rule {suitable_rule.id} for {product.display_name}")
            else:
                _logger.warning(f"[Price Rule] No suitable rule found for {product.display_name}")
            
            # Calculate final price
            if compute_price and suitable_rule:
                try:
                    # _compute_price in pricelist_item will handle UoM
                    price = suitable_rule._compute_price(
                        product, quantity, date=date, currency=currency, uom=target_uom
                    )
                    _logger.info(f"[Price Rule] Final price for {product.display_name}: ${price}")
                except Exception as e:
                    _logger.error(f"[Price Rule] Error computing price: {e}", exc_info=True)
                    price = 0.0
            else:
                price = 0.0
            
            results[product.id] = (price, suitable_rule.id if suitable_rule else False)
        
        return results
