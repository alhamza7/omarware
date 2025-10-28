#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Warehouses and Stock Status"""

print("=" * 80)
print("Warehouse and Stock Status Check")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# 1. Check Warehouses
print("\n1. Warehouses in Odoo:")
warehouses = env['stock.warehouse'].search([])
print(f"   Total: {len(warehouses)}")
for wh in warehouses:
    print(f"   - {wh.code}: {wh.name}")

# 2. Check SAP Warehouse Info
print("\n2. SAP Warehouse Info records:")
wh_info = env['sap.product.warehouse.info'].search([])
print(f"   Total: {len(wh_info)}")
if wh_info:
    for info in wh_info[:5]:
        print(f"   - Product: {info.product_id.default_code}")
        print(f"     Warehouse: {info.sap_warehouse_code}")
        print(f"     InStock: {info.last_in_stock}")

# 3. Check Stock Quants
print("\n3. Stock Quants (Inventory):")
quants = env['stock.quant'].search([])
print(f"   Total: {len(quants)}")

# Only for products with codes
quants_with_code = env['stock.quant'].search([
    ('product_id.default_code', '!=', False)
])
print(f"   For SAP products: {len(quants_with_code)}")

if quants_with_code:
    print("\n   Sample Stock Quants:")
    for q in quants_with_code[:5]:
        print(f"   - Product: {q.product_id.default_code}")
        print(f"     Location: {q.location_id.complete_name}")
        print(f"     Quantity: {q.quantity}")

# 4. Check latest migration wizard
print("\n4. Latest Migration Results:")
wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizard:
    print(f"   State: {wizard.state}")
    print(f"   Products: {wizard.total_products}")
    print(f"   Warehouses: {wizard.total_warehouses}")
    print(f"   Pricelists: {wizard.total_pricelists}")
    print(f"   Prices: {wizard.total_prices}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if len(wh_info) > 0:
    print("\nWarehouses: IMPORTED")
else:
    print("\nWarehouses: NOT IMPORTED YET")

if len(quants_with_code) > 0:
    print("Stock Quantities: UPDATED")
else:
    print("Stock Quantities: NOT UPDATED YET")

print("\n" + "=" * 80)

env.cr.commit()




