#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test reading products"""

print("Testing product read...")

try:
    # Test reading products
    products = env['product.product'].search([], limit=10)
    
    print(f"\nFound {len(products)} products")
    
    for p in products:
        print(f"  - {p.id}: {p.default_code or 'N/A'} - {p.name}")
        print(f"    Price: {p.list_price}")
        print(f"    UoM: {p.uom_id.name}")
        print(f"    Sale OK: {p.sale_ok}")
        print(f"    POS OK: {p.available_in_pos}")
    
    print("\nSUCCESS - Products can be read without errors!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

env.cr.commit()




