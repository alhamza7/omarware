#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث سعر الصرف في POS Perfume إلى 1510
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def update_pos_perfume_rate():
    """تحديث سعر الصرف في POS Perfume"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    # الحصول على اسم قاعدة البيانات
    db_name = odoo.tools.config.get('db_name', '')
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else ''
    
    if not db_name:
        dbfilter = odoo.tools.config.get('dbfilter', '')
        if dbfilter:
            import re
            match = re.match(r'\^?(\w+).*\$?', dbfilter)
            if match:
                db_name = match.group(1)
    
    if not db_name:
        db_name = 'nbs_lugalai'
    
    print(f"\n{'='*70}")
    print(f"تحديث سعر الصرف في POS Perfume - قاعدة البيانات: {db_name}")
    print(f"{'='*70}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من وحدة pos_perfume_custom
            print("1. التحقق من وحدة pos_perfume_custom...")
            
            module = env['ir.module.module'].search([
                ('name', '=', 'pos_perfume_custom')
            ], limit=1)
            
            if not module:
                print("   ❌ وحدة pos_perfume_custom غير موجودة!")
                return
            
            print(f"   ✅ الوحدة موجودة (الحالة: {module.state})")
            
            # 2. عرض السعر الحالي
            print("\n2. السعر الحالي في POS Perfume...")
            
            current_rate = env['ir.config_parameter'].get_param(
                'pos_perfume.default_exchange_rate_usd_iqd',
                default='1510.0'
            )
            
            print(f"   📊 السعر الحالي: {current_rate} IQD")
            
            # 3. تحديث السعر إلى 1510
            print(f"\n3. تحديث السعر إلى 1510...")
            
            env['ir.config_parameter'].set_param(
                'pos_perfume.default_exchange_rate_usd_iqd',
                '1510.0'
            )
            
            print("   ✅ تم تحديث السعر في ir.config_parameter")
            
            # 4. التحقق من النتيجة
            print(f"\n4. التحقق من السعر الجديد...")
            
            new_rate = env['ir.config_parameter'].get_param(
                'pos_perfume.default_exchange_rate_usd_iqd'
            )
            
            print(f"   ✅ السعر الجديد: {new_rate} IQD")
            
            # 5. التحقق من الطلبات الموجودة
            print(f"\n5. التحقق من طلبات POS Perfume...")
            
            orders = env['pos.perfume.order'].search([], limit=5, order='id desc')
            
            if orders:
                print(f"   وجدت {len(orders)} طلب (آخر 5):")
                print(f"\n   {'ID':<8} {'التاريخ':<12} {'السعر المستخدم':<15}")
                print(f"   {'-'*40}")
                
                for order in orders:
                    rate_used = order.exchange_rate or 0
                    print(f"   {order.id:<8} {str(order.date_order)[:10]:<12} {rate_used:>13.2f}")
            else:
                print("   ℹ️  لا توجد طلبات POS Perfume بعد")
            
            # 6. مسح الكاش
            print(f"\n6. مسح الكاش...")
            env['ir.config_parameter'].invalidate_model()
            env['res.config.settings'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*70}")
            print("✅ تم تحديث سعر الصرف في POS Perfume!")
            print(f"{'='*70}\n")
            
            print("📋 الخطوات التالية:")
            print("")
            print("1. في المتصفح:")
            print("   - امسح الكاش: Ctrl+Shift+Delete")
            print("   - أعد تحميل الصفحة: F5")
            print("")
            print("2. في POS Perfume:")
            print("   - افتح POS Perfume من القائمة")
            print("   - أنشئ طلب جديد")
            print("   - تحقق من السعر: يجب أن يكون 1510")
            print("")
            print("3. اختبار:")
            print("   - امسح باركود منتج")
            print("   - السعر بـ IQD = السعر بـ USD × 1510")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    update_pos_perfume_rate()
