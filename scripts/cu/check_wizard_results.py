#!/usr/bin/env python3
# Check Complete Migration Wizard Results

print("=" * 80)
print("CHECKING COMPLETE MIGRATION WIZARD RESULTS")
print("=" * 80)

# Find the latest wizard run
wizards = env['sap.product.complete.migration'].search([], order='create_date desc', limit=1)

if not wizards:
    print("\nNO WIZARD FOUND - Complete Migration was not run yet")
else:
    wizard = wizards[0]
    print(f"\nWizard ID: {wizard.id}")
    print(f"State: {wizard.state}")
    print(f"Backend: {wizard.backend_id.name}")
    
    if wizard.start_time:
        print(f"Start Time: {wizard.start_time}")
    if wizard.end_time:
        print(f"End Time: {wizard.end_time}")
        print(f"Duration: {wizard.duration_seconds} seconds")
    
    print("\n" + "-" * 80)
    print("STATISTICS FROM WIZARD:")
    print("-" * 80)
    print(f"UoM Groups: {wizard.total_uom_groups}")
    print(f"Products: {wizard.total_products}")
    print(f"Pricelists: {wizard.total_pricelists}")
    print(f"Price Records: {wizard.total_prices}")
    print(f"Warehouse Records: {wizard.total_warehouses}")
    print(f"Errors: {wizard.errors_count}")
    
    if wizard.migration_log:
        print("\n" + "-" * 80)
        print("MIGRATION LOG (Last 30 lines):")
        print("-" * 80)
        lines = wizard.migration_log.split('\n')
        for line in lines[-30:]:
            if line.strip():
                print(line)

# Actual database counts
print("\n" + "=" * 80)
print("ACTUAL DATABASE COUNTS:")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if backend:
    products = env['product.product'].search([('default_code', '!=', False)])
    extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
    prices = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
    wh_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
    uoms = env['sap.uom.sync'].search([('backend_id', '=', backend.id)])
    
    print(f"Products: {len(products)}")
    print(f"Extended Info: {len(extended)}")
    print(f"UoMs: {len(uoms)}")
    print(f"Price Records: {len(prices)}")
    print(f"Warehouse Info: {len(wh_info)}")
    
    # Sample extended if exists
    if extended:
        print("\n" + "-" * 80)
        print("SAMPLE EXTENDED INFO:")
        print("-" * 80)
        ext = extended[0]
        p = ext.product_id
        print(f"Product: {p.default_code}")
        print(f"  Foreign Name: {ext.foreign_name or 'N/A'}")
        print(f"  Items Group: {ext.items_group_name or 'N/A'}")
        print(f"  Dimensions: {ext.length1}x{ext.width1}x{ext.height1}")
        print(f"  Batch Mgmt: {ext.manage_batch_numbers}")
        print(f"  Min Stock: {ext.min_level}")
    
    # Sample price if exists
    if prices:
        print("\n" + "-" * 80)
        print("SAMPLE PRICE:")
        print("-" * 80)
        price = prices[0]
        p = price.product_id
        print(f"Product: {p.default_code}")
        print(f"  Pricelist: {price.odoo_pricelist_id.name}")
        print(f"  Price: {price.price} {price.currency_id.name}")
        if price.uom_id:
            print(f"  UoM: {price.uom_id.name}")
    
    # Sample warehouse if exists
    if wh_info:
        print("\n" + "-" * 80)
        print("SAMPLE WAREHOUSE:")
        print("-" * 80)
        wh = wh_info[0]
        p = wh.product_id
        print(f"Product: {p.default_code}")
        print(f"  Warehouse: {wh.warehouse_id.name}")
        print(f"  SAP Code: {wh.sap_warehouse_code}")
        print(f"  In Stock (SAP): {wh.last_in_stock}")
        print(f"  Available (Odoo): {wh.current_qty_available}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

env.cr.commit()











