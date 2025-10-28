#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("="*80)
print("Warehouse and Stock Check")
print("="*80)

# Warehouses
warehouses = env['stock.warehouse'].search([])
print(f"\nWarehouses: {len(warehouses)}")

# SAP Warehouse Info
wh_info = env['sap.product.warehouse.info'].search([])
print(f"SAP Warehouse Info: {len(wh_info)}")

# Stock Quants
quants = env['stock.quant'].search([])
print(f"Total Stock Quants: {len(quants)}")

quants_sap = env['stock.quant'].search([
    ('product_id.default_code', '!=', False)
])
print(f"Stock Quants for SAP products: {len(quants_sap)}")

# Latest wizard
wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizard:
    print(f"\nLatest Migration:")
    print(f"  State: {wizard.state}")
    print(f"  Products: {wizard.total_products}")
    print(f"  Warehouses: {wizard.total_warehouses}")
    print(f"  Prices: {wizard.total_prices}")
    print(f"  Progress: {wizard.progress_percentage}%")

print("\n" + "="*80)
print("RESULT:")
print("="*80)

if len(wh_info) > 0:
    print(f"Warehouses: IMPORTED ({len(wh_info)} records)")
else:
    print("Warehouses: NOT IMPORTED")

if len(quants_sap) > 0:
    print(f"Stock Quantities: UPDATED ({len(quants_sap)} quants)")
else:
    print("Stock Quantities: NOT UPDATED")

env.cr.commit()




