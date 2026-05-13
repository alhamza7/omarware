#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete clean and reimport of ALL UoM Groups"""

import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("FULL CLEAN AND REIMPORT - ALL 160+ GROUPS")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected")

# Delete all old data
print("\nStep 1: Deleting ALL old data...")
print("-" * 80)

# Delete sap.uom.sync
sync_ids = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search', [[]])
if sync_ids:
    models.execute_kw(db, uid, password, 'sap.uom.sync', 'unlink', [sync_ids])
    print("   Deleted %d UoM Sync records" % len(sync_ids))

# Delete sap.uom.group
group_ids = models.execute_kw(db, uid, password, 'sap.uom.group', 'search', [[]])
if group_ids:
    models.execute_kw(db, uid, password, 'sap.uom.group', 'unlink', [group_ids])
    print("   Deleted %d UoM Group records" % len(group_ids))

# Get backend
print("\nStep 2: Getting SAP Backend...")
print("-" * 80)

backends = models.execute_kw(db, uid, password,
    'sap.backend', 'search_read',
    [[('active', '=', True)]],
    {'fields': ['id', 'name'], 'limit': 1}
)

backend = backends[0]
print("   Using: %s (ID: %d)" % (backend['name'], backend['id']))

# Import
print("\nStep 3: Importing ALL UoM Groups from SAP...")
print("-" * 80)
print("   This will fetch ALL 160+ groups")
print("   Please wait... (may take 1-2 minutes)")
print()

start = time.time()

try:
    result = models.execute_kw(db, uid, password,
        'sap.uom.sync', 'import_all_uoms_from_sap',
        [backend['id']]
    )
    
    duration = time.time() - start
    print("   Import completed in %.2f seconds" % duration)
    print("   Result: %d UoMs imported" % result)
    
except Exception as e:
    print("   ERROR: %s" % str(e)[:300])
    exit(1)

# Verify
print("\nStep 4: Verification...")
print("-" * 80)

groups = models.execute_kw(db, uid, password, 'sap.uom.group', 'search_count', [[]])
syncs = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])

print("\nResults:")
print("   - UoM Groups: %d" % groups)
print("   - UoM Syncs: %d" % syncs)

if groups >= 160:
    print("\n✅✅✅ SUCCESS! Got all 160+ groups!")
elif groups > 40:
    print("\n✅ PROGRESS! Got %d groups (more than before)" % groups)
else:
    print("\n⚠️ Only got %d groups - expected 160+" % groups)

# Check quality
if syncs > 0:
    sample_syncs = models.execute_kw(db, uid, password,
        'sap.uom.sync', 'search_read',
        [[]],
        {'fields': ['sap_uom_entry', 'sap_group_id'], 'limit': 20}
    )
    
    with_entry = sum(1 for s in sample_syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
    with_group = sum(1 for s in sample_syncs if s.get('sap_group_id'))
    
    print("\nQuality (sample of %d):" % len(sample_syncs))
    print("   - With SAP Entry: %d/%d" % (with_entry, len(sample_syncs)))
    print("   - With Group link: %d/%d" % (with_group, len(sample_syncs)))

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)




