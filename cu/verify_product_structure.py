#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to verify that products are stored as ONE product with multiple UoM prices
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

def verify_product_structure():
    """Verify that products are stored correctly"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Product Structure Verification")
        print("=" * 80)
        
        # Get a test product
        product_code = input("\nEnter product code (or press Enter for R00205): ").strip()
        if not product_code:
            product_code = 'R00205'
        
        product = env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            print(f"ERROR: Product {product_code} not found!")
            return False
        
        print(f"\nProduct Found:")
        print(f"  ID: {product.id}")
        print(f"  Code: {product.default_code}")
        print(f"  Name: {product.name}")
        print(f"  Template ID: {product.product_tmpl_id.id}")
        print(f"  Base UoM: {product.uom_id.name}")
        
        # Check if it's a variant
        variants = env['product.product'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id)
        ])
        
        print(f"\n  Total Variants for this template: {len(variants)}")
        if len(variants) > 1:
            print("  WARNING: This product has multiple variants!")
            for v in variants:
                print(f"    - {v.default_code}: {v.name}")
        else:
            print("  OK: This is a single product (not a variant)")
        
        # Check pricelist items
        print("\n" + "=" * 80)
        print("Pricelist Items for this Product:")
        print("=" * 80)
        
        pricelist_items = env['product.pricelist.item'].search([
            ('product_id', '=', product.id)
        ])
        
        print(f"\nTotal Pricelist Items: {len(pricelist_items)}")
        print("\nGrouped by Pricelist:")
        
        # Group by pricelist
        pricelists = {}
        for item in pricelist_items:
            pricelist_name = item.pricelist_id.name
            if pricelist_name not in pricelists:
                pricelists[pricelist_name] = []
            pricelists[pricelist_name].append(item)
        
        for pricelist_name, items in pricelists.items():
            print(f"\n  {pricelist_name} ({len(items)} items):")
            for item in items:
                uom_name = item.product_packaging_id.name if item.product_packaging_id else "Base UoM"
                print(f"    - {uom_name}: ${item.fixed_price:.2f}")
        
        # Check SAP sync records
        print("\n" + "=" * 80)
        print("SAP Sync Records for this Product:")
        print("=" * 80)
        
        sync_records = env['sap.product.pricelist.sync'].search([
            ('product_id', '=', product.id)
        ])
        
        print(f"\nTotal Sync Records: {len(sync_records)}")
        
        # Group by pricelist
        sap_pricelists = {}
        for sync in sync_records:
            pl_name = f"SAP PL {sync.sap_pricelist_num}"
            if pl_name not in sap_pricelists:
                sap_pricelists[pl_name] = []
            sap_pricelists[pl_name].append(sync)
        
        for pl_name, syncs in sap_pricelists.items():
            print(f"\n  {pl_name} ({len(syncs)} UoMs):")
            for sync in syncs:
                uom_name = sync.uom_id.name if sync.uom_id else "Base"
                linked = "Linked" if sync.odoo_pricelist_item_id else "NOT LINKED"
                print(f"    - {uom_name}: ${sync.price:.2f} ({linked})")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        
        print(f"\nProduct Structure:")
        print(f"  Product ID: {product.id}")
        print(f"  Template ID: {product.product_tmpl_id.id}")
        print(f"  Is Single Product: {'YES' if len(variants) == 1 else 'NO (Has ' + str(len(variants)) + ' variants)'}")
        
        print(f"\nPricing Structure:")
        print(f"  Total Pricelist Items: {len(pricelist_items)}")
        print(f"  Unique Pricelists: {len(pricelists)}")
        print(f"  Total SAP Sync Records: {len(sync_records)}")
        
        if len(variants) == 1 and len(pricelist_items) > 1:
            print("\nSTATUS: OK - Single product with multiple UoM prices")
        elif len(variants) > 1:
            print("\nSTATUS: WARNING - Multiple product variants detected")
            print("This might be a misconfiguration. Each UoM should be a price variation,")
            print("not a separate product variant.")
        else:
            print("\nSTATUS: OK")
        
        return True

if __name__ == '__main__':
    try:
        verify_product_structure()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

