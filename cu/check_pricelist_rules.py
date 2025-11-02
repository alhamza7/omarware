#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if pricelist rules exist
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

def check_rules():
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Checking Pricelist Rules")
        print("=" * 80)
        
        product = env['product.product'].search([('default_code', '=', 'R00205')], limit=1)
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        print(f"\nProduct: {product.default_code} (ID: {product.id})")
        print(f"Template: {product.product_tmpl_id.id}")
        print(f"Pricelist: {pricelist.name} (ID: {pricelist.id})")
        
        # Search for all rules
        all_rules = env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ])
        
        print(f"\n✅ Found {len(all_rules)} rules total:")
        for rule in all_rules:
            pkg_info = f"pkg_id={rule.product_packaging_id.id} ({rule.product_packaging_id.name})" if rule.product_packaging_id else "No packaging"
            print(f"  - Rule {rule.id}: Price=${rule.fixed_price:.2f}, applied_on={rule.applied_on}, {pkg_info}")
        
        # Test _get_applicable_rules
        print(f"\n{'='*60}")
        print("Testing _get_applicable_rules")
        print(f"{'='*60}")
        
        applicable = pricelist._get_applicable_rules(product, date=False)
        print(f"\n✅ _get_applicable_rules returned {len(applicable)} rules:")
        for rule in applicable:
            pkg_info = f"pkg_id={rule.product_packaging_id.id}" if rule.product_packaging_id else "None"
            print(f"  - Rule {rule.id}: Price=${rule.fixed_price:.2f}, {pkg_info}")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        check_rules()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

