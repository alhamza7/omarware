#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check for duplicate stock quants"""

import sys
import os

# Setup Odoo environment
sys.path.insert(0, 'L:/Lugal-ai')

import odoo
from odoo import api, SUPERUSER_ID

# Connect to database
db_name = 'lugal'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("=" * 80)
    print("Checking for duplicate stock.quant records")
    print("=" * 80)
    
    # Find products with duplicate quants in same location
    query = """
        SELECT 
            product_id,
            location_id,
            COUNT(*) as count,
            SUM(quantity) as total_qty,
            STRING_AGG(id::text, ', ') as quant_ids
        FROM stock_quant
        WHERE location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
        GROUP BY product_id, location_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 50
    """
    
    cr.execute(query)
    duplicates = cr.dictfetchall()
    
    if not duplicates:
        print("\n✓ No duplicate quants found!")
    else:
        print(f"\n✗ Found {len(duplicates)} products with duplicate quants:\n")
        
        for dup in duplicates[:10]:  # Show first 10
            product = env['product.product'].browse(dup['product_id'])
            location = env['stock.location'].browse(dup['location_id'])
            
            print(f"Product: {product.name} (ID: {product.id})")
            print(f"  Location: {location.complete_name}")
            print(f"  Duplicate count: {dup['count']}")
            print(f"  Total quantity: {dup['total_qty']}")
            print(f"  Quant IDs: {dup['quant_ids']}")
            print()
    
    print("=" * 80)
    print("Checking total stock.quant records")
    print("=" * 80)
    
    cr.execute("SELECT COUNT(*) FROM stock_quant")
    total = cr.fetchone()[0]
    print(f"Total stock.quant records: {total}")
    
    cr.execute("SELECT COUNT(DISTINCT(product_id, location_id)) FROM stock_quant")
    unique = cr.fetchone()[0]
    print(f"Unique (product, location) combinations: {unique}")
    print(f"Difference (duplicates): {total - unique}")



