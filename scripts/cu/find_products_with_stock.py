#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find Products with Stock in SAP Warehouse Info"""

cr = env.cr

print("=" * 80)
print("PRODUCTS WITH STOCK IN SAP WAREHOUSE INFO")
print("=" * 80)
print()

# Find products with highest stock
cr.execute("""
    SELECT 
        product_code,
        SUM(last_in_stock) as total_stock,
        SUM(last_available) as total_available,
        COUNT(*) as warehouse_count
    FROM sap_product_warehouse_info
    WHERE last_in_stock > 0
    GROUP BY product_code
    ORDER BY SUM(last_in_stock) DESC
    LIMIT 20
""")

print("Top 20 products by stock quantity:")
print("-" * 80)
print(f"{'Product':<15} {'Total Stock':<15} {'Available':<15} {'Warehouses'}")
print("-" * 80)

for code, stock, available, wh_count in cr.fetchall():
    print(f"{code:<15} {stock:<15.2f} {available:<15.2f} {wh_count}")

print()
print("=" * 80)
print("TRY THESE PRODUCTS IN ODOO UI:")
print("=" * 80)
print("1. Go to: SAP Integration > Warehouse > Product Warehouse Info")
print("2. Search for any product code from above")
print("3. You will see all warehouses for that product")
print()
print("OR")
print()
print("1. Go to: Inventory > Products > Products")
print("2. Search: PK00075 (has 998,588 pieces)")
print("3. Click Inventory tab")
print("=" * 80)

exit()






