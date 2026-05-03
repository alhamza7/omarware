# -*- coding: utf-8 -*-
#############################################################################
#
#    Smart UoM Pricing for POS
#    نظام التسعير الذكي في نقاط البيع
#
#############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrderLineSmart(models.Model):
    """
    تطبيق نظام التسعير الذكي في POS
    
    الأولوية:
    1. سعر محدد في Pricelist للـ UoM المختار
    2. حساب بالمعامل من السعر الأساسي
    """
    _inherit = 'pos.order.line'
    
    @api.model
    def _order_line_fields(self, line, session_id=None):
        """
        تجهيز بيانات السطر للـ POS
        نستخدم هذا لحساب السعر الصحيح
        """
        result = super()._order_line_fields(line, session_id=session_id)
        
        # إذا كان هناك UoM مخصص، احسب السعر الصحيح
        if line.get('uom_id') and line.get('product_id'):
            try:
                product = self.env['product.product'].browse(line['product_id'])
                uom = self.env['uom.uom'].browse(line['uom_id'])
                
                # الحصول على الـ pricelist من الجلسة
                if session_id:
                    session = self.env['pos.session'].browse(session_id)
                    pricelist = session.config_id.pricelist_id
                elif line.get('pricelist_id'):
                    pricelist = self.env['product.pricelist'].browse(
                        line['pricelist_id']
                    )
                else:
                    # استخدام pricelist افتراضي
                    pricelist = self.env['product.pricelist'].search([], limit=1)
                
                if pricelist and product and uom:
                    # استخدام المنطق الذكي
                    price_result = pricelist._compute_price_rule(
                        products=product,
                        quantity=line.get('qty', 1.0),
                        uom=uom,
                        date=fields.Datetime.now(),
                        compute_price=True
                    )
                    
                    if product.id in price_result:
                        price, rule_id = price_result[product.id]
                        if price > 0:
                            result['price_unit'] = price
                            _logger.info(
                                f"POS: سعر {product.name} @ {uom.name} = ${price:.2f}"
                            )
            except Exception as e:
                _logger.error(f"خطأ في حساب سعر POS: {e}")
        
        return result


class PosSessionSmart(models.Model):
    """تحسينات على جلسة POS"""
    _inherit = 'pos.session'
    
    def _loader_params_product_product(self):
        """
        تحميل معلومات إضافية للمنتجات في POS
        نضيف معلومات UoM و Pricelist Items
        """
        result = super()._loader_params_product_product()
        
        # إضافة حقول UoM
        if 'search_params' in result and 'fields' in result['search_params']:
            result['search_params']['fields'].extend([
                'uom_id',
                'uom_name',
            ])
        
        return result
    
    def _get_pos_ui_product_product(self, params):
        """
        تحميل بيانات المنتجات مع أسعار UoM
        """
        products = super()._get_pos_ui_product_product(params)
        
        # إضافة معلومات Pricelist Items لكل منتج
        pricelist = self.config_id.pricelist_id
        
        if pricelist:
            PricelistItem = self.env['product.pricelist.item']
            
            for product in products:
                product_id = product['id']
                # الحصول على product_tmpl_id من المنتج (متوافق مع SAP - الأسعار مرتبطة بالمنتج الأساسي)
                product_obj = self.env['product.product'].browse(product_id)
                product_tmpl_id = product_obj.product_tmpl_id.id if product_obj else None
                
                if not product_tmpl_id:
                    continue
                
                # جلب جميع قواعد التسعير لهذا المنتج
                # استخدام product_tmpl_id وليس product_id (متوافق مع SAP)
                items = PricelistItem.search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', product_tmpl_id),
                    ('product_uom_id', '!=', False),
                ])
                
                # إضافة أسعار UoM
                uom_prices = {}
                for item in items:
                    if item.compute_price == 'fixed':
                        uom_prices[item.product_uom_id.id] = {
                            'price': item.fixed_price,
                            'uom_name': item.product_uom_id.name,
                        }
                
                product['uom_prices'] = uom_prices
        
        return products



