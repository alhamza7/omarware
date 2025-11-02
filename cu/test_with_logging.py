#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test _compute_price_rule with detailed logging
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
import logging

# Set logging
logging.basicConfig(level=logging.INFO)

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

def test_with_logging():
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing _compute_price_rule WITH DETAILED LOGGING")
        print("=" * 80)
        
        product = env['product.product'].search([('default_code', '=', 'R00205')], limit=1)
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        uom = env['uom.uom'].browse(76)  # 50 غم
        
        print(f"\nProduct: {product.display_name}")
        print(f"UoM: {uom.name} (ID: {uom.id})")
        print(f"Pricelist: {pricelist.name}\n")
        
        # Enable detailed logging
        logger = logging.getLogger('odoo.addons.uom_in_pricelist')
        logger.setLevel(logging.INFO)
        
        # Call _compute_price_rule
        result = pricelist._compute_price_rule(
            products=product,
            quantity=1.0,
            uom=uom,
            date=False,
            compute_price=True
        )
        
        print(f"\n{'='*60}")
        print("RESULT:")
        print(f"{'='*60}")
        if product.id in result:
            price, rule_id = result[product.id]
            print(f"Price: ${price:.2f}")
            print(f"Rule ID: {rule_id}")
        else:
            print("NO RESULT!")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        test_with_logging()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

