#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update ALL Existing Products - Complete Fix"""

print("=" * 80)
print("UPDATE ALL EXISTING PRODUCTS")
print("=" * 80)
print()

cr = env.cr

# 1. Check current state
print("Step 1: Checking current state...")
cr.execute("""
    SELECT 
        pt.type,
        COUNT(DISTINCT pp.id) as product_count,
        COUNT(DISTINCT pt.id) as template_count
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("Current state:")
for ptype, prod_count, tmpl_count in cr.fetchall():
    print(f"  Type '{ptype}': {prod_count} products, {tmpl_count} templates")
print()

# 2. Update ALL product templates to be stockable
print("Step 2: Updating ALL products to Goods (Stockable)...")
cr.execute("""
    UPDATE product_template pt
    SET 
        type = 'product',
        tracking = 'none'
    FROM product_product pp
    WHERE pp.product_tmpl_id = pt.id
    AND pp.default_code IS NOT NULL
    AND pp.default_code != ''
""")

updated = cr.rowcount
print(f"  Updated {updated} product templates")
env.cr.commit()
print()

# 3. Verify update
print("Step 3: Verifying updates...")
cr.execute("""
    SELECT 
        pt.type,
        COUNT(DISTINCT pp.id) as product_count
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("After update:")
all_correct = True
for ptype, count in cr.fetchall():
    status = "OK" if ptype == 'product' else "ERROR"
    print(f"  Type '{ptype}': {count} products [{status}]")
    if ptype != 'product':
        all_correct = False
print()

# 4. Count products with specific features
print("Step 4: Checking product features...")

cr.execute("""
    SELECT COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pt.type = 'product'
""")
stockable_count = cr.fetchone()[0]

cr.execute("""
    SELECT COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pt.sale_ok = true
""")
saleable_count = cr.fetchone()[0]

cr.execute("""
    SELECT COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pt.available_in_pos = true
""")
pos_count = cr.fetchone()[0]

print(f"  Stockable products: {stockable_count}")
print(f"  Can be sold: {saleable_count}")
print(f"  Available in POS: {pos_count}")
print()

print("=" * 80)
print("FINAL RESULT:")
print("=" * 80)

if all_correct and stockable_count > 0:
    print("  SUCCESS! All products updated successfully!")
    print()
    print("  ALL PRODUCTS NOW:")
    print("    - Product Type: Goods (Stockable)")
    print("    - Track Inventory: Enabled")
    print("    - Can have stock quantities: YES")
    print("    - Visible in Inventory: YES")
    print()
    print("  You can now:")
    print("    - Track inventory for all products")
    print("    - View quantities in Inventory > On Hand")
    print("    - Use in POS with stock tracking")
else:
    print("  WARNING: Some products may need manual review")

print("=" * 80)

exit()





