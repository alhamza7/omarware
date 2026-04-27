# Test creating sale order from POS order
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Get latest POS order
    pos_order = env['pos.perfume.order'].search([], limit=1, order='id desc')
    
    if not pos_order:
        print("No POS orders found!")
    else:
        print(f"\nPOS Order: {pos_order.name} (ID: {pos_order.id})")
        print(f"  State: {pos_order.state}")
        print(f"  Partner: {pos_order.partner_id.name}")
        print(f"  Lines: {len(pos_order.order_line_ids)}")
        
        if pos_order.sale_order_id:
            print(f"  Sale Order: {pos_order.sale_order_id.name} (ID: {pos_order.sale_order_id.id})")
        else:
            print(f"  Sale Order: NOT CREATED YET")
            
            # Try to create sale order
            print(f"\nTrying to create sale order...")
            try:
                result = pos_order.action_confirm()
                print(f"Result: {result}")
                
                # Check if sale order was created
                pos_order.invalidate_recordset()
                pos_order = env['pos.perfume.order'].browse(pos_order.id)
                
                if pos_order.sale_order_id:
                    print(f"\nSUCCESS! Sale Order created:")
                    print(f"  Number: {pos_order.sale_order_id.name}")
                    print(f"  State: {pos_order.sale_order_id.state}")
                    print(f"  Lines: {len(pos_order.sale_order_id.order_line)}")
                    
                    for line in pos_order.sale_order_id.order_line:
                        print(f"    - {line.product_id.display_name}: {line.product_uom_qty} {line.product_uom.name} @ ${line.price_unit}")
                else:
                    print("ERROR: Sale order not created!")
                    
            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()

