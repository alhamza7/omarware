#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find products with codes similar to adf00002
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

def find_products():
    """Find products with codes similar to adf00002"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Searching for Products")
        print("=" * 80)
        
        # Search variations
        searches = [
            ('default_code', '=', 'adf00002'),
            ('default_code', 'ilike', 'adf00002'),
            ('default_code', 'ilike', 'adf%'),
            ('default_code', 'ilike', 'ADF%'),
            ('name', 'ilike', 'adf00002'),
        ]
        
        for domain_field, operator, value in searches:
            print(f"\nSearching: {domain_field} {operator} '{value}'")
            products = env['product.product'].search([
                (domain_field, operator, value)
            ], limit=10)
            
            if products:
                print(f"  Found {len(products)} products:")
                for p in products:
                    print(f"    - [{p.default_code}] {p.name}")
            else:
                print(f"  No products found")
        
        # Show sample products with pricelist items
        print(f"\n{'='*60}")
        print("Sample Products with Pricelist Items (first 10)")
        print(f"{'='*60}")
        
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if pricelist:
            items = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('applied_on', '=', '1_product'),
                ('product_packaging_id', '!=', False),
            ], limit=10)
            
            print(f"\nShowing {len(items)} products with UoM-specific prices:")
            
            seen_products = set()
            for item in items:
                prod_code = item.product_tmpl_id.default_code
                if prod_code not in seen_products:
                    seen_products.add(prod_code)
                    print(f"\n  [{prod_code}] {item.product_tmpl_id.name[:50]}")
                    
                    # Get all items for this product
                    prod_items = env['product.pricelist.item'].search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_tmpl_id', '=', item.product_tmpl_id.id),
                        ('applied_on', '=', '1_product'),
                    ])
                    
                    print(f"    UoMs: {len(prod_items)}")
                    for pi in prod_items:
                        uom_name = pi.product_packaging_id.name if pi.product_packaging_id else "Base"
                        print(f"      - {uom_name:30} | ${pi.fixed_price:>8.2f}")
                    
                    if len(seen_products) >= 5:
                        break
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        find_products()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

