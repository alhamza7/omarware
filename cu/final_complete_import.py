#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Complete Import - will create ALL UoMs from Groups
"""

import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("FINAL COMPLETE IMPORT - ALL UoMs FROM ALL GROUPS")
print("=" * 100)
print("\nThis will:")
print("  1. Delete old data")
print("  2. Import all UoM Groups (169)")
print("  3. Create UoM Sync for EVERY UoM in EVERY Group")
print("  4. Set conversion factors for all")
print("\nExpected result: Hundreds of UoMs with proper linking!")
print()

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("Connected")

# Delete all
print("\nStep 1: Cleaning...")
sync_ids = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search', [[]])
group_ids = models.execute_kw(db, uid, password, 'sap.uom.group', 'search', [[]])

if sync_ids:
    models.execute_kw(db, uid, password, 'sap.uom.sync', 'unlink', [sync_ids])
    print("   Deleted %d UoM Syncs" % len(sync_ids))

if group_ids:
    models.execute_kw(db, uid, password, 'sap.uom.group', 'unlink', [group_ids])
    print("   Deleted %d Groups" % len(group_ids))

# Import
backends = models.execute_kw(db, uid, password,
    'sap.backend', 'search', [[('active', '=', True)]])
backend_id = backends[0]

print("\nStep 2: Importing from SAP...")
print("   (This may take 2-5 minutes as it will fetch details for each group)")
print()

start = time.time()

try:
    result = models.execute_kw(db, uid, password,
        'sap.uom.sync', 'import_all_uoms_from_sap',
        [backend_id]
    )
    
    duration = time.time() - start
    print("\n✅ Import completed in %.2f seconds (%.2f minutes)" % (duration, duration/60))
    
except Exception as e:
    print("\n❌ Error: %s" % str(e)[:500])
    exit(1)

# Verify
print("\nStep 3: Verification...")
print("-" * 100)

groups = models.execute_kw(db, uid, password, 'sap.uom.group', 'search_count', [[]])
syncs = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])

print("\nResults:")
print("   - UoM Groups: %d" % groups)
print("   - UoM Syncs: %d (was: 20)" % syncs)

if syncs > 100:
    print("\n✅✅✅ EXCELLENT! Got %d UoMs (was 20)!" % syncs)
elif syncs > 50:
    print("\n✅ GOOD! Got %d UoMs (was 20)" % syncs)
elif syncs > 20:
    print("\n✅ PROGRESS! Got %d UoMs (was 20)" % syncs)
else:
    print("\n⚠️ Same as before: %d UoMs" % syncs)

# Sample groups
groups_data = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['name', 'uom_count'], 'order': 'uom_count desc', 'limit': 10}
)

print("\nTop Groups by UoM count:")
for g in groups_data:
    print("   %s: %d UoMs" % (g['name'][:40].ljust(40), g.get('uom_count', 0)))

# Quality check
sample_syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['sap_group_id', 'odoo_uom_id'], 'limit': 100}
)

linked = sum(1 for s in sample_syncs if s.get('sap_group_id'))
with_odoo = sum(1 for s in sample_syncs if s.get('odoo_uom_id'))

print("\nQuality (sample of %d):" % len(sample_syncs))
print("   - Linked to Groups: %d/%d (%.0f%%)" % (linked, len(sample_syncs), linked*100/len(sample_syncs) if sample_syncs else 0))
print("   - With Odoo UoM: %d/%d (%.0f%%)" % (with_odoo, len(sample_syncs), with_odoo*100/len(sample_syncs) if sample_syncs else 0))

print("\n" + "=" * 100)
print("DONE!")
print("=" * 100)




