#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to test Sale Order Line pricing with onchange methods
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
    """Test Sale Order Line pricing with onchange"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing Sale Order Line UoM Pricing WITH onchange")
        print("=" * 80)
        
        # Get product
        product_code = 'R00205'
        product = env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            print(f"ERROR: Product {product_code} not found!")
            return False
        
        print(f"\nProduct: {product.default_code} - {product.name}")
        print(f"Template ID: {product.product_tmpl_id.id}")
        
        # Get pricelist
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if not pricelist:
            print("\nERROR: SAP Price List 1 not found!")
            return False
        
        print(f"Pricelist: {pricelist.name} (ID: {pricelist.id})")
        
        # Create a test sale order
        partner = env['res.partner'].search([], limit=1)
        
        sale_order = env['sale.order'].create({
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
        })
        
        print(f"\nCreated test Sale Order: {sale_order.name}")
        
        # Test UoMs
        test_uoms = [
            ('50 غم', 76),
            ('100 غم', 77),
            ('125 غم', 78),
            ('0.5 كيلو', 79),
        ]
        
        for uom_name, uom_id in test_uoms:
            print(f"\n{'='*60}")
            print(f"Testing UoM: {uom_name} (ID: {uom_id})")
            print(f"{'='*60}")
            
            # Check pricelist item
            pricelist_item = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product'),
                ('product_packaging_id', '=', uom_id),
            ], limit=1)
            
            if pricelist_item:
                print(f"✅ Found pricelist item: ${pricelist_item.fixed_price:.2f}")
            else:
                print(f"❌ No pricelist item found")
            
            # Create line and trigger onchange
            try:
                line = env['sale.order.line'].new({
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'product_uom_id': uom_id,
                })
                
                # Trigger onchange
                line._onchange_product_id()
                
                # Convert to real record
                line_vals = line._convert_to_write(line._cache)
                line_real = env['sale.order.line'].create(line_vals)
                
                print(f"\n📝 Created Sale Order Line:")
                print(f"   UoM: {line_real.product_uom_id.name}")
                print(f"   Price Unit: ${line_real.price_unit:.2f}")
                
                if pricelist_item:
                    expected = pricelist_item.fixed_price
                    actual = line_real.price_unit
                    if abs(actual - expected) < 0.01:
                        print(f"   ✅ Price matches! Expected: ${expected:.2f}, Got: ${actual:.2f}")
                    else:
                        print(f"   ❌ Price mismatch! Expected: ${expected:.2f}, Got: ${actual:.2f}")
                
                # Test _get_display_price directly
                display_price = line_real._get_display_price()
                print(f"   _get_display_price(): ${display_price:.2f}")
                
                # Clean up
                line_real.unlink()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
        
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

