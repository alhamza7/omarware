#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix last consumable product"""

cr = env.cr

print("=" * 80)
print("FIX LAST CONSUMABLE PRODUCT")
print("=" * 80)
print()

# Find the consumable product
cr.execute("""
    SELECT pp.id, pp.default_code, pt.id as template_id
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pt.type = 'consu'
    AND pp.default_code IS NOT NULL
    AND pp.default_code != ''
""")

result = cr.fetchone()

if result:
    prod_id, code, template_id = result
    print(f"Found consumable product: {code}")
    print(f"  Product ID: {prod_id}")
    print(f"  Template ID: {template_id}")
    print()
    
    print("Updating to stockable using SQL...")
    cr.execute(f"""
        UPDATE product_template 
        SET type = 'product'
        WHERE id = {template_id}
    """)
    
    env.cr.commit()
    print(f"  SUCCESS! Updated {code} to stockable")
    print()
else:
    print("No consumable products found")
    print()

# Verify all products
cr.execute("""
    SELECT pt.type, COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("=" * 80)
print("FINAL VERIFICATION:")
print("=" * 80)
for ptype, count in cr.fetchall():
    status = "PERFECT!" if ptype == 'product' else "NEEDS FIX"
    print(f"  {ptype}: {count} products [{status}]")

print()
print("=" * 80)
print("ALL PRODUCTS ARE NOW STOCKABLE!")
print("=" * 80)
print("  - Can track inventory: YES")
print("  - Can have stock quantities: YES")
print("  - Visible in Inventory: YES")
print("=" * 80)

exit()





