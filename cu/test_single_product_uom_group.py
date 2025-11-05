#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to fetch a single product (S01084) with its UoM Group from SAP
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

def test_fetch_product_with_uom_group(item_code='S01084'):
    """Test fetching a product with its UoM Group"""
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print(f"Testing Single Product Fetch: {item_code}")
        print("="*80)
        
        # Get backend
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        if not backend:
            print("[ERROR] No active SAP backend found!")
            return
        
        print(f"\n[Backend] {backend.name}")
        print(f"[URL] {backend.base_url}")
        
        # Import and create SAP Service Layer connection
        from addons.sap_integration.models.sap_service_layer import SapServiceLayerConnection
        
        service_layer = SapServiceLayerConnection(
            base_url=backend.base_url,
            username=backend.username,
            password=backend.password,
            company_db=backend.company_db,
            verify_ssl=backend.verify_ssl
        )
        
        # ===========================================
        # Step 1: Fetch Item from SAP
        # ===========================================
        print(f"\n{'='*80}")
        print(f"STEP 1: Fetching Item {item_code} from SAP")
        print(f"{'='*80}")
        
        endpoint = f"Items('{item_code}')"
        item_data = service_layer.get(endpoint)
        
        if not item_data:
            print(f"[ERROR] Item {item_code} not found in SAP!")
            return
        
        print(f"\n[SUCCESS] Item fetched from SAP")
        print(f"  - ItemCode: {item_data.get('ItemCode')}")
        print(f"  - ItemName: {item_data.get('ItemName')}")
        print(f"  - InventoryUOM: {item_data.get('InventoryUOM')}")
        print(f"  - UoMGroupEntry: {item_data.get('UoMGroupEntry')}")
        
        uom_group_entry = item_data.get('UoMGroupEntry')
        if not uom_group_entry or uom_group_entry == -1:
            print(f"\n[WARNING] Item has no UoM Group (Entry: {uom_group_entry})")
        else:
            print(f"\n[INFO] Item belongs to UoM Group Entry: {uom_group_entry}")
        
        # ===========================================
        # Step 2: Check if UoM Group exists in Odoo
        # ===========================================
        print(f"\n{'='*80}")
        print(f"STEP 2: Checking UoM Group in Odoo")
        print(f"{'='*80}")
        
        if uom_group_entry and uom_group_entry != -1:
            uom_group = env['sap.uom.group'].search([
                ('sap_abs_entry', '=', uom_group_entry),
                ('backend_id', '=', backend.id)
            ], limit=1)
            
            if uom_group:
                print(f"\n[FOUND] UoM Group exists in Odoo:")
                print(f"  - ID: {uom_group.id}")
                print(f"  - Name: {uom_group.name}")
                print(f"  - Code: {uom_group.sap_group_code}")
                print(f"  - SAP Entry: {uom_group.sap_abs_entry}")
                print(f"  - Base UoM: {uom_group.base_uom_id.name if uom_group.base_uom_id else 'N/A'}")
                
                # Show UoMs in this group
                print(f"\n  [UoMs in Group] ({len(uom_group.uom_ids)} units):")
                for uom_sync in uom_group.uom_ids:
                    odoo_uom = uom_sync.odoo_uom_id
                    print(f"    - {uom_sync.sap_uom_code}: {odoo_uom.name if odoo_uom else 'NOT LINKED'}")
                    if odoo_uom:
                        print(f"      Factor: {uom_sync.base_quantity} (SAP) -> {odoo_uom.factor_inv} (Odoo)")
            else:
                print(f"\n[NOT FOUND] UoM Group Entry {uom_group_entry} not in Odoo")
                print(f"[ACTION] Fetching UoM Group from SAP...")
                
                # Fetch UoM Group from SAP
                group_endpoint = f"UoMGroups({uom_group_entry})"
                group_data = service_layer.get(group_endpoint)
                
                if group_data:
                    print(f"\n[SUCCESS] UoM Group fetched from SAP:")
                    print(f"  - AbsEntry: {group_data.get('AbsEntry')}")
                    print(f"  - Code: {group_data.get('Code')}")
                    print(f"  - Name: {group_data.get('Name')}")
                    print(f"  - BaseUoM: {group_data.get('BaseUoM')}")
                    
                    # Show UoM definitions
                    definitions = group_data.get('UoMGroupDefinitionCollection', [])
                    print(f"\n  [UoM Definitions] ({len(definitions)} units):")
                    for defn in definitions:
                        print(f"    - {defn.get('AlternateUoM')}: BaseQty={defn.get('BaseQuantity')}, Factor={defn.get('AlternateQuantity')}")
                else:
                    print(f"[ERROR] Failed to fetch UoM Group from SAP")
        
        # ===========================================
        # Step 3: Check if Product exists in Odoo
        # ===========================================
        print(f"\n{'='*80}")
        print(f"STEP 3: Checking Product in Odoo")
        print(f"{'='*80}")
        
        product = env['product.product'].search([
            ('default_code', '=', item_code)
        ], limit=1)
        
        if product:
            print(f"\n[FOUND] Product exists in Odoo:")
            print(f"  - ID: {product.id}")
            print(f"  - Name: {product.name}")
            print(f"  - Code: {product.default_code}")
            print(f"  - UoM: {product.uom_id.name}")
            
            # Check SAP Extended info
            extended = env['sap.product.extended'].search([
                ('product_id', '=', product.id),
                ('backend_id', '=', backend.id)
            ], limit=1)
            
            if extended:
                print(f"\n  [SAP Extended Info]:")
                print(f"    - SAP Item Code: {extended.sap_item_code}")
                print(f"    - UoM Group Entry: {extended.sap_uom_group_entry}")
                print(f"    - UoM Group: {extended.sap_uom_group_id.name if extended.sap_uom_group_id else 'NOT LINKED'}")
            else:
                print(f"\n  [NO SAP INFO] Product has no SAP extended information")
        else:
            print(f"\n[NOT FOUND] Product {item_code} not in Odoo")
            print(f"[ACTION] Would need to run Complete Migration to import it")
        
        # ===========================================
        # Step 4: Show Summary
        # ===========================================
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"\nItem {item_code}:")
        print(f"  [SAP] {'YES' if item_data else 'NO'}")
        print(f"  [UoM Group Entry] {uom_group_entry if uom_group_entry else 'N/A'}")
        
        if uom_group_entry and uom_group_entry != -1:
            uom_group_exists = env['sap.uom.group'].search_count([
                ('sap_abs_entry', '=', uom_group_entry),
                ('backend_id', '=', backend.id)
            ])
            print(f"  [UoM Group in Odoo] {'YES' if uom_group_exists else 'NO'}")
        
        product_exists = env['product.product'].search_count([
            ('default_code', '=', item_code)
        ])
        print(f"  [Product in Odoo] {'YES' if product_exists else 'NO'}")
        
        print(f"\n{'='*80}\n")

if __name__ == '__main__':
    item_code = sys.argv[1] if len(sys.argv) > 1 else 'S01084'
    try:
        test_fetch_product_with_uom_group(item_code)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

