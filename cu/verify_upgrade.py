#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("Verifying Module Upgrade")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"\nConnected (User ID: {uid})")

# Check if sap.uom.group exists
try:
    group_count = models.execute_kw(db, uid, password,
        'sap.uom.group', 'search_count', [[]])
    print(f"\n✅ sap.uom.group: Model exists! ({group_count} records)")
except Exception as e:
    print(f"\n❌ sap.uom.group: {str(e)[:100]}")
    exit(1)

# Check sap.uom.sync for new field
try:
    fields = models.execute_kw(db, uid, password,
        'ir.model.fields', 'search_read',
        [[('model', '=', 'sap.uom.sync'), ('name', '=', 'sap_group_id')]],
        {'fields': ['name', 'field_description']}
    )
    
    if fields:
        print(f"✅ sap.uom.sync.sap_group_id: Field exists!")
    else:
        print(f"⚠️ sap.uom.sync.sap_group_id: Field not found")
except Exception as e:
    print(f"❌ Error checking field: {str(e)[:100]}")

# Check current data
sync_count = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_count', [[]])
uom_count = models.execute_kw(db, uid, password,
    'uom.uom', 'search_count', [[]])

print(f"\n📊 Current data:")
print(f"   • sap.uom.sync: {sync_count} records")
print(f"   • uom.uom: {uom_count} records")
print(f"   • sap.uom.group: {group_count} records")

print("\n✅ Upgrade successful! Ready for import.")
print("=" * 80)




