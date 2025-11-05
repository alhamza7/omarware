# Check sale orders
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Check sale orders with origin from POS
    sale_orders = env['sale.order'].search([
        ('origin', 'like', 'POS/25/%')
    ], order='id desc', limit=10)
    
    print(f"\nSale Orders created from POS:")
    print("="*80)
    
    for so in sale_orders:
        print(f"\n{so.name} (ID: {so.id})")
        print(f"  Origin: {so.origin}")
        print(f"  Partner: {so.partner_id.name}")
        print(f"  State: {so.state}")
        print(f"  Lines: {len(so.order_line)}")
        for line in so.order_line:
            print(f"    - {line.product_id.display_name}: {line.product_uom_qty} {line.product_uom_id.name} @ ${line.price_unit}")
            if hasattr(line, 'product_warehouse_id') and line.product_warehouse_id:
                print(f"      Warehouse: {line.product_warehouse_id.name}")

