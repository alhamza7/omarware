#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث عبر Odoo API باستخدام SQL مباشر
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("تحديث Foreign Name والأسعار عبر Odoo")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل بـ Odoo\n")
    
    # سنستخدم compute method لتنفيذ عمليات SQL
    # أولاً: جلب البيانات ثم التحديث بشكل دفعات
    
    print("=" * 80)
    print("1️⃣ جلب البيانات من SAP Extended")
    print("=" * 80)
    
    # جلب المنتجات التي تحتاج تحديث
    sap_data = models.execute_kw(db, uid, password,
        'sap.product.extended', 'search_read',
        [[['product_id', '!=', False], ['foreign_name', '!=', False]]],
        {'fields': ['product_id', 'foreign_name']})
    
    print(f"عدد السجلات: {len(sap_data)}\n")
    
    # التحديث بدفعات
    print("=" * 80)
    print("2️⃣ تحديث Foreign Name")
    print("=" * 80)
    
    batch_size = 100
    updated_count = 0
    
    for i in range(0, len(sap_data), batch_size):
        batch = sap_data[i:i+batch_size]
        
        for item in batch:
            product_id = item['product_id'][0]
            foreign_name = item['foreign_name']
            
            try:
                models.execute_kw(db, uid, password,
                    'product.product', 'write',
                    [[product_id], {'foreign_name': foreign_name}])
                updated_count += 1
            except:
                pass
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"   تم معالجة {updated_count} منتج...")
    
    print(f"✅ تم تحديث {updated_count} منتج\n")
    
    # تحديث الأسعار
    print("=" * 80)
    print("3️⃣ تحديث الأسعار")
    print("=" * 80)
    
    # جلب قائمة الأسعار
    pricelist = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', '=', 'SAP Price List 1']]],
        {'fields': ['id'], 'limit': 1})
    
    if pricelist:
        # جلب عناصر الأسعار
        items = models.execute_kw(db, uid, password,
            'product.pricelist.item', 'search_read',
            [[['pricelist_id', '=', pricelist[0]['id']], ['fixed_price', '>', 0]]],
            {'fields': ['product_id', 'fixed_price']})
        
        print(f"عدد الأسعار: {len(items)}")
        
        price_updated = 0
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            for item in batch:
                if item.get('product_id'):
                    product_id = item['product_id'][0]
                    price = item['fixed_price']
                    
                    try:
                        models.execute_kw(db, uid, password,
                            'product.product', 'write',
                            [[product_id], {'list_price': price}])
                        price_updated += 1
                    except:
                        pass
            
            if (i // batch_size + 1) % 10 == 0:
                print(f"   تم معالجة {price_updated} سعر...")
        
        print(f"✅ تم تحديث {price_updated} سعر\n")
    
    # عرض النتائج
    print("=" * 80)
    print("✅ النتائج النهائية")
    print("=" * 80)
    
    with_foreign = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['foreign_name', '!=', False]]])
    
    with_price = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['list_price', '>', 0]]])
    
    print(f"منتجات لديها Foreign Name: {with_foreign}")
    print(f"منتجات لديها سعر > 0: {with_price}")
    
    # عينة
    print("\nعينة:")
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['foreign_name', '!=', False]]],
        {'fields': ['name', 'default_code', 'foreign_name', 'list_price'], 'limit': 3})
    
    for p in products:
        print(f"\n📦 {p['name']} ({p['default_code']})")
        print(f"   Foreign: {p['foreign_name']}")
        print(f"   السعر: {p['list_price']}")
    
    print("\n" + "=" * 80)
    print("✅ تم بنجاح!")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

