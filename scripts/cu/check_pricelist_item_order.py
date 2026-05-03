#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص ترتيب وأولوية pricelist items
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    
    print("=" * 80)
    print("🔍 فحص Pricelist Items للمنتج ADF00005")
    print("=" * 80 + "\n")
    
    # جلب المنتج
    product = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name'], 'limit': 1})[0]
    
    print(f"المنتج: {product['name']} (ID: {product['id']})\n")
    
    # جلب Pricelist
    pricelist = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', 'ilike', 'SAP%Price%List%1']]],
        {'fields': ['id', 'name'], 'limit': 1})[0]
    
    print(f"Pricelist: {pricelist['name']} (ID: {pricelist['id']})\n")
    
    # جلب جميع items لهذا المنتج في هذا Pricelist
    items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['pricelist_id', '=', pricelist['id']], 
          ['product_id', '=', product['id']]]],
        {'fields': ['id', 'product_uom_id', 'fixed_price', 'compute_price', 
                    'applied_on', 'min_quantity']})
    
    print("=" * 80)
    print(f"📋 عدد Items: {len(items)}")
    print("=" * 80 + "\n")
    
    for i, item in enumerate(items, 1):
        uom_name = "N/A"
        uom_id = None
        if item.get('product_uom_id'):
            uom_id = item['product_uom_id'][0]
            uom = models.execute_kw(db, uid, password,
                'uom.uom', 'read',
                [uom_id],
                {'fields': ['name']})[0]
            uom_name = uom['name']
        
        print(f"Item #{i} (ID: {item['id']}):")
        print(f"   ├─ UoM: {uom_name} (ID: {uom_id})")
        print(f"   ├─ Price: ${item.get('fixed_price', 0):.2f}")
        print(f"   ├─ Type: {item.get('compute_price', 'N/A')}")
        print(f"   ├─ Applied On: {item.get('applied_on', 'N/A')}")
        print(f"   └─ Min Qty: {item.get('min_quantity', 0)}\n")
    
    print("=" * 80)
    print("💡 الملاحظات")
    print("=" * 80 + "\n")
    
    print("""
إذا كانت جميع Items لها نفس ال priority:
   → Odoo قد يختار عشوائياً أو حسب ID
   → في Odoo 19: لا يوجد sequence, بل priority
   
الترتيب المطلوب:
   1. Manual (أعلى priority)
   2. 0.5 كيلو
   3. 0.25 كغم
   4. كغم (الأساسي - أقل priority)
   
المشكلة الحقيقية:
   → Module يجب أن يتحقق من UoM قبل تطبيق القاعدة!
""")

except Exception as e:
    print(f"❌ {e}")
    import traceback
    traceback.print_exc()

