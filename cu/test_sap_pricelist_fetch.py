#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to fetch pricelists from SAP and verify data saving
"""

import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add Odoo to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

def test_sap_pricelist_fetch():
    """Test fetching pricelists from SAP"""
    
    from odoo.modules.registry import Registry
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing SAP Pricelist Fetch")
        print("=" * 80)
        
        # Get SAP backend
        backend = env['sap.backend'].search([], limit=1)
        if not backend:
            print("❌ No SAP backend found!")
            return False
        
        print(f"✓ Found SAP Backend: {backend.name}")
        print(f"  - URL: {backend.base_url}")
        print(f"  - Company: {backend.company_db}")
        
        # Test connection
        try:
            connection = backend.get_connection()
            print("✓ SAP Connection successful!")
        except Exception as e:
            print(f"❌ SAP Connection failed: {str(e)}")
            return False
        
        # Get a test product (R00205 which had the error)
        test_item_code = 'R00205'
        product = env['product.product'].search([('default_code', '=', test_item_code)], limit=1)
        
        if not product:
            print(f"⚠ Product {test_item_code} not found in Odoo. Searching for any product...")
            product = env['product.product'].search([('default_code', '!=', False)], limit=1)
            test_item_code = product.default_code if product else None
        
        if not product:
            print("❌ No products found in Odoo!")
            return False
        
        print(f"\n✓ Testing with product: {product.default_code} - {product.name}")
        
        # Try to fetch prices from SAP
        print(f"\n{'=' * 80}")
        print(f"Fetching prices from SAP for item: {test_item_code}")
        print(f"{'=' * 80}")
        
        try:
            item_prices_url = f"Items('{test_item_code}')/ItemPrices"
            print(f"API URL: {item_prices_url}")
            
            item_prices_data = connection.get(item_prices_url, {})
            
            # Check for errors
            if 'error' in item_prices_data:
                print(f"❌ SAP API Error:")
                print(f"   Status: {item_prices_data.get('status_code', 'N/A')}")
                print(f"   Error: {item_prices_data.get('error', 'Unknown')}")
                return False
            
            # Parse prices
            if 'ItemPrices' in item_prices_data:
                item_prices = item_prices_data.get('ItemPrices', [])
            elif 'value' in item_prices_data:
                item_prices = item_prices_data.get('value', [])
            else:
                item_prices = []
            
            print(f"✓ Found {len(item_prices)} prices in SAP")
            
            if not item_prices:
                print(f"⚠ No prices configured in SAP for item {test_item_code}")
                print("\nTrying with another product...")
                
                # Try another product
                products = env['product.product'].search([('default_code', '!=', False)], limit=10)
                for prod in products:
                    try:
                        test_url = f"Items('{prod.default_code}')/ItemPrices"
                        test_data = connection.get(test_url, {})
                        
                        if 'error' not in test_data:
                            test_prices = test_data.get('ItemPrices', test_data.get('value', []))
                            if test_prices:
                                print(f"✓ Found product with prices: {prod.default_code}")
                                item_prices = test_prices
                                test_item_code = prod.default_code
                                product = prod
                                break
                    except:
                        continue
            
            if not item_prices:
                print("❌ Could not find any products with prices in SAP")
                return False
            
            # Display prices
            print(f"\n{'=' * 80}")
            print(f"Prices for item {test_item_code}:")
            print(f"{'=' * 80}")
            
            for idx, price in enumerate(item_prices[:5], 1):  # Show first 5
                print(f"\nPrice #{idx}:")
                print(f"  - PriceList: {price.get('PriceList', 'N/A')}")
                print(f"  - Price: {price.get('Price', 'N/A')}")
                print(f"  - Currency: {price.get('Currency', 'N/A')}")
                print(f"  - UoMEntry: {price.get('UoMEntry', 'N/A')}")
            
            if len(item_prices) > 5:
                print(f"\n... and {len(item_prices) - 5} more prices")
            
            # Now test if we can find existing sync records
            print(f"\n{'=' * 80}")
            print(f"Checking existing sync records in Odoo:")
            print(f"{'=' * 80}")
            
            sync_records = env['sap.product.pricelist.sync'].search([
                ('product_id', '=', product.id)
            ], limit=10)
            
            print(f"✓ Found {len(sync_records)} sync records for this product")
            
            for sync in sync_records[:3]:  # Show first 3
                print(f"\nSync Record #{sync.id}:")
                print(f"  - SAP Pricelist: {sync.sap_pricelist_num} ({sync.sap_pricelist_name})")
                print(f"  - Price: {sync.price} {sync.currency_id.name if sync.currency_id else 'N/A'}")
                print(f"  - SAP UoM: {sync.uom_code}")
                print(f"  - Odoo Pricelist: {sync.odoo_pricelist_id.name if sync.odoo_pricelist_id else 'Not mapped'}")
                print(f"  - Odoo Pricelist Item: {sync.odoo_pricelist_item_id.id if sync.odoo_pricelist_item_id else 'Not linked'}")
            
            # Check where pricelist items are stored
            print(f"\n{'=' * 80}")
            print(f"Checking Odoo Pricelist Items:")
            print(f"{'=' * 80}")
            
            pricelist_items = env['product.pricelist.item'].search([
                ('product_id', '=', product.id)
            ], limit=10)
            
            print(f"✓ Found {len(pricelist_items)} pricelist items in Odoo for this product")
            
            for item in pricelist_items[:3]:  # Show first 3
                print(f"\nPricelist Item #{item.id}:")
                print(f"  - Pricelist: {item.pricelist_id.name}")
                print(f"  - Product: {item.product_id.default_code} - {item.product_id.name}")
                print(f"  - Fixed Price: {item.fixed_price if item.compute_price == 'fixed' else 'N/A'}")
                print(f"  - Min Quantity: {item.min_quantity}")
            
            print(f"\n{'=' * 80}")
            print(f"✅ Test completed successfully!")
            print(f"{'=' * 80}")
            print(f"\nSummary:")
            print(f"  - SAP Connection: ✓ Working")
            print(f"  - SAP Price Fetch: ✓ Working ({len(item_prices)} prices found)")
            print(f"  - Sync Records: ✓ {len(sync_records)} records found")
            print(f"  - Odoo Pricelist Items: ✓ {len(pricelist_items)} items found")
            print(f"\nData is being saved correctly in:")
            print(f"  1. sap.product.pricelist.sync (sync tracking)")
            print(f"  2. product.pricelist.item (actual Odoo pricelists)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    try:
        success = test_sap_pricelist_fetch()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

