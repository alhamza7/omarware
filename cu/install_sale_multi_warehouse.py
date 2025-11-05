# -*- coding: utf-8 -*-
"""
Install sale_order_line_multi_warehouse module - Odoo 19 Compatible
"""
import sys
import os
import time

# Add Odoo to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

def install_module():
    """Install sale_order_line_multi_warehouse module"""
    
    # Parse config
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    db_name = 'lugal'
    
    print(f"\n{'='*70}")
    print(f"🚀 تفعيل إضافة Multiple Warehouses in Sale Order Lines")
    print(f"   Database: {db_name}")
    print(f"{'='*70}\n")
    
    # Wait for Odoo to start
    print("⏳ انتظار تشغيل Odoo...")
    time.sleep(5)
    
    try:
        # Get registry and cursor
        registry = Registry(db_name)
        
        with registry.cursor() as cr:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})
            
            # First, update module list to detect new modules
            print("📋 تحديث قائمة الإضافات...")
            env['ir.module.module'].update_list()
            cr.commit()
            
            # Search for the module
            module = env['ir.module.module'].search([
                ('name', '=', 'sale_order_line_multi_warehouse')
            ], limit=1)
            
            if not module:
                print("\n❌ الإضافة غير موجودة في مسار addons!")
                print("   تأكد من وجود المجلد: addons/sale_order_line_multi_warehouse")
                return False
            
            print(f"\n✅ تم العثور على الإضافة:")
            print(f"   الاسم: {module.name}")
            print(f"   الحالة: {module.state}")
            print(f"   الإصدار: {module.latest_version}")
            print(f"   الملخص: {module.summary}")
            
            if module.state == 'installed':
                print("\n📦 الإضافة مثبتة بالفعل. جاري الترقية...")
                module.button_immediate_upgrade()
                print("✅ تم ترقية الإضافة بنجاح!")
                
            elif module.state in ('uninstalled', 'to install'):
                print("\n📦 جاري تثبيت الإضافة...")
                module.button_immediate_install()
                print("✅ تم تثبيت الإضافة بنجاح!")
                
            else:
                print(f"\n⚠️ حالة الإضافة: {module.state}")
                print("محاولة الترقية...")
                module.button_immediate_upgrade()
                print("✅ تمت الترقية!")
            
            cr.commit()
            
            # Verify installation
            module.invalidate_recordset()
            module = env['ir.module.module'].search([
                ('name', '=', 'sale_order_line_multi_warehouse')
            ], limit=1)
            
            print(f"\n{'='*70}")
            print(f"✅ الحالة النهائية:")
            print(f"   الإضافة: {module.name}")
            print(f"   الحالة: {module.state}")
            print(f"   الإصدار المثبت: {module.installed_version}")
            print(f"{'='*70}\n")
            
            if module.state == 'installed':
                print("🎉 تم تثبيت الإضافة بنجاح!")
                print("\n📌 كيفية الاستخدام:")
                print("=" * 70)
                print("1. اذهب إلى: Sales → Orders → Quotations/Orders")
                print("2. أنشئ أو افتح أمر مبيعات")
                print("3. في سطور الطلب (Order Lines):")
                print("   - أضف منتج")
                print("   - ستجد عمود جديد: 'Warehouse' بعد عمود UoM")
                print("   - اختر مستودع مختلف لكل سطر حسب حاجتك")
                print("4. عند تأكيد الطلب:")
                print("   - سيتم إنشاء Delivery Orders منفصلة لكل مستودع")
                print("   - كل طلب توصيل سيكون مرتبط بالمستودع المحدد")
                print("=" * 70)
                print("\n✨ المزايا:")
                print("  • اختيار مستودع مختلف لكل منتج في نفس الطلب")
                print("  • إدارة أفضل للمخزون عبر مستودعات متعددة")
                print("  • عمليات توصيل منظمة حسب الموقع")
                print("  • مرونة في تلبية الطلبات من مواقع مختلفة")
                print("=" * 70)
                return True
            else:
                print("⚠️ قد تحتاج الإضافة إلى تدخل يدوي")
                print(f"الحالة الحالية: {module.state}")
                return False
                
    except Exception as e:
        print(f"\n❌ خطأ أثناء التثبيت: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = install_module()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ خطأ فادح: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
