# -*- coding: utf-8 -*-
#############################################################################
#
#    UoM Pricelist Enhancement
#    Auto Calculate UoM Prices Wizard
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AutoCalculateUomPrices(models.TransientModel):
    """معالج لحساب أسعار UoM تلقائياً بناءً على نسب التحويل"""
    _name = 'auto.calculate.uom.prices'
    _description = 'Auto Calculate UoM Prices'
    
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='قائمة الأسعار / Price List',
        required=True,
        help='قائمة الأسعار التي سيتم تطبيق الحساب التلقائي عليها'
    )
    
    product_ids = fields.Many2many(
        'product.product',
        string='المنتجات / Products',
        help='اختر منتجات محددة، أو اترك فارغاً للتطبيق على جميع المنتجات'
    )
    
    base_uom_price_source = fields.Selection([
        ('list_price', 'سعر القائمة للمنتج / Product List Price'),
        ('existing_rule', 'قاعدة موجودة / Existing Pricelist Rule'),
    ], string='مصدر السعر الأساسي', default='existing_rule', required=True)
    
    overwrite_existing = fields.Boolean(
        string='استبدال الأسعار الموجودة / Overwrite Existing',
        default=False,
        help='إذا تم التفعيل، سيتم استبدال الأسعار الموجودة بالأسعار المحسوبة'
    )
    
    min_price = fields.Float(
        string='الحد الأدنى للسعر / Min Price',
        default=0.01,
        help='لن يتم إنشاء قواعد للمنتجات أقل من هذا السعر'
    )
    
    def action_calculate_prices(self):
        """حساب الأسعار تلقائياً لجميع UoM"""
        self.ensure_one()
        
        PricelistItem = self.env['product.pricelist.item']
        
        # تحديد المنتجات
        if self.product_ids:
            products = self.product_ids
        else:
            products = self.env['product.product'].search([
                ('sale_ok', '=', True),
                ('active', '=', True)
            ])
        
        _logger.info(f"🚀 بدء الحساب التلقائي ل {len(products)} منتج")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for product in products:
            try:
                result = self._calculate_product_uom_prices(product, PricelistItem)
                created_count += result['created']
                updated_count += result['updated']
                skipped_count += result['skipped']
            except Exception as e:
                _logger.error(f"❌ خطأ في المنتج {product.display_name}: {e}")
                error_count += 1
                continue
        
        message = _(
            f'✅ تم بنجاح!\n\n'
            f'• تم الإنشاء: {created_count} قاعدة جديدة\n'
            f'• تم التحديث: {updated_count} قاعدة\n'
            f'• تم التخطي: {skipped_count} قاعدة\n'
            f'• أخطاء: {error_count}'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('اكتمل الحساب التلقائي'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
    
    def _calculate_product_uom_prices(self, product, PricelistItem):
        """حساب أسعار UoM لمنتج واحد"""
        created = 0
        updated = 0
        skipped = 0
        
        # الحصول على السعر الأساسي
        base_price, base_uom = self._get_base_price_and_uom(product)
        
        if not base_price or base_price < self.min_price:
            _logger.debug(f"⏭️ تخطي {product.display_name} - سعر منخفض جداً")
            return {'created': 0, 'updated': 0, 'skipped': 1}
        
        _logger.info(f"💰 {product.display_name}: السعر الأساسي = {base_price} ({base_uom.name})")
        
        # الحصول على جميع UoM البديلة
        # في Odoo 19، نستخدم related_uom_ids بدلاً من category
        alternative_uoms = self._get_alternative_uoms(product, base_uom)
        
        for uom in alternative_uoms:
            # حساب السعر بناءً على factor
            calculated_price = self._calculate_price_for_uom(
                base_price, base_uom, uom
            )
            
            if not calculated_price or calculated_price < self.min_price:
                skipped += 1
                continue
            
            # البحث عن قاعدة موجودة
            # ملاحظة: نستخدم product_tmpl_id وليس product_id لربط السعر بالمنتج الأساسي ووحدة القياس
            # وليس بالتنوع، مما يتوافق مع منطق SAP
            existing_item = PricelistItem.search([
                ('pricelist_id', '=', self.pricelist_id.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_uom_id', '=', uom.id)
            ], limit=1)
            
            if existing_item:
                if self.overwrite_existing:
                    # تحديث
                    existing_item.write({
                        'fixed_price': calculated_price,
                        'compute_price': 'fixed',
                    })
                    updated += 1
                    _logger.info(f"   ✏️ تحديث {uom.name}: {calculated_price:.2f}")
                else:
                    skipped += 1
                    _logger.debug(f"   ⏭️ تخطي {uom.name} - موجود مسبقاً")
            else:
                # إنشاء جديد - مرتبط بـ product template ووحدة القياس (ليس بالتنوع)
                PricelistItem.create({
                    'pricelist_id': self.pricelist_id.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_uom_id': uom.id,
                    'compute_price': 'fixed',
                    'fixed_price': calculated_price,
                    'applied_on': '1_product',  # Product Template وليس Variant
                })
                created += 1
                _logger.info(f"   ✨ إنشاء {uom.name}: {calculated_price:.2f}")
        
        return {'created': created, 'updated': updated, 'skipped': skipped}
    
    def _get_base_price_and_uom(self, product):
        """الحصول على السعر الأساسي والوحدة"""
        if self.base_uom_price_source == 'list_price':
            return product.list_price, product.uom_id
        else:
            # البحث عن قاعدة موجودة للوحدة الأساسية
            # استخدام product_tmpl_id وليس product_id (متوافق مع SAP)
            PricelistItem = self.env['product.pricelist.item']
            existing_rule = PricelistItem.search([
                ('pricelist_id', '=', self.pricelist_id.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_uom_id', '=', product.uom_id.id),
                ('compute_price', '=', 'fixed')
            ], limit=1)
            
            if existing_rule:
                return existing_rule.fixed_price, existing_rule.product_uom_id
            else:
                # fallback إلى list_price
                return product.list_price, product.uom_id
    
    def _get_alternative_uoms(self, product, base_uom):
        """الحصول على وحدات القياس البديلة"""
        # في Odoo 19، نحتاج للبحث عن UoM في نفس المجموعة
        # يمكننا استخدام related_uom_ids
        
        all_uoms = []
        
        # إضافة UoM المرتبطة مباشرة
        if base_uom.related_uom_ids:
            all_uoms.extend(base_uom.related_uom_ids)
        
        # البحث عن UoM التي تشير لنفس reference
        if base_uom.relative_uom_id:
            ref_uom = base_uom.relative_uom_id
            related = self.env['uom.uom'].search([
                ('relative_uom_id', '=', ref_uom.id),
                ('id', '!=', base_uom.id)
            ])
            all_uoms.extend(related)
        
        # إزالة المكررات
        return list(set(all_uoms))
    
    def _calculate_price_for_uom(self, base_price, base_uom, target_uom):
        """حساب السعر لوحدة قياس معينة بناءً على factor"""
        
        try:
            # في Odoo 19، factor هو الرقم المطلق
            if target_uom.factor > 0 and base_uom.factor > 0:
                ratio = target_uom.factor / base_uom.factor
                calculated_price = base_price * ratio
                
                # تقريب للرقمين العشريين
                return round(calculated_price, 2)
            else:
                _logger.warning(f"⚠️ factor غير صالح: {target_uom.name}")
                return 0.0
        except Exception as e:
            _logger.error(f"❌ خطأ في الحساب: {e}")
            return 0.0
    
    def action_preview_calculations(self):
        """معاينة الحسابات قبل التطبيق"""
        # يمكن تطوير هذا لاحقاً لعرض جدول بالحسابات المتوقعة
        raise UserError(_(
            'معاينة الحسابات:\n\n'
            'هذه الميزة قيد التطوير.\n'
            'سيتم عرض جدول بجميع الحسابات المتوقعة قبل التطبيق.'
        ))



