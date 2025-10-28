#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check where stock quants are located"""

print("=" * 80)
print("STOCK LOCATIONS CHECK")
print("=" * 80)
print()

cr = env.cr

# Find where the stock quants are
cr.execute("""
    SELECT 
        sl.id,
        sl.name,
        sl.usage,
        COUNT(sq.id) as quant_count,
        SUM(sq.quantity) as total_qty
    FROM stock_quant sq
    JOIN stock_location sl ON sq.location_id = sl.id
    WHERE sq.quantity > 0
    GROUP BY sl.id, sl.name, sl.usage
    ORDER BY COUNT(sq.id) DESC
    LIMIT 20
""")

print("Locations with stock:")
print("-" * 80)
for row in cr.fetchall():
    loc_id, loc_name, usage, count, total = row
    print(f"Location ID: {loc_id}")
    print(f"  Name: {loc_name}")
    print(f"  Usage: {usage}")
    print(f"  Products: {count}")
    print(f"  Total Qty: {total}")
    print()

# Check if these locations are linked to warehouses
print("=" * 80)
print("Checking warehouse linkage...")
print("-" * 80)

cr.execute("""
    SELECT 
        sw.id,
        sw.name,
        sw.code,
        sl.id as lot_stock_id
    FROM stock_warehouse sw
    JOIN stock_location sl ON sw.lot_stock_id = sl.id
""")

print("Warehouses and their stock locations:")
for row in cr.fetchall():
    wh_id, wh_name, wh_code, loc_id = row
    
    # Count quants in this location
    cr.execute(f"""
        SELECT COUNT(*), SUM(quantity)
        FROM stock_quant
        WHERE location_id = {loc_id} AND quantity > 0
    """)
    count, qty = cr.fetchone()
    
    print(f"Warehouse: {wh_name} (Code: {wh_code})")
    print(f"  Stock Location ID: {loc_id}")
    print(f"  Products with stock: {count or 0}")
    print(f"  Total quantity: {qty or 0}")
    print()

print("=" * 80)
print("SOLUTION:")
print("=" * 80)
print("The stock is in locations that may not be linked to warehouses")
print("You can view it in: Inventory > Operations > On Hand")
print("Filter by: Location or Product")
print("=" * 80)

exit()




