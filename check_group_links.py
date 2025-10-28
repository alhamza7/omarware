#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("Checking UoM Groups and Links")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Count groups
group_count = models.execute_kw(db, uid, password, 'sap.uom.group', 'search_count', [[]])
print("\nTotal UoM Groups: %d" % group_count)

# Get sample groups
groups = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['name', 'sap_abs_entry', 'base_uom_code', 'uom_count'], 'limit': 10, 'order': 'uom_count desc'}
)

print("\nTop 10 Groups (by UoM count):")
print("%-40s %s %s %s" % ("Name", "Entry", "Base", "UoMs"))
print("-" * 80)
for g in groups:
    print("%-40s %5d %-10s %3d" % (
        g['name'][:40],
        g.get('sap_abs_entry', 0),
        g.get('base_uom_code', 'N/A')[:10],
        g.get('uom_count', 0)
    ))

# Check UoM syncs with group links
syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['sap_uom_id', 'sap_uom_entry', 'sap_group_id', 'odoo_uom_id']}
)

with_group = sum(1 for s in syncs if s.get('sap_group_id'))
with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
with_odoo = sum(1 for s in syncs if s.get('odoo_uom_id'))

print("\n" + "=" * 80)
print("UoM Sync Status:")
print("=" * 80)
print("Total: %d" % len(syncs))
print("With SAP Entry (!= 0): %d/%d (%.0f%%)" % (with_entry, len(syncs), with_entry*100/len(syncs) if syncs else 0))
print("With Group Link: %d/%d (%.0f%%)" % (with_group, len(syncs), with_group*100/len(syncs) if syncs else 0))
print("With Odoo UoM: %d/%d (%.0f%%)" % (with_odoo, len(syncs), with_odoo*100/len(syncs) if syncs else 0))

# Show linked ones
if with_group > 0:
    print("\nUoMs linked to Groups:")
    linked = [s for s in syncs if s.get('sap_group_id')]
    for s in linked[:10]:
        group_name = s['sap_group_id'][1] if s.get('sap_group_id') else 'N/A'
        print("   %s -> %s" % (s['sap_uom_id'], group_name))

# Check factors
if with_odoo > 0:
    uom_ids = [s['odoo_uom_id'][0] for s in syncs if s.get('odoo_uom_id')]
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[('id', 'in', uom_ids)]],
        {'fields': ['name', 'factor']}
    )
    
    non_one = [u for u in uoms if abs(u.get('factor', 1.0) - 1.0) > 0.001]
    
    print("\n" + "=" * 80)
    print("Conversion Factors:")
    print("=" * 80)
    print("Total UoMs: %d" % len(uoms))
    print("With factor = 1.0: %d" % (len(uoms) - len(non_one)))
    print("With factor != 1.0: %d" % len(non_one))
    
    if non_one:
        print("\nFactors found:")
        for u in non_one[:10]:
            print("   %s: %.6f" % (u['name'], u['factor']))

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if with_group > 0 and len(non_one) > 0:
    print("✅ UoMs ARE linked to Groups")
    print("✅ Conversion factors ARE present")
elif with_group > 0:
    print("✅ UoMs ARE linked to Groups")
    print("❌ But NO conversion factors")
else:
    print("❌ UoMs are NOT linked to Groups")
    print("❌ NO conversion factors")

print("=" * 80)


