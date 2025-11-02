#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test - call _get_display_price() directly
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

def test_direct_pricing():
    """Test _get_display_price() directly"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing _get_display_price() DIRECTLY")
        print("=" * 80)
        
        # Get product
        product = env['product.product'].search([('default_code', '=', 'R00205')], limit=1)
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        partner = env['res.partner'].search([], limit=1)
        
        # Create sale order
        order = env['sale.order'].create({
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
        })
        
        # Create line with UoM 76 (50 غم)
        uom = env['uom.uom'].browse(76)
        
        print(f"\nProduct: {product.default_code}")
        print(f"UoM: {uom.name} (ID: {uom.id})")
        print(f"Pricelist: {pricelist.name}")
        
        # Create line
        line = env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom_id': uom.id,
        })
        
        print(f"\nLine created: {line.id}")
        print(f"Line product_uom_id: {line.product_uom_id.name}")
        print(f"Line order_id.pricelist_id: {line.order_id.pricelist_id.name}")
        
        # Check _get_display_price method resolution
        print(f"\n🔍 Checking method resolution order:")
        for cls in type(line).__mro__:
            if hasattr(cls, '_get_display_price') and '_get_display_price' in cls.__dict__:
                print(f"   - {cls.__module__}.{cls.__name__}")
        
        # Call _get_display_price directly
        print(f"\n📞 Calling _get_display_price() directly...")
        try:
            price = line._get_display_price()
            print(f"Result: ${price:.2f}")
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Check price_unit
        print(f"\nLine price_unit: ${line.price_unit:.2f}")
        
        # Clean up
        order.unlink()
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        test_direct_pricing()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

