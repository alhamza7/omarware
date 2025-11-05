# Check packaging model
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Get packaging ID 87
    packaging = env['product.packaging'].browse(87)
    
    print(f"Packaging ID 87:")
    print(f"  Name: {packaging.name}")
    print(f"  Product: {packaging.product_id.display_name if packaging.product_id else 'N/A'}")
    print(f"  Qty: {packaging.qty}")
    
    # Check if it has product_uom_id
    if hasattr(packaging, 'product_uom_id'):
        print(f"  UoM: {packaging.product_uom_id.name if packaging.product_uom_id else 'NOT SET'}")
    else:
        print("  No product_uom_id field!")
    
    # List all fields
    print(f"\n  All fields containing 'uom':")
    for field in packaging._fields:
        if 'uom' in field.lower():
            print(f"    - {field}")
