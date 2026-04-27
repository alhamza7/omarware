#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إلغاء وإعادة تثبيت uom_in_pricelist
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("إعادة تثبيت uom_in_pricelist")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # البحث عن الوحدة
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if not module_ids:
        print("❌ الوحدة غير موجودة!")
        exit(1)
    
    module = models.execute_kw(db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['name', 'state']})[0]
    
    print(f"الحالة الحالية: {module['state']}\n")
    
    # إلغاء طلب التثبيت
    if module['state'] in ['to install', 'to upgrade', 'to remove']:
        print("إلغاء طلب التثبيت السابق...")
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_uninstall_cancel',
                [module_ids])
            print("✅ تم الإلغاء\n")
        except:
            print("⚠️ لم يتم الإلغاء (قد لا يكون ضرورياً)\n")
    
    # محاولة التثبيت من جديد
    print("محاولة التثبيت...")
    try:
        models.execute_kw(db, uid, password,
            'ir.module.module', 'button_immediate_install',
            [module_ids])
        
        print("✅✅✅ نجح التثبيت!\n")
        
        # التحقق
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['state']})[0]
        
        print(f"الحالة الجديدة: {module['state']}\n")
        
        if module['state'] == 'installed':
            print("=" * 80)
            print("🎉 التثبيت نجح بالكامل!")
            print("=" * 80)
            print("""
يمكنك الآن:

1. اذهب إلى: Sales → Configuration → Pricelists
2. افتح أي pricelist
3. Edit → Add a line
4. اختر منتج
5. ستجد حقل "Unit of Measure" ✨
6. حدد UoM والسعر
7. Save

اختبار:
1. Sales → Orders → New
2. أضف منتج
3. غيّر UoM
4. السعر يتغير حسب القاعدة! ✨
""")
        else:
            print(f"⚠️ الحالة: {module['state']}")
            print("قد تحتاج إعادة تشغيل Odoo\n")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ فشل التثبيت!\n")
        
        # تحليل الخطأ
        if "ParseError" in error_msg and "xpath" in error_msg:
            print("⚠️ المشكلة: الـ View لا يتطابق مع Odoo 19")
            print("   يحتاج تعديل على الـ xpath\n")
        
        print("رسالة الخطأ (أول 500 حرف):")
        print(error_msg[:500])
        print("\n...")

except Exception as e:
    print(f"❌ خطأ: {e}")

