#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص شامل لبيانات المنتجات: foreign name، الأسعار، ووحدات القياس
"""

import xmlrpc.client
import ssl

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص بيانات المنتجات الشامل")
print("=" * 80)

try:
    # الاتصال بـ Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ تم الاتصال بنجاح - User ID: {uid}\n")
    
    # 1. فحص حقل foreign_name في المنتجات
    print("=" * 80)
    print("1️⃣ فحص حقل Foreign Name في المنتجات")
    print("=" * 80)
    
    # البحث عن المنتجات
    product_ids = models.execute_kw(db, uid, password,
        'product.product', 'search', [[]], {'limit': 10})
    
    # أولاً: فحص الحقول المتاحة
    try:
        fields_info = models.execute_kw(db, uid, password,
            'product.product', 'fields_get', [],
            {'attributes': ['string', 'type']})
        
        print("الحقول المتعلقة بـ foreign/sap في product.product:")
        for field_name, field_info in fields_info.items():
            if 'foreign' in field_name.lower() or 'sap' in field_name.lower():
                print(f"   - {field_name}: {field_info.get('string', 'N/A')} ({field_info.get('type', 'N/A')})")
        print()
    except Exception as e:
        print(f"⚠️ لا يمكن جلب معلومات الحقول: {e}\n")
    
    if product_ids:
        products = models.execute_kw(db, uid, password,
            'product.product', 'read', [product_ids],
            {'fields': ['name', 'default_code', 'foreign_name']})
        
        print(f"عدد المنتجات المفحوصة: {len(products)}\n")
        
        has_foreign_name = 0
        no_foreign_name = 0
        
        for product in products:
            print(f"\n📦 المنتج: {product.get('name', 'N/A')}")
            print(f"   الكود: {product.get('default_code', 'N/A')}")
            
            foreign_name = product.get('foreign_name', False)
            if foreign_name:
                print(f"   ✅ Foreign Name: {foreign_name}")
                has_foreign_name += 1
            else:
                print(f"   ❌ Foreign Name: غير موجود")
                no_foreign_name += 1
        
        print(f"\n📊 ملخص Foreign Name:")
        print(f"   ✅ منتجات لديها foreign_name: {has_foreign_name}")
        print(f"   ❌ منتجات بدون foreign_name: {no_foreign_name}")
    else:
        print("❌ لا توجد منتجات في النظام")
    
    # 2. فحص الأسعار (Pricelists)
    print("\n" + "=" * 80)
    print("2️⃣ فحص الأسعار (Pricelists)")
    print("=" * 80)
    
    # البحث عن pricelists
    pricelist_ids = models.execute_kw(db, uid, password,
        'product.pricelist', 'search', [[]])
    
    if pricelist_ids:
        pricelists = models.execute_kw(db, uid, password,
            'product.pricelist', 'read', [pricelist_ids],
            {'fields': ['name', 'currency_id', 'item_ids']})
        
        print(f"عدد قوائم الأسعار: {len(pricelists)}\n")
        
        for pricelist in pricelists:
            print(f"\n💰 قائمة الأسعار: {pricelist.get('name', 'N/A')}")
            print(f"   العملة: {pricelist.get('currency_id', ['N/A'])[1] if pricelist.get('currency_id') else 'N/A'}")
            item_ids = pricelist.get('item_ids', [])
            print(f"   عدد عناصر الأسعار: {len(item_ids)}")
            
            if item_ids:
                # جلب بعض عناصر الأسعار
                items = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'read', [item_ids[:5]],
                    {'fields': ['product_tmpl_id', 'product_id', 'fixed_price', 'min_quantity', 'compute_price']})
                
                for item in items:
                    product_name = item.get('product_tmpl_id', ['N/A'])[1] if item.get('product_tmpl_id') else \
                                   item.get('product_id', ['N/A'])[1] if item.get('product_id') else 'عام'
                    print(f"      - {product_name}: {item.get('fixed_price', 'N/A')} (الحد الأدنى: {item.get('min_quantity', 1)})")
    else:
        print("❌ لا توجد قوائم أسعار في النظام")
    
    # 3. فحص وحدات القياس المتعددة (UoM)
    print("\n" + "=" * 80)
    print("3️⃣ فحص وحدات القياس المتعددة")
    print("=" * 80)
    
    # البحث عن مجموعات وحدات القياس
    uom_group_ids = models.execute_kw(db, uid, password,
        'uom.group', 'search', [[]])
    
    if uom_group_ids:
        uom_groups = models.execute_kw(db, uid, password,
            'uom.group', 'read', [uom_group_ids[:5]],
            {'fields': ['name', 'uom_ids']})
        
        print(f"عدد مجموعات وحدات القياس: {len(uom_group_ids)}\n")
        
        for group in uom_groups:
            print(f"\n📏 مجموعة: {group.get('name', 'N/A')}")
            uom_ids = group.get('uom_ids', [])
            print(f"   عدد الوحدات: {len(uom_ids)}")
            
            if uom_ids:
                uoms = models.execute_kw(db, uid, password,
                    'product.uom', 'read', [uom_ids],
                    {'fields': ['name', 'uom_type', 'factor', 'rounding']})
                
                for uom in uoms:
                    print(f"      - {uom.get('name', 'N/A')}: {uom.get('uom_type', 'N/A')} (معامل: {uom.get('factor', 'N/A')})")
    else:
        print("❌ لا توجد مجموعات وحدات قياس في النظام")
    
    # 4. فحص منتج محدد بالتفصيل
    print("\n" + "=" * 80)
    print("4️⃣ فحص منتج محدد بالتفصيل")
    print("=" * 80)
    
    if product_ids:
        sample_product_id = product_ids[0]
        product_detail = models.execute_kw(db, uid, password,
            'product.product', 'read', [sample_product_id],
            {'fields': ['name', 'default_code', 'foreign_name', 'list_price', 
                       'standard_price', 'uom_id', 'uom_po_id', 'product_tmpl_id']})
        
        if product_detail:
            product = product_detail[0]
            print(f"\n📦 المنتج النموذجي: {product.get('name', 'N/A')}")
            print(f"   الكود: {product.get('default_code', 'N/A')}")
            print(f"   Foreign Name: {product.get('foreign_name', 'غير موجود')}")
            print(f"   سعر البيع: {product.get('list_price', 'N/A')}")
            print(f"   التكلفة: {product.get('standard_price', 'N/A')}")
            print(f"   وحدة القياس: {product.get('uom_id', ['N/A'])[1] if product.get('uom_id') else 'N/A'}")
            print(f"   وحدة الشراء: {product.get('uom_po_id', ['N/A'])[1] if product.get('uom_po_id') else 'N/A'}")
            
            # البحث عن أسعار هذا المنتج في قوائم الأسعار
            if product.get('product_tmpl_id'):
                tmpl_id = product['product_tmpl_id'][0]
                pricelist_items = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'search_read',
                    [[['product_tmpl_id', '=', tmpl_id]]],
                    {'fields': ['pricelist_id', 'fixed_price', 'min_quantity']})
                
                if pricelist_items:
                    print(f"\n   💰 الأسعار في قوائم الأسعار:")
                    for item in pricelist_items:
                        pricelist_name = item.get('pricelist_id', ['N/A'])[1] if item.get('pricelist_id') else 'N/A'
                        print(f"      - {pricelist_name}: {item.get('fixed_price', 'N/A')} (الحد الأدنى: {item.get('min_quantity', 1)})")
                else:
                    print(f"\n   ⚠️ لا توجد أسعار محددة لهذا المنتج في قوائم الأسعار")
    
    # 5. فحص حقول SAP
    print("\n" + "=" * 80)
    print("5️⃣ فحص حقول SAP في المنتجات")
    print("=" * 80)
    
    # محاولة قراءة بيانات SAP
    try:
        sap_products = models.execute_kw(db, uid, password,
            'sap.product', 'search_read', [[]],
            {'fields': ['material_number', 'foreign_name', 'material_description'], 'limit': 5})
        
        if sap_products:
            print(f"عدد منتجات SAP: {len(sap_products)}\n")
            for sap_prod in sap_products:
                print(f"\n🔷 SAP Material: {sap_prod.get('material_number', 'N/A')}")
                print(f"   Description: {sap_prod.get('material_description', 'N/A')}")
                print(f"   Foreign Name: {sap_prod.get('foreign_name', 'N/A')}")
        else:
            print("⚠️ لا توجد بيانات SAP Products")
    except Exception as e:
        print(f"⚠️ لا يمكن الوصول لجدول sap.product: {e}")
    
    # 6. فحص SAP UOM Prices
    print("\n" + "=" * 80)
    print("6️⃣ فحص أسعار وحدات القياس من SAP")
    print("=" * 80)
    
    try:
        sap_uom_prices = models.execute_kw(db, uid, password,
            'sap.uom.price', 'search_read', [[]],
            {'fields': ['material_number', 'uom_code', 'price', 'currency'], 'limit': 10})
        
        if sap_uom_prices:
            print(f"عدد أسعار وحدات القياس من SAP: {len(sap_uom_prices)}\n")
            for price in sap_uom_prices[:5]:
                print(f"\n💵 Material: {price.get('material_number', 'N/A')}")
                print(f"   UoM: {price.get('uom_code', 'N/A')}")
                print(f"   السعر: {price.get('price', 'N/A')} {price.get('currency', 'N/A')}")
        else:
            print("⚠️ لا توجد بيانات SAP UoM Prices")
    except Exception as e:
        print(f"⚠️ لا يمكن الوصول لجدول sap.uom.price: {e}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

