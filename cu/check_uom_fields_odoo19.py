#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""التحقق من حقول UoM في Odoo 19"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)

print("فحص حقول uom.uom في Odoo 19:\n")
print("="*80)

fields_info = models.execute_kw(db, uid, password,
    'uom.uom', 'fields_get',
    [], {'attributes': ['string', 'type']})

print("الحقول المتاحة:")
for field_name, field_data in sorted(fields_info.items()):
    print(f"  • {field_name}: {field_data.get('string', 'N/A')} ({field_data.get('type', 'N/A')})")



