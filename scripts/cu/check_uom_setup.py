#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check UoM setup for products with multiple prices
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

def check_uom_setup():
    """Check UoM configuration for products"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Checking UoM Setup for Products with Multiple Prices")
        print("=" * 80)
        
        # Get a sample product with multiple UoM prices
        pricelist_items = env['product.pricelist.item'].search([
            ('product_packaging_id', '!=', False),
            ('applied_on', '=', '1_product'),
        ], limit=50)
        
        print(f"\nFound {len(pricelist_items)} pricelist items with UoM")
        
        # Group by product
        products_data = {}
        for item in pricelist_items:
            tmpl = item.product_tmpl_id
            if tmpl.id not in products_data:
                products_data[tmpl.id] = {
                    'template': tmpl,
                    'base_uom': tmpl.uom_id,
                    'price_uoms': []
                }
            products_data[tmpl.id]['price_uoms'].append({
                'uom': item.product_packaging_id,
                'price': item.fixed_price,
            })
        
        print(f"\nSample Products (first 5):")
        print("=" * 80)
        
        for idx, (tmpl_id, data) in enumerate(list(products_data.items())[:5], 1):
            template = data['template']
            base_uom = data['base_uom']
            price_uoms = data['price_uoms']
            
            print(f"\n{idx}. Product: {template.name}")
            print(f"   Default Code: {template.default_code}")
            base_cat = getattr(base_uom, 'category_id', None)
            base_cat_name = base_cat.name if base_cat else 'N/A'
            print(f"   Base UoM: {base_uom.name} (Category: {base_cat_name})")
            print(f"   \nPrice UoMs:")
            
            for i, uom_data in enumerate(price_uoms, 1):
                uom = uom_data['uom']
                price = uom_data['price']
                uom_cat = getattr(uom, 'category_id', None)
                uom_cat_name = uom_cat.name if uom_cat else 'N/A'
                same_category = (base_cat and uom_cat and uom_cat == base_cat)
                status = "SAME" if same_category else "DIFFERENT"
                
                print(f"     {i}. {uom.name:20} | ${price:>8.2f} | Category: {uom_cat_name:20} [{status}]")
            
            # Check if product has packagings (if model exists)
            try:
                packagings = env['product.packaging'].search([
                    ('product_tmpl_id', '=', template.id)
                ])
                
                print(f"   \nProduct Packagings: {len(packagings)}")
                if packagings:
                    for pkg in packagings:
                        print(f"     - {pkg.name} (UoM: {pkg.product_uom_id.name}, Qty: {pkg.qty})")
            except KeyError:
                print(f"   \nProduct Packagings: N/A (model not available)")
        
        # Check UoM categories
        print(f"\n{'='*80}")
        print("UoM Categories Used in Prices")
        print(f"{'='*80}")
        
        uom_categories = {}
        for data in products_data.values():
            for uom_data in data['price_uoms']:
                uom = uom_data['uom']
                cat = getattr(uom, 'category_id', None)
                cat_name = cat.name if cat else 'N/A'
                if cat_name not in uom_categories:
                    uom_categories[cat_name] = []
                if uom.name not in uom_categories[cat_name]:
                    uom_categories[cat_name].append(uom.name)
        
        for cat_name, uoms in sorted(uom_categories.items()):
            print(f"\n{cat_name}:")
            for uom_name in sorted(uoms):
                print(f"  - {uom_name}")
        
        # Summary
        print(f"\n{'='*80}")
        print("Analysis")
        print(f"{'='*80}")
        
        products_with_diff_categories = 0
        for data in products_data.values():
            base_cat = getattr(data['base_uom'], 'category_id', None)
            for uom_data in data['price_uoms']:
                uom_cat = getattr(uom_data['uom'], 'category_id', None)
                if base_cat and uom_cat and uom_cat != base_cat:
                    products_with_diff_categories += 1
                    break
        
        print(f"\nProducts with prices in different UoM categories: {products_with_diff_categories}")
        print(f"Total products analyzed: {len(products_data)}")
        
        if products_with_diff_categories > 0:
            print(f"\n⚠ WARNING: Some products have prices in UoM categories different from their base UoM!")
            print(f"   This will prevent UoM selection in Sale Order Lines.")
            print(f"   \nSolution options:")
            print(f"   1. Change product base UoM to match price UoMs")
            print(f"   2. Use Product Packaging instead of direct UoM selection")
            print(f"   3. Allow UoM selection across categories (requires custom module)")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        check_uom_setup()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
