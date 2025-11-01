#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
البحث عن model الصحيح للـ packaging في Odoo 19
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
    print("البحث عن Packaging Model")
    print("=" * 80 + "\n")
    
    # البحث عن models تحتوي على packaging
    all_models = models.execute_kw(db, uid, password,
        'ir.model', 'search_read',
        [[['model', 'ilike', 'packaging']]],
        {'fields': ['model', 'name']})
    
    print(f"Models تحتوي على 'packaging':\n")
    for model in all_models:
        print(f"   📦 {model['model']} - {model['name']}")
    
    # البحث عن models تحتوي على product
    print(f"\n{'='*80}")
    print("Models المتعلقة بـ product.product:")
    print("=" * 80 + "\n")
    
    product_models = models.execute_kw(db, uid, password,
        'ir.model', 'search_read',
        [[['model', 'like', 'product.%']]],
        {'fields': ['model', 'name'], 'limit': 30})
    
    for model in product_models:
        print(f"   📦 {model['model']} - {model['name']}")
    
    # فحص حقول product.product
    print(f"\n{'='*80}")
    print("الحقول المتعلقة بـ packaging في product.product:")
    print("=" * 80 + "\n")
    
    fields_info = models.execute_kw(db, uid, password,
        'product.product', 'fields_get', [],
        {'attributes': ['string', 'type']})
    
    for field_name, field_info in fields_info.items():
        if 'packag' in field_name.lower() or 'uom' in field_name.lower():
            print(f"   📌 {field_name}: {field_info.get('string')} ({field_info.get('type')})")

except Exception as e:
    print(f"❌ خطأ: {e}")

