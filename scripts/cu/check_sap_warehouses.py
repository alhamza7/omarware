# -*- coding: utf-8 -*-
"""Check SAP warehouse info"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

def check_sap_warehouses():
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, 1, {})
        
        # Check if SAP model exists
        if 'sap.product.warehouse.info' not in env:
            print("SAP model not found!")
            return
        
        # Get sample product
        product = env['product.product'].search([('default_code', '=', 'R00461')], limit=1)
        print(f"Product: {product.display_name} (ID: {product.id})")
        print("="*70)
        
        # Get SAP warehouse info
        sap_infos = env['sap.product.warehouse.info'].search([
            ('product_id', '=', product.id)
        ])
        
        print(f"\nFound {len(sap_infos)} SAP warehouse info records:\n")
        
        for info in sap_infos:
            print(f"Warehouse: {info.warehouse_id.name if info.warehouse_id else 'NO WAREHOUSE'}")
            print(f"  SAP Code: {info.sap_warehouse_code}")
            print(f"  SAP Name: {info.sap_warehouse_name}")
            print(f"  Last In Stock (SAP): {info.last_in_stock}")
            print(f"  Last Committed: {info.last_committed}")
            print(f"  Last Available: {info.last_available}")
            print(f"  Current Qty Available (Odoo): {info.current_qty_available}")
            print(f"  Current Qty Reserved (Odoo): {info.current_qty_reserved}")
            print()

if __name__ == '__main__':
    check_sap_warehouses()

