#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create product packaging from SAP UoMs for products with multiple price UoMs
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

def create_product_packaging():
    """Create product packaging entries for products with multiple UoM prices"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Creating Product Packaging from SAP UoM Prices")
        print("=" * 80)
        
        # Get all pricelist items with UoM (product_packaging_id points to uom.uom)
        pricelist_items = env['product.pricelist.item'].search([
            ('product_packaging_id', '!=', False),
            ('applied_on', '=', '1_product'),
        ])
        
        print(f"\nFound {len(pricelist_items)} pricelist items with UoM")
        
        # Group by product template
        products_with_uoms = {}
        for item in pricelist_items:
            tmpl_id = item.product_tmpl_id.id
            if tmpl_id not in products_with_uoms:
                products_with_uoms[tmpl_id] = {
                    'template': item.product_tmpl_id,
                    'uoms': set()
                }
            products_with_uoms[tmpl_id]['uoms'].add(item.product_packaging_id.id)
        
        print(f"Products with multiple UoM prices: {len(products_with_uoms)}")
        
        # Create packaging for each product-UoM combination
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n{'='*60}")
        print("Creating Product Packaging entries...")
        print(f"{'='*60}\n")
        
        for tmpl_id, data in products_with_uoms.items():
            template = data['template']
            uoms = data['uoms']
            
            # Skip if only one UoM (base UoM)
            if len(uoms) <= 1:
                skipped_count += 1
                continue
            
            print(f"Processing: {template.name[:50]}")
            print(f"  UoMs: {len(uoms)}")
            
            for uom_id in uoms:
                uom = env['uom.uom'].browse(uom_id)
                
                # Skip base UoM
                if uom == template.uom_id:
                    continue
                
                # Check if packaging already exists
                existing = env['product.packaging'].search([
                    ('product_tmpl_id', '=', template.id),
                    ('product_uom_id', '=', uom.id),
                ], limit=1)
                
                if existing:
                    print(f"    - {uom.name}: Already exists")
                    skipped_count += 1
                    continue
                
                try:
                    # Calculate qty based on UoM factor
                    # If UoM is bigger than base (e.g., 100 gm vs 1 kg), factor_inv is larger
                    qty = 1.0
                    if uom.factor_inv and template.uom_id.factor_inv:
                        qty = uom.factor_inv / template.uom_id.factor_inv
                    
                    # Create packaging
                    packaging = env['product.packaging'].create({
                        'name': uom.name,
                        'product_tmpl_id': template.id,
                        'product_uom_id': uom.id,
                        'qty': qty,
                    })
                    
                    print(f"    + {uom.name}: Created (qty={qty:.4f})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"    x {uom.name}: ERROR - {str(e)}")
                    error_count += 1
        
        # Commit changes
        cr.commit()
        
        # Summary
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"  Products processed: {len(products_with_uoms)}")
        print(f"  Packaging created: {created_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Errors: {error_count}")
        
        # Verify - show sample products with packaging
        print(f"\n{'='*60}")
        print("Sample Products with Packaging (first 5)")
        print(f"{'='*60}\n")
        
        sample_products = list(products_with_uoms.values())[:5]
        for data in sample_products:
            template = data['template']
            packagings = env['product.packaging'].search([
                ('product_tmpl_id', '=', template.id)
            ])
            
            print(f"{template.name[:50]}")
            print(f"  Base UoM: {template.uom_id.name}")
            if packagings:
                print(f"  Packagings: {len(packagings)}")
                for pkg in packagings[:3]:
                    print(f"    - {pkg.name} (qty={pkg.qty:.4f} {pkg.product_uom_id.name})")
            else:
                print(f"  Packagings: None")
            print()
        
        print("=" * 80)

if __name__ == '__main__':
    try:
        create_product_packaging()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

