# -*- coding: utf-8 -*-
#############################################################################
#
#    Smart UoM Pricing - Override لحل مشكلة التوافق
#    يحل مشكلة: pricelist_item_id._compute_price() got unexpected keyword argument 'uom'
#
#############################################################################
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ProductPricelistItemCompatible(models.Model):
    """
    Override لـ _compute_price للتوافق مع Odoo 19
    
    المشكلة: sale.order.line يستدعي pricelist_item_id._compute_price(... uom=...)
    الحل: نقبل uom كـ parameter لكن نتجاهله (Odoo 19 لا يستخدمه)
    """
    _inherit = "product.pricelist.item"
    
    def _compute_price(self, product, quantity, date=False, currency=False, **kwargs):
        """
        Override متوافق مع كل من:
        - Odoo 19: _compute_price(product, quantity, date, currency)
        - Sale module: _compute_price(product, quantity, uom=..., date=..., currency=...)
        
        الحل: نقبل **kwargs ونتجاهل uom إذا تم تمريره
        """
        # Handle empty recordset case (when pricelist_item_id is False)
        # This matches the base implementation pattern: self and self.ensure_one()
        if not self:
            # Extract uom from kwargs if present
            uom = kwargs.pop('uom', None)
            if not uom and product:
                # Fallback to product's default UoM if uom not provided
                uom = product.uom_id
            if not uom:
                # Last resort: get default UoM from env
                uom = self.env['uom.uom'].search([], limit=1)
            # When self is empty, compute base price directly (matching base method behavior)
            # The base method's else clause calls _compute_base_price with self.base or 'list_price'
            # Since self is empty, self.base is False, so it defaults to 'list_price'
            currency = currency or self.env.company.currency_id
            price = product._price_compute('list_price', uom=uom, date=date or False)[product.id]
            src_currency = product.currency_id
            if src_currency != currency:
                price = src_currency._convert(price, currency, self.env.company, date or False, round=False)
            return price
        
        self.ensure_one()
        
        # إزالة uom من kwargs إذا وُجد (Odoo 19 لا يستخدمه)
        kwargs.pop('uom', None)
        
        # نظام الأولويات الذكي:
        # إذا كان هذا item له uom محدد وهو fixed price، استخدمه مباشرة
        if self.product_uom_id and self.compute_price == 'fixed':
            _logger.debug(f"Using fixed price {self.fixed_price} for {self.product_uom_id.name}")
            return self.fixed_price
        
        # في جميع الحالات الأخرى، استخدم الحساب القياسي
        return super()._compute_price(product, quantity, date=date, currency=currency, **kwargs)

