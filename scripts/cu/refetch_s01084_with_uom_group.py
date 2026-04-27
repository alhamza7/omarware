#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete S01084 extended info and re-fetch from SAP
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

def refetch_s01084():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print("Re-fetching S01084 with UoM Group Fix")
        print("="*80)
        
        # Find product
        product = env['product.product'].search([('default_code', '=', 'S01084')], limit=1)
        if not product:
            print("\n[ERROR] Product S01084 not found!")
            return
        
        print(f"\n[Product Found] {product.name} (ID: {product.id})")
        
        # Delete extended info to re-fetch
        extended = env['sap.product.extended'].search([
            ('product_id', '=', product.id)
        ])
        
        if extended:
            print(f"[Deleting] Old extended info (ID: {extended.id})")
            extended.unlink()
        
        # Get backend
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        
        # Fetch item from SAP
        print(f"\n[Fetching from SAP...]")
        from addons.sap_integration.models.sap_service_layer import SapServiceLayerConnection
        
        conn = SapServiceLayerConnection(
            base_url=backend.base_url,
            username=backend.username,
            password=backend.password,
            company_db=backend.company_db,
            verify_ssl=backend.verify_ssl
        )
        
        item_data = conn.get(f"Items('S01084')")
        
        if not item_data:
            print("[ERROR] Could not fetch item from SAP!")
            return
        
        print(f"[SAP Data Retrieved]")
        print(f"  - ItemCode: {item_data.get('ItemCode')}")
        print(f"  - ItemName: {item_data.get('ItemName')}")
        print(f"  - UoMGroupEntry: {item_data.get('UoMGroupEntry')}")
        
        # Create extended info
        print(f"\n[Creating Extended Info...]")
        extended = env['sap.product.extended'].create_or_update_from_sap(
            product, backend, item_data
        )
        
        print(f"[Extended Info Created] ID: {extended.id}")
        print(f"  - SAP UoM Group Entry: {extended.sap_uom_group_entry}")
        print(f"  - SAP UoM Group: {extended.sap_uom_group_id.name if extended.sap_uom_group_id else 'NOT LINKED'}")
        
        if extended.sap_uom_group_id:
            print(f"\n[SUCCESS] Product linked to UoM Group!")
            print(f"  - Group Name: {extended.sap_uom_group_id.name}")
            print(f"  - Group Code: {extended.sap_uom_group_id.sap_group_code}")
            print(f"  - Number of UoMs: {len(extended.sap_uom_group_id.uom_ids)}")
        else:
            print(f"\n[WARNING] UoM Group not linked!")
            print(f"  - Reason: Group Entry {extended.sap_uom_group_entry} not found in Odoo")
            print(f"  - Solution: Import UoM Groups first")
        
        cr.commit()
        print(f"\n" + "="*80)
        print(f"[COMPLETED]")
        print("="*80 + "\n")

if __name__ == '__main__':
    refetch_s01084()


