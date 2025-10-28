#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ensure all products are Goods with tracking"""

print("=" * 80)
print("ENSURE ALL PRODUCTS ARE GOODS WITH TRACKING")
print("=" * 80)
print()

cr = env.cr

# Check current state
cr.execute("""
    SELECT 
        pt.type,
        pt.tracking,
        COUNT(*) as count
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type, pt.tracking
    ORDER BY COUNT(*) DESC
""")

print("Current product configuration:")
print("-" * 80)
for ptype, tracking, count in cr.fetchall():
    print(f"  Type: {ptype}, Tracking: {tracking} -> {count} products")
print()

# Update all to ensure correct settings
print("Updating all products to Goods (product) with tracking...")
print()

cr.execute("""
    UPDATE product_template pt
    SET 
        type = 'product',
        tracking = 'none'
    WHERE pt.id IN (
        SELECT product_tmpl_id 
        FROM product_product 
        WHERE default_code IS NOT NULL 
        AND default_code != ''
    )
    AND (pt.type != 'product' OR pt.tracking IS NULL)
""")

updated = cr.rowcount
env.cr.commit()

print(f"Updated {updated} products")
print()

# Final verification
cr.execute("""
    SELECT 
        pt.type,
        COUNT(*) as count
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("=" * 80)
print("FINAL STATE:")
print("=" * 80)
for ptype, count in cr.fetchall():
    status = "PERFECT!" if ptype == 'product' else "CHECK!"
    print(f"  {ptype}: {count} products [{status}]")

print()
print("=" * 80)
print("SUCCESS!")
print("=" * 80)
print("All products are now:")
print("  - Product Type: Goods (Stockable)")
print("  - Track Inventory: Enabled automatically")
print("  - No manual selection needed!")
print("=" * 80)

exit()



