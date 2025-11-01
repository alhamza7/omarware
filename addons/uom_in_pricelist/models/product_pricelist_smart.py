# -*- coding: utf-8 -*-
#############################################################################
#
#    Smart UoM Pricing - Priority-based pricing logic
#    الأولوية: Pricelist أولاً، ثم المعامل
#    Odoo 19 Compatible
#
#############################################################################
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductPricelistSmart(models.Model):
    """
    نظام تسعير ذكي بالأولويات:
    1. ابحث عن سعر محدد في Pricelist لهذا UoM
    2. إذا وُجد → استخدمه مباشرة
    3. إذا لم يُوجد → احسب بالمعامل من السعر الأساسي
    """
    _inherit = "product.pricelist"

    def _compute_price_rule(
            self, products, quantity, currency=None, uom=None, date=False,
            compute_price=True,
            **kwargs
    ):
        """
        حساب السعر مع نظام الأولويات الذكي - Odoo 19 Compatible
        
        الخوارزمية:
        1. للـ UoM المطلوب، ابحث عن قاعدة محددة في Pricelist
        2. إذا وُجدت قاعدة محددة → استخدم سعرها مباشرة
        3. إذا لم توجد → ابحث عن سعر الوحدة الأساسية واحسب بالمعامل
        """
        self.ensure_one()
        if not products:
            return {}
        if not date:
            date = fields.Datetime.now()
        
        results = {}
        
        for product in products:
            target_uom = uom or product.uom_id
            
            # تحويل الكمية للوحدة الأساسية
            qty_in_product_uom = quantity
            if uom and uom != product.uom_id:
                try:
                    qty_in_product_uom = uom._compute_quantity(
                        quantity, product.uom_id, raise_if_failure=False
                    ) or quantity
                except:
                    qty_in_product_uom = quantity
            
            # ==========================================
            # الأولوية 1: ابحث عن سعر محدد لهذا UoM
            # ==========================================
            specific_price, specific_rule = self._find_specific_uom_price(
                product, qty_in_product_uom, target_uom, date
            )
            
            if specific_price is not None:
                # ✅ وُجد سعر محدد - استخدمه!
                _logger.info(
                    f"✅ [{product.default_code}] {product.name}: "
                    f"سعر محدد ل {target_uom.name} = ${specific_price:.2f}"
                )
                results[product.id] = (specific_price, specific_rule.id if specific_rule else False)
                continue
            
            # ==========================================
            # الأولوية 2: احسب بالمعامل من السعر الأساسي
            # ==========================================
            calculated_price, base_rule = self._calculate_from_base_uom(
                product, qty_in_product_uom, target_uom, date, currency
            )
            
            if calculated_price is not None:
                # ✅ تم الحساب بالمعامل
                _logger.info(
                    f"🧮 [{product.default_code}] {product.name}: "
                    f"سعر محسوب ل {target_uom.name} = ${calculated_price:.2f} "
                    f"(من الوحدة الأساسية)"
                )
                results[product.id] = (calculated_price, base_rule.id if base_rule else False)
                continue
            
            # ==========================================
            # الأولوية 3: السعر الافتراضي (fallback)
            # ==========================================
            _logger.warning(
                f"⚠️ [{product.default_code}] {product.name}: "
                f"لم يتم العثور على سعر محدد أو أساسي ل {target_uom.name}"
            )
            results[product.id] = (0.0, False)
        
        return results
    
    def _find_specific_uom_price(self, product, quantity, uom, date):
        """
        البحث عن سعر محدد لهذا UoM في Pricelist
        
        Returns:
            (price, rule) أو (None, None) إذا لم يُوجد
        """
        PricelistItem = self.env['product.pricelist.item']
        
        # جلب جميع القواعد المتاحة
        rules = self._get_applicable_rules(product, date)
        
        for rule in rules:
            # فحص إذا القاعدة تنطبق على هذا المنتج والكمية
            if not rule._is_applicable_for(product, quantity):
                continue
            
            # ✅ القاعدة الحاسمة: هل هذه القاعدة محددة لهذا UoM؟
            if rule.product_uom_id and rule.product_uom_id.id == uom.id:
                # وُجدت قاعدة محددة لهذا UoM!
                if rule.compute_price == 'fixed':
                    # سعر ثابت - استخدمه مباشرة
                    price = rule.fixed_price
                    
                    # تحويل العملة إذا لزم
                    if self.currency_id != product.currency_id:
                        price = self.currency_id._convert(
                            price, product.currency_id,
                            self.env.company, date
                        )
                    
                    return (price, rule)
                else:
                    # نوع حساب آخر (percentage, formula)
                    # احسب السعر حسب نوع القاعدة (بدون uom parameter في Odoo 19)
                    price = rule._compute_price(
                        product, quantity, date=date, currency=self.currency_id
                    )
                    return (price, rule)
        
        # لم يُوجد سعر محدد لهذا UoM
        return (None, None)
    
    def _calculate_from_base_uom(self, product, quantity, target_uom, date, currency):
        """
        حساب السعر بالمعامل من السعر الأساسي
        
        الخوارزمية:
        1. ابحث عن سعر الوحدة الأساسية للمنتج
        2. احسب النسبة بين target_uom والوحدة الأساسية
        3. السعر النهائي = السعر الأساسي × النسبة
        
        Returns:
            (price, rule) أو (None, None) إذا لم يُوجد سعر أساسي
        """
        base_uom = product.uom_id
        
        # ابحث عن سعر الوحدة الأساسية
        base_price, base_rule = self._find_specific_uom_price(
            product, quantity, base_uom, date
        )
        
        if base_price is None:
            # لم يُوجد حتى سعر للوحدة الأساسية
            # استخدم list_price كملاذ أخير
            base_price = product.list_price
            base_rule = None
            
            if not base_price or base_price <= 0:
                return (None, None)
        
        # حساب النسبة بين الوحدتين
        if target_uom.id == base_uom.id:
            # نفس الوحدة!
            return (base_price, base_rule)
        
        try:
            # في Odoo 19، نستخدم factor
            if target_uom.factor > 0 and base_uom.factor > 0:
                ratio = target_uom.factor / base_uom.factor
                calculated_price = base_price * ratio
                
                _logger.debug(
                    f"📐 حساب السعر: {base_uom.name} ({base_price}) × "
                    f"{ratio:.6f} = {target_uom.name} ({calculated_price})"
                )
                
                return (round(calculated_price, 2), base_rule)
            else:
                _logger.warning(
                    f"⚠️ factor غير صالح: {target_uom.name} "
                    f"(factor={target_uom.factor})"
                )
                return (None, None)
        except Exception as e:
            _logger.error(f"❌ خطأ في حساب السعر بالمعامل: {e}")
            return (None, None)


class ProductPricelistItemSmart(models.Model):
    """تعديلات على Pricelist Item للنظام الذكي"""
    _inherit = "product.pricelist.item"
    
    is_calculated = fields.Boolean(
        string="محسوب تلقائياً",
        default=False,
        help="إذا كان true، هذا السعر محسوب تلقائياً بالمعامل وليس مُدخل يدوياً"
    )
    
    calculation_note = fields.Char(
        string="ملاحظة الحساب",
        help="توضيح كيف تم حساب هذا السعر"
    )
