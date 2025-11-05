# Check product with multiple prices
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Search for LOWCOST M
    products = env['product.product'].search([
        '|', ('name', 'ilike', 'لاكوست  M'),
        ('name', 'ilike', 'LOWCOST M')
    ], limit=5)
    
    pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
    
    print(f"Pricelist: {pricelist.name} (ID: {pricelist.id})")
    print("="*80)
    
    for product in products:
        print(f"\nProduct: {product.display_name}")
        print(f"  Base UoM: {product.uom_id.name} (ID: {product.uom_id.id})")
        
        # Get pricelist items
        items = env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ])
        
        print(f"  Pricelist items: {len(items)}")
        for item in items:
            uom = item.product_uom_id or product.uom_id
            packaging = item.product_packaging_id
            print(f"    - UoM: {uom.name} (ID: {uom.id}), Packaging: {packaging.name if packaging else 'None'} (ID: {packaging.id if packaging else None}), Price: ${item.fixed_price}")
        
        # Test price with base UoM
        try:
            price = pricelist._get_product_price(product, 1.0, uom=product.uom_id)
            print(f"  Price for BASE UoM ({product.uom_id.name}): ${price}")
        except Exception as e:
            print(f"  ERROR: {e}")

