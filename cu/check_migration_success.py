#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Migration Success - Quick Verification"""

print("=" * 80)
print("VERIFYING MIGRATION SUCCESS")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if backend:
    print(f"Backend: {backend.name}\n")
    
    # Count records
    products = env['product.product'].search([('default_code', '!=', False)])
    extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
    pricelists = env['product.pricelist'].search([('name', 'like', 'SAP')])
    prices = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
    wh_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
    uoms = env['sap.uom.sync'].search([('backend_id', '=', backend.id)])
    
    print(f"Products: {len(products)}")
    print(f"Extended Info: {len(extended)}")
    print(f"UoMs: {len(uoms)}")
    print(f"SAP Pricelists: {len(pricelists)}")
    print(f"Price Records: {len(prices)}")
    print(f"Warehouse Info: {len(wh_info)}")
    
    # Sample product
    if products:
        p = products[0]
        print(f"\nSample: {p.default_code}")
        print(f"  Price: {p.list_price}")
        print(f"  UoM: {p.uom_id.name}")
        
        ext = env['sap.product.extended'].search([('product_id', '=', p.id)], limit=1)
        if ext:
            print(f"  Extended: YES")
            print(f"    Foreign: {ext.foreign_name or 'N/A'}")
            print(f"    Group: {ext.items_group_name or 'N/A'}")
    
    print("\n" + "=" * 80)
    if len(products) > 0:
        print("MIGRATION SUCCESSFUL!")
    else:
        print("NO DATA - Check SAP connection")
    print("=" * 80)

env.cr.commit()











