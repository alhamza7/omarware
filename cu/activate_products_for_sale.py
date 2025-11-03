#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Activate products for sale and point of sale
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

def activate_products():
    """Activate products for sale and POS"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Activating Products for Sale and Point of Sale")
        print("=" * 80)
        
        # Find all products that are NOT active for sale or POS
        all_products = env['product.product'].search([
            ('active', '=', True),  # Only active products
        ])
        
        print(f"\nTotal products found: {len(all_products)}")
        
        # Show breakdown by type
        stockable = all_products.filtered(lambda p: p.type == 'product')
        consumable = all_products.filtered(lambda p: p.type == 'consu')
        service = all_products.filtered(lambda p: p.type == 'service')
        
        print(f"\nBreakdown by type:")
        print(f"  - Stockable (product): {len(stockable)}")
        print(f"  - Consumable (consu): {len(consumable)}")
        print(f"  - Service: {len(service)}")
        
        # Check current status
        not_for_sale = all_products.filtered(lambda p: not p.sale_ok)
        not_for_pos = all_products.filtered(lambda p: not p.available_in_pos)
        
        print(f"\nCurrent Status:")
        print(f"  - Not available for Sale: {len(not_for_sale)}")
        print(f"  - Not available for POS: {len(not_for_pos)}")
        
        if not not_for_sale and not not_for_pos:
            print("\n✓ All products are already activated!")
            return
        
        # Activate for sale
        if not_for_sale:
            print(f"\nActivating {len(not_for_sale)} products for Sale...")
            try:
                not_for_sale.write({'sale_ok': True})
                print(f"  ✓ Activated {len(not_for_sale)} products for Sale")
            except Exception as e:
                print(f"  ✗ Error activating for sale: {str(e)}")
        
        # Activate for POS
        if not_for_pos:
            print(f"\nActivating {len(not_for_pos)} products for Point of Sale...")
            try:
                not_for_pos.write({'available_in_pos': True})
                print(f"  ✓ Activated {len(not_for_pos)} products for POS")
            except Exception as e:
                print(f"  ✗ Error activating for POS: {str(e)}")
        
        # Commit changes
        cr.commit()
        
        # Verify
        print(f"\n{'='*60}")
        print("Verification")
        print(f"{'='*60}")
        
        all_products.invalidate_recordset()
        
        still_not_for_sale = all_products.filtered(lambda p: not p.sale_ok)
        still_not_for_pos = all_products.filtered(lambda p: not p.available_in_pos)
        
        print(f"\nAfter activation:")
        print(f"  - Available for Sale: {len(all_products) - len(still_not_for_sale)}")
        print(f"  - Available for POS: {len(all_products) - len(still_not_for_pos)}")
        
        if still_not_for_sale or still_not_for_pos:
            print(f"\n⚠ Warning:")
            if still_not_for_sale:
                print(f"  - {len(still_not_for_sale)} products still not for sale")
            if still_not_for_pos:
                print(f"  - {len(still_not_for_pos)} products still not for POS")
        else:
            print(f"\n✓ SUCCESS! All products are now activated!")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        activate_products()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

