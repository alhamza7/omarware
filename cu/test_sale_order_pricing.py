#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to test Sale Order Line pricing with different UoMs
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

def test_sale_order_pricing():
    """Test Sale Order Line pricing with different UoMs"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing Sale Order Line UoM Pricing")
        print("=" * 80)
        
        # Get product
        product_code = 'R00205'
        product = env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            print(f"ERROR: Product {product_code} not found!")
            return False
        
        print(f"\nProduct: {product.default_code} - {product.name}")
        print(f"Template ID: {product.product_tmpl_id.id}")
        print(f"Base UoM: {product.uom_id.name} (ID: {product.uom_id.id})")
        
        # Get pricelist
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if not pricelist:
            print("\nERROR: SAP Price List 1 not found!")
            return False
        
        print(f"Pricelist: {pricelist.name} (ID: {pricelist.id})")
        
        # Show available pricelist items
        print("\n" + "=" * 80)
        print("Available Pricelist Items:")
        print("=" * 80)
        
        items = env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
        ])
        
        print(f"\nFound {len(items)} pricelist items:")
        for item in items:
            uom_info = f"UoM ID: {item.product_packaging_id.id} ({item.product_packaging_id.name})" if item.product_packaging_id else "Base (no packaging)"
            print(f"  - Price: ${item.fixed_price:.2f}, {uom_info}")
        
        # Test different UoMs
        print("\n" + "=" * 80)
        print("Testing Sale Order Line with different UoMs:")
        print("=" * 80)
        
        # Get available UoMs
        test_uoms = [
            product.uom_id,  # Base UoM
            env['uom.uom'].search([('name', '=', '50 غم')], limit=1),
            env['uom.uom'].search([('name', '=', '100 غم')], limit=1),
            env['uom.uom'].search([('name', '=', '125 غم')], limit=1),
            env['uom.uom'].search([('name', '=', '0.5 كيلو')], limit=1),
            env['uom.uom'].search([('name', '=', '0.25 كغم بالأساسي')], limit=1),
        ]
        
        # Create a test sale order
        partner = env['res.partner'].search([], limit=1)
        
        sale_order = env['sale.order'].create({
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
        })
        
        print(f"\nCreated test Sale Order: {sale_order.name}")
        
        for uom in test_uoms:
            if not uom:
                continue
            
            print(f"\n{'='*60}")
            print(f"Testing UoM: {uom.name} (ID: {uom.id})")
            print(f"{'='*60}")
            
            # Search for matching pricelist item
            print(f"\nSearching for pricelist item with:")
            print(f"  - pricelist_id: {pricelist.id}")
            print(f"  - product_tmpl_id: {product.product_tmpl_id.id}")
            print(f"  - applied_on: '1_product'")
            print(f"  - product_packaging_id: {uom.id}")
            
            pricelist_item = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product'),
                ('product_packaging_id', '=', uom.id),
                ('compute_price', '=', 'fixed'),
            ], limit=1)
            
            if pricelist_item:
                print(f"✅ Found pricelist item!")
                print(f"   Price: ${pricelist_item.fixed_price:.2f}")
            else:
                print(f"❌ No pricelist item found for this UoM")
                
                # Try base price
                base_item = env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('applied_on', '=', '1_product'),
                    ('product_packaging_id', '=', False),
                ], limit=1)
                
                if base_item:
                    print(f"   Found base price: ${base_item.fixed_price:.2f}")
                else:
                    print(f"   No base price found either!")
            
            # Create sale order line
            try:
                line = env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'product_uom_id': uom.id,
                })
                
                print(f"\n📝 Created Sale Order Line:")
                print(f"   Product: {line.product_id.name}")
                print(f"   UoM: {line.product_uom_id.name}")
                print(f"   Price Unit: ${line.price_unit:.2f}")
                
                if pricelist_item:
                    if abs(line.price_unit - pricelist_item.fixed_price) < 0.01:
                        print(f"   ✅ Price matches expected price!")
                    else:
                        print(f"   ❌ Price mismatch! Expected ${pricelist_item.fixed_price:.2f}")
                
                # Clean up
                line.unlink()
                
            except Exception as e:
                print(f"   ❌ Error creating line: {str(e)}")
        
        # Clean up
        sale_order.unlink()
        
        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)
        
        return True

if __name__ == '__main__':
    try:
        test_sale_order_pricing()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

