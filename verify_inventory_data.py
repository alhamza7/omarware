#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Inventory Data"""

print("=" * 80)
print("INVENTORY DATA VERIFICATION")
print("=" * 80)
print()

# 1. Check stock quants
quants = env['stock.quant'].search([('quantity', '>', 0)])
print(f"1. Stock Quants (qty > 0): {len(quants)}")
print()

if len(quants) > 0:
    print("Sample quants with location names:")
    for quant in quants[:10]:
        product = quant.product_id
        location = quant.location_id
        print(f"  Product: {product.default_code} - {product.name}")
        print(f"    Location: {location.complete_name}")
        print(f"    Quantity: {quant.quantity}")
        print(f"    Reserved: {quant.reserved_quantity}")
        print()

# 2. Check warehouses
warehouses = env['stock.warehouse'].search([])
print(f"2. Warehouses in Odoo: {len(warehouses)}")
for wh in warehouses:
    print(f"  - {wh.name} (Code: {wh.code})")
print()

# 3. Check locations
locations = env['stock.location'].search([('usage', '=', 'internal')])
print(f"3. Internal Locations: {len(locations)}")
for loc in locations[:10]:
    quant_count = env['stock.quant'].search_count([
        ('location_id', '=', loc.id),
        ('quantity', '>', 0)
    ])
    print(f"  - {loc.complete_name}: {quant_count} products with stock")
print()

# 4. Check if SAP warehouse info has warehouse_id
warehouse_info = env['sap.product.warehouse.info'].search([], limit=10)
print(f"4. Checking SAP Warehouse Info:")
has_warehouse = 0
no_warehouse = 0
for info in warehouse_info:
    if info.warehouse_id:
        has_warehouse += 1
    else:
        no_warehouse += 1

print(f"  Records with warehouse_id: {has_warehouse}")
print(f"  Records without warehouse_id: {no_warehouse}")
print()

if no_warehouse > 0:
    print("  PROBLEM: SAP warehouse names not linked to Odoo warehouses!")
    print("  SOLUTION: Need to create warehouses and link them")

print()
print("=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"  Stock Quants: {len(quants)} ✅")
print(f"  Odoo Warehouses: {len(warehouses)}")
print(f"  Locations with stock: Multiple")
print("=" * 80)

exit()




