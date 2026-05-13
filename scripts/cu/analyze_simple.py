#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("="*80)
print("Odoo Models Analysis")
print("="*80)

# UoM
uoms = env['uom.uom'].search([])
print(f"\nTotal UoM: {len(uoms)}")
for uom in uoms[:15]:
    print(f"  - {uom.id}: {uom.name}")

# Pricelists
pricelists = env['product.pricelist'].search([])
print(f"\nTotal Pricelists: {len(pricelists)}")
for pl in pricelists:
    print(f"  - {pl.id}: {pl.name}")

# Warehouses
warehouses = env['stock.warehouse'].search([])
print(f"\nTotal Warehouses: {len(warehouses)}")
for wh in warehouses:
    print(f"  - {wh.id}: {wh.name} ({wh.code})")

# Stock Locations
locations = env['stock.location'].search([('usage', '=', 'internal')])
print(f"\nInternal Locations: {len(locations)}")
for loc in locations[:5]:
    print(f"  - {loc.id}: {loc.complete_name}")

# SAP Extended fields
ext = env['sap.product.extended'].search([], limit=1)
if ext:
    print(f"\nSAP Extended Info sample:")
    print(f"  Product: {ext.product_id.default_code if ext.product_id else 'N/A'}")
    print(f"  Has foreign_name field: {hasattr(ext, 'foreign_name')}")
    print(f"  Has manufacturer field: {hasattr(ext, 'manufacturer')}")
    print(f"  Has sales_unit field: {hasattr(ext, 'sales_unit')}")
    print(f"  Has purchase_unit field: {hasattr(ext, 'purchase_unit')}")
    print(f"  Has inventory_uom field: {hasattr(ext, 'inventory_uom')}")
    
    if hasattr(ext, 'foreign_name'):
        print(f"  Foreign name value: {ext.foreign_name}")

env.cr.commit()




