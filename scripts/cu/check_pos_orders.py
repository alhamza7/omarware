# Check if orders were created
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Check last 10 POS Perfume orders
    orders = env['pos.perfume.order'].search([], limit=10, order='id desc')
    
    print(f"\nLast {len(orders)} POS Perfume Orders:")
    print("="*80)
    
    for order in orders:
        print(f"\nOrder #{order.id}: {order.name}")
        print(f"  Partner: {order.partner_id.name if order.partner_id else 'N/A'}")
        print(f"  State: {order.state}")
        print(f"  Date: {order.date}")
        print(f"  Lines: {len(order.order_line_ids)}")
        
        for line in order.order_line_ids:
            print(f"    - {line.product_id.display_name}")
            print(f"      UoM: {line.product_uom_id.name if line.product_uom_id else 'N/A'}")
            print(f"      Warehouse: {line.warehouse_id.name if line.warehouse_id else 'N/A'}")
            print(f"      Qty: {line.quantity}, Price: ${line.unit_price}")

