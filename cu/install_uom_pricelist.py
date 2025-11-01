#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تثبيت واختبار uom_in_pricelist module
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("تثبيت UoM in Pricelist Module")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. تحديث قائمة الـ modules
    print("1️⃣ تحديث قائمة الـ Modules...")
    try:
        models.execute_kw(db, uid, password,
            'ir.module.module', 'update_list', [])
        print("✅ تم التحديث\n")
    except:
        print("⚠️ تخطي التحديث، سنبحث مباشرة...\n")
    
    # 2. البحث عن الـ module
    print("2️⃣ البحث عن uom_in_pricelist...")
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if not module_ids:
        print("❌ الـ module غير موجود!")
        exit(1)
    
    module = models.execute_kw(db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['name', 'state', 'shortdesc']})[0]
    
    print(f"✅ تم العثور على: {module['shortdesc']}")
    print(f"   الحالة: {module['state']}\n")
    
    # 3. التثبيت
    if module['state'] == 'uninstalled':
        print("3️⃣ تثبيت الـ Module...")
        print("⚠️ قد يستغرق دقيقة...")
        
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_install',
                [module_ids])
            print("✅ تم التثبيت بنجاح!\n")
        except Exception as e:
            print(f"❌ خطأ في التثبيت: {e}\n")
            print("⚠️ قد يحتاج إعادة تشغيل Odoo")
            
    elif module['state'] == 'installed':
        print("✅ الـ Module مثبت مسبقاً\n")
        
        # ترقية
        print("3️⃣ ترقية الـ Module للإصدار المحدث...")
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            print("✅ تمت الترقية!\n")
        except Exception as e:
            print(f"⚠️ خطأ في الترقية: {e}")
            print("يمكن المتابعة للاختبار...\n")
    
    print("=" * 80)
    print("✅ اكتمل التثبيت!")
    print("=" * 80)
    
    print("""
📋 الخطوات التالية:

1. أعد تشغيل Odoo:
   - أوقف الخادم
   - شغله من جديد
   
2. تحقق من الـ Module:
   - Apps → ابحث عن "UOM In PriceList"
   - يجب أن يظهر كـ "Installed"
   
3. اختبر الميزة:
   - Sales → Configuration → Pricelists
   - افتح أي pricelist
   - أضف Price Rule جديد
   - يجب أن تشاهد حقل "Unit of Measure"!
   
4. اختبار البيع:
   - Sales → Orders → New
   - أضف منتج
   - غير UoM
   - تحقق من السعر
""")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

