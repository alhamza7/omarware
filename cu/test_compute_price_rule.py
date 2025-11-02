#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test _compute_price_rule directly
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

def test_compute_price_rule():
    """Test _compute_price_rule directly"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing _compute_price_rule DIRECTLY")
        print("=" * 80)
        
        # Get product and pricelist
        product = env['product.product'].search([('default_code', '=', 'R00205')], limit=1)
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        # Test different UoMs
        test_cases = [
            (76, '50 غم'),
            (77, '100 غم'),
            (78, '125 غم'),
            (79, '0.5 كيلو'),
        ]
        
        for uom_id, uom_name in test_cases:
            uom = env['uom.uom'].browse(uom_id)
            
            print(f"\n{'='*60}")
            print(f"Testing UoM: {uom_name} (ID: {uom_id})")
            print(f"{'='*60}")
            
            # Call _compute_price_rule directly
            try:
                result = pricelist._compute_price_rule(
                    products=product,
                    quantity=1.0,
                    uom=uom,
                    date=False,
                    compute_price=True
                )
                
                if product.id in result:
                    price, rule_id = result[product.id]
                    print(f"✅ Result: Price=${price:.2f}, Rule ID={rule_id}")
                    
                    if rule_id:
                        rule = env['product.pricelist.item'].browse(rule_id)
                        print(f"   Rule details:")
                        print(f"   - Fixed Price: ${rule.fixed_price:.2f}")
                        print(f"   - product_packaging_id: {rule.product_packaging_id.id if rule.product_packaging_id else 'None'}")
                else:
                    print(f"❌ No result for product {product.id}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        test_compute_price_rule()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

