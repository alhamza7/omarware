#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check available UoMs for product adf00002 in sale order line
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

def check_product_uoms():
    """Check UoMs for product adf00002"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Checking UoMs for Product adf00002")
        print("=" * 80)
        
        # Find product
        product = env['product.product'].search([
            ('default_code', 'ilike', 'adf00002')
        ], limit=1)
        
        if not product:
            print("\nProduct adf00002 not found!")
            return
        
        print(f"\nProduct Found:")
        print(f"  Name: {product.name}")
        print(f"  Code: {product.default_code}")
        print(f"  Base UoM: {product.uom_id.name}")
        
        # Check pricelist items for this product
        print(f"\n{'='*60}")
        print("Pricelist Items (SAP Price List 1)")
        print(f"{'='*60}")
        
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if not pricelist:
            print("SAP Price List 1 not found!")
            return
        
        # Search by template
        items = env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
        ])
        
        print(f"\nTotal pricelist items: {len(items)}")
        
        if items:
            print(f"\nPrice List:")
            for idx, item in enumerate(items, 1):
                uom_name = item.product_packaging_id.name if item.product_packaging_id else "Base (any UoM)"
                price = item.fixed_price
                print(f"  {idx}. {uom_name:30} | ${price:>10.2f}")
            
            # Available UoMs
            print(f"\n{'='*60}")
            print("Available UoMs for Selection in Sale Order Line")
            print(f"{'='*60}")
            
            uom_ids = items.mapped('product_packaging_id')
            print(f"\nUoMs with specific prices: {len(uom_ids)}")
            for idx, uom in enumerate(uom_ids, 1):
                print(f"  {idx}. {uom.name}")
            
            # Check if base price exists (without specific UoM)
            base_item = items.filtered(lambda i: not i.product_packaging_id)
            if base_item:
                print(f"\n  + Base price (default UoM: {product.uom_id.name}): ${base_item[0].fixed_price:.2f}")
        else:
            print("\n  No pricelist items found for this product!")
        
        # Check all available UoMs in system
        print(f"\n{'='*60}")
        print("All UoMs in System")
        print(f"{'='*60}")
        
        all_uoms = env['uom.uom'].search([])
        print(f"\nTotal UoMs: {len(all_uoms)}")
        print("\nSample UoMs (first 20):")
        for idx, uom in enumerate(all_uoms[:20], 1):
            cat = getattr(uom, 'category_id', None)
            cat_name = cat.name if cat else 'N/A'
            print(f"  {idx:2}. {uom.name:30} | Category: {cat_name}")
        
        # Summary
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"\nFor product {product.default_code}:")
        print(f"  - Base UoM: {product.uom_id.name}")
        print(f"  - Pricelist items: {len(items)}")
        print(f"  - UoMs with prices: {len(uom_ids)}")
        
        if len(items) == 0:
            print(f"\n⚠ WARNING: No prices configured for this product!")
            print(f"   You need to sync prices from SAP.")
        elif len(uom_ids) == 0:
            print(f"\n✓ Only base price configured")
            print(f"   User can select any UoM, but price won't change.")
        else:
            print(f"\n✓ Product has {len(uom_ids)} specific UoM prices")
            print(f"   These UoMs should be selectable in sale order line.")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        check_product_uoms()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

