#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص حالة تثبيت uom_in_pricelist
"""

import xmlrpc.client
import time

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص حالة التثبيت")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول - Odoo قد يكون قيد إعادة التشغيل")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # فحص حالة الوحدة
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if module_ids:
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['name', 'state', 'shortdesc']})[0]
        
        state = module['state']
        print(f"الوحدة: {module['shortdesc']}")
        print(f"الحالة: {state}\n")
        
        if state == 'installed':
            print("🎉 ✅ التثبيت نجح!\n")
            
            # اختبار الميزة
            print("=" * 80)
            print("اختبار الميزة")
            print("=" * 80)
            
            # فحص الحقول
            fields_info = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'fields_get',
                [], {'attributes': ['string', 'type']})
            
            if 'product_uom_id' in fields_info:
                print("\n✅ حقل product_uom_id موجود!")
                print(f"   النوع: {fields_info['product_uom_id'].get('type')}")
                print(f"   العنوان: {fields_info['product_uom_id'].get('string')}\n")
                
                print("=" * 80)
                print("الخطوات التالية")
                print("=" * 80)
                print("""
1. افتح Odoo في المتصفح
2. اذهب إلى: Sales → Configuration → Pricelists
3. افتح "SAP Price List 1"
4. اضغط Edit
5. أضف Price Rule جديد
6. اختر منتج
7. سترى حقل "Unit of Measure" ✨
8. اختر UoM (مثلاً: نصف كيلو)
9. حدد السعر
10. Save

الآن يمكنك:
• تحديد أسعار مختلفة لوحدات قياس مختلفة
• في Sales Order، عند اختيار UoM، السعر يتغير تلقائياً!
""")
            else:
                print("⚠️ حقل product_uom_id غير موجود!")
                print("   قد تحتاج إعادة تشغيل Odoo\n")
        
        elif state == 'to install':
            print("⚠️ الوحدة في انتظار التثبيت")
            print("   أعد تشغيل Odoo لإتمام التثبيت\n")
        
        elif state == 'to upgrade':
            print("⚠️ الوحدة في انتظار الترقية")
            print("   أعد تشغيل Odoo لإتمام الترقية\n")
        
        elif state == 'uninstalled':
            print("❌ التثبيت فشل!")
            print("   الوحدة ما زالت غير مثبتة\n")
            print("جرب:")
            print("  1. إعادة تشغيل Odoo")
            print("  2. Apps → Update Apps List")
            print("  3. ابحث عن 'UOM In PriceList'")
            print("  4. Install من الواجهة\n")
    else:
        print("❌ الوحدة غير موجودة في القائمة!")

except Exception as e:
    print(f"❌ خطأ: {e}")

