# Convert POS Order #20 to Sale Order
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Get POS Order #20
    pos_order = env['pos.perfume.order'].browse(20)
    
    if not pos_order.exists():
        print("Order not found!")
    else:
        print(f"POS Order: {pos_order.name}")
        print(f"  State: {pos_order.state}")
        print(f"  Lines: {len(pos_order.order_line_ids)}")
        
        if pos_order.sale_order_id:
            print(f"  Already has sale order: {pos_order.sale_order_id.name}")
        else:
            print("\nConverting to sale order...")
            try:
                result = pos_order.action_confirm()
                print(f"SUCCESS! Result: {result}")
                
                pos_order.invalidate_recordset()
                pos_order = env['pos.perfume.order'].browse(20)
                
                if pos_order.sale_order_id:
                    print(f"\nSale Order created: {pos_order.sale_order_id.name} (ID: {pos_order.sale_order_id.id})")
                    
            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()

