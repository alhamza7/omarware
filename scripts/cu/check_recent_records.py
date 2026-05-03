#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check pricelist records created today
"""

import sys
import os
import io
from datetime import datetime, timedelta

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add Odoo to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

def check_recent_records():
    """Check recently created pricelist records"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Checking Recent Pricelist Records")
        print("=" * 80)
        
        # Check records created today
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        print(f"\nSearching for records created after: {today_start}")
        
        # 1. Check SAP Product Pricelist Sync records
        print(f"\n{'='*60}")
        print("1. SAP Product Pricelist Sync Records")
        print(f"{'='*60}")
        
        sync_records = env['sap.product.pricelist.sync'].search([
            ('create_date', '>=', today_start)
        ])
        
        print(f"Total created today: {len(sync_records)}")
        
        if sync_records:
            # Group by product
            products = {}
            for rec in sync_records:
                prod_code = rec.product_id.default_code
                if prod_code not in products:
                    products[prod_code] = []
                products[prod_code].append(rec)
            
            print(f"Products with prices: {len(products)}")
            
            # Show first 5 products
            for idx, (prod_code, recs) in enumerate(list(products.items())[:5], 1):
                print(f"\n  {idx}. {prod_code}: {len(recs)} prices")
                for rec in recs[:3]:
                    uom_info = f"UoM: {rec.uom_id.name}" if rec.uom_id else "Base"
                    print(f"     - ${rec.price:.2f} | {uom_info}")
        
        # 2. Check Product Pricelist Items
        print(f"\n{'='*60}")
        print("2. Product Pricelist Items (SAP Price List 1)")
        print(f"{'='*60}")
        
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if pricelist:
            items = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('create_date', '>=', today_start)
            ])
            
            print(f"Total items created today: {len(items)}")
            
            if items:
                # Count by applied_on
                template_count = len(items.filtered(lambda i: i.applied_on == '1_product'))
                variant_count = len(items.filtered(lambda i: i.applied_on == '0_product_variant'))
                
                print(f"\nBreakdown:")
                print(f"  - Template-level: {template_count}")
                print(f"  - Variant-level: {variant_count}")
                
                # Count with UoM
                with_uom = len(items.filtered(lambda i: i.product_packaging_id))
                without_uom = len(items) - with_uom
                
                print(f"\n  - With UoM: {with_uom}")
                print(f"  - Base (no UoM): {without_uom}")
                
                # Show sample
                print(f"\nSample items (first 5):")
                for idx, item in enumerate(items[:5], 1):
                    prod_name = item.product_tmpl_id.name if item.product_tmpl_id else item.product_id.name
                    uom_info = f"{item.product_packaging_id.name}" if item.product_packaging_id else "Base"
                    applied = "Template" if item.applied_on == '1_product' else "Variant"
                    print(f"  {idx}. {prod_name[:30]:30} | ${item.fixed_price:>6.2f} | {applied:8} | {uom_info}")
        else:
            print("ERROR: SAP Price List 1 not found!")
        
        # 3. Check last hour records
        print(f"\n{'='*60}")
        print("3. Records Created in Last Hour")
        print(f"{'='*60}")
        
        last_hour = datetime.now() - timedelta(hours=1)
        
        recent_sync = env['sap.product.pricelist.sync'].search([
            ('create_date', '>=', last_hour)
        ])
        
        recent_items = env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('create_date', '>=', last_hour)
        ]) if pricelist else []
        
        print(f"Sync records (last hour): {len(recent_sync)}")
        print(f"Pricelist items (last hour): {len(recent_items)}")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        check_recent_records()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

