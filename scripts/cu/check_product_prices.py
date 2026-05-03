#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض جميع أسعار منتج معين حسب وحدات القياس
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

# المنتج المطلوب (غيّر هذا حسب حاجتك)
PRODUCT_CODE = "S-175"  # أو أي كود منتج آخر

print("=" * 80)
print(f"عرض جميع أسعار المنتج: {PRODUCT_CODE}")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. البحث عن المنتج
    print(f"البحث عن المنتج {PRODUCT_CODE}...")
    
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', PRODUCT_CODE]]],
        {'fields': ['id', 'name', 'default_code', 'foreign_name', 
                   'product_tmpl_id', 'uom_id'], 'limit': 1})
    
    if not products:
        print(f"❌ لم يتم العثور على المنتج {PRODUCT_CODE}")
        exit(1)
    
    product = products[0]
    product_id = product['id']
    product_tmpl_id = product['product_tmpl_id'][0]
    
    print(f"\n✅ تم العثور على المنتج:")
    print(f"   الاسم: {product['name']}")
    print(f"   الكود: {product['default_code']}")
    print(f"   Foreign Name: {product.get('foreign_name', 'غير موجود')}")
    uom = product.get('uom_id', ['N/A'])[1] if product.get('uom_id') else 'N/A'
    print(f"   الوحدة الأساسية: {uom}\n")
    
    # 2. البحث عن جميع الأسعار في Pricelists
    print("=" * 80)
    print("الأسعار في قوائم الأسعار المختلفة:")
    print("=" * 80)
    
    # البحث عن عناصر الأسعار
    price_items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['product_id', '=', product_id]]],
        {'fields': ['pricelist_id', 'fixed_price', 'min_quantity', 'applied_on']})
    
    if not price_items:
        # محاولة البحث بـ product_tmpl_id
        price_items = models.execute_kw(db, uid, password,
            'product.pricelist.item', 'search_read',
            [[['product_tmpl_id', '=', product_tmpl_id]]],
            {'fields': ['pricelist_id', 'fixed_price', 'min_quantity', 'applied_on']})
    
    if price_items:
        print(f"\nعدد الأسعار المختلفة: {len(price_items)}\n")
        
        # تنظيم حسب Pricelist
        by_pricelist = {}
        for item in price_items:
            pricelist_name = item.get('pricelist_id', ['Unknown'])[1] if item.get('pricelist_id') else 'Unknown'
            
            if pricelist_name not in by_pricelist:
                by_pricelist[pricelist_name] = []
            
            by_pricelist[pricelist_name].append({
                'price': item.get('fixed_price', 0),
                'min_qty': item.get('min_quantity', 1)
            })
        
        # عرض النتائج
        for pricelist_name, items in by_pricelist.items():
            print(f"\n💰 {pricelist_name}:")
            print(f"   {'الكمية الأدنى':<15} | {'السعر':<10}")
            print(f"   {'-'*15} | {'-'*10}")
            
            for item in sorted(items, key=lambda x: x['min_qty']):
                print(f"   {item['min_qty']:<15.2f} | ${item['price']:<10.2f}")
    else:
        print("⚠️ لا توجد أسعار محددة لهذا المنتج في Pricelists")
    
    # 3. عرض السعر الأساسي
    print("\n" + "=" * 80)
    print("السعر الأساسي (من product.template):")
    print("=" * 80)
    
    template = models.execute_kw(db, uid, password,
        'product.template', 'read',
        [[product_tmpl_id]],
        {'fields': ['list_price', 'standard_price']})
    
    if template:
        print(f"\n💵 السعر الأساسي (List Price): ${template[0].get('list_price', 0):.2f}")
        print(f"💵 التكلفة (Cost): ${template[0].get('standard_price', 0):.2f}")
    
    print("\n" + "=" * 80)
    print("✅ تم")
    print("=" * 80)
    
    print("\n📝 ملاحظة:")
    print("   • الأسعار المتعددة تُستخدم في المبيعات عند اختيار Pricelist")
    print("   • السعر يتغير حسب الكمية الأدنى أو وحدة القياس")
    print("   • يمكنك تعديل الأسعار من: Sales → Configuration → Pricelists")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

