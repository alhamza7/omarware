#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync ALL 169 Groups to extract ALL UoMs
This will take ~10-30 minutes as it processes each group individually
"""

import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("SYNC ALL 169 GROUPS - GET ALL UoMs")
print("=" * 100)
print("\n⚠️ WARNING: This will take 10-30 minutes!")
print("   It will fetch details for each of 169 groups")
print()
print("Benefits:")
print("   ✅ Will get ALL UoMs from SAP (hundreds)")
print("   ✅ All groups will have proper UoM count")
print("   ✅ All conversion factors extracted")
print()

response = input("Continue? (y/n): ")
if response.lower() != 'y':
    print("Cancelled.")
    exit(0)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected")

# Get all groups
groups = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'sap_abs_entry', 'uom_count']}
)

print("\nFound %d groups" % len(groups))

# Process each group
start_total = time.time()
processed = 0
total_uoms_created = 0

for i, group in enumerate(groups, 1):
    if group.get('sap_abs_entry') in [-1, None]:
        continue
    
    print("\n[%d/%d] Processing: %s (Entry: %d, Current UoMs: %d)" % (
        i, len(groups),
        group['name'][:40],
        group.get('sap_abs_entry', 0),
        group.get('uom_count', 0)
    ))
    
    try:
        # Call action_sync_from_sap for this group
        result = models.execute_kw(db, uid, password,
            'sap.uom.group', 'action_sync_from_sap',
            [[group['id']]]
        )
        
        # Check result
        if result and 'params' in result:
            message = result['params'].get('message', '')
            print("   %s" % message)
            
            # Extract numbers from message
            if 'Created' in message:
                # Try to parse number
                import re
                match = re.search(r'Created (\d+)', message)
                if match:
                    created = int(match.group(1))
                    total_uoms_created += created
        
        processed += 1
        
        # Progress update every 10 groups
        if i % 10 == 0:
            elapsed = time.time() - start_total
            avg_time = elapsed / processed if processed > 0 else 0
            remaining = (len(groups) - i) * avg_time
            print("\n   Progress: %d/%d (%.0f%%), Est. remaining: %.1f minutes" % (
                i, len(groups), i*100/len(groups), remaining/60
            ))
        
    except Exception as e:
        print("   ❌ Error: %s" % str(e)[:100])

duration = time.time() - start_total

print("\n" + "=" * 100)
print("COMPLETE!")
print("=" * 100)
print("\nProcessed: %d groups in %.2f minutes" % (processed, duration/60))
print("Total UoMs created: ~%d" % total_uoms_created)

# Final check
final_syncs = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])
print("\nFinal UoM Syncs: %d" % final_syncs)

print("\n" + "=" * 100)


