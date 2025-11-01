#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enable All Products for Sales and POS"""

print("=" * 80)
print("ENABLE ALL PRODUCTS FOR SALES & POS")
print("=" * 80)
print()

cr = env.cr

# 1. Check current state
print("Step 1: Current state...")
cr.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN pt.sale_ok = true THEN 1 END) as can_sell,
        COUNT(CASE WHEN pt.available_in_pos = true THEN 1 END) as in_pos
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
""")

total, can_sell, in_pos = cr.fetchone()
print(f"  Total products: {total}")
print(f"  Can be sold: {can_sell}")
print(f"  Available in POS: {in_pos}")
print()

# 2. Update ALL products
print("Step 2: Enabling all products for Sales & POS...")

cr.execute("""
    UPDATE product_template pt
    SET 
        sale_ok = true,
        available_in_pos = true,
        active = true
    FROM product_product pp
    WHERE pp.product_tmpl_id = pt.id
    AND pp.default_code IS NOT NULL
    AND pp.default_code != ''
""")

updated = cr.rowcount
env.cr.commit()

print(f"  Updated {updated} product templates")
print()

# 3. Verify
print("Step 3: Verification...")
cr.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN pt.sale_ok = true THEN 1 END) as can_sell,
        COUNT(CASE WHEN pt.available_in_pos = true THEN 1 END) as in_pos,
        COUNT(CASE WHEN pt.active = true THEN 1 END) as active
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
""")

total, can_sell, in_pos, active = cr.fetchone()

print("After update:")
print(f"  Total products: {total}")
print(f"  Can be sold: {can_sell} ({can_sell/total*100:.1f}%)")
print(f"  Available in POS: {in_pos} ({in_pos/total*100:.1f}%)")
print(f"  Active: {active} ({active/total*100:.1f}%)")
print()

print("=" * 80)
print("SUCCESS!")
print("=" * 80)
print()
print(f"ALL {total} PRODUCTS ARE NOW:")
print("  - Can be sold: YES")
print("  - Available in POS: YES")
print("  - Active: YES")
print()
print("You can now:")
print("  - Use all products in Sales orders")
print("  - Use all products in Point of Sale")
print("  - Products visible in POS interface")
print()
print("=" * 80)

exit()





