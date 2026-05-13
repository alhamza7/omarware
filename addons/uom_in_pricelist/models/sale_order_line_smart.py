# -*- coding: utf-8 -*-
#############################################################################
#
#    Smart UoM Pricing for Sales Orders
#    نظام التسعير الذكي في أوامر البيع
#
#############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLineSmart(models.Model):
    """
    تطبيق نظام التسعير الذكي في Sales Orders
    
    الأولوية:
    1. سعر محدد في Pricelist للـ UoM المختار
    2. حساب بالمعامل من السعر الأساسي
    3. list_price كملاذ أخير
    """
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        """
        حساب السعر مع نظام الأولويات
        
        هذا المنهج يتم استدعاؤه تلقائياً عند:
        - اختيار منتج
        - تغيير وحدة القياس
        - تغيير الكمية
        """
        for line in self:
            # تخطي إذا لم يكن هناك منتج
            if not line.product_id or not line.order_id.pricelist_id:
                super(SaleOrderLineSmart, line)._compute_price_unit()
                continue
            
            # الحصول على المعلومات الأساسية
            pricelist = line.order_id.pricelist_id
            product = line.product_id
            uom = line.product_uom_id or product.uom_id
            quantity = line.product_uom_qty or 1.0
            
            _logger.info(
                f"💰 حساب سعر: [{product.default_code}] {product.name} "
                f"@ {quantity} {uom.name}"
            )
            
            try:
                # ==========================================
                # استخدام منطق Pricelist الذكي
                # ==========================================
                
                # استدعاء _compute_price_rule الذي عدّلناه
                price_result = pricelist._compute_price_rule(
                    products=product,
                    quantity=quantity,
                    uom=uom,
                    date=line.order_id.date_order or fields.Date.today(),
                    compute_price=True
                )
                
                if product.id in price_result:
                    price, rule_id = price_result[product.id]
                    
                    if price > 0:
                        # وُجد سعر - استخدمه
                        _logger.info(f"✅ السعر النهائي: ${price:.2f}")
                        
                        # تحويل العملة إذا لزم
                        if pricelist.currency_id != line.currency_id:
                            price = pricelist.currency_id._convert(
                                price,
                                line.currency_id,
                                line.company_id,
                                line.order_id.date_order or fields.Date.today()
                            )
                        
                        line.price_unit = price
                        continue
                
                # إذا فشل كل شيء، استخدم المنطق الافتراضي
                _logger.warning(
                    f"⚠️ استخدام المنطق الافتراضي ل {product.name}"
                )
                super(SaleOrderLineSmart, line)._compute_price_unit()
                
            except Exception as e:
                _logger.error(
                    f"❌ خطأ في حساب السعر ل {product.name}: {e}"
                )
                # fallback إلى المنطق الافتراضي
                super(SaleOrderLineSmart, line)._compute_price_unit()
    
    @api.onchange('product_uom_id', 'product_uom_qty')
    def _onchange_product_uom(self):
        """
        عند تغيير وحدة القياس، أعد حساب السعر
        """
        if self.product_id:
            self._compute_price_unit()

