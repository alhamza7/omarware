#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to check UoM Groups for a product
"""
import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add Odoo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config
from odoo.orm.registry import Registry

# Parse config
config.parse_config(['--config=odoo.conf', '--database=lugal'])

# Initialize Odoo registry
registry = Registry('lugal')

def check_product_uom_group(item_code='S01084'):
    """Check product UoM Group setup in Odoo"""
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print(f"Checking Product: {item_code}")
        print("="*80)
        
        # Check if product exists
        product = env['product.product'].search([
            ('default_code', '=', item_code)
        ], limit=1)
        
        if not product:
            print(f"\n[NOT FOUND] Product {item_code} does not exist in Odoo")
            print("\n[SOLUTION] Run Complete Migration to import it from SAP")
            return
        
        print(f"\n[PRODUCT FOUND]")
        print(f"  - ID: {product.id}")
        print(f"  - Name: {product.name}")
        print(f"  - Code: {product.default_code}")
        print(f"  - UoM: {product.uom_id.name}")
        print(f"  - Active for Sale: {product.sale_ok}")
        print(f"  - Active for POS: {product.available_in_pos}")
        
        # Check SAP extended info
        extended = env['sap.product.extended'].search([
            ('product_id', '=', product.id)
        ], limit=1)
        
        if not extended:
            print(f"\n[NO SAP INFO] Product has no SAP extended information")
            return
        
        print(f"\n[SAP EXTENDED INFO]")
        print(f"  - SAP Item Code: {extended.sap_item_code}")
        print(f"  - SAP UoM Group Entry: {extended.sap_uom_group_entry or 'N/A'}")
        print(f"  - SAP UoM Group: {extended.sap_uom_group_id.name if extended.sap_uom_group_id else 'NOT LINKED'}")
        
        if not extended.sap_uom_group_id:
            print(f"\n[WARNING] Product is not linked to any UoM Group!")
            print(f"[SOLUTION] UoM Group Entry {extended.sap_uom_group_entry} needs to be imported first")
            
            # Check if UoM Group exists
            if extended.sap_uom_group_entry:
                uom_group = env['sap.uom.group'].search([
                    ('sap_abs_entry', '=', extended.sap_uom_group_entry)
                ], limit=1)
                
                if uom_group:
                    print(f"\n[INFO] UoM Group exists but not linked:")
                    print(f"  - Name: {uom_group.name}")
                    print(f"  - Code: {uom_group.sap_group_code}")
                    print(f"  - UoMs: {len(uom_group.uom_ids)}")
                else:
                    print(f"\n[INFO] UoM Group Entry {extended.sap_uom_group_entry} does not exist in Odoo")
                    print(f"  [ACTION] Import UoM Groups from SAP first")
            return
        
        # Product has UoM Group - show details
        uom_group = extended.sap_uom_group_id
        print(f"\n[UOM GROUP DETAILS]")
        print(f"  - ID: {uom_group.id}")
        print(f"  - Name: {uom_group.name}")
        print(f"  - Code: {uom_group.sap_group_code}")
        print(f"  - SAP Entry: {uom_group.sap_abs_entry}")
        print(f"  - Base UoM: {uom_group.base_uom_id.name if uom_group.base_uom_id else 'N/A'}")
        print(f"  - Number of UoMs: {len(uom_group.uom_ids)}")
        
        # Show all UoMs in this group
        print(f"\n[UoMs IN GROUP]")
        for idx, uom_sync in enumerate(uom_group.uom_ids, 1):
            odoo_uom = uom_sync.odoo_uom_id
            print(f"\n  {idx}. SAP UoM: {uom_sync.sap_uom_code}")
            print(f"     - Odoo UoM: {odoo_uom.name if odoo_uom else '[NOT LINKED]'}")
            print(f"     - Base Quantity: {uom_sync.base_quantity}")
            
            if odoo_uom:
                print(f"     - Odoo Factor: {odoo_uom.factor_inv}")
                print(f"     - Odoo UoM ID: {odoo_uom.id}")
        
        # Check pricelists for this product
        print(f"\n" + "="*80)
        print(f"PRICELIST ITEMS")
        print("="*80)
        
        pricelist_items = env['product.pricelist.item'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
        ])
        
        if not pricelist_items:
            print(f"\n[NO PRICES] No pricelist items found for this product")
        else:
            print(f"\n[FOUND] {len(pricelist_items)} pricelist items:")
            
            for item in pricelist_items:
                uom = item.product_packaging_id
                print(f"\n  - Pricelist: {item.pricelist_id.name}")
                print(f"    Price: {item.fixed_price}")
                print(f"    UoM: {uom.name if uom else '[Base/All UoMs]'}")
                print(f"    Min Qty: {item.min_quantity}")
        
        print(f"\n" + "="*80)
        print(f"SUMMARY")
        print("="*80)
        print(f"\n Product: {product.default_code} - {product.name}")
        print(f"  - Has SAP Info: {'YES' if extended else 'NO'}")
        print(f"  - Has UoM Group: {'YES' if extended.sap_uom_group_id else 'NO'}")
        print(f"  - Number of UoMs: {len(uom_group.uom_ids) if extended.sap_uom_group_id else 0}")
        print(f"  - Number of Prices: {len(pricelist_items)}")
        print(f"  - Active for Sale: {'YES' if product.sale_ok else 'NO'}")
        print(f"\n" + "="*80 + "\n")

if __name__ == '__main__':
    item_code = sys.argv[1] if len(sys.argv) > 1 else 'S01084'
    try:
        check_product_uom_group(item_code)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


