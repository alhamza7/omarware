#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed analysis of UoM Groups, Definitions, and Syncs
Shows exactly what we have and why linking may not be working
"""

import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("DETAILED UoM DATA ANALYSIS")
print("=" * 100)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected")

# Get all groups
groups = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['id', 'name', 'sap_abs_entry', 'base_uom_code', 'uom_count'], 'order': 'sap_abs_entry', 'limit': 10}
)

# Get all syncs
syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['id', 'sap_uom_id', 'sap_uom_entry', 'sap_group_id', 'odoo_uom_id'], 'order': 'sap_uom_entry'}
)

print("\n" + "=" * 100)
print("PART 1: UoM GROUPS")
print("=" * 100)

print("\nTotal Groups: %d" % len(models.execute_kw(db, uid, password, 'sap.uom.group', 'search', [[]])))
print("\nFirst 10 Groups:")
print("%-5s %-8s %-40s %-10s %s" % ("ID", "Entry", "Name", "BaseUoM", "UoMs"))
print("-" * 100)

for g in groups:
    print("%-5d %-8d %-40s %-10s %d" % (
        g['id'],
        g.get('sap_abs_entry', 0),
        g['name'][:40],
        str(g.get('base_uom_code', 'N/A'))[:10],
        g.get('uom_count', 0)
    ))

print("\n" + "=" * 100)
print("PART 2: UoM SYNCS")
print("=" * 100)

print("\nTotal Syncs: %d" % len(syncs))
print("\nAll UoM Syncs:")
print("%-5s %-8s %-25s %-10s %-30s" % ("ID", "Entry", "SAP UoM", "Group?", "Odoo UoM"))
print("-" * 100)

for s in syncs:
    has_group = "YES (ID:%d)" % s['sap_group_id'][0] if s.get('sap_group_id') else "NO"
    has_odoo = s['odoo_uom_id'][1] if s.get('odoo_uom_id') else "NOT LINKED"
    
    print("%-5d %-8d %-25s %-10s %-30s" % (
        s['id'],
        s.get('sap_uom_entry', 0),
        s['sap_uom_id'][:25],
        has_group[:10],
        has_odoo[:30]
    ))

print("\n" + "=" * 100)
print("PART 3: CROSS-REFERENCE ANALYSIS")
print("=" * 100)

# Create mapping
entry_to_sync = {s['sap_uom_entry']: s for s in syncs if s.get('sap_uom_entry')}

print("\nUoM Entries we have in sap.uom.sync:")
print("Entries: %s" % sorted(list(entry_to_sync.keys())))

print("\n\nNow let's check what SAP says...")
print("(This requires checking odoo.log for UoMGroupDefinitionCollection data)")
print()
print("From logs, we saw definitions with AlternateUoM entries.")
print("We need to match these AlternateUoM values with our sap_uom_entry values.")
print()

# Summary statistics
with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
with_group = sum(1 for s in syncs if s.get('sap_group_id'))
with_odoo = sum(1 for s in syncs if s.get('odoo_uom_id'))

print("=" * 100)
print("STATISTICS:")
print("=" * 100)
print("Total UoM Syncs: %d" % len(syncs))
print("   - With SAP Entry (!=0): %d (%.0f%%)" % (with_entry, with_entry*100/len(syncs) if syncs else 0))
print("   - With Group Link: %d (%.0f%%)" % (with_group, with_group*100/len(syncs) if syncs else 0))
print("   - With Odoo UoM: %d (%.0f%%)" % (with_odoo, with_odoo*100/len(syncs) if syncs else 0))

print("\n" + "=" * 100)
print("DIAGNOSIS:")
print("=" * 100)

if with_entry == len(syncs):
    print("✅ All UoMs have SAP Entry - GOOD")
else:
    print("❌ Some UoMs missing SAP Entry")

if with_group == 0:
    print("❌ NO UoMs linked to Groups - THIS IS THE PROBLEM")
    print()
    print("Possible reasons:")
    print("1. AlternateUoM values in Definitions don't match sap_uom_entry values")
    print("2. Code logic issue in processing loop")
    print("3. UoM sync records created AFTER group processing")
else:
    print("✅ Some UoMs linked to Groups")

# Let's create a diagnostic script for Odoo shell
print("\n" + "=" * 100)
print("NEXT STEP: RUN THIS IN ODOO SHELL")
print("=" * 100)

shell_script = """
# Run: python odoo-bin shell -c odoo.conf -d lugal

backend = env['sap.backend'].browse(2)
connection = backend.get_connection()

# Get one group with details
response = connection.get('UnitOfMeasurementGroups(2)', {})
defs = response.get('UoMGroupDefinitionCollection', [])

print("Group 2 has %%d definitions" %% len(defs))
print()

# Show what AlternateUoM values we get
print("AlternateUoM entries in Group 2:")
for d in defs:
    alt_uom = d.get('AlternateUoM')
    base_qty = d.get('BaseQuantity')
    alt_qty = d.get('AlternateQuantity')
    factor = base_qty / alt_qty if alt_qty != 0 else 1.0
    print(f"   AlternateUoM: {alt_uom}, Factor: {factor:.4f} ({alt_qty} = {base_qty} base)")

print()
print("Now checking if these entries exist in sap.uom.sync:")
for d in defs:
    alt_uom = d.get('AlternateUoM')
    sync = env['sap.uom.sync'].search([
        ('sap_uom_entry', '=', alt_uom),
        ('backend_id', '=', 2)
    ])
    
    if sync:
        print(f"   ✓ Entry {alt_uom}: FOUND -> {sync.sap_uom_id}")
    else:
        print(f"   ✗ Entry {alt_uom}: NOT FOUND in sap.uom.sync")
"""

with open('diagnose_matching.py', 'w', encoding='utf-8') as f:
    f.write(shell_script)

print()
print("Saved to: diagnose_matching.py")
print()
print("Run in new terminal:")
print("   python odoo-bin shell -c odoo.conf -d lugal")
print()
print("Then:")
print("   exec(open('diagnose_matching.py').read())")
print()
print("=" * 100)


