#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نقل البيانات من SAP Extended إلى المنتجات
ربط foreign_name والأسعار ووحدات القياس
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("نقل البيانات من SAP إلى المنتجات")
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
    
    # 1. فحص الحقول المتاحة في sap.product.extended
    print("=" * 80)
    print("1️⃣ فحص الحقول المتاحة في sap.product.extended")
    print("=" * 80)
    
    extended_fields = models.execute_kw(db, uid, password,
        'sap.product.extended', 'fields_get', [],
        {'attributes': ['string', 'type']})
    
    print("الحقول المتاحة:")
    important_fields = []
    for field_name, field_info in extended_fields.items():
        if any(keyword in field_name.lower() for keyword in ['foreign', 'name', 'code', 'product', 'price', 'uom']):
            print(f"   - {field_name}: {field_info.get('string', 'N/A')} ({field_info.get('type', 'N/A')})")
            important_fields.append(field_name)
    print()
    
    # 2. جلب عينة من البيانات
    print("=" * 80)
    print("2️⃣ عينة من البيانات في sap.product.extended")
    print("=" * 80)
    
    # استخدام الحقول المتاحة فقط
    available_fields = ['product_id', 'foreign_name']
    if 'sap_code' in extended_fields:
        available_fields.append('sap_code')
    if 'item_code' in extended_fields:
        available_fields.append('item_code')
    
    extended_data = models.execute_kw(db, uid, password,
        'sap.product.extended', 'search_read',
        [[['product_id', '!=', False]]],
        {'fields': available_fields, 'limit': 10})
    
    print(f"عدد السجلات المربوطة بمنتجات: {len(extended_data)}\n")
    
    for ext in extended_data:
        product_name = ext.get('product_id', ['N/A'])[1] if ext.get('product_id') else 'N/A'
        print(f"📦 {product_name}")
        print(f"   Foreign Name في SAP: {ext.get('foreign_name', 'N/A')}")
        if 'sap_code' in ext:
            print(f"   SAP Code: {ext.get('sap_code', 'N/A')}")
        if 'item_code' in ext:
            print(f"   Item Code: {ext.get('item_code', 'N/A')}")
        print()
    
    # 3. بدء نقل البيانات
    print("=" * 80)
    print("3️⃣ نقل Foreign Name من SAP Extended إلى المنتجات")
    print("=" * 80)
    
    # جلب جميع السجلات التي لديها foreign_name
    extended_with_foreign = models.execute_kw(db, uid, password,
        'sap.product.extended', 'search_read',
        [[['product_id', '!=', False], ['foreign_name', '!=', False]]],
        {'fields': ['product_id', 'foreign_name']})
    
    print(f"عدد السجلات التي لديها Foreign Name: {len(extended_with_foreign)}\n")
    
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, ext in enumerate(extended_with_foreign, 1):
        if i % 100 == 0:
            print(f"   معالجة السجل {i}/{len(extended_with_foreign)}...")
        
        product_id_tuple = ext.get('product_id')
        foreign_name = ext.get('foreign_name')
        
        if not product_id_tuple or not foreign_name:
            skipped_count += 1
            continue
        
        product_id = product_id_tuple[0]
        
        try:
            # تحديث المنتج
            models.execute_kw(db, uid, password,
                'product.product', 'write',
                [[product_id], {'foreign_name': foreign_name}])
            updated_count += 1
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # عرض أول 5 أخطاء فقط
                print(f"   ⚠️ خطأ في تحديث المنتج {product_id}: {str(e)[:100]}")
    
    print(f"\n✅ تم التحديث:")
    print(f"   ✅ نجح: {updated_count}")
    print(f"   ❌ فشل: {failed_count}")
    print(f"   ⏭️  تم تخطيه: {skipped_count}")
    
    # 4. نقل الأسعار من Pricelists إلى list_price
    print("\n" + "=" * 80)
    print("4️⃣ نقل الأسعار من SAP Price List 1 إلى list_price")
    print("=" * 80)
    
    # البحث عن SAP Price List 1
    pricelist = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', '=', 'SAP Price List 1']]],
        {'fields': ['id', 'item_ids'], 'limit': 1})
    
    if pricelist:
        pricelist_id = pricelist[0]['id']
        item_ids = pricelist[0].get('item_ids', [])
        
        print(f"عدد عناصر الأسعار في SAP Price List 1: {len(item_ids)}\n")
        
        if item_ids:
            # جلب العناصر
            items = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'read', [item_ids],
                {'fields': ['product_id', 'product_tmpl_id', 'fixed_price']})
            
            price_updated = 0
            price_failed = 0
            
            for i, item in enumerate(items, 1):
                if i % 100 == 0:
                    print(f"   معالجة السعر {i}/{len(items)}...")
                
                fixed_price = item.get('fixed_price', 0)
                product_id_tuple = item.get('product_id')
                
                # إذا كان السعر > 0 ويوجد product_id
                if fixed_price > 0 and product_id_tuple:
                    product_id = product_id_tuple[0]
                    
                    try:
                        models.execute_kw(db, uid, password,
                            'product.product', 'write',
                            [[product_id], {'list_price': fixed_price}])
                        price_updated += 1
                    except Exception as e:
                        price_failed += 1
                        if price_failed <= 5:
                            print(f"   ⚠️ خطأ في تحديث السعر للمنتج {product_id}: {str(e)[:100]}")
            
            print(f"\n✅ تم تحديث الأسعار:")
            print(f"   ✅ نجح: {price_updated}")
            print(f"   ❌ فشل: {price_failed}")
    else:
        print("⚠️ لم يتم العثور على SAP Price List 1")
    
    # 5. التحقق من النتائج
    print("\n" + "=" * 80)
    print("5️⃣ التحقق من النتائج")
    print("=" * 80)
    
    # إحصائيات بعد التحديث
    products_with_foreign = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['foreign_name', '!=', False], ['foreign_name', '!=', '']]])
    print(f"منتجات لديها Foreign Name الآن: {products_with_foreign}")
    
    products_with_price = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['list_price', '>', 0]]])
    print(f"منتجات لديها سعر > 0 الآن: {products_with_price}")
    
    # عينة من المنتجات المحدثة
    print("\nعينة من المنتجات بعد التحديث:")
    updated_products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['foreign_name', '!=', False]]],
        {'fields': ['name', 'default_code', 'foreign_name', 'list_price'], 'limit': 5})
    
    for product in updated_products:
        print(f"\n📦 {product.get('name', 'N/A')} ({product.get('default_code', 'N/A')})")
        print(f"   Foreign Name: ✅ {product.get('foreign_name', 'N/A')}")
        print(f"   السعر: {product.get('list_price', 0)}")
    
    print("\n" + "=" * 80)
    print("✅ انتهت عملية النقل")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

