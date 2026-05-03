#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ترقية الموديول عبر XML-RPC (بدون إيقاف Odoo)
"""

import sys
import io
import xmlrpc.client

# Fix Unicode encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}\n")

def main():
    try:
        print_section("🔌 الاتصال بـ Odoo")
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("❌ فشل تسجيل الدخول")
            print("\n💡 تأكد من:")
            print("   1. Odoo يعمل على localhost:8069")
            print("   2. اسم المستخدم وكلمة المرور صحيحة")
            return
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
        print(f"✅ متصل بنجاح! User ID: {uid}")
        
        print_section("🔄 ترقية موديول UoM Pricelist")
        
        # البحث عن الموديول
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', 'uom_in_pricelist')]])
        
        if not module_ids:
            print("❌ الموديول غير موجود!")
            return
        
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids], {'fields': ['name', 'state', 'latest_version']})[0]
        
        print(f"📦 الموديول: {module['name']}")
        print(f"   الحالة: {module['state']}")
        print(f"   الإصدار: {module.get('latest_version', 'N/A')}")
        
        if module['state'] != 'installed':
            print("\n⚠️ الموديول غير مثبت!")
            print("   يرجى تثبيته من: Apps → UOM In PriceList → Install")
            return
        
        print("\n🔄 جاري الترقية...")
        
        try:
            # محاولة الترقية
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            
            print("✅ تمت الترقية بنجاح!")
            
            print_section("✅ اكتمل!")
            
            print("🎉 الترقية نجحت!")
            print("\n📋 الخطوات التالية:")
            print("   1. حدّث صفحة المتصفح (Ctrl+F5)")
            print("   2. اختبر في Sales Order:")
            print("      Sales → Orders → Create")
            print("   3. اختر منتج وغيّر UoM")
            print("   4. ✅ يجب أن يعمل بدون أخطاء!")
            
        except Exception as e:
            error_msg = str(e)
            
            if 'locked' in error_msg.lower() or 'in use' in error_msg.lower():
                print("⚠️ الموديول قيد الاستخدام حالياً")
                print("\n💡 الحل:")
                print("   الخيار 1: أعد تحميل الصفحة وحاول مرة أخرى")
                print("   الخيار 2: أعد تشغيل Odoo:")
                print("      - أوقف Odoo (Ctrl+C)")
                print("      - python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init")
                print("      - python odoo-bin -c odoo.conf")
            else:
                print(f"❌ خطأ في الترقية: {error_msg}")
                print("\n💡 جرّب:")
                print("   1. إعادة تشغيل Odoo")
                print("   2. Apps → UOM In PriceList → Upgrade")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        print("\n💡 تأكد من:")
        print("   1. Odoo يعمل على localhost:8069")
        print("   2. قاعدة البيانات 'lugal' موجودة")

if __name__ == '__main__':
    main()



