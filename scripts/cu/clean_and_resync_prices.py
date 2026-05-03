#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to delete old variant-based pricelist items and re-sync from SAP
"""

import sys
import os
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add Odoo to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

def clean_and_resync():
    """Delete old variant-based items and re-sync from SAP"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Clean and Re-sync Product Prices")
        print("=" * 80)
        
        # Get product
        product_code = input("\nEnter product code (or press Enter for R00205): ").strip()
        if not product_code:
            product_code = 'R00205'
        
        product = env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            print(f"ERROR: Product {product_code} not found!")
            return False
        
        print(f"\nProduct: {product.default_code} - {product.name}")
        print(f"Template ID: {product.product_tmpl_id.id}")
        
        # Delete old variant-based pricelist items
        print("\n" + "=" * 80)
        print("Deleting old variant-based pricelist items...")
        print("=" * 80)
        
        old_items = env['product.pricelist.item'].search([
            ('product_id', '=', product.id),
            ('applied_on', '=', '0_product_variant')
        ])
        
        print(f"Found {len(old_items)} old variant-based items to delete")
        
        if old_items:
            old_items.unlink()
            print("Deleted!")
        
        # Commit deletions
        cr.commit()
        
        # Get SAP backend
        backend = env['sap.backend'].search([], limit=1)
        if not backend:
            print("\nERROR: No SAP backend found!")
            return False
        
        # Get connection
        try:
            connection = backend.get_connection()
            print(f"\nConnected to SAP: {backend.base_url}")
        except Exception as e:
            print(f"\nERROR: Connection failed: {str(e)}")
            return False
        
        # Fetch prices from SAP
        print("\n" + "=" * 80)
        print("Fetching prices from SAP...")
        print("=" * 80)
        
        try:
            item_prices_url = f"Items('{product_code}')/ItemPrices"
            item_prices_data = connection.get(item_prices_url, {})
            
            if 'error' in item_prices_data:
                print(f"ERROR: {item_prices_data.get('error')}")
                return False
            
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
            
            # Sync prices
            print("\n" + "=" * 80)
            print("Syncing prices...")
            print("=" * 80)
            
            sync_model = env['sap.product.pricelist.sync']
            
            for price_data in item_prices:
                pricelist_num = price_data.get('PriceList')
                if not pricelist_num:
                    continue
                
                print(f"\nSyncing PriceList {pricelist_num}...")
                
                result = sync_model.sync_product_prices_from_sap(
                    product, backend, [price_data]
                )
                
                print(f"  Created: {result.get('created', 0)}")
                print(f"  Updated: {result.get('updated', 0)}")
                print(f"  Errors: {result.get('errors', 0)}")
            
            # Commit
            cr.commit()
            
            # Verify results
            print("\n" + "=" * 80)
            print("Verification:")
            print("=" * 80)
            
            new_items = env['product.pricelist.item'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product')
            ])
            
            print(f"\nTotal new pricelist items (template-based): {len(new_items)}")
            
            for item in new_items:
                uom_name = item.product_packaging_id.name if item.product_packaging_id else "Base UoM"
                print(f"  - {item.pricelist_id.name}: {uom_name} = ${item.fixed_price:.2f}")
            
            print("\n" + "=" * 80)
            print("SUCCESS! Prices re-synced as product template (not variant)")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    try:
        clean_and_resync()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

