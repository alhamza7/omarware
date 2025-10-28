#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Product ADF00527"""

print("=" * 80)
print("CHECK PRODUCT: ADF00527")
print("=" * 80)
print()

# Find the product
product = env['product.product'].search([('default_code', '=', 'ADF00527')], limit=1)

if product:
    print(f"PRODUCT FOUND:")
    print(f"  Name: {product.name}")
    print(f"  Code: {product.default_code}")
    print(f"  Type: {product.type}")
    print(f"  Available Qty: {product.qty_available}")
    print(f"  Virtual Qty: {product.virtual_available}")
    print()
    
    # Check stock quants for this product
    quants = env['stock.quant'].search([
        ('product_id', '=', product.id),
        ('quantity', '!=', 0)
    ])
    
    if quants:
        print(f"STOCK LOCATIONS ({len(quants)} locations):")
        print("-" * 80)
        for quant in quants:
            print(f"  Location: {quant.location_id.complete_name}")
            print(f"    Quantity: {quant.quantity}")
            print(f"    Reserved: {quant.reserved_quantity}")
            print(f"    Available: {quant.quantity - quant.reserved_quantity}")
            print()
    else:
        print("NO stock quants found for this product")
        print()
    
    # Check warehouse info
    warehouse_info = env['sap.product.warehouse.info'].search([
        ('product_code', '=', 'ADF00527')
    ])
    
    if warehouse_info:
        print(f"SAP WAREHOUSE INFO ({len(warehouse_info)} warehouses):")
        print("-" * 80)
        for info in warehouse_info[:10]:
            print(f"  SAP Warehouse: {info.sap_warehouse_name}")
            print(f"    In Stock: {info.last_in_stock}")
            print(f"    Available: {info.last_available}")
            print()
    else:
        print("NO warehouse info from SAP for this product")
    
else:
    print("PRODUCT NOT FOUND!")

print("=" * 80)

exit()




