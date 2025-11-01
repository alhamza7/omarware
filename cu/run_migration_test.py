#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick Migration Test Script"""

print("\n" + "=" * 80)
print("🚀 SAP PRODUCT COMPLETE MIGRATION - STARTING")
print("=" * 80)

try:
    # Get backend
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    if not backend:
        print("❌ No active SAP backend found!")
        print("\nPlease create and activate a SAP backend first:")
        print("  SAP Integration > Configuration > Backends")
    else:
        print(f"✅ Backend: {backend.name}")
        print(f"   URL: {backend.base_url}")
        print(f"   Status: {backend.connection_status}")
        
        # Test connection first
        print("\n" + "-" * 80)
        print("Testing SAP Connection...")
        print("-" * 80)
        try:
            result = backend.test_connection()
            print("✅ Connection successful!")
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            print("\nPlease fix connection and try again.")
            raise
        
        # Create wizard
        print("\n" + "-" * 80)
        print("Creating Migration Wizard...")
        print("-" * 80)
        
        wizard = env['sap.product.complete.migration'].create({
            'backend_id': backend.id,
            'stage1_uom_groups': True,
            'stage2_products': True,
            'stage3_pricelists': True,
            'stage4_warehouse_info': True,
            'batch_size': 20,  # Small batch for testing
            'update_existing': True,
            'skip_errors': True,
        })
        print(f"✅ Wizard created (ID: {wizard.id})")
        
        # Run migration
        print("\n" + "=" * 80)
        print("🚀 RUNNING MIGRATION...")
        print("=" * 80)
        
        wizard.run_complete_migration()
        
        # Display results
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETED!")
        print("=" * 80)
        
        print(f"\n📊 Statistics:")
        print(f"   State: {wizard.state}")
        print(f"   Duration: {wizard.duration_seconds} seconds")
        print(f"   UoM Groups: {wizard.total_uom_groups}")
        print(f"   Products: {wizard.total_products}")
        print(f"   Pricelists: {wizard.total_pricelists}")
        print(f"   Price Records: {wizard.total_prices}")
        print(f"   Warehouse Records: {wizard.total_warehouses}")
        print(f"   Errors: {wizard.errors_count}")
        
        # Show migration log
        print("\n" + "=" * 80)
        print("📝 MIGRATION LOG (Last 30 lines)")
        print("=" * 80)
        if wizard.migration_log:
            log_lines = wizard.migration_log.split('\n')
            for line in log_lines[-30:]:
                print(line)
        
        # Verification
        print("\n" + "=" * 80)
        print("🔍 VERIFICATION")
        print("=" * 80)
        
        # Count records
        products = env['product.product'].search([('default_code', '!=', False)])
        extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
        pricelists = env['product.pricelist'].search([('name', 'like', 'SAP Price List')])
        prices = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
        wh_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
        
        print(f"✓ Products in Odoo: {len(products)}")
        print(f"✓ Extended Info Records: {len(extended)}")
        print(f"✓ SAP Pricelists: {len(pricelists)}")
        print(f"✓ Price Sync Records: {len(prices)}")
        print(f"✓ Warehouse Info Records: {len(wh_info)}")
        
        # Sample data
        if products:
            print(f"\n📦 Sample Product:")
            p = products[0]
            print(f"   Code: {p.default_code}")
            print(f"   Name: {p.name}")
            print(f"   Price: {p.list_price} {p.currency_id.name if p.currency_id else ''}")
            print(f"   UoM: {p.uom_id.name}")
            
            # Check extended
            ext = env['sap.product.extended'].search([('product_id', '=', p.id)], limit=1)
            if ext:
                print(f"   ✓ Has Extended Info:")
                if ext.foreign_name:
                    print(f"     - Foreign Name: {ext.foreign_name}")
                if ext.items_group_name:
                    print(f"     - Group: {ext.items_group_name}")
                if ext.manufacturer_id:
                    print(f"     - Manufacturer: {ext.manufacturer_id.name}")
            
            # Check prices
            p_prices = env['sap.product.pricelist.sync'].search([('product_id', '=', p.id)])
            if p_prices:
                print(f"   ✓ Prices ({len(p_prices)}):")
                for price in p_prices[:3]:
                    uom_text = f" ({price.uom_id.name})" if price.uom_id else ""
                    print(f"     - {price.odoo_pricelist_id.name}{uom_text}: {price.price}")
            
            # Check warehouse
            p_wh = env['sap.product.warehouse.info'].search([('product_id', '=', p.id)])
            if p_wh:
                print(f"   ✓ Warehouse Info ({len(p_wh)}):")
                for wh in p_wh[:2]:
                    print(f"     - {wh.warehouse_name}: {wh.current_qty_available} available")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("❌ TEST FAILED")
    print("=" * 80)

# Commit to save wizard record
env.cr.commit()











