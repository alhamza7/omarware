# Check what product_packaging_id actually contains
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Get pricelist item
    item = env['product.pricelist.item'].browse(141422)
    
    print(f"Pricelist Item #{item.id}:")
    print(f"  Pricelist: {item.pricelist_id.name}")
    print(f"  Product Template: {item.product_tmpl_id.name}")
    print(f"  product_uom_id: {item.product_uom_id.id if item.product_uom_id else None} - {item.product_uom_id.name if item.product_uom_id else 'None'}")
    print(f"  product_packaging_id: {item.product_packaging_id}")
    print(f"  product_packaging_id (raw): {item._fields['product_packaging_id']}")
    print(f"  Fixed Price: ${item.fixed_price}")
    
    # Check if product_packaging_id is actually an integer (UoM ID)
    print(f"\n  Type of product_packaging_id value: {type(item.product_packaging_id)}")
    
    # Try to browse it as UoM
    if item.product_packaging_id:
        try:
            uom = env['uom.uom'].browse(item.product_packaging_id)
            print(f"  As UoM: {uom.name} (exists: {uom.exists()})")
        except:
            print(f"  Cannot browse as UoM")

