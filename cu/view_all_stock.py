#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""View All Stock - Complete List"""

print("=" * 80)
print("ALL STOCK QUANTITIES")
print("=" * 80)
print()

cr = env.cr

# Get all stock with location names
cr.execute("""
    SELECT 
        pp.default_code,
        sq.quantity,
        sl.id as location_id,
        sl.name as location_name
    FROM stock_quant sq
    JOIN product_product pp ON sq.product_id = pp.id
    JOIN stock_location sl ON sq.location_id = sl.id
    WHERE sq.quantity > 0
    AND pp.default_code IS NOT NULL
    ORDER BY sq.quantity DESC
    LIMIT 50
""")

print("Top 50 products by quantity:")
print("-" * 80)
print(f"{'Product':<15} {'Quantity':<12} {'Location ID':<12} {'Location Name'}")
print("-" * 80)

for code, qty, loc_id, loc_name in cr.fetchall():
    print(f"{code:<15} {qty:<12.2f} {loc_id:<12} {loc_name}")

print()
print("=" * 80)
print("HOW TO VIEW IN ODOO:")
print("=" * 80)
print("1. Go to: Inventory > Operations > On Hand")
print("2. Remove all filters")
print("3. Search for a product code (e.g., ADF00002)")
print("4. You will see it with quantities in different locations")
print()
print("OR")
print()
print("1. Go to: Inventory > Products > Products")
print("2. Open any product")
print("3. Click the blue 'On Hand' button")
print("4. You will see quantities by location")
print("=" * 80)

exit()






