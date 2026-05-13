#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to fetch a single product S01084 from SAP
"""
import sys
import os
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config
from odoo.orm.registry import Registry

config.parse_config(['--config=odoo.conf', '--database=lugal'])
registry = Registry('lugal')

def fetch_product_s01084():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print("Fetching Product S01084 from SAP")
        print("="*80)
        
        # Get backend
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        print(f"\n[Backend] {backend.name}")
        
        # Create wizard
        wizard = env['sap.product.complete.migration'].create({
            'backend_id': backend.id,
            'stage1_uom_groups': True,
            'stage2_products': True,
            'stage3_pricelists': True,
            'stage4_warehouse_info': False,
            'product_limit': 1,
        })
        
        print(f"[Wizard] Created ID: {wizard.id}")
        print(f"\n[Starting Migration...]")
        print(f"  - Stage 1: UoM Groups")
        print(f"  - Stage 2: Products (limit 1)")
        print(f"  - Stage 3: Pricelists")
        
        try:
            # Start migration
            wizard.run_complete_migration()
            
            print(f"\n[SUCCESS] Migration completed!")
            
            # Check result
            product = env['product.product'].search([('default_code', '=', 'S01084')], limit=1)
            if product:
                print(f"\n[Product Found] {product.name}")
                extended = env['sap.product.extended'].search([('product_id', '=', product.id)], limit=1)
                if extended and extended.sap_uom_group_id:
                    print(f"[UoM Group] {extended.sap_uom_group_id.name} - {len(extended.sap_uom_group_id.uom_ids)} UoMs")
            
            cr.commit()
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fetch_product_s01084()

