#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار حقيقي من خلال Sales Order
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("🛒 اختبار UoM Pricing من خلال Sales Order")
print("=" * 80 + "\n")

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. جلب partner
    partners = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['is_company', '=', True]]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    if not partners:
        print("❌ لا يوجد عميل!")
        exit(1)
    
    partner = partners[0]
    print(f"👤 العميل: {partner['name']}\n")
    
    # 2. جلب المنتج
    product = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name', 'default_code', 'uom_id'], 'limit': 1})[0]
    
    print(f"📦 المنتج: {product['name']}\n")
    
    # 3. جلب Pricelist
    pricelist = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', 'ilike', 'SAP%Price%List%1']]],
        {'fields': ['id', 'name'], 'limit': 1})[0]
    
    print(f"💰 Pricelist: {pricelist['name']}\n")
    
    # 4. إنشاء Sales Order
    print("=" * 80)
    print("📝 إنشاء Sales Order")
    print("=" * 80 + "\n")
    
    order_id = models.execute_kw(db, uid, password,
        'sale.order', 'create',
        [{
            'partner_id': partner['id'],
            'pricelist_id': pricelist['id'],
        }])
    
    print(f"✅ Order ID: {order_id}\n")
    
    # 5. اختبار إضافة Lines بـ UoMs مختلفة
    print("=" * 80)
    print("🧪 اختبار الأسعار")
    print("=" * 80 + "\n")
    
    test_cases = [
        ('Manual', 70, 40.0),
        ('0.5 كيلو', 79, 22.0),
        ('0.25 كغم بلاستك', 80, 12.0),
    ]
    
    results = []
    
    for uom_name, uom_id, expected_price in test_cases:
        try:
            # إنشاء order line
            line_id = models.execute_kw(db, uid, password,
                'sale.order.line', 'create',
                [{
                    'order_id': order_id,
                    'product_id': product['id'],
                    'product_uom_qty': 1.0,
                    'product_uom_id': uom_id,  # في Odoo 19: product_uom_id وليس product_uom
                }])
            
            # قراءة السعر الفعلي
            line = models.execute_kw(db, uid, password,
                'sale.order.line', 'read',
                [line_id],
                {'fields': ['price_unit', 'product_uom_id']})[0]
            
            actual_price = line['price_unit']
            
            status = "✅" if abs(actual_price - expected_price) < 0.01 else "❌"
            
            print(f"{status} {uom_name}:")
            print(f"   ├─ المتوقع: ${expected_price:.2f}")
            print(f"   ├─ الفعلي: ${actual_price:.2f}")
            
            if abs(actual_price - expected_price) < 0.01:
                print(f"   └─ ✅ صحيح!\n")
                results.append(True)
            else:
                diff = actual_price - expected_price
                print(f"   ├─ الفرق: ${diff:.2f}")
                print(f"   └─ ❌ خطأ!\n")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {uom_name}: خطأ")
            print(f"   {str(e)[:200]}\n")
            results.append(False)
    
    # 6. حذف Sales Order
    print("🗑️ حذف Sales Order التجريبي...")
    models.execute_kw(db, uid, password,
        'sale.order', 'unlink',
        [[order_id]])
    print("✅ تم الحذف\n")
    
    # 7. النتيجة النهائية
    print("=" * 80)
    print("📊 النتيجة النهائية")
    print("=" * 80 + "\n")
    
    if all(results):
        print("🎉🎉🎉 نجح الإصلاح! Module يعمل بشكل صحيح!\n")
        print("✅ الأسعار المستقلة لكل UoM تعمل!")
        print("✅ جاهز للاستخدام!")
    elif any(results):
        print("⚠️ بعض الحالات تعمل، وبعضها لا")
        print("→ يحتاج مزيد من التعديلات")
    else:
        print("❌ Module ما زال لا يعمل كما هو متوقع")
        print("→ قد نحتاج استراتيجية مختلفة")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

