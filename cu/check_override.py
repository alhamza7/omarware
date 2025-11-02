#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if override is working
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

def check_override():
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Checking Override")
        print("=" * 80)
        
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        # Check method resolution order
        print(f"\n🔍 Method Resolution Order for _compute_price_rule:")
        for cls in type(pricelist).__mro__:
            if hasattr(cls, '_compute_price_rule') and '_compute_price_rule' in cls.__dict__:
                print(f"   - {cls.__module__}.{cls.__name__}")
        
        # Check source code
        import inspect
        source = inspect.getsource(pricelist._compute_price_rule)
        if "Looking for rules" in source:
            print("\n✅ OUR OVERRIDE IS ACTIVE!")
        else:
            print("\n❌ OUR OVERRIDE IS NOT ACTIVE!")
            print(f"\nFirst 200 chars of source:\n{source[:200]}")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        check_override()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

