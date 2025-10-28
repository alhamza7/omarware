#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check stock quants"""

print("=" * 80)
print("STOCK QUANTS CHECK")
print("=" * 80)
print()

cr = env.cr

# Check warehouse info
cr.execute("SELECT COUNT(*) FROM sap_product_warehouse_info")
warehouse_count = cr.fetchone()[0]

# Check stock quants
cr.execute("SELECT COUNT(*) FROM stock_quant WHERE quantity > 0")
quant_count = cr.fetchone()[0]

print(f"Warehouse Info records: {warehouse_count}")
print(f"Stock Quants (qty > 0): {quant_count}")
print()

if quant_count > 0:
    print("Sample stock quants:")
    cr.execute("""
        SELECT sq.product_id, pp.default_code, sq.quantity, sq.location_id
        FROM stock_quant sq
        JOIN product_product pp ON sq.product_id = pp.id
        WHERE sq.quantity > 0
        LIMIT 10
    """)
    
    for row in cr.fetchall():
        print(f"  Product: {row[1]}, Qty: {row[2]}, Location: {row[3]}")
else:
    print("NO stock quants found!")
    print("The warehouse data needs to be synced to stock.quant")

print()
print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
if quant_count == 0:
    print("  Problem: Warehouse info exists but NOT synced to stock.quant")
    print("  Solution: Need to run sync from warehouse info to stock")
else:
    print("  Stock quants are populated correctly")
print("=" * 80)

exit()




