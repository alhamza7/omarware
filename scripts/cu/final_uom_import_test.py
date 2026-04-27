#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("FINAL UOM GROUPS IMPORT TEST")
print("=" * 100)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"\n✅ Connected (User ID: {uid})")

# Get backend
backends = models.execute_kw(db, uid, password,
    'sap.backend', 'search_read',
    [[('active', '=', True)]],
    {'fields': ['id', 'name'], 'limit': 1}
)

if not backends:
    print("\n❌ No active backend found")
    exit(1)

backend = backends[0]
print(f"\n✅ Using backend: {backend['name']} (ID: {backend['id']})")

# Import UoMs from SAP
print("\n" + "=" * 100)
print("Starting UoM Import from SAP...")
print("=" * 100)

import time
start_time = time.time()

try:
    result = models.execute_kw(db, uid, password,
        'sap.uom.sync', 'import_all_uoms_from_sap',
        [backend['id']]
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Import completed in {duration:.2f} seconds")
    print(f"   Result: {result}")
    
except Exception as e:
    print(f"\n❌ Import failed: {str(e)[:500]}")
    exit(1)

# Check results
print("\n" + "=" * 100)
print("Checking Results...")
print("=" * 100)

# Count groups
group_count = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_count', [[]])

# Count UoM syncs
sync_count = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_count', [[]])

# Count UoMs
uom_count = models.execute_kw(db, uid, password,
    'uom.uom', 'search_count', [[]])

print(f"\n📊 Totals:")
print(f"   • SAP UoM Groups: {group_count}")
print(f"   • SAP UoM Sync records: {sync_count}")
print(f"   • Odoo UoMs: {uom_count}")

# Get sample groups
if group_count > 0:
    groups = models.execute_kw(db, uid, password,
        'sap.uom.group', 'search_read',
        [[]],
        {'fields': ['name', 'sap_group_code', 'base_uom_code', 'uom_count'], 'limit': 10}
    )
    
    print(f"\n📋 Sample Groups:")
    for g in groups:
        print(f"   • {g['name']} (Code: {g['sap_group_code']}, Base: {g.get('base_uom_code', 'N/A')}, UoMs: {g.get('uom_count', 0)})")

# Get sample UoM syncs with entry
if sync_count > 0:
    syncs = models.execute_kw(db, uid, password,
        'sap.uom.sync', 'search_read',
        [[]],
        {'fields': ['sap_uom_id', 'sap_uom_entry', 'sap_group_id', 'odoo_uom_id'], 'limit': 15}
    )
    
    with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
    with_group = sum(1 for s in syncs if s.get('sap_group_id'))
    with_odoo = sum(1 for s in syncs if s.get('odoo_uom_id'))
    
    print(f"\n📊 UoM Sync Quality:")
    print(f"   • With SAP Entry (not 0): {with_entry}/{len(syncs)}")
    print(f"   • With Group link: {with_group}/{len(syncs)}")
    print(f"   • With Odoo UoM link: {with_odoo}/{len(syncs)}")
    
    print(f"\n📋 Sample UoM Syncs:")
    for s in syncs[:10]:
        entry = s.get('sap_uom_entry', 0)
        group = s['sap_group_id'][1] if s.get('sap_group_id') else 'NO GROUP'
        uom = s['odoo_uom_id'][1] if s.get('odoo_uom_id') else 'NOT LINKED'
        entry_status = "✅" if entry != 0 else "❌"
        group_status = "✅" if s.get('sap_group_id') else "❌"
        
        print(f"   {entry_status}{group_status} {s['sap_uom_id']:<20} Entry:{entry:>5}  Group: {group:<30}  Odoo: {uom}")

# Check for factors
if with_odoo > 0:
    uom_ids = [s['odoo_uom_id'][0] for s in syncs if s.get('odoo_uom_id')]
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[('id', 'in', uom_ids)]],
        {'fields': ['name', 'factor']}
    )
    
    unique_factors = set()
    for uom in uoms:
        factor = uom.get('factor', 1.0)
        if abs(factor - 1.0) > 0.001:
            unique_factors.add(round(factor, 6))
    
    print(f"\n📊 Conversion Factors:")
    print(f"   • UoMs with factor = 1.0: {sum(1 for u in uoms if abs(u.get('factor', 1.0) - 1.0) < 0.001)}")
    print(f"   • UoMs with factor ≠ 1.0: {len(unique_factors)}")
    
    if unique_factors:
        print(f"\n   ✅ Unique factors found: {sorted(list(unique_factors))[:10]}")
    else:
        print(f"\n   ⚠️ All factors are 1.0 - conversion factors may need review")

print("\n" + "=" * 100)
print("IMPORT TEST COMPLETE!")
print("=" * 100)

if group_count > 0 and with_entry > 0 and with_group > 0:
    print("\n✅ SUCCESS: UoM Groups imported correctly!")
    print("   • Groups created ✅")
    print("   • SAP Entries saved ✅")
    print("   • Group links established ✅")
else:
    print("\n⚠️ PARTIAL SUCCESS - Review needed:")
    if group_count == 0:
        print("   ❌ No groups created")
    if with_entry == 0:
        print("   ❌ SAP Entries not saved")
    if with_group == 0:
        print("   ❌ Group links not established")

print("\n" + "=" * 100)




