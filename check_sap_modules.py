#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص وحدات SAP المثبتة والنماذج المتاحة
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص وحدات SAP والنماذج")
print("=" * 80)

try:
    # الاتصال بـ Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ تم الاتصال بنجاح\n")
    
    # 1. فحص الوحدات المثبتة المتعلقة بـ SAP
    print("=" * 80)
    print("1️⃣ وحدات SAP المثبتة")
    print("=" * 80)
    
    modules = models.execute_kw(db, uid, password,
        'ir.module.module', 'search_read',
        [[['name', 'ilike', 'sap']]],
        {'fields': ['name', 'state', 'shortdesc', 'installed_version']})
    
    if modules:
        for module in modules:
            state_emoji = "✅" if module['state'] == 'installed' else "❌"
            print(f"\n{state_emoji} {module['name']}")
            print(f"   الاسم: {module.get('shortdesc', 'N/A')}")
            print(f"   الحالة: {module['state']}")
            print(f"   الإصدار: {module.get('installed_version', 'N/A')}")
    else:
        print("❌ لا توجد وحدات SAP مثبتة!")
    
    # 2. فحص جميع النماذج المتاحة المتعلقة بـ SAP
    print("\n" + "=" * 80)
    print("2️⃣ النماذج (Models) المتاحة المتعلقة بـ SAP")
    print("=" * 80)
    
    all_models = models.execute_kw(db, uid, password,
        'ir.model', 'search_read',
        [[['model', 'ilike', 'sap']]],
        {'fields': ['model', 'name', 'info']})
    
    if all_models:
        print(f"عدد النماذج المتعلقة بـ SAP: {len(all_models)}\n")
        for model in all_models:
            print(f"📋 {model['model']}")
            print(f"   الاسم: {model.get('name', 'N/A')}")
            if model.get('info'):
                print(f"   معلومات: {model['info'][:100]}...")
            print()
    else:
        print("❌ لا توجد نماذج SAP متاحة!")
    
    # 3. فحص النماذج المتاحة بشكل عام (كل شيء)
    print("=" * 80)
    print("3️⃣ عينة من جميع النماذج المتاحة")
    print("=" * 80)
    
    # نحصل على قائمة بجميع النماذج
    try:
        # طريقة بديلة - فحص ir.model
        model_count = models.execute_kw(db, uid, password,
            'ir.model', 'search_count', [[]])
        print(f"إجمالي عدد النماذج في النظام: {model_count}\n")
        
        # البحث عن أي نماذج تحتوي على product أو price أو foreign
        relevant_models = models.execute_kw(db, uid, password,
            'ir.model', 'search_read',
            [[['model', 'in', ['product.product', 'product.template', 
                               'product.pricelist', 'product.pricelist.item',
                               'product.uom', 'uom.uom']]]],
            {'fields': ['model', 'name']})
        
        print("النماذج المتعلقة بالمنتجات ووحدات القياس:")
        for model in relevant_models:
            print(f"   ✅ {model['model']} - {model['name']}")
            
    except Exception as e:
        print(f"⚠️ خطأ في جلب النماذج: {e}")
    
    # 4. فحص حقول product.product بالتفصيل
    print("\n" + "=" * 80)
    print("4️⃣ حقول product.product المتاحة")
    print("=" * 80)
    
    try:
        fields_info = models.execute_kw(db, uid, password,
            'product.product', 'fields_get', [],
            {'attributes': ['string', 'type', 'help']})
        
        # عرض الحقول المهمة فقط
        important_keywords = ['foreign', 'sap', 'price', 'uom', 'name']
        print("الحقول المهمة في product.product:\n")
        
        relevant_fields = []
        for field_name, field_info in fields_info.items():
            for keyword in important_keywords:
                if keyword in field_name.lower():
                    relevant_fields.append((field_name, field_info))
                    break
        
        # ترتيب وعرض
        for field_name, field_info in sorted(relevant_fields):
            print(f"   📌 {field_name}")
            print(f"      النوع: {field_info.get('type', 'N/A')}")
            print(f"      العنوان: {field_info.get('string', 'N/A')}")
            if field_info.get('help'):
                print(f"      المساعدة: {field_info['help'][:100]}")
            print()
            
    except Exception as e:
        print(f"❌ خطأ في جلب حقول product.product: {e}")
    
    # 5. فحص الوحدات في addons
    print("\n" + "=" * 80)
    print("5️⃣ البحث عن ملفات SAP في المجلد addons")
    print("=" * 80)
    
    import os
    addons_path = "L:\\Lugal-ai\\addons"
    
    if os.path.exists(addons_path):
        sap_folders = []
        for item in os.listdir(addons_path):
            item_path = os.path.join(addons_path, item)
            if os.path.isdir(item_path) and 'sap' in item.lower():
                sap_folders.append(item)
        
        if sap_folders:
            print("المجلدات المتعلقة بـ SAP في addons:")
            for folder in sap_folders:
                folder_path = os.path.join(addons_path, folder)
                print(f"\n   📁 {folder}")
                
                # فحص وجود __manifest__.py
                manifest_path = os.path.join(folder_path, '__manifest__.py')
                if os.path.exists(manifest_path):
                    print(f"      ✅ يحتوي على __manifest__.py")
                    
                    # قراءة محتوى الـ manifest
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # البحث عن اسم الوحدة
                            if "'name'" in content or '"name"' in content:
                                lines = content.split('\n')
                                for line in lines[:20]:  # أول 20 سطر
                                    if 'name' in line.lower() and (':' in line or '=' in line):
                                        print(f"      {line.strip()}")
                                        break
                    except Exception as e:
                        print(f"      ⚠️ خطأ في قراءة manifest: {e}")
                else:
                    print(f"      ❌ لا يحتوي على __manifest__.py")
        else:
            print("❌ لا توجد مجلدات SAP في addons")
    else:
        print(f"❌ المسار غير موجود: {addons_path}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

