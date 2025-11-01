#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ترقية موديول UoM Pricelist مع إضافة Wizard للحساب التلقائي
"""

import xmlrpc.client

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
        # الاتصال
        print_section("🔌 الاتصال بـ Odoo")
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("❌ فشل تسجيل الدخول")
            return
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
        print(f"✅ متصل بنجاح! User ID: {uid}")
        
        # ترقية الموديول
        print_section("🔄 ترقية موديول UoM Pricelist")
        
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', 'uom_in_pricelist')]])
        
        if not module_ids:
            print("❌ الموديول غير موجود!")
            return
        
        print("📦 الموديول موجود، جاري الترقية...")
        
        # زر upgrade
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            
            print("✅ تمت الترقية بنجاح!")
            
        except Exception as e:
            print(f"⚠️ ملاحظة: {e}")
            print("💡 قد تحتاج لترقية الموديول من الواجهة:")
            print("   Apps → UOM In PriceList → Upgrade")
        
        # التحقق من الترقية
        print_section("🔍 التحقق من الميزات الجديدة")
        
        # فحص model الجديد
        try:
            wizard_ids = models.execute_kw(db, uid, password,
                'ir.model', 'search',
                [[('model', '=', 'auto.calculate.uom.prices')]])
            
            if wizard_ids:
                print("✅ Wizard موجود!")
                print("   Model: auto.calculate.uom.prices")
            else:
                print("⚠️ Wizard غير موجود بعد")
                print("   قد تحتاج لإعادة تشغيل Odoo")
        except Exception as e:
            print(f"⚠️ لم يتم العثور على Wizard: {e}")
        
        # فحص القائمة
        try:
            menu_ids = models.execute_kw(db, uid, password,
                'ir.ui.menu', 'search',
                [[('name', 'like', 'حساب أسعار UoM')]])
            
            if menu_ids:
                print("✅ القائمة موجودة!")
                menu = models.execute_kw(db, uid, password,
                    'ir.ui.menu', 'read',
                    [menu_ids], {'fields': ['name', 'parent_id']})[0]
                print(f"   الاسم: {menu['name']}")
                if menu.get('parent_id'):
                    print(f"   تحت: {menu['parent_id'][1]}")
            else:
                print("⚠️ القائمة غير موجودة بعد")
        except Exception as e:
            print(f"⚠️ لم يتم العثور على القائمة: {e}")
        
        # التعليمات
        print_section("📝 كيفية الاستخدام")
        
        print("✨ الميزة الجديدة: حساب أسعار UoM تلقائياً!")
        print()
        print("🎯 كيفية الوصول:")
        print("   1. افتح Odoo في المتصفح")
        print("   2. اذهب إلى: Sales → Configuration → Pricelists")
        print("   3. في القائمة العلوية، ابحث عن:")
        print("      'حساب أسعار UoM تلقائياً'")
        print("      أو")
        print("      'Auto Calculate UoM Prices'")
        print()
        print("📋 الخطوات:")
        print("   1. اختر قائمة الأسعار")
        print("   2. اختياري: حدد منتجات معينة")
        print("   3. اختر مصدر السعر الأساسي")
        print("   4. اضغط 'حساب الأسعار'")
        print()
        print("💡 النتيجة:")
        print("   سيتم حساب جميع أسعار وحدات القياس البديلة")
        print("   تلقائياً بناءً على نسب التحويل!")
        
        print_section("✅ اكتمل")
        
        print("🎉 الموديول جاهز للاستخدام!")
        print()
        print("⚠️ ملاحظة مهمة:")
        print("   إذا لم تظهر الميزة الجديدة، قم بـ:")
        print("   1. إعادة تشغيل Odoo Server")
        print("   2. تحديث الصفحة في المتصفح (Ctrl+F5)")
        print("   3. Apps → UOM In PriceList → Upgrade")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()



