#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص الحقول الفعلية في uom.uom في Odoo 19
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
    print("فحص حقول uom.uom في Odoo 19")
    print("=" * 80)
    
    # جلب جميع الحقول
    fields_info = models.execute_kw(db, uid, password,
        'uom.uom', 'fields_get', [],
        {'attributes': ['string', 'type', 'help']})
    
    print("\nجميع الحقول في uom.uom:\n")
    
    for field_name, field_info in sorted(fields_info.items()):
        print(f"📌 {field_name}")
        print(f"   النوع: {field_info.get('type', 'N/A')}")
        print(f"   العنوان: {field_info.get('string', 'N/A')}")
        if field_info.get('help'):
            print(f"   المساعدة: {field_info['help'][:80]}...")
        print()
    
    # عينة من البيانات
    print("\n" + "=" * 80)
    print("عينة من وحدات القياس:")
    print("=" * 80 + "\n")
    
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read', [[]],
        {'fields': ['name', 'factor', 'rounding', 'active'], 'limit': 10})
    
    for uom in uoms:
        print(f"📏 {uom['name']}")
        print(f"   Factor: {uom.get('factor', 'N/A')}")
        print(f"   Rounding: {uom.get('rounding', 'N/A')}")
        print()

except Exception as e:
    print(f"❌ خطأ: {e}")

