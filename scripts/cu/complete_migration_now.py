#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete the Remaining Migration Stages"""

print("\n" + "=" * 80)
print("COMPLETING REMAINING MIGRATION STAGES")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if not backend:
    print("ERROR: No backend!")
else:
    print(f"Backend: {backend.name}\n")
    
    # Get all products
    products = env['product.product'].search([('default_code', '!=', False)])
    print(f"Found {len(products)} products to process\n")
    
    # Stage 2b: Add Extended Info to existing products
    print("-" * 80)
    print("Adding Extended Info to Products...")
    print("-" * 80)
    
    connection = backend.get_connection()
    extended_created = 0
    
    for idx, product in enumerate(products, 1):
        try:
            # Check if already has extended info
            existing = env['sap.product.extended'].search([
                ('product_id', '=', product.id),
                ('backend_id', '=', backend.id)
            ])
            
            if existing:
                continue  # Skip
            
            # Get from SAP
            item_code = product.default_code
            items_data = connection.get('Items', {
                '$filter': f"ItemCode eq '{item_code}'"
            })
            
            if items_data.get('value'):
                item_data = items_data['value'][0]
                
                # Create extended info
                env['sap.product.extended'].create_or_update_from_sap(
                    product, backend, item_data
                )
                extended_created += 1
                
                if extended_created % 10 == 0:
                    print(f"  Processed {extended_created}/{len(products)}...")
                    env.cr.commit()  # Commit every 10
        except Exception as e:
            pass  # Skip errors
    
    print(f"\nCreated {extended_created} extended info records")
    
    # Stage 3: Import Pricelists
    print("\n" + "-" * 80)
    print("Importing Pricelists...")
    print("-" * 80)
    
    try:
        pricelist_sync = env['sap.product.pricelist.sync']
        result = pricelist_sync.import_all_pricelists_from_sap(backend, 50)
        print(f"  Products processed: {result['successful_products']}")
        print(f"  Price records created: {result['created_prices']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Stage 4: Import Warehouse Info
    print("\n" + "-" * 80)
    print("Importing Warehouse Info...")
    print("-" * 80)
    
    try:
        warehouse_sync = env['sap.product.warehouse.info']
        result = warehouse_sync.import_all_warehouse_info_from_sap(backend, 50)
        print(f"  Products processed: {result['successful_products']}")
        print(f"  Warehouse records created: {result['created_records']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Final commit
    env.cr.commit()
    
    # Final check
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    
    extended_final = env['sap.product.extended'].search([])
    prices_final = env['sap.product.pricelist.sync'].search([])
    wh_final = env['sap.product.warehouse.info'].search([])
    
    print(f"Products: {len(products)}")
    print(f"Extended Info: {len(extended_final)}")
    print(f"Prices: {len(prices_final)}")
    print(f"Warehouse Info: {len(wh_final)}")
    
    if len(extended_final) == len(products):
        print("\nMIGRATION COMPLETE!")
    else:
        print(f"\nPartial: {len(extended_final)}/{len(products)} products have extended info")
    
    print("=" * 80)











