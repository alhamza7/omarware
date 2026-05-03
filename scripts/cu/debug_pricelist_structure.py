# -*- coding: utf-8 -*-
"""
Debug script to understand how pricelist items are structured
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

def debug_pricelist():
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    db_name = 'lugal'
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # Get a sample product
        product = env['product.product'].search([('default_code', '=', 'R00461')], limit=1)
        
        if not product:
            print("Product R00461 not found, using any product...")
            product = env['product.product'].search([('sale_ok', '=', True)], limit=1)
        
        print(f"\n{'='*70}")
        print(f"Product: {product.display_name}")
        print(f"Base UoM: {product.uom_id.name} (ID: {product.uom_id.id})")
        print(f"List Price: {product.list_price}")
        print(f"{'='*70}\n")
        
        # Get pricelists
        pricelists = env['product.pricelist'].search([], limit=5)
        
        for pricelist in pricelists:
            print(f"\n--- Pricelist: {pricelist.name} (ID: {pricelist.id}) ---")
            
            # Get pricelist items for this product
            items = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ])
            
            print(f"Found {len(items)} pricelist items:")
            
            for item in items:
                print(f"\n  Item ID: {item.id}")
                print(f"    Product: {item.product_id.display_name if item.product_id else 'ALL VARIANTS'}")
                print(f"    UoM: {item.product_uom_id.name if item.product_uom_id else 'NOT SET'} (ID: {item.product_uom_id.id if item.product_uom_id else None})")
                print(f"    Packaging: {item.product_packaging_id.name if item.product_packaging_id else 'NOT SET'}")
                if item.product_packaging_id:
                    print(f"      Packaging UoM: {item.product_packaging_id.product_uom_id.name if item.product_packaging_id.product_uom_id else 'NOT SET'}")
                print(f"    Compute Price: {item.compute_price}")
                print(f"    Fixed Price: {item.fixed_price}")
                print(f"    Min Quantity: {item.min_quantity}")
                
                # Try to get price
                try:
                    uom = item.product_uom_id or product.uom_id
                    price = pricelist._get_product_price(product, 1.0, uom=uom)
                    print(f"    Computed Price: {price}")
                except Exception as e:
                    print(f"    ERROR getting price: {e}")
        
        # Check warehouses
        print(f"\n\n{'='*70}")
        print("Warehouses with stock:")
        print(f"{'='*70}\n")
        
        query = """
            SELECT 
                sw.id,
                sw.name,
                sw.code,
                SUM(sq.quantity) as total_qty,
                SUM(sq.reserved_quantity) as reserved_qty,
                SUM(sq.quantity - sq.reserved_quantity) as available_qty
            FROM stock_warehouse sw
            LEFT JOIN stock_location sl ON sl.warehouse_id = sw.id AND sl.usage = 'internal'
            LEFT JOIN stock_quant sq ON sq.location_id = sl.id AND sq.product_id = %s
            WHERE sw.active = true
            GROUP BY sw.id, sw.name, sw.code
            ORDER BY sw.name
        """
        
        env.cr.execute(query, (product.id,))
        results = env.cr.dictfetchall()
        
        for row in results:
            print(f"Warehouse: {row['name']} ({row['code']})")
            print(f"  Total: {row['total_qty'] or 0}")
            print(f"  Reserved: {row['reserved_qty'] or 0}")
            print(f"  Available: {row['available_qty'] or 0}")
            print()

if __name__ == '__main__':
    debug_pricelist()

