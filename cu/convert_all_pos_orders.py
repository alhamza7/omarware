# Convert all pending POS orders to Sale Orders
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    # Get all POS orders without sale_order_id
    pos_orders = env['pos.perfume.order'].search([
        ('state', '=', 'draft'),
        ('sale_order_id', '=', False)
    ], order='id asc')
    
    print(f"\nFound {len(pos_orders)} POS orders to convert")
    print("="*80)
    
    success_count = 0
    error_count = 0
    
    for order in pos_orders:
        try:
            print(f"\nConverting {order.name} (ID: {order.id})...")
            result = order.action_confirm()
            
            order.invalidate_recordset()
            order = env['pos.perfume.order'].browse(order.id)
            
            if order.sale_order_id:
                print(f"  ✅ SUCCESS: {order.sale_order_id.name}")
                success_count += 1
            else:
                print(f"  ❌ FAILED: No sale order created")
                error_count += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            error_count += 1
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(pos_orders)}")
    print(f"{'='*80}\n")
    
    print("Now check Sales → Quotations for the new orders!")

