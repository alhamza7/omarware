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
        Returns: dict{product_id: (price, suitable_rule) for the given
        price list}
        
        Enhanced for Odoo 19 with UoM-specific pricing support.
        """
        self.ensure_one()
        if not products:
            return {}
        if not date:
            date = fields.Datetime.now()
        
        # جلب جميع القواعد المتاحة
        rules = self._get_applicable_rules(products, date, **kwargs)
        results = {}
        
        for product in products:
            suitable_rule = self.env['product.pricelist.item']
            target_uom = uom or product.uom_id
            
            # تحويل الكمية للوحدة الأساسية للمنتج
            qty_in_product_uom = quantity
            if uom and uom != product.uom_id:
                try:
                    qty_in_product_uom = uom._compute_quantity(
                        quantity, product.uom_id, raise_if_failure=False
                    ) or quantity
                except:
                    qty_in_product_uom = quantity
            
            # البحث عن أفضل قاعدة تنطبق
            for rule in rules:
                # فحص القاعدة الأساسية
                if not rule._is_applicable_for(product, qty_in_product_uom):
                    continue
                
                # فحص UoM إذا كان محدد في القاعدة
                if rule.product_uom_id:
                    # إذا القاعدة لها UoM محدد
                    if uom and rule.product_uom_id.id == uom.id:
                        # مطابقة تامة! استخدم هذه القاعدة
                        _logger.info(f"✅ Found matching rule for {product.display_name} with UoM {uom.name}")
                        suitable_rule = rule
                        break
                    else:
                        # UoM لا يطابق - تخطي هذه القاعدة
                        _logger.debug(f"⏭️ Skipping rule - UoM mismatch")
                        continue
                else:
                    # القاعدة ليس لها UoM محدد - يمكن استخدامها
                    suitable_rule = rule
                    break
            
            # حساب السعر النهائي
            if compute_price and suitable_rule:
                try:
                    # _compute_price في pricelist_item سيتعامل مع UoM
                    price = suitable_rule._compute_price(
                        product, quantity, target_uom, date=date, currency=currency
                    )
                    _logger.info(f"💰 Final price for {product.display_name}: {price}")
                except Exception as e:
                    _logger.error(f"❌ Error computing price: {e}")
                    price = 0.0
            else:
                price = 0.0
            
            results[product.id] = (price, suitable_rule.id)
        
        return results
