#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محاولة تثبيت الوحدة بطريقة بسيطة
"""

import xmlrpc.client
import time

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("تثبيت uom_in_pricelist")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # البحث عن الـ module
    print("البحث عن الوحدة...")
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if not module_ids:
        print("❌ الوحدة غير موجودة!")
        print("\nتأكد من:")
        print("  1. المجلد موجود في addons/uom_in_pricelist")
        print("  2. Odoo يقرأ من مسار addons الصحيح")
        exit(1)
    
    module = models.execute_kw(db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['name', 'state', 'shortdesc', 'latest_version']})[0]
    
    print(f"✅ الوحدة: {module['shortdesc']}")
    print(f"   الإصدار: {module.get('latest_version', 'N/A')}")
    print(f"   الحالة: {module['state']}\n")
    
    if module['state'] == 'uninstalled':
        print("محاولة التثبيت...")
        print("⚠️ هذا قد يستغرق 1-2 دقيقة...\n")
        
        # محاولة button_install
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_install',
                [module_ids])
            
            print("✅ تم إرسال طلب التثبيت!")
            print("\n⚠️ ملاحظة:")
            print("   - قد تحتاج إعادة تحميل الصفحة في Odoo")
            print("   - أو إعادة تشغيل Odoo")
            print("   - تحقق من Apps للتأكد من التثبيت\n")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ خطأ في التثبيت!\n")
            
            # استخراج الخطأ الحقيقي
            if "KeyError" in error_msg:
                print("⚠️ المشكلة: حقل غير موجود في Odoo 19")
                print("   الحل: يجب تصحيح الكود\n")
            elif "ValidationError" in error_msg:
                print("⚠️ المشكلة: خطأ في البيانات")
            else:
                print(f"⚠️ الخطأ: {error_msg[:500]}\n")
            
            print("=" * 80)
            print("الحل البديل:")
            print("=" * 80)
            print("""
1. افتح Odoo في المتصفح
2. اذهب إلى Settings → Activate Developer Mode
3. اذهب إلى Apps → Update Apps List  
4. ابحث عن "UOM In PriceList"
5. حاول Install من الواجهة
6. ستظهر رسالة الخطأ بوضوح أكثر
""")
    
    elif module['state'] == 'installed':
        print("✅ الوحدة مثبتة مسبقاً!\n")
        print("يمكنك استخدامها الآن:")
        print("  Sales → Configuration → Pricelists")
        print("  → افتح أي pricelist")
        print("  → أضف Price Rule")
        print("  → ستجد حقل 'Unit of Measure'\n")
    
    elif module['state'] == 'to install':
        print("⚠️ الوحدة في انتظار التثبيت")
        print("   أعد تشغيل Odoo لإتمام التثبيت\n")
    
    elif module['state'] == 'to upgrade':
        print("⚠️ الوحدة في انتظار الترقية")
        print("   أعد تشغيل Odoo لإتمام الترقية\n")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

