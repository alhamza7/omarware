#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if UoM Group exists for S01084's UoMGroupEntry
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

def check_uom_group_for_s01084():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\n" + "="*80)
        print("Checking UoM Group for S01084")
        print("="*80)
        
        # According to SAP screenshot: UoM Group = "كارتون 120 ق"
        # We need to find what AbsEntry this group has
        
        # Find the UoM Group
        uom_groups = env['sap.uom.group'].search([])
        print(f"\n[Total UoM Groups in Odoo] {len(uom_groups)}")
        
        # Look for كارتون 120
        for group in uom_groups:
            if '120' in group.name or 'كارتون' in group.name:
                print(f"\n[Found Matching Group]")
                print(f"  - ID: {group.id}")
                print(f"  - Name: {group.name}")
                print(f"  - Code: {group.sap_group_code}")
                print(f"  - SAP AbsEntry: {group.sap_abs_entry}")
                print(f"  - Number of UoMs: {len(group.uom_ids)}")
                
                # Show UoMs in this group
                print(f"\n  [UoMs in this group]:")
                for uom_sync in group.uom_ids:
                    sap_code = uom_sync.sap_uom_id if hasattr(uom_sync, 'sap_uom_id') else 'N/A'
                    print(f"    - {sap_code}: {uom_sync.odoo_uom_id.name if uom_sync.odoo_uom_id else 'NOT LINKED'}")
        
        # Check product S01084
        product = env['product.product'].search([('default_code', '=', 'S01084')], limit=1)
        if product:
            print(f"\n[Product S01084]")
            extended = env['sap.product.extended'].search([('product_id', '=', product.id)], limit=1)
            if extended:
                print(f"  - UoM Group Entry: {extended.sap_uom_group_entry}")
                print(f"  - UoM Group Linked: {extended.sap_uom_group_id.name if extended.sap_uom_group_id else 'NO'}")
        
        print(f"\n" + "="*80 + "\n")

if __name__ == '__main__':
    check_uom_group_for_s01084()

