#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص حالة Complete Migration والبيانات التي تم نقلها
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص حالة Complete Migration من SAP")
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
    
    # 1. فحص سجلات Complete Migration
    print("=" * 80)
    print("1️⃣ سجلات Complete Migration")
    print("=" * 80)
    
    try:
        migration_count = models.execute_kw(db, uid, password,
            'sap.product.complete.migration', 'search_count', [[]])
        print(f"عدد سجلات Complete Migration: {migration_count}\n")
        
        if migration_count > 0:
            migrations = models.execute_kw(db, uid, password,
                'sap.product.complete.migration', 'search_read', [[]],
                {'fields': ['state', 'create_date', 'products_migrated', 'migration_log'], 
                 'order': 'create_date desc', 'limit': 5})
            
            for i, migration in enumerate(migrations, 1):
                print(f"\n[{i}] التاريخ: {migration.get('create_date', 'N/A')}")
                print(f"    الحالة: {migration.get('state', 'N/A')}")
                print(f"    المنتجات المنقولة: {migration.get('products_migrated', 0)}")
                
                log = migration.get('migration_log', '')
                if log:
                    # عرض آخر 300 حرف من السجل
                    log_preview = log[-300:] if len(log) > 300 else log
                    print(f"    آخر سطور السجل:")
                    for line in log_preview.split('\n')[-5:]:
                        if line.strip():
                            print(f"      {line[:100]}")
        else:
            print("⚠️ لا توجد سجلات Complete Migration!")
    except Exception as e:
        print(f"❌ خطأ في الوصول لـ sap.product.complete.migration: {e}")
    
    # 2. فحص البيانات في المنتجات بعد Migration
    print("\n" + "=" * 80)
    print("2️⃣ فحص بيانات المنتجات بعد Migration")
    print("=" * 80)
    
    # إحصائيات عامة
    total_products = models.execute_kw(db, uid, password,
        'product.product', 'search_count', [[]])
    print(f"إجمالي المنتجات: {total_products}")
    
    products_with_foreign = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['foreign_name', '!=', False], ['foreign_name', '!=', '']]])
    print(f"منتجات لديها Foreign Name: {products_with_foreign}")
    
    products_with_price = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['list_price', '>', 0]]])
    print(f"منتجات لديها سعر > 0: {products_with_price}")
    
    # 3. فحص عينة من المنتجات بالتفصيل
    print("\n" + "=" * 80)
    print("3️⃣ عينة من المنتجات (أول 10 منتجات)")
    print("=" * 80)
    
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read', [[]],
        {'fields': ['name', 'default_code', 'foreign_name', 'list_price', 
                   'standard_price', 'uom_id'], 'limit': 10})
    
    for product in products:
        print(f"\n📦 {product.get('name', 'N/A')}")
        print(f"   الكود: {product.get('default_code', 'N/A')}")
        print(f"   Foreign Name: {product.get('foreign_name') or '❌ غير موجود'}")
        print(f"   سعر البيع: {product.get('list_price', 0)}")
        print(f"   التكلفة: {product.get('standard_price', 0)}")
        uom = product.get('uom_id', ['N/A'])[1] if product.get('uom_id') else 'N/A'
        print(f"   الوحدة: {uom}")
    
    # 4. فحص الأسعار في Pricelists
    print("\n" + "=" * 80)
    print("4️⃣ فحص الأسعار في Pricelists")
    print("=" * 80)
    
    pricelists = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read', [[]],
        {'fields': ['name', 'currency_id', 'item_ids']})
    
    for pricelist in pricelists:
        item_count = len(pricelist.get('item_ids', []))
        currency = pricelist.get('currency_id', ['N/A'])[1] if pricelist.get('currency_id') else 'N/A'
        print(f"\n💰 {pricelist.get('name', 'N/A')} ({currency})")
        print(f"   عدد العناصر: {item_count}")
        
        if item_count > 0:
            # جلب عينة من العناصر
            items = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'read', [pricelist['item_ids'][:3]],
                {'fields': ['product_tmpl_id', 'product_id', 'fixed_price', 'min_quantity']})
            
            for item in items:
                product_name = 'عام'
                if item.get('product_id'):
                    product_name = item['product_id'][1]
                elif item.get('product_tmpl_id'):
                    product_name = item['product_tmpl_id'][1]
                
                price = item.get('fixed_price', 0)
                min_qty = item.get('min_quantity', 1)
                print(f"      - {product_name}: {price} (حد أدنى: {min_qty})")
    
    # 5. فحص SAP Product Extended
    print("\n" + "=" * 80)
    print("5️⃣ فحص SAP Product Extended (البيانات الموسعة)")
    print("=" * 80)
    
    try:
        extended_count = models.execute_kw(db, uid, password,
            'sap.product.extended', 'search_count', [[]])
        print(f"عدد سجلات SAP Product Extended: {extended_count}\n")
        
        if extended_count > 0:
            extended = models.execute_kw(db, uid, password,
                'sap.product.extended', 'search_read', [[]],
                {'fields': ['product_id', 'foreign_name', 'material_description'], 'limit': 5})
            
            for ext in extended:
                product_name = ext.get('product_id', ['N/A'])[1] if ext.get('product_id') else 'N/A'
                print(f"📦 {product_name}")
                print(f"   Foreign Name: {ext.get('foreign_name', 'N/A')}")
                print(f"   Description: {ext.get('material_description', 'N/A')}\n")
        else:
            print("⚠️ لا توجد بيانات SAP Product Extended")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.product.extended: {e}")
    
    # 6. فحص SAP Product Binding
    print("\n" + "=" * 80)
    print("6️⃣ فحص SAP Product Binding (الربط مع SAP)")
    print("=" * 80)
    
    try:
        binding_count = models.execute_kw(db, uid, password,
            'sap.product.product', 'search_count', [[]])
        print(f"عدد منتجات SAP المربوطة: {binding_count}\n")
        
        if binding_count > 0:
            bindings = models.execute_kw(db, uid, password,
                'sap.product.product', 'search_read', [[]],
                {'fields': ['product_id', 'external_id', 'sync_status'], 'limit': 5})
            
            for binding in bindings:
                product_name = binding.get('product_id', ['N/A'])[1] if binding.get('product_id') else 'N/A'
                print(f"📦 {product_name}")
                print(f"   SAP ID: {binding.get('external_id', 'N/A')}")
                print(f"   حالة المزامنة: {binding.get('sync_status', 'N/A')}\n")
        else:
            print("⚠️ لا توجد منتجات مربوطة مع SAP")
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
    
    # 7. فحص Product UoM (وحدات القياس للمنتجات)
    print("\n" + "=" * 80)
    print("7️⃣ فحص وحدات القياس المتعددة للمنتجات")
    print("=" * 80)
    
    # فحص منتج واحد بالتفصيل
    product_ids = models.execute_kw(db, uid, password,
        'product.product', 'search', [[['default_code', '=', 'ADF00001']]])
    
    if product_ids:
        product = models.execute_kw(db, uid, password,
            'product.product', 'read', [product_ids[0]],
            {'fields': ['name', 'default_code', 'uom_id', 'uom_po_id', 'product_tmpl_id']})[0]
        
        print(f"فحص المنتج: {product.get('name', 'N/A')} ({product.get('default_code', 'N/A')})\n")
        print(f"   وحدة البيع: {product.get('uom_id', ['N/A'])[1] if product.get('uom_id') else 'N/A'}")
        print(f"   وحدة الشراء: {product.get('uom_po_id', ['N/A'])[1] if product.get('uom_po_id') else 'N/A'}")
        
        # البحث عن أسعار بوحدات مختلفة
        tmpl_id = product['product_tmpl_id'][0] if product.get('product_tmpl_id') else None
        if tmpl_id:
            pricelist_items = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'search_read',
                [[['product_tmpl_id', '=', tmpl_id]]],
                {'fields': ['pricelist_id', 'fixed_price', 'min_quantity']})
            
            if pricelist_items:
                print(f"\n   الأسعار في قوائم الأسعار:")
                for item in pricelist_items:
                    pricelist_name = item.get('pricelist_id', ['N/A'])[1] if item.get('pricelist_id') else 'N/A'
                    print(f"      - {pricelist_name}: {item.get('fixed_price', 0)} (حد أدنى: {item.get('min_quantity', 1)})")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)
    
    # ملخص المشاكل
    print("\n" + "=" * 80)
    print("📋 ملخص المشاكل المكتشفة")
    print("=" * 80)
    
    if products_with_foreign == 0:
        print("❌ لا توجد منتجات لديها Foreign Name")
    else:
        print(f"✅ {products_with_foreign} منتج لديه Foreign Name")
    
    if products_with_price == 0:
        print("❌ جميع المنتجات بسعر 0")
    else:
        print(f"⚠️ {products_with_price} منتج فقط لديه سعر > 0 من أصل {total_products}")

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

