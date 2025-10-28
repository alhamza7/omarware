#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final sync - get ALL UoMs from ALL Groups"""

import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("FINAL SYNC - GET ALL UoMs FROM ALL 169 GROUPS")
print("=" * 100)
print("\nThis will process all 169 groups and create UoM syncs for every UoM")
print("Estimated time: ~15-20 minutes")
print()

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("Connected")

# Check before
before = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])
print("\nBefore: %d UoM Syncs" % before)

# Get all groups that have definitions in SAP
groups = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search',
    [[('sap_abs_entry', '>', 0)]]  # Skip Manual (-1)
)

print("Will process: %d groups" % len(groups))
print("\nStarting sync...")
print("-" * 100)

start = time.time()
success_count = 0
error_count = 0

for i, group_id in enumerate(groups, 1):
    try:
        result = models.execute_kw(db, uid, password,
            'sap.uom.group', 'action_sync_from_sap',
            [[group_id]]
        )
        
        success_count += 1
        
        if i % 20 == 0:
            elapsed = time.time() - start
            avg = elapsed / i
            remaining = (len(groups) - i) * avg
            print("[%d/%d] Progress: %.0f%%, Est. remaining: %.1f min" % (
                i, len(groups), i*100/len(groups), remaining/60
            ))
        
    except Exception as e:
        error_count += 1
        if 'No UoM definitions' in str(e):
            pass  # Silent - group is empty in SAP
        else:
            if error_count <= 5:
                print("   Error on group %d: %s" % (group_id, str(e)[:80]))

duration = time.time() - start

# Check after
after = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])

print("\n" + "=" * 100)
print("COMPLETE!")
print("=" * 100)
print("\nTime: %.2f minutes" % (duration/60))
print("Processed: %d groups" % success_count)
print("Errors: %d" % error_count)
print("\nUoM Syncs:")
print("   Before: %d" % before)
print("   After: %d" % after)
print("   Created: %d" % (after - before))

# Final stats
groups_data = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['name', 'uom_count'], 'order': 'uom_count desc', 'limit': 15}
)

print("\nTop 15 Groups by UoM count:")
for g in groups_data:
    print("   %s: %d UoMs" % (g['name'][:45].ljust(45), g.get('uom_count', 0)))

# Groups with UoMs
groups_with_uoms = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_count',
    [[('uom_count', '>', 0)]]
)

print("\nGroups with UoMs: %d/%d (%.0f%%)" % (
    groups_with_uoms, 169, groups_with_uoms*100/169
))

print("\n" + "=" * 100)
if after >= 100:
    print("✅✅✅ EXCELLENT! Got %d UoMs!" % after)
elif after > before:
    print("✅ SUCCESS! Improved from %d to %d UoMs" % (before, after))
else:
    print("⚠️ No change: %d UoMs" % after)
print("=" * 100)


