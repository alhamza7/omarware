#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch a single product from SAP with UoM Group information
Uses the Complete Migration wizard logic
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

def fetch_product_from_sap(item_code='S01084'):
    """Fetch a single product from SAP"""
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print(f"Fetching Product from SAP: {item_code}")
        print("="*80)
        
        # Get backend
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        if not backend:
            print("\n[ERROR] No active SAP backend found!")
            return False
        
        print(f"\n[Backend] {backend.name} - {backend.base_url}")
        
        # Create Complete Migration wizard
        wizard = env['sap.product.complete.migration'].create({
            'backend_id': backend.id,
            'stage1_uom_groups': True,
            'stage2_products': True,
            'stage3_pricelists': True,
            'stage4_warehouse_info': False,
            'product_limit': 1,  # Only one product
            'skip_errors': False,
        })
        
        print(f"\n[Wizard Created] ID: {wizard.id}")
        
        # Modify wizard to fetch only one product
        print(f"\n[Action] Fetching product {item_code} from SAP...")
        
        try:
            # Call the wizard's action to start migration
            result = wizard.action_start_migration()
            
            print(f"\n[SUCCESS] Migration completed!")
            print(f"Result: {result}")
            
            # Check if product was created/updated
            product = env['product.product'].search([
                ('default_code', '=', item_code)
            ], limit=1)
            
            if product:
                print(f"\n[PRODUCT INFO]")
                print(f"  - ID: {product.id}")
                print(f"  - Name: {product.name}")
                print(f"  - Code: {product.default_code}")
                print(f"  - UoM: {product.uom_id.name}")
                
                # Check SAP extended info
                extended = env['sap.product.extended'].search([
                    ('product_id', '=', product.id)
                ], limit=1)
                
                if extended:
                    print(f"\n[SAP EXTENDED INFO]")
                    print(f"  - SAP Item Code: {extended.sap_item_code}")
                    print(f"  - UoM Group Entry: {extended.sap_uom_group_entry or 'N/A'}")
                    
                    if extended.sap_uom_group_id:
                        uom_group = extended.sap_uom_group_id
                        print(f"  - UoM Group: {uom_group.name}")
                        print(f"  - UoM Group Code: {uom_group.sap_group_code}")
                        print(f"  - Base UoM: {uom_group.base_uom_id.name if uom_group.base_uom_id else 'N/A'}")
                        print(f"  - Number of UoMs: {len(uom_group.uom_ids)}")
                        
                        # Show UoMs
                        print(f"\n[UoMs IN GROUP]")
                        for idx, uom_sync in enumerate(uom_group.uom_ids, 1):
                            odoo_uom = uom_sync.odoo_uom_id
                            print(f"  {idx}. {uom_sync.sap_uom_code}: {odoo_uom.name if odoo_uom else 'NOT LINKED'}")
                    else:
                        print(f"  - UoM Group: NOT LINKED")
                
                # Check pricelists
                pricelist_items = env['product.pricelist.item'].search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('applied_on', '=', '1_product'),
                ])
                
                print(f"\n[PRICELIST ITEMS] {len(pricelist_items)} items found")
                for item in pricelist_items[:5]:  # Show first 5
                    uom = item.product_packaging_id
                    print(f"  - {item.pricelist_id.name}: ${item.fixed_price} ({uom.name if uom else 'Base'})")
            else:
                print(f"\n[WARNING] Product not found after import!")
            
            cr.commit()
            return True
            
        except AttributeError as e:
            # Wizard might not have the batch method, use regular import
            print(f"\n[INFO] Using alternative import method...")
            
            try:
                # Import single product using sync wizard
                sync_wizard = env['sap.product.sync.wizard'].create({
                    'backend_id': backend.id,
                    'item_code_filter': item_code,
                })
                
                sync_wizard.action_sync_products()
                
                print(f"\n[SUCCESS] Product sync completed!")
                
                # Check product
                product = env['product.product'].search([
                    ('default_code', '=', item_code)
                ], limit=1)
                
                if product:
                    print(f"\n[PRODUCT FOUND] {product.name}")
                    
                    # Check extended info
                    extended = env['sap.product.extended'].search([
                        ('product_id', '=', product.id)
                    ], limit=1)
                    
                    if extended and extended.sap_uom_group_entry:
                        print(f"[UoM Group Entry] {extended.sap_uom_group_entry}")
                        
                        # Check if group exists
                        uom_group = env['sap.uom.group'].search([
                            ('sap_abs_entry', '=', extended.sap_uom_group_entry)
                        ], limit=1)
                        
                        if not uom_group:
                            print(f"\n[ACTION] Importing UoM Group {extended.sap_uom_group_entry}...")
                            backend.action_import_uom_groups()
                        else:
                            print(f"[UoM Group] {uom_group.name} - {len(uom_group.uom_ids)} UoMs")
                
                cr.commit()
                return True
                
            except Exception as e2:
                print(f"\n[ERROR] {e2}")
                import traceback
                traceback.print_exc()
                return False
        
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    item_code = sys.argv[1] if len(sys.argv) > 1 else 'S01084'
    print(f"\n{'='*80}")
    print(f"SAP Product Import Script")
    print(f"Target Product: {item_code}")
    print(f"{'='*80}")
    
    success = fetch_product_from_sap(item_code)
    
    if success:
        print(f"\n{'='*80}")
        print(f"[COMPLETED] Product import finished successfully!")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"[FAILED] Product import failed!")
        print(f"{'='*80}\n")

