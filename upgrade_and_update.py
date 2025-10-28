#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ترقية وحدة SAP وتشغيل التحديث السريع
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("ترقية SAP Integration وتشغيل التحديث")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل بـ Odoo\n")
    
    # 1. ترقية الوحدة
    print("=" * 80)
    print("1️⃣ ترقية وحدة SAP Integration")
    print("=" * 80)
    
    try:
        # البحث عن الوحدة
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[['name', '=', 'sap_integration']]])
        
        if module_ids:
            print("تحديث الوحدة...")
            
            # تحديث قائمة الوحدات
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            
            print("✅ تمت ترقية الوحدة\n")
        else:
            print("⚠️ الوحدة غير موجودة\n")
    except Exception as e:
        print(f"⚠️ خطأ في الترقية: {e}")
        print("سنحاول المتابعة...\n")
    
    # 2. إنشاء وتشغيل الـ wizard
    print("=" * 80)
    print("2️⃣ تشغيل Quick Product Update")
    print("=" * 80)
    
    try:
        # إنشاء wizard
        wizard_id = models.execute_kw(db, uid, password,
            'sap.quick.product.update', 'create',
            [{}])
        
        print(f"تم إنشاء Wizard (ID: {wizard_id})")
        
        # تشغيل التحديث
        print("تنفيذ التحديث...")
        
        result = models.execute_kw(db, uid, password,
            'sap.quick.product.update', 'action_update_products',
            [[wizard_id]])
        
        # قراءة النتيجة
        wizard_data = models.execute_kw(db, uid, password,
            'sap.quick.product.update', 'read',
            [[wizard_id]],
            {'fields': ['result_message', 'state']})
        
        if wizard_data:
            print("\n" + "=" * 80)
            print("النتائج")
            print("=" * 80)
            print(wizard_data[0].get('result_message', 'لا توجد رسالة'))
            print(f"\nالحالة: {wizard_data[0].get('state', 'N/A')}")
        
        print("\n✅ تم التحديث بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في التحديث: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

