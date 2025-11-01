#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detailed Migration Verification with Arabic Support"""

print("\n" + "=" * 80)
print("DETAILED MIGRATION VERIFICATION")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if not backend:
    print("ERROR: No backend found")
else:
    print(f"Backend: {backend.name}")
    print(f"URL: {backend.base_url}")
    print(f"Status: {backend.connection_status}")
    
    print("\n" + "-" * 80)
    print("STAGE 1: UoM Groups")
    print("-" * 80)
    
    uoms = env['sap.uom.sync'].search([('backend_id', '=', backend.id)])
    uoms_success = uoms.filtered(lambda x: x.sync_status == 'success')
    print(f"Total UoM Records: {len(uoms)}")
    print(f"Successfully Synced: {len(uoms_success)}")
    
    if uoms_success:
        print("\nTop 5 UoMs:")
        for uom in uoms_success[:5]:
            try:
                odoo_uom = uom.odoo_uom_id
                print(f"  {uom.sap_uom_id} -> {odoo_uom.name} (Cat: {odoo_uom.category_id.name})")
            except:
                print(f"  {uom.sap_uom_id} -> ERROR")
    
    print("\n" + "-" * 80)
    print("STAGE 2: Products")
    print("-" * 80)
    
    products = env['product.product'].search([('default_code', '!=', False)])
    print(f"Products with SAP codes: {len(products)}")
    
    if products:
        print(f"\nFirst 5 products:")
        for p in products[:5]:
            try:
                code = p.default_code or 'NO CODE'
                price = p.list_price
                uom = p.uom_id.name if p.uom_id else 'NO UOM'
                print(f"  [{code}] Price: {price} | UoM: {uom}")
            except Exception as e:
                print(f"  Error: {e}")
    
    print("\n" + "-" * 80)
    print("EXTENDED INFO")
    print("-" * 80)
    
    extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
    print(f"Extended Info Records: {len(extended)}")
    
    if extended:
        print("\nSample Extended Info:")
        ext = extended[0]
        print(f"  Product: {ext.product_id.default_code}")
        print(f"  Foreign Name: {ext.foreign_name or 'N/A'}")
        print(f"  Group: {ext.items_group_name or 'N/A'}")
        print(f"  Dimensions: {ext.length1}x{ext.width1}x{ext.height1}")
    else:
        print("  NO EXTENDED INFO CREATED!")
        print("  This means Stage 2 (extended) did not run or had errors")
    
    print("\n" + "-" * 80)
    print("STAGE 3: Pricelists")
    print("-" * 80)
    
    pricelists = env['product.pricelist'].search([('name', 'like', 'SAP')])
    print(f"SAP Pricelists: {len(pricelists)}")
    
    for pl in pricelists:
        print(f"  - {pl.name}: {len(pl.item_ids)} items")
    
    prices = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
    print(f"Price Sync Records: {len(prices)}")
    
    print("\n" + "-" * 80)
    print("STAGE 4: Warehouse Info")
    print("-" * 80)
    
    wh_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
    print(f"Warehouse Info Records: {len(wh_info)}")
    
    if wh_info:
        wh = wh_info[0]
        print(f"\nSample Warehouse:")
        print(f"  Product: {wh.product_id.default_code}")
        print(f"  Warehouse: {wh.warehouse_id.name}")
        print(f"  SAP Code: {wh.sap_warehouse_code}")
        print(f"  In Stock: {wh.last_in_stock}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_expected = len(products)
    total_actual = len(extended)
    
    stages_complete = 0
    if len(uoms) > 0:
        stages_complete += 1
        print("Stage 1 (UoMs): COMPLETE")
    if len(products) > 0:
        stages_complete += 1
        print("Stage 2 (Products Basic): COMPLETE")
    if len(extended) > 0:
        stages_complete += 1
        print("Stage 2 (Products Extended): COMPLETE")
    elif len(products) > 0:
        print("Stage 2 (Products Extended): INCOMPLETE")
    if len(prices) > 0:
        stages_complete += 1
        print("Stage 3 (Pricelists): COMPLETE")
    elif len(products) > 0:
        print("Stage 3 (Pricelists): NOT RUN")
    if len(wh_info) > 0:
        stages_complete += 1
        print("Stage 4 (Warehouse): COMPLETE")
    elif len(products) > 0:
        print("Stage 4 (Warehouse): NOT RUN")
    
    print(f"\nCompletion: {stages_complete}/5 stages")
    
    if stages_complete == 5:
        print("\nSTATUS: FULL MIGRATION COMPLETE!")
    elif stages_complete >= 2:
        print("\nSTATUS: PARTIAL MIGRATION")
        print("Some stages completed, others need to run")
    else:
        print("\nSTATUS: MIGRATION NOT STARTED")
    
    print("=" * 80)

env.cr.commit()











