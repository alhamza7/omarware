#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("Checking UOM Data")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Count UoMs
uom_count = models.execute_kw(db, uid, password,
    'uom.uom', 'search_count', [[]])

# Count SAP UoM Sync
sync_count = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_count', [[]])

# Get SAP syncs with details
syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['id', 'sap_uom_id', 'sap_uom_entry', 'odoo_uom_id', 'sync_status']}
)

print(f"\nTotal UoMs in Odoo: {uom_count}")
print(f"Total SAP UoM Sync records: {sync_count}")
print()

# Count with SAP Entry
with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
with_odoo = sum(1 for s in syncs if s.get('odoo_uom_id'))

print(f"SAP Sync records with Entry (not 0): {with_entry}/{sync_count}")
print(f"SAP Sync records linked to Odoo: {with_odoo}/{sync_count}")
print()

# Show some examples
print("Sample records:")
for sync in syncs[:10]:
    entry = sync.get('sap_uom_entry', 0)
    uom = sync['odoo_uom_id'][1] if sync.get('odoo_uom_id') else 'NOT LINKED'
    print(f"  ID:{sync['id']:3d} | SAP:{sync.get('sap_uom_id', 'N/A'):20s} | Entry:{entry:4d} | Odoo: {uom}")

# Check for unique factors
if with_odoo > 0:
    uom_ids = [s['odoo_uom_id'][0] for s in syncs if s.get('odoo_uom_id')]
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[('id', 'in', uom_ids)]],
        {'fields': ['id', 'name', 'factor']}
    )
    
    factors = set()
    for uom in uoms:
        factor = uom.get('factor', 1.0)
        if abs(factor - 1.0) > 0.001:
            factors.add(round(factor, 6))
    
    print()
    print(f"UoMs with factor != 1.0: {len(factors)}")
    if factors:
        print("  Factors found:", sorted(list(factors))[:10])
    else:
        print("  All UoMs have factor = 1.0")

print()
print("=" * 80)


