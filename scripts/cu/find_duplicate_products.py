#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find and report duplicate products by default_code
"""

import sys
import os

# Add Odoo directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import odoo
from odoo import api, SUPERUSER_ID

def find_duplicates(env):
    """Find products with duplicate default_code"""
    
    print("=" * 80)
    print("🔍 Searching for duplicate products...")
    print("=" * 80)
    print()
    
    # Get all products with default_code
    products = env['product.product'].search([
        ('default_code', '!=', False)
    ], order='default_code, id')
    
    # Group by default_code
    code_groups = {}
    for product in products:
        code = product.default_code.strip() if product.default_code else ''
        if not code:
            continue
        if code not in code_groups:
            code_groups[code] = []
        code_groups[code].append(product)
    
    # Find duplicates
    duplicates = {code: prods for code, prods in code_groups.items() if len(prods) > 1}
    
    if not duplicates:
        print("✅ No duplicate products found!")
        return
    
    print(f"⚠️  Found {len(duplicates)} product codes with duplicates:")
    print()
    
    total_duplicates = 0
    for code, products in sorted(duplicates.items()):
        total_duplicates += len(products) - 1
        print(f"📦 Product Code: {code} ({len(products)} duplicates)")
        for i, product in enumerate(products, 1):
            active_str = "✓ ACTIVE" if product.active else "✗ ARCHIVED"
            print(f"   {i}. ID: {product.id:6d} | {active_str:12s} | {product.name[:50]}")
        print()
    
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   - {len(duplicates)} unique codes with duplicates")
    print(f"   - {total_duplicates} duplicate products (extra copies)")
    print("=" * 80)
    print()
    print("💡 Recommendation:")
    print("   - Archive old/inactive duplicates")
    print("   - Keep the most recent/active version")
    print("   - Re-run Complete Migration with 'Update Existing' = True")
    print()

if __name__ == '__main__':
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', 'odoo.conf'])
    
    db_name = odoo.tools.config['db_name'] or 'nbs_lugalai'
    
    with odoo.api.Environment.manage():
        registry = odoo.registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            find_duplicates(env)


