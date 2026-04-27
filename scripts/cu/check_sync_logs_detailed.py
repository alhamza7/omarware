#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص تفصيلي لسجلات المزامنة ومجموعات UoM
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص سجلات المزامنة ومجموعات UoM")
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
    
    # 1. فحص سجلات المزامنة بالتفصيل
    print("=" * 80)
    print("1️⃣ سجلات المزامنة (17 سجل)")
    print("=" * 80)
    
    logs = models.execute_kw(db, uid, password,
        'sap.sync.log', 'search_read', [[]],
        {'fields': ['model_name', 'operation', 'status', 'message', 'create_date',
                   'error_type', 'error_traceback'], 
         'order': 'create_date desc'})
    
    if logs:
        print(f"إجمالي السجلات: {len(logs)}\n")
        
        for i, log in enumerate(logs, 1):
            status_emoji = "✅" if log.get('status') == 'success' else "❌"
            print(f"{status_emoji} [{i}] {log.get('create_date', 'N/A')}")
            print(f"      النموذج: {log.get('model_name', 'N/A')}")
            print(f"      العملية: {log.get('operation', 'N/A')}")
            print(f"      الحالة: {log.get('status', 'N/A')}")
            
            message = log.get('message', '')
            if message:
                # عرض أول 200 حرف من الرسالة
                print(f"      الرسالة: {message[:200]}")
                if len(message) > 200:
                    print(f"               ...")
            
            if log.get('error_type'):
                print(f"      نوع الخطأ: {log.get('error_type', 'N/A')}")
            
            if log.get('error_traceback'):
                traceback = log.get('error_traceback', '')[:200]
                print(f"      التتبع: {traceback}...")
            
            print()
    
    # 2. فحص مجموعات UoM بالتفصيل
    print("\n" + "=" * 80)
    print("2️⃣ مجموعات UoM من SAP (169 مجموعة)")
    print("=" * 80)
    
    # أولاً: فحص الحقول المتاحة
    uom_group_fields = models.execute_kw(db, uid, password,
        'sap.uom.group', 'fields_get', [],
        {'attributes': ['string', 'type']})
    
    print("الحقول المتاحة في sap.uom.group:")
    for field_name, field_info in list(uom_group_fields.items())[:15]:
        print(f"   - {field_name}: {field_info.get('string', 'N/A')} ({field_info.get('type', 'N/A')})")
    print()
    
    # الآن جلب البيانات بالحقول الصحيحة
    uom_groups = models.execute_kw(db, uid, password,
        'sap.uom.group', 'search_read', [[]],
        {'fields': ['name', 'uom_ids'], 'limit': 10})
    
    print(f"عينة من مجموعات UoM:\n")
    for group in uom_groups:
        print(f"📏 {group.get('name', 'N/A')}")
        uom_ids = group.get('uom_ids', [])
        print(f"   عدد الوحدات: {len(uom_ids)}")
        
        if uom_ids:
            # جلب معلومات الوحدات
            try:
                uoms = models.execute_kw(db, uid, password,
                    'uom.uom', 'read', [uom_ids],
                    {'fields': ['name', 'uom_type', 'factor', 'category_id']})
                
                for uom in uoms[:3]:  # أول 3 وحدات فقط
                    category = uom.get('category_id', ['N/A'])[1] if uom.get('category_id') else 'N/A'
                    print(f"      - {uom.get('name', 'N/A')}: {uom.get('uom_type', 'N/A')} "
                          f"(معامل: {uom.get('factor', 'N/A')}, فئة: {category})")
            except Exception as e:
                print(f"      ⚠️ خطأ في جلب الوحدات: {e}")
        print()
    
    # 3. فحص إحصائيات المنتجات
    print("\n" + "=" * 80)
    print("3️⃣ إحصائيات المنتجات")
    print("=" * 80)
    
    total_products = models.execute_kw(db, uid, password,
        'product.product', 'search_count', [[]])
    print(f"إجمالي المنتجات: {total_products}")
    
    products_with_foreign = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['foreign_name', '!=', False], ['foreign_name', '!=', '']]])
    print(f"منتجات لديها Foreign Name: {products_with_foreign}")
    
    products_with_code = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['default_code', '!=', False]]])
    print(f"منتجات لديها كود (default_code): {products_with_code}")
    
    # 4. فحص SAP Backend Config
    print("\n" + "=" * 80)
    print("4️⃣ فحص إعدادات SAP Backend")
    print("=" * 80)
    
    try:
        # فحص الحقول أولاً
        backend_fields = models.execute_kw(db, uid, password,
            'sap.backend', 'fields_get', [],
            {'attributes': ['string', 'type']})
        
        print("الحقول المتاحة في sap.backend:")
        for field_name in list(backend_fields.keys())[:20]:
            print(f"   - {field_name}: {backend_fields[field_name].get('string', 'N/A')}")
        print()
        
        # جلب البيانات بالحقول الصحيحة
        backends = models.execute_kw(db, uid, password,
            'sap.backend', 'search_read', [[]],
            {'fields': ['name', 'active']})
        
        if backends:
            print(f"عدد الـ Backends: {len(backends)}\n")
            for backend in backends:
                active_emoji = "✅" if backend.get('active') else "❌"
                print(f"{active_emoji} {backend.get('name', 'N/A')}")
        else:
            print("❌ لا توجد Backends معرفة")
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
    
    # 5. فحص عينة من المنتجات والأسعار
    print("\n" + "=" * 80)
    print("5️⃣ عينة من المنتجات والأسعار")
    print("=" * 80)
    
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read', [[]],
        {'fields': ['name', 'default_code', 'foreign_name', 'list_price', 'uom_id'], 'limit': 5})
    
    for product in products:
        print(f"\n📦 {product.get('name', 'N/A')} ({product.get('default_code', 'N/A')})")
        print(f"   Foreign Name: {product.get('foreign_name', '❌ غير موجود')}")
        print(f"   السعر: {product.get('list_price', 'N/A')}")
        uom_name = product.get('uom_id', ['N/A'])[1] if product.get('uom_id') else 'N/A'
        print(f"   الوحدة: {uom_name}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

