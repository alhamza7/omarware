#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض المنتجات التي لديها أسعار متعددة
"""

import xmlrpc.client
from collections import defaultdict

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("المنتجات التي لديها أسعار متعددة")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # جلب جميع عناصر الأسعار
    print("جلب بيانات الأسعار...")
    
    price_items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['product_id', '!=', False], ['fixed_price', '>', 0]]],
        {'fields': ['product_id', 'pricelist_id', 'fixed_price', 'min_quantity'], 'limit': 1000})
    
    print(f"تم جلب {len(price_items)} عنصر سعر\n")
    
    # تجميع حسب المنتج
    by_product = defaultdict(list)
    
    for item in price_items:
        product_id = item['product_id'][0]
        product_name = item['product_id'][1]
        pricelist = item.get('pricelist_id', ['Unknown'])[1] if item.get('pricelist_id') else 'Unknown'
        
        by_product[product_id].append({
            'name': product_name,
            'pricelist': pricelist,
            'price': item.get('fixed_price', 0),
            'min_qty': item.get('min_quantity', 1)
        })
    
    # البحث عن المنتجات التي لديها أكثر من سعر
    multi_price_products = {k: v for k, v in by_product.items() if len(v) > 1}
    
    print(f"عدد المنتجات التي لديها أسعار متعددة: {len(multi_price_products)}\n")
    
    # عرض أول 10 منتجات كأمثلة
    print("=" * 80)
    print("أمثلة على المنتجات التي لديها أسعار متعددة:")
    print("=" * 80)
    
    count = 0
    for product_id, prices in multi_price_products.items():
        if count >= 10:
            break
        
        # الحصول على معلومات المنتج
        product = models.execute_kw(db, uid, password,
            'product.product', 'read',
            [[product_id]],
            {'fields': ['name', 'default_code', 'foreign_name']})
        
        if product:
            prod = product[0]
            print(f"\n📦 {prod.get('name', 'N/A')} ({prod.get('default_code', 'N/A')})")
            if prod.get('foreign_name'):
                print(f"   Foreign Name: {prod['foreign_name']}")
            
            print(f"\n   الأسعار:")
            print(f"   {'قائمة الأسعار':<30} | {'الكمية':<10} | {'السعر':<10}")
            print(f"   {'-'*30} | {'-'*10} | {'-'*10}")
            
            for price_info in sorted(prices, key=lambda x: x['price']):
                pricelist_short = price_info['pricelist'][:28] if len(price_info['pricelist']) > 28 else price_info['pricelist']
                print(f"   {pricelist_short:<30} | {price_info['min_qty']:<10.2f} | ${price_info['price']:<10.2f}")
            
            count += 1
    
    print("\n" + "=" * 80)
    print("📋 كيفية استخدام الأسعار المتعددة:")
    print("=" * 80)
    print("""
1️⃣ في أمر البيع (Sales Order):
   • اذهب إلى Sales → Orders → New
   • اختر العميل
   • اختر Pricelist (مثلاً: SAP Price List 1)
   • أضف المنتج
   • السعر سيُطبق حسب Pricelist المختار

2️⃣ في نقطة البيع (POS):
   • افتح POS
   • في الإعدادات، اختر Pricelist المطلوب
   • عند إضافة المنتج، سيُطبق السعر من Pricelist المحدد

3️⃣ لعرض/تعديل الأسعار:
   • اذهب إلى Sales → Configuration → Pricelists
   • افتح قائمة الأسعار المطلوبة
   • ستجد جميع الأسعار في تبويب "Price Rules"
""")
    
    print("=" * 80)
    print("✅ تم")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

