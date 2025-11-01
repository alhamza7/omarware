#!/usr/bin/env python3
# Run the wizard that was created

print("=" * 80)
print("RUNNING COMPLETE MIGRATION WIZARD")
print("=" * 80)

# Get the draft wizard
wizard = env['sap.product.complete.migration'].browse(2)

if wizard.exists():
    print(f"\nWizard ID: {wizard.id}")
    print(f"State: {wizard.state}")
    print(f"Backend: {wizard.backend_id.name}")
    
    print("\n" + "-" * 80)
    print("Starting Migration...")
    print("-" * 80)
    
    try:
        # Run migration
        wizard.run_complete_migration()
        
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETED!")
        print("=" * 80)
        
        print(f"\nFinal State: {wizard.state}")
        print(f"Duration: {wizard.duration_seconds} seconds")
        
        print(f"\nStatistics:")
        print(f"  UoM Groups: {wizard.total_uom_groups}")
        print(f"  Products: {wizard.total_products}")
        print(f"  Pricelists: {wizard.total_pricelists}")
        print(f"  Prices: {wizard.total_prices}")
        print(f"  Warehouses: {wizard.total_warehouses}")
        print(f"  Errors: {wizard.errors_count}")
        
        # Check database
        print("\n" + "-" * 80)
        print("Database Verification:")
        print("-" * 80)
        
        extended = env['sap.product.extended'].search([])
        prices = env['sap.product.pricelist.sync'].search([])
        wh_info = env['sap.product.warehouse.info'].search([])
        
        print(f"Extended Info: {len(extended)}")
        print(f"Prices: {len(prices)}")
        print(f"Warehouse Info: {len(wh_info)}")
        
        env.cr.commit()
        
        print("\n" + "=" * 80)
        if len(extended) > 0:
            print("SUCCESS! Extended info created")
        else:
            print("Extended info not created - check SAP data")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        env.cr.rollback()
else:
    print("\nWizard not found! Creating new one...")
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    new_wizard = env['sap.product.complete.migration'].create({
        'backend_id': backend.id,
        'stage1_uom_groups': True,
        'stage2_products': True,
        'stage3_pricelists': True,
        'stage4_warehouse_info': True,
        'batch_size': 50,
        'update_existing': True,
        'skip_errors': True,
    })
    
    print(f"Created new wizard ID: {new_wizard.id}")
    print("Running migration...")
    
    new_wizard.run_complete_migration()
    
    print(f"\nState: {new_wizard.state}")
    print(f"Products: {new_wizard.total_products}")
    
    env.cr.commit()











