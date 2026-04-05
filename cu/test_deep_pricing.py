#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل لـ UoM Pricing بعد الإصلاح العميق
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("🔬 اختبار UoM Pricing - الإصدار العميق")
print("=" * 80 + "\n")

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. جلب البيانات
    product = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name', 'default_code', 'uom_id'], 'limit': 1})[0]
    
    print(f"📦 المنتج: {product['name']}")
    print(f"   SKU: {product['default_code']}\n")
    
    # جلب Pricelist
    pricelist = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', 'ilike', 'SAP%Price%List%1']]],
        {'fields': ['id', 'name'], 'limit': 1})[0]
    
    print(f"💰 Pricelist: {pricelist['name']}\n")
    
    # جلب جميع pricelist items لهذا المنتج
    pricelist_items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['pricelist_id', '=', pricelist['id']], 
          ['product_id', '=', product['id']]]],
        {'fields': ['id', 'product_uom_id', 'fixed_price', 'compute_price']})
    
    print("=" * 80)
    print("📋 Pricelist Items الموجودة:")
    print("=" * 80 + "\n")
    
    for item in pricelist_items:
        uom_name = "N/A"
        if item.get('product_uom_id'):
            uom = models.execute_kw(db, uid, password,
                'uom.uom', 'read',
                [item['product_uom_id'][0]],
                {'fields': ['name']})[0]
            uom_name = uom['name']
        
        print(f"   Item ID {item['id']}:")
        print(f"   ├─ UoM: {uom_name}")
        print(f"   ├─ Price: ${item.get('fixed_price', 0):.2f}")
        print(f"   └─ Type: {item.get('compute_price', 'N/A')}\n")
    
    # 2. اختبار حساب السعر من خلال _compute_price_rule
    print("=" * 80)
    print("🧪 اختبار حساب السعر")
    print("=" * 80 + "\n")
    
    # UoMs للاختبار
    test_cases = [
        ('Manual', 70, 40.0),
        ('0.5 كيلو', 79, 22.0),
        ('0.25 كغم بلاستك', 80, 12.0),
    ]
    
    for uom_name, uom_id, expected_price in test_cases:
        try:
            # استدعاء مباشر لـ _compute_price_rule
            result = models.execute_kw(db, uid, password,
                'product.pricelist', '_compute_price_rule',
                [pricelist['id'],  # pricelist
                 [product['id']],  # products (as recordset)
                 1.0],             # quantity
                {'uom': uom_id,    # UoM ID
                 'compute_price': True})
            
            if product['id'] in result:
                actual_price = result[product['id']][0]
                rule_id = result[product['id']][1]
                
                status = "✅" if abs(actual_price - expected_price) < 0.01 else "❌"
                
                print(f"{status} {uom_name}:")
                print(f"   ├─ المتوقع: ${expected_price:.2f}")
                print(f"   ├─ الفعلي: ${actual_price:.2f}")
                print(f"   └─ Rule ID: {rule_id}")
                
                if abs(actual_price - expected_price) < 0.01:
                    print(f"   ✅ صحيح!\n")
                else:
                    print(f"   ❌ خطأ - يستخدم معامل التحويل!\n")
            else:
                print(f"❌ {uom_name}: لم يتم إرجاع نتيجة\n")
                
        except Exception as e:
            print(f"❌ {uom_name}: خطأ")
            print(f"   {str(e)[:200]}\n")
    
    print("=" * 80)
    print("📊 النتيجة النهائية")
    print("=" * 80 + "\n")
    
    print("""
✅✅✅ = Module يعمل بشكل صحيح!
❌❌❌ = ما زالت المشكلة موجودة
⚠️⚠️⚠️ = يحتاج مزيد من التعديلات
""")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

