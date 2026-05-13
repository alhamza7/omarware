# -*- coding: utf-8 -*-
"""Check all UoMs and prices for a product"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

def check_all_uoms_and_prices():
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, 1, {})
        
        # Get a product with multiple UoMs
        product = env['product.product'].search([('default_code', '=', 'S00711')], limit=1)
        
        if not product:
            product = env['product.product'].search([('sale_ok', '=', True)], limit=1)
        
        print(f"\n{'='*80}")
        print(f"Product: {product.display_name}")
        print(f"Base UoM: {product.uom_id.name} (ID: {product.uom_id.id})")
        print(f"{'='*80}\n")
        
        # Get ALL pricelist items for this product (regardless of pricelist)
        all_items = env['product.pricelist.item'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ], order='pricelist_id, id')
        
        print(f"Found {len(all_items)} total pricelist items across all pricelists:\n")
        
        current_pricelist = None
        for item in all_items:
            if item.pricelist_id != current_pricelist:
                current_pricelist = item.pricelist_id
                print(f"\n{'─'*80}")
                print(f"📋 Pricelist: {item.pricelist_id.name} (ID: {item.pricelist_id.id})")
                print(f"{'─'*80}")
            
            print(f"\n  Item #{item.id}:")
            print(f"    Applied On: {item.applied_on}")
            print(f"    Product ID: {item.product_id.display_name if item.product_id else 'ALL VARIANTS'}")
            print(f"    Product UoM ID: {item.product_uom_id.name if item.product_uom_id else 'NOT SET'} (ID: {item.product_uom_id.id if item.product_uom_id else None})")
            print(f"    Product Packaging: {item.product_packaging_id.name if item.product_packaging_id else 'NOT SET'} (ID: {item.product_packaging_id.id if item.product_packaging_id else None})")
            print(f"    Compute Price: {item.compute_price}")
            print(f"    Fixed Price: ${item.fixed_price}")
            print(f"    Min Quantity: {item.min_quantity}")
        
        # Now test getting prices with different UoMs
        print(f"\n\n{'='*80}")
        print(f"Testing Price Retrieval with Different UoMs:")
        print(f"{'='*80}\n")
        
        # Get SAP Price List 1
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if pricelist:
            print(f"Using Pricelist: {pricelist.name}\n")
            
            # Get all UoMs mentioned in pricelist items
            uom_ids = set()
            for item in all_items.filtered(lambda i: i.pricelist_id == pricelist):
                if item.product_uom_id:
                    uom_ids.add(item.product_uom_id.id)
                if item.product_packaging_id and item.product_packaging_id.product_uom_id:
                    uom_ids.add(item.product_packaging_id.product_uom_id.id)
            
            # Add base UoM
            uom_ids.add(product.uom_id.id)
            
            print(f"Testing with {len(uom_ids)} different UoMs:\n")
            
            for uom_id in uom_ids:
                uom = env['uom.uom'].browse(uom_id)
                try:
                    price = pricelist._get_product_price(product, 1.0, uom=uom)
                    print(f"  UoM: {uom.name:20s} (ID: {uom.id:3d}) → Price: ${price}")
                except Exception as e:
                    print(f"  UoM: {uom.name:20s} (ID: {uom.id:3d}) → ERROR: {e}")

if __name__ == '__main__':
    check_all_uoms_and_prices()

