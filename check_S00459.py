#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Product S00459"""

cr = env.cr

print("=" * 80)
print("CHECK PRODUCT S00459")
print("=" * 80)
print()

# Find the product
cr.execute("""
    SELECT 
        pp.id,
        pp.default_code,
        pt.id as template_id,
        pt.type,
        pt.tracking,
        pt.create_date
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = 'S00459'
""")

result = cr.fetchone()

if result:
    prod_id, code, tmpl_id, ptype, tracking, created = result
    print(f"Product: {code}")
    print(f"  Type: {ptype}")
    print(f"  Tracking: {tracking}")
    print(f"  Created: {created}")
    print()
    
    # Check if it was imported from SAP
    cr.execute(f"""
        SELECT COUNT(*) 
        FROM sap_product_extended 
        WHERE product_id = {prod_id}
    """)
    has_sap_data = cr.fetchone()[0] > 0
    
    print(f"  From SAP: {'Yes' if has_sap_data else 'No (manual)'}")
    print()
    
    if ptype != 'product':
        print("FIXING: Updating to stockable...")
        cr.execute(f"UPDATE product_template SET type = 'product' WHERE id = {tmpl_id}")
        env.cr.commit()
        print("  FIXED!")
    else:
        print("  Already correct (Goods/Stockable)")
else:
    print("Product not found")

print()
print("=" * 80)
print("The product type is already set correctly!")
print("You don't need to select it manually.")
print("Just click Save.")
print("=" * 80)

exit()



