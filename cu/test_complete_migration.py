#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAP Product Complete Migration Test Script

This script tests and verifies the complete product migration from SAP to Odoo.
Run from terminal: python test_complete_migration.py
Or from Odoo shell: exec(open('test_complete_migration.py').read())
"""

import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_migration(env):
    """Test complete product migration"""
    
    print("\n" + "=" * 80)
    print("SAP PRODUCT COMPLETE MIGRATION TEST")
    print("=" * 80)
    
    try:
        # Get backend
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        if not backend:
            print("❌ No active SAP backend found!")
            return False
        
        print(f"✅ Using Backend: {backend.name}")
        print(f"   URL: {backend.base_url}")
        print(f"   Company DB: {backend.company_db}")
        
        # Test connection
        print("\n" + "-" * 80)
        print("Testing SAP Connection...")
        print("-" * 80)
        
        try:
            connection = backend.get_connection()
            test_result = connection.test_connection()
            if test_result:
                print("✅ SAP Connection successful!")
            else:
                print("❌ SAP Connection failed!")
                return False
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
        
        # Run Complete Migration
        print("\n" + "=" * 80)
        print("RUNNING COMPLETE MIGRATION")
        print("=" * 80)
        
        wizard = env['sap.product.complete.migration'].create({
            'backend_id': backend.id,
            'stage1_uom_groups': True,
            'stage2_products': True,
            'stage3_pricelists': True,
            'stage4_warehouse_info': True,
            'batch_size': 50,  # Small batch for testing
            'update_existing': True,
            'skip_errors': True,
        })
        
        print("\n🚀 Starting migration...")
        wizard.run_complete_migration()
        
        # Display results
        print("\n" + "=" * 80)
        print("MIGRATION RESULTS")
        print("=" * 80)
        print(f"State: {wizard.state}")
        print(f"Duration: {wizard.duration_seconds} seconds")
        print(f"\nStatistics:")
        print(f"  ✓ UoM Groups: {wizard.total_uom_groups}")
        print(f"  ✓ Products: {wizard.total_products}")
        print(f"  ✓ Pricelists: {wizard.total_pricelists}")
        print(f"  ✓ Price Records: {wizard.total_prices}")
        print(f"  ✓ Warehouse Records: {wizard.total_warehouses}")
        print(f"  ⚠ Errors: {wizard.errors_count}")
        
        # Verification
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)
        
        # Check UoMs
        uom_count = env['sap.uom.sync'].search_count([
            ('backend_id', '=', backend.id),
            ('sync_status', '=', 'success')
        ])
        print(f"✓ UoM Sync Records: {uom_count}")
        
        # Check Products
        product_count = env['product.product'].search_count([
            ('default_code', '!=', False)
        ])
        print(f"✓ Products with SAP codes: {product_count}")
        
        # Check Extended Info
        extended_count = env['sap.product.extended'].search_count([
            ('backend_id', '=', backend.id)
        ])
        print(f"✓ Extended Product Info: {extended_count}")
        
        # Check Pricelists
        pricelist_count = env['product.pricelist'].search_count([
            ('name', 'like', 'SAP Price List')
        ])
        print(f"✓ SAP Pricelists: {pricelist_count}")
        
        price_sync_count = env['sap.product.pricelist.sync'].search_count([
            ('backend_id', '=', backend.id)
        ])
        print(f"✓ Price Sync Records: {price_sync_count}")
        
        # Check Warehouse Info
        warehouse_info_count = env['sap.product.warehouse.info'].search_count([
            ('backend_id', '=', backend.id)
        ])
        print(f"✓ Warehouse Info Records: {warehouse_info_count}")
        
        # Sample Data
        print("\n" + "=" * 80)
        print("SAMPLE DATA")
        print("=" * 80)
        
        # Sample UoM
        sample_uom = env['sap.uom.sync'].search([
            ('backend_id', '=', backend.id),
            ('sync_status', '=', 'success')
        ], limit=1)
        if sample_uom:
            print(f"\nSample UoM:")
            print(f"  SAP Code: {sample_uom.sap_uom_id}")
            print(f"  SAP Name: {sample_uom.sap_uom_name}")
            print(f"  Odoo UoM: {sample_uom.odoo_uom_id.name}")
            print(f"  Category: {sample_uom.odoo_uom_id.category_id.name}")
        
        # Sample Product
        sample_product = env['product.product'].search([
            ('default_code', '!=', False)
        ], limit=1)
        if sample_product:
            print(f"\nSample Product:")
            print(f"  Code: {sample_product.default_code}")
            print(f"  Name: {sample_product.name}")
            print(f"  Price: {sample_product.list_price}")
            print(f"  UoM: {sample_product.uom_id.name}")
            
            # Check if has extended info
            extended = env['sap.product.extended'].search([
                ('product_id', '=', sample_product.id)
            ], limit=1)
            if extended:
                print(f"  ✓ Has Extended Info:")
                if extended.foreign_name:
                    print(f"    - Foreign Name: {extended.foreign_name}")
                if extended.manufacturer_id:
                    print(f"    - Manufacturer: {extended.manufacturer_id.name}")
                if extended.items_group_name:
                    print(f"    - Group: {extended.items_group_name}")
        
        # Sample Pricelist
        sample_pricelist = env['product.pricelist'].search([
            ('name', 'like', 'SAP Price List')
        ], limit=1)
        if sample_pricelist:
            print(f"\nSample Pricelist:")
            print(f"  Name: {sample_pricelist.name}")
            print(f"  Currency: {sample_pricelist.currency_id.name}")
            print(f"  Items: {len(sample_pricelist.item_ids)}")
        
        # Sample Warehouse Info
        sample_warehouse = env['sap.product.warehouse.info'].search([
            ('backend_id', '=', backend.id)
        ], limit=1)
        if sample_warehouse:
            print(f"\nSample Warehouse Info:")
            print(f"  Product: {sample_warehouse.product_name}")
            print(f"  Warehouse: {sample_warehouse.warehouse_name}")
            print(f"  SAP Code: {sample_warehouse.sap_warehouse_code}")
            print(f"  In Stock (SAP): {sample_warehouse.last_in_stock}")
            print(f"  Available (Odoo): {sample_warehouse.current_qty_available}")
            if sample_warehouse.minimum_stock > 0:
                print(f"  Min Stock: {sample_warehouse.minimum_stock}")
        
        # Migration Log
        print("\n" + "=" * 80)
        print("MIGRATION LOG (Last 20 lines)")
        print("=" * 80)
        if wizard.migration_log:
            log_lines = wizard.migration_log.split('\n')
            for line in log_lines[-20:]:
                print(line)
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# If running from terminal
if __name__ == '__main__':
    print("This script should be run from Odoo shell:")
    print("python odoo-bin shell -d YOUR_DATABASE --no-http")
    print(">>> exec(open('test_complete_migration.py').read())")
    sys.exit(1)


# Auto-run if 'env' is available (in Odoo shell)
if 'env' in globals():
    test_migration(env)











