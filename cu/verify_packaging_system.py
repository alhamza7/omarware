#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص شامل لنظام Product Packaging في Odoo 19
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص نظام Product Packaging في Odoo 19")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. البحث عن جميع Models المتعلقة بـ package
    print("=" * 80)
    print("1️⃣ البحث عن Package/Packaging Models")
    print("=" * 80 + "\n")
    
    all_models = models.execute_kw(db, uid, password,
        'ir.model', 'search_read',
        [[['model', 'ilike', 'pack']]],
        {'fields': ['model', 'name']})
    
    if all_models:
        print("Models المتعلقة بـ package/packaging:")
        for model in all_models:
            print(f"   📦 {model['model']} - {model['name']}")
        print()
    else:
        print("❌ لا توجد models packaging!\n")
    
    # 2. فحص product.uom بالتفصيل
    print("=" * 80)
    print("2️⃣ فحص product.uom")
    print("=" * 80 + "\n")
    
    # جلب حقول product.uom
    uom_fields = models.execute_kw(db, uid, password,
        'product.uom', 'fields_get', [],
        {'attributes': ['string', 'type', 'relation']})
    
    print("حقول product.uom:\n")
    for field_name, field_info in list(uom_fields.items())[:15]:
        relation = f" → {field_info.get('relation')}" if field_info.get('relation') else ""
        print(f"   📌 {field_name}: {field_info.get('string')} ({field_info.get('type')}){relation}")
    
    # عد السجلات
    uom_count = models.execute_kw(db, uid, password,
        'product.uom', 'search_count', [[]])
    print(f"\nعدد سجلات product.uom: {uom_count}\n")
    
    if uom_count > 0:
        # جلب عينة
        uom_samples = models.execute_kw(db, uid, password,
            'product.uom', 'search_read', [[]],
            {'fields': ['product_id', 'uom_id', 'qty', 'name', 'barcode'], 'limit': 5})
        
        print("عينة من product.uom:")
        for sample in uom_samples:
            prod = sample.get('product_id', ['N/A'])[1] if sample.get('product_id') else 'N/A'
            uom = sample.get('uom_id', ['N/A'])[1] if sample.get('uom_id') else 'N/A'
            print(f"   • Product: {prod}")
            print(f"     UoM: {uom}")
            print(f"     Qty: {sample.get('qty', 'N/A')}")
            print(f"     Name: {sample.get('name', 'N/A')}")
            print(f"     Barcode: {sample.get('barcode', 'N/A')}")
            print()
    
    # 3. محاولة إنشاء packaging تجريبي
    print("=" * 80)
    print("3️⃣ محاولة إنشاء Packaging تجريبي")
    print("=" * 80 + "\n")
    
    # جلب منتج للاختبار
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name', 'default_code', 'uom_id'], 'limit': 1})
    
    if products:
        product = products[0]
        print(f"المنتج التجريبي: {product['name']} ({product['default_code']})")
        
        base_uom = product.get('uom_id', [False, 'كغم'])
        print(f"الوحدة الأساسية: {base_uom[1]}\n")
        
        # محاولة إنشاء packaging
        print("محاولة إنشاء packaging...")
        
        # جلب UoM للنصف كيلو
        half_uom = models.execute_kw(db, uid, password,
            'uom.uom', 'search_read',
            [[['name', 'ilike', '0.5'], ['active', '=', True]]],
            {'fields': ['id', 'name'], 'limit': 1})
        
        if half_uom:
            try:
                # محاولة إنشاء product.uom (packaging)
                pkg_data = {
                    'product_id': product['id'],
                    'uom_id': half_uom[0]['id'],
                    'qty': 1.0,
                    'name': "علبة متوسطة (0.5 كغم)",
                    'barcode': f"{product['default_code']}-500G",
                }
                
                pkg_id = models.execute_kw(db, uid, password,
                    'product.uom', 'create',
                    [pkg_data])
                
                print(f"✅ تم إنشاء Packaging!")
                print(f"   ID: {pkg_id}")
                print(f"   الاسم: علبة متوسطة (0.5 كغم)")
                print(f"   الباركود: {product['default_code']}-500G\n")
                
                # التحقق
                created = models.execute_kw(db, uid, password,
                    'product.uom', 'read',
                    [[pkg_id]],
                    {'fields': ['name', 'barcode', 'qty', 'product_id', 'uom_id']})
                
                if created:
                    print("تفاصيل Packaging المُنشأ:")
                    for key, value in created[0].items():
                        print(f"   {key}: {value}")
                
            except Exception as e:
                print(f"❌ فشل إنشاء Packaging: {e}\n")
        else:
            print("⚠️ لم يتم العثور على UoM للنصف كيلو\n")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

