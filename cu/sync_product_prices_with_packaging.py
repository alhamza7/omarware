#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fetch and sync ALL prices for a product from SAP with proper UoM/packaging linking
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

def sync_product_prices_with_packaging():
    """Sync product prices from SAP with proper UoM/packaging linking"""
    
    from odoo.modules.registry import Registry
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("SAP Product Prices Sync with Packaging")
        print("=" * 80)
        
        # Get SAP backend
        backend = env['sap.backend'].search([], limit=1)
        if not backend:
            print("ERROR: No SAP backend found!")
            return False
        
        print(f"\nSAP Backend: {backend.name}")
        print(f"URL: {backend.base_url}")
        
        # Test connection
        try:
            connection = backend.get_connection()
            print("Connection: OK")
        except Exception as e:
            print(f"ERROR: Connection failed: {str(e)}")
            return False
        
        # Get product code from user or use default
        product_code = input("\nEnter product code (or press Enter for R00205): ").strip()
        if not product_code:
            product_code = 'R00205'
        
        # Find product in Odoo
        product = env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            print(f"ERROR: Product {product_code} not found in Odoo!")
            return False
        
        print(f"\nProduct: {product.default_code} - {product.name}")
        print(f"Base UoM: {product.uom_id.name}")
        
        # Show existing packaging/UoMs for this product
        print("\n" + "=" * 80)
        print("Available UoMs for this product:")
        print("=" * 80)
        
        # Get all UoMs from the same category
        if hasattr(product.uom_id, 'category_id'):
            available_uoms = env['uom.uom'].search([
                ('category_id', '=', product.uom_id.category_id.id)
            ])
        else:
            # Try with uom_category_id (some Odoo versions)
            available_uoms = env['uom.uom'].search([])
            # Filter manually by category
            if hasattr(product.uom_id, 'uom_type'):
                # Group by type
                available_uoms = available_uoms.filtered(
                    lambda u: hasattr(u, 'uom_type') and u.uom_type == product.uom_id.uom_type
                )
            # Limit to 20 for display
            available_uoms = available_uoms[:20]
        
        for idx, uom in enumerate(available_uoms, 1):
            factor = getattr(uom, 'factor', getattr(uom, 'factor_inv', 1.0))
            ratio = getattr(uom, 'ratio', 1.0)
            print(f"{idx}. {uom.name} (Factor: {factor:.4f}, Ratio: {ratio:.4f})")
        
        # Fetch prices from SAP
        print("\n" + "=" * 80)
        print(f"Fetching prices from SAP for: {product_code}")
        print("=" * 80)
        
        try:
            # Method 1: Try with ItemPrices navigation
            item_prices_url = f"Items('{product_code}')/ItemPrices"
            print(f"\nAPI Call: {item_prices_url}")
            
            item_prices_data = connection.get(item_prices_url, {})
            
            # Check for errors
            if 'error' in item_prices_data:
                print(f"ERROR: {item_prices_data.get('error')}")
                return False
            
            # Parse prices
            if 'ItemPrices' in item_prices_data:
                item_prices = item_prices_data.get('ItemPrices', [])
            elif 'value' in item_prices_data:
                item_prices = item_prices_data.get('value', [])
            else:
                item_prices = []
            
            print(f"Found {len(item_prices)} prices in SAP")
            
            if not item_prices:
                print("No prices found!")
                return False
            
            # Display all prices
            print("\n" + "=" * 80)
            print("SAP Prices:")
            print("=" * 80)
            
            for idx, price in enumerate(item_prices, 1):
                print(f"\nPrice #{idx}:")
                print(f"  PriceList: {price.get('PriceList')}")
                print(f"  Price: {price.get('Price')} {price.get('Currency')}")
                print(f"  UoMEntry: {price.get('UoMEntry', 'N/A')}")
                print(f"  Additional UoMPrices: {len(price.get('UoMPrices', []))}")
                
                # Show UoM-specific prices if available
                uom_prices = price.get('UoMPrices', [])
                if uom_prices:
                    print(f"  UoM-Specific Prices:")
                    for uom_price in uom_prices:
                        print(f"    - UoMEntry: {uom_price.get('UoMEntry')}, "
                              f"Price: {uom_price.get('Price')}, "
                              f"Currency: {uom_price.get('Currency')}")
            
            # Now sync these prices
            print("\n" + "=" * 80)
            print("Syncing prices to Odoo...")
            print("=" * 80)
            
            # Use the sync model
            sync_model = env['sap.product.pricelist.sync']
            
            for price_data in item_prices:
                pricelist_num = price_data.get('PriceList')
                if not pricelist_num:
                    continue
                
                print(f"\nSyncing PriceList {pricelist_num}...")
                
                # Sync base price
                result = sync_model.sync_product_prices_from_sap(
                    product, backend, [price_data]
                )
                
                print(f"  Created: {result.get('created', 0)}")
                print(f"  Updated: {result.get('updated', 0)}")
                print(f"  Errors: {result.get('errors', 0)}")
                
                if result.get('error_messages'):
                    for err in result.get('error_messages', []):
                        print(f"  ERROR: {err}")
            
            # Commit the changes
            cr.commit()
            
            # Show final results
            print("\n" + "=" * 80)
            print("Verification:")
            print("=" * 80)
            
            # Check sync records
            sync_records = env['sap.product.pricelist.sync'].search([
                ('product_id', '=', product.id)
            ])
            
            print(f"\nTotal sync records: {len(sync_records)}")
            for sync in sync_records:
                print(f"\n  - Pricelist {sync.sap_pricelist_num} ({sync.odoo_pricelist_id.name})")
                print(f"    Price: {sync.price} {sync.currency_id.name}")
                if sync.uom_id:
                    print(f"    UoM: {sync.uom_id.name}")
                if sync.odoo_pricelist_item_id:
                    print(f"    Linked to pricelist item: {sync.odoo_pricelist_item_id.id}")
            
            # Check pricelist items
            pricelist_items = env['product.pricelist.item'].search([
                ('product_id', '=', product.id)
            ])
            
            print(f"\nTotal pricelist items: {len(pricelist_items)}")
            for item in pricelist_items:
                print(f"\n  - {item.pricelist_id.name}")
                print(f"    Price: {item.fixed_price}")
                if item.product_packaging_id:
                    print(f"    Packaging/UoM: {item.product_packaging_id.name}")
                print(f"    Min Qty: {item.min_quantity}")
            
            print("\n" + "=" * 80)
            print("SUCCESS! Prices synced with packaging")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"\nERROR during sync: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    try:
        success = sync_product_prices_with_packaging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

