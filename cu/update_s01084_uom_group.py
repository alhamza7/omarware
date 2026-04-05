#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update S01084 extended info from SAP
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config
from odoo.orm.registry import Registry

config.parse_config(['--config=odoo.conf', '--database=lugal'])
registry = Registry('lugal')

def update_s01084_from_sap():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print("Updating S01084 Extended Info from SAP")
        print("="*80)
        
        # Find product and backend
        product = env['product.product'].search([('default_code', '=', 'S01084')], limit=1)
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        
        if not product or not backend:
            print("[ERROR] Product or Backend not found!")
            return
        
        print(f"\n[Product] {product.name} (ID: {product.id})")
        print(f"[Backend] {backend.name}")
        
        # Delete old extended info
        extended = env['sap.product.extended'].search([
            ('product_id', '=', product.id)
        ])
        
        if extended:
            print(f"\n[Deleting] Old extended info")
            extended.unlink()
        
        # Manually create SAP data (from screenshot)
        # We know from SAP that UoMGroupEntry should be 120
        sap_data = {
            'ItemCode': 'S01084',
            'ItemName': 'S-1062',
            'ForeignName': 'درام ملون 50 كل',
            'UoMGroupEntry': 120,  # From SAP screenshot
            'InventoryUoM': 'درزن',
        }
        
        print(f"\n[Creating] Extended info with UoMGroupEntry: {sap_data['UoMGroupEntry']}")
        
        # Create extended info
        extended = env['sap.product.extended'].create_or_update_from_sap(
            product, backend, sap_data
        )
        
        print(f"\n[Extended Info Created]")
        print(f"  - SAP UoM Group Entry: {extended.sap_uom_group_entry}")
        print(f"  - SAP UoM Group: {extended.sap_uom_group_id.name if extended.sap_uom_group_id else 'NOT LINKED'}")
        
        if extended.sap_uom_group_id:
            group = extended.sap_uom_group_id
            print(f"\n[SUCCESS] Product linked to UoM Group!")
            print(f"  - Group Name: {group.name}")
            print(f"  - Group Code: {group.sap_group_code}")
            print(f"  - SAP AbsEntry: {group.sap_abs_entry}")
            print(f"  - Number of UoMs: {len(group.uom_ids)}")
            
            print(f"\n  [Available UoMs for this product]:")
            for uom_sync in group.uom_ids:
                if uom_sync.odoo_uom_id:
                    print(f"    - {uom_sync.odoo_uom_id.name}")
        
        cr.commit()
        
        print(f"\n" + "="*80)
        print(f"[COMPLETED]")
        print("="*80 + "\n")

if __name__ == '__main__':
    update_s01084_from_sap()


