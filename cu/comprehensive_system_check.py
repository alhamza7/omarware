#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive System Check - Full Verification
Checks everything: Groups, UoMs, Links, Factors, Integration
"""

import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("COMPREHENSIVE SYSTEM CHECK - FULL VERIFICATION")
print("=" * 100)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected (User ID: %d)" % uid)

# ============================================================================
# TEST 1: Models Existence
# ============================================================================
print("\n" + "=" * 100)
print("TEST 1: MODELS EXISTENCE")
print("=" * 100)

tests_passed = 0
tests_total = 0

# Check sap.uom.group
tests_total += 1
try:
    group_count = models.execute_kw(db, uid, password, 'sap.uom.group', 'search_count', [[]])
    print("\n✅ sap.uom.group: EXISTS (%d records)" % group_count)
    tests_passed += 1
except Exception as e:
    print("\n❌ sap.uom.group: FAILED - %s" % str(e)[:80])

# Check sap.uom.sync
tests_total += 1
try:
    sync_count = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])
    print("✅ sap.uom.sync: EXISTS (%d records)" % sync_count)
    tests_passed += 1
except Exception as e:
    print("❌ sap.uom.sync: FAILED - %s" % str(e)[:80])

# Check field sap_group_id exists
tests_total += 1
try:
    fields = models.execute_kw(db, uid, password,
        'ir.model.fields', 'search_count',
        [[('model', '=', 'sap.uom.sync'), ('name', '=', 'sap_group_id')]]
    )
    if fields > 0:
        print("✅ sap.uom.sync.sap_group_id: FIELD EXISTS")
        tests_passed += 1
    else:
        print("❌ sap.uom.sync.sap_group_id: FIELD NOT FOUND")
except Exception as e:
    print("❌ Field check failed: %s" % str(e)[:80])

# ============================================================================
# TEST 2: Data Quality
# ============================================================================
print("\n" + "=" * 100)
print("TEST 2: DATA QUALITY")
print("=" * 100)

# Get all groups
groups = models.execute_kw(db, uid, password,
    'sap.uom.group', 'search_read',
    [[]],
    {'fields': ['id', 'sap_abs_entry', 'uom_count']}
)

# Get all syncs
syncs = models.execute_kw(db, uid, password,
    'sap.uom.sync', 'search_read',
    [[]],
    {'fields': ['sap_uom_entry', 'sap_group_id', 'odoo_uom_id']}
)

# Statistics
groups_with_uoms = sum(1 for g in groups if g.get('uom_count', 0) > 0)
syncs_with_entry = sum(1 for s in syncs if s.get('sap_uom_entry') and s['sap_uom_entry'] != 0)
syncs_with_group = sum(1 for s in syncs if s.get('sap_group_id'))
syncs_with_odoo = sum(1 for s in syncs if s.get('odoo_uom_id'))

print("\nGroups Quality:")
print("   Total groups: %d" % len(groups))
tests_total += 1
if len(groups) >= 160:
    print("   ✅ PASS: Got 160+ groups (%d)" % len(groups))
    tests_passed += 1
else:
    print("   ❌ FAIL: Expected 160+, got %d" % len(groups))

print("   Groups with UoMs: %d/%d (%.0f%%)" % (
    groups_with_uoms, len(groups), 
    groups_with_uoms*100/len(groups) if groups else 0
))

print("\nUoM Syncs Quality:")
print("   Total syncs: %d" % len(syncs))

tests_total += 1
if syncs_with_entry == len(syncs):
    print("   ✅ PASS: All have SAP Entry (%d/%d)" % (syncs_with_entry, len(syncs)))
    tests_passed += 1
else:
    print("   ❌ FAIL: SAP Entry %d/%d" % (syncs_with_entry, len(syncs)))

tests_total += 1
if syncs_with_group >= len(syncs) * 0.8:  # At least 80%
    print("   ✅ PASS: Group linking good (%d/%d = %.0f%%)" % (
        syncs_with_group, len(syncs), syncs_with_group*100/len(syncs)
    ))
    tests_passed += 1
else:
    print("   ❌ FAIL: Group linking poor (%d/%d = %.0f%%)" % (
        syncs_with_group, len(syncs), syncs_with_group*100/len(syncs)
    ))

tests_total += 1
if syncs_with_odoo >= len(syncs) * 0.5:  # At least 50%
    print("   ✅ PASS: Odoo UoM linking good (%d/%d = %.0f%%)" % (
        syncs_with_odoo, len(syncs), syncs_with_odoo*100/len(syncs)
    ))
    tests_passed += 1
else:
    print("   ❌ FAIL: Odoo UoM linking poor (%d/%d = %.0f%%)" % (
        syncs_with_odoo, len(syncs), syncs_with_odoo*100/len(syncs)
    ))

# ============================================================================
# TEST 3: Conversion Factors
# ============================================================================
print("\n" + "=" * 100)
print("TEST 3: CONVERSION FACTORS")
print("=" * 100)

if syncs_with_odoo > 0:
    uom_ids = [s['odoo_uom_id'][0] for s in syncs if s.get('odoo_uom_id')]
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[('id', 'in', uom_ids)]],
        {'fields': ['name', 'factor']}
    )
    
    factors_not_one = [u for u in uoms if abs(u.get('factor', 1.0) - 1.0) > 0.001]
    
    print("\nTotal Odoo UoMs: %d" % len(uoms))
    print("With factor = 1.0: %d" % (len(uoms) - len(factors_not_one)))
    print("With factor != 1.0: %d" % len(factors_not_one))
    
    tests_total += 1
    if len(factors_not_one) >= 5:  # At least 5 UoMs with conversion
        print("\n✅ PASS: Conversion factors present (%d UoMs)" % len(factors_not_one))
        tests_passed += 1
        
        print("\nSample factors:")
        for u in factors_not_one[:10]:
            print("   %s: %.6f" % (u['name'][:35].ljust(35), u['factor']))
    else:
        print("\n❌ FAIL: Not enough conversion factors (%d)" % len(factors_not_one))

# ============================================================================
# TEST 4: Integration with Core Modules
# ============================================================================
print("\n" + "=" * 100)
print("TEST 4: INTEGRATION WITH CORE MODULES")
print("=" * 100)

# Check if products exist
tests_total += 1
product_count = models.execute_kw(db, uid, password,
    'product.product', 'search_count',
    [[('default_code', '!=', False)]]
)
if product_count > 0:
    print("\n✅ PASS: Products exist (%d)" % product_count)
    tests_passed += 1
else:
    print("\n❌ FAIL: No products found")

# Check if pricelists exist
tests_total += 1
pricelist_count = models.execute_kw(db, uid, password,
    'product.pricelist', 'search_count', [[]]
)
if pricelist_count > 0:
    print("✅ PASS: Pricelists exist (%d)" % pricelist_count)
    tests_passed += 1
else:
    print("❌ FAIL: No pricelists found")

# Check SAP backend
tests_total += 1
backend_count = models.execute_kw(db, uid, password,
    'sap.backend', 'search_count',
    [[('active', '=', True)]]
)
if backend_count > 0:
    print("✅ PASS: SAP Backend active (%d)" % backend_count)
    tests_passed += 1
else:
    print("❌ FAIL: No active SAP backend")

# ============================================================================
# TEST 5: Sample Data Verification
# ============================================================================
print("\n" + "=" * 100)
print("TEST 5: SAMPLE DATA VERIFICATION")
print("=" * 100)

# Get a group with UoMs
groups_with_uoms = [g for g in groups if g.get('uom_count', 0) > 0]

if groups_with_uoms:
    sample_group = groups_with_uoms[0]
    group_full = models.execute_kw(db, uid, password,
        'sap.uom.group', 'read',
        [[sample_group['id']]],
        {'fields': ['name', 'uom_count', 'uom_ids']}
    )[0]
    
    print("\nSample Group: %s" % group_full['name'])
    print("   UoM Count: %d" % group_full.get('uom_count', 0))
    
    if group_full.get('uom_ids'):
        uom_ids_in_group = group_full['uom_ids']
        uoms_in_group = models.execute_kw(db, uid, password,
            'sap.uom.sync', 'read',
            [uom_ids_in_group],
            {'fields': ['sap_uom_id', 'sap_uom_entry', 'odoo_uom_id']}
        )
        
        print("\n   UoMs in this group:")
        for u in uoms_in_group[:5]:
            odoo_name = u['odoo_uom_id'][1] if u.get('odoo_uom_id') else 'NOT LINKED'
            print("      - %s (Entry: %d) -> %s" % (
                u['sap_uom_id'],
                u.get('sap_uom_entry', 0),
                odoo_name
            ))
        
        tests_total += 1
        if len(uoms_in_group) > 0:
            print("\n   ✅ PASS: Group contains UoMs")
            tests_passed += 1
        else:
            print("\n   ❌ FAIL: Group empty")
    else:
        print("   ⚠️ No UoMs in sample group")

# ============================================================================
# FINAL SCORE
# ============================================================================
print("\n" + "=" * 100)
print("FINAL SCORE")
print("=" * 100)

score_percentage = (tests_passed * 100 / tests_total) if tests_total > 0 else 0

print("\nTests Passed: %d/%d (%.0f%%)" % (tests_passed, tests_total, score_percentage))

if score_percentage >= 90:
    print("\n✅✅✅ EXCELLENT! System is fully operational!")
    print("\nAll major components working:")
    print("   ✅ Models created and loaded")
    print("   ✅ Data imported from SAP")
    print("   ✅ Relationships established")
    print("   ✅ Conversion factors active")
    print("   ✅ Integration with core modules")
    print("\n🎉 SYSTEM READY FOR PRODUCTION USE! 🎉")
elif score_percentage >= 70:
    print("\n✅ GOOD! System is mostly operational")
    print("   Some minor issues but ready to use")
elif score_percentage >= 50:
    print("\n⚠️ PARTIAL: System needs attention")
    print("   Works but with limitations")
else:
    print("\n❌ CRITICAL: System has major issues")
    print("   Needs immediate attention")

print("\n" + "=" * 100)
print("DETAILED SUMMARY")
print("=" * 100)

print("\n📊 Current Data:")
print("   - UoM Groups: %d" % len(groups))
print("   - UoM Syncs: %d" % len(syncs))
print("   - Products: %d" % product_count)
print("   - Pricelists: %d" % pricelist_count)

print("\n📈 Quality Metrics:")
print("   - SAP Entries: %d/%d (%.0f%%)" % (
    syncs_with_entry, len(syncs), 
    syncs_with_entry*100/len(syncs) if syncs else 0
))
print("   - Group Links: %d/%d (%.0f%%)" % (
    syncs_with_group, len(syncs),
    syncs_with_group*100/len(syncs) if syncs else 0
))
print("   - Odoo Links: %d/%d (%.0f%%)" % (
    syncs_with_odoo, len(syncs),
    syncs_with_odoo*100/len(syncs) if syncs else 0
))
print("   - Conversion Factors: %d/%d (%.0f%%)" % (
    len(factors_not_one), len(uoms),
    len(factors_not_one)*100/len(uoms) if uoms else 0
))

print("\n🎯 System Status:")
if tests_passed == tests_total:
    print("   ✅ ALL SYSTEMS GO - PERFECT!")
elif tests_passed >= tests_total * 0.9:
    print("   ✅ OPERATIONAL - Excellent!")
elif tests_passed >= tests_total * 0.7:
    print("   ✅ FUNCTIONAL - Good!")
else:
    print("   ⚠️ NEEDS ATTENTION")

print("\n" + "=" * 100)




