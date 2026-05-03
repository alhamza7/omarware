#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تلقائي لـ UoM Pricing بعد الإصلاح
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("اختبار UoM Pricing")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. جلب المنتج والـ UoMs
    print("1️⃣ جلب البيانات التجريبية...\n")
    
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name', 'default_code'], 'limit': 1})
    
    if not products:
        print("❌ المنتج غير موجود!")
        exit(1)
    
    product = products[0]
    print(f"المنتج: {product['name']} ({product['default_code']})\n")
    
    # جلب Pricelist
    pricelists = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', 'ilike', 'SAP%Price%List%1']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    if not pricelists:
        print("❌ Pricelist غير موجود!")
        exit(1)
    
    pricelist = pricelists[0]
    print(f"Pricelist: {pricelist['name']}\n")
    
    # جلب UoMs للاختبار
    uom_manual = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['name', '=', 'Manual']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    uom_half = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['name', 'ilike', '0.5%كيلو']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    uom_quarter = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['name', 'ilike', '0.25%كغم']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    print("UoMs للاختبار:")
    if uom_manual:
        print(f"   ✅ {uom_manual[0]['name']} (ID: {uom_manual[0]['id']})")
    if uom_half:
        print(f"   ✅ {uom_half[0]['name']} (ID: {uom_half[0]['id']})")
    if uom_quarter:
        print(f"   ✅ {uom_quarter[0]['name']} (ID: {uom_quarter[0]['id']})")
    print()
    
    # 2. اختبار حساب السعر
    print("=" * 80)
    print("2️⃣ اختبار حساب السعر")
    print("=" * 80 + "\n")
    
    # إنشاء order line تجريبي
    # نحاكي ما يحدث عند إضافة منتج في Sales Order
    
    test_cases = [
        ('Manual', uom_manual[0]['id'] if uom_manual else None, 40.0),
        ('0.5 كيلو', uom_half[0]['id'] if uom_half else None, 22.0),
        ('0.25 كغم', uom_quarter[0]['id'] if uom_quarter else None, 12.0),
    ]
    
    print("النتائج:\n")
    
    for uom_name, uom_id, expected_price in test_cases:
        if not uom_id:
            continue
        
        # استدعاء get_product_price للحصول على السعر
        try:
            # طريقة مباشرة - جلب السعر من Pricelist
            price_info = models.execute_kw(db, uid, password,
                'product.pricelist', 'get_product_price',
                [pricelist['id'], product['id'], 1.0, uom_id])
            
            status = "✅" if abs(price_info - expected_price) < 0.01 else "❌"
            print(f"{status} {uom_name}:")
            print(f"   المتوقع: ${expected_price:.2f}")
            print(f"   الفعلي: ${price_info:.2f}")
            
            if abs(price_info - expected_price) < 0.01:
                print(f"   ✅ صحيح!\n")
            else:
                print(f"   ❌ خطأ - يستخدم معامل التحويل!\n")
                
        except Exception as e:
            print(f"❌ {uom_name}: خطأ - {str(e)[:100]}\n")
    
    print("=" * 80)
    print("النتيجة")
    print("=" * 80 + "\n")
    
    print("""
إذا رأيت ✅✅✅ = نجح الإصلاح! 🎉

إذا رأيت ❌ = ما زالت المشكلة موجودة
   → سنحتاج تعديلات أعمق
   → أو استخدام Product Variants
""")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

