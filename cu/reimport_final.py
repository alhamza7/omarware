#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("REIMPORT UOM GROUPS")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected (User ID: %d)" % uid)

# Delete old records
print("\n1. Deleting old UoM Sync records...")
old_ids = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search', [[]])
if old_ids:
    models.execute_kw(db, uid, password, 'sap.uom.sync', 'unlink', [old_ids])
    print("   Deleted %d old records" % len(old_ids))

# Get backend
backends = models.execute_kw(db, uid, password,
    'sap.backend', 'search_read',
    [[('active', '=', True)]],
    {'fields': ['id', 'name'], 'limit': 1}
)

backend = backends[0]
print("\n2. Using backend: %s (ID: %d)" % (backend['name'], backend['id']))

# Import
print("\n3. Importing UOM Groups from SAP...")
print("   Please wait...")

start = time.time()
result = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'import_all_uoms_from_sap',
    [backend['id']]
)
duration = time.time() - start

print("   Import completed in %.2f seconds" % duration)
print("   Result: %d UoMs imported" % result)

# Verify
print("\n4. Verifying Results...")

group_count = models.execute_kw(db, uid, password, 'sap.uom.group', 'search_count', [[]])
sync_count = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])

print("\nTotals:")
print("   - UoM Groups: %d" % group_count)
print("   - UoM Syncs: %d" % sync_count)

# Get sample
syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['sap_uom_id', 'sap_uom_entry', 'sap_group_id', 'odoo_uom_id'], 'limit': 20}
)

with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
with_group = sum(1 for s in syncs if s.get('sap_group_id'))

print("\nQuality:")
print("   - With SAP Entry (!= 0): %d/%d" % (with_entry, len(syncs)))
print("   - With Group link: %d/%d" % (with_group, len(syncs)))

print("\nSample (first 10):")
for s in syncs[:10]:
    entry = s.get('sap_uom_entry', 0)
    has_group = 'YES' if s.get('sap_group_id') else 'NO'
    has_odoo = 'YES' if s.get('odoo_uom_id') else 'NO'
    print("   %s | Entry:%4d | Group:%3s | Odoo:%3s" % (
        s.get('sap_uom_id', 'N/A')[:20].ljust(20),
        entry,
        has_group,
        has_odoo
    ))

print("\n" + "=" * 80)
if with_entry > 0 and with_group > 0:
    print("SUCCESS! UoM Groups imported correctly!")
else:
    print("PARTIAL SUCCESS - needs review")
print("=" * 80)




