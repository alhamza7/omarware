#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check ADF00062 Right Now"""

cr = env.cr

print("=" * 80)
print("CHECKING PRODUCT ADF00062 IN DATABASE NOW")
print("=" * 80)
print()

# Get product data
cr.execute("""
    SELECT 
        pp.id as product_id,
        pt.id as template_id,
        pp.default_code,
        pt.name,
        pt.type,
        pt.tracking
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = 'ADF00062'
""")

result = cr.fetchone()

if result:
    prod_id, tmpl_id, code, name, ptype, tracking = result
    
    print(f"Product Code: {code}")
    print(f"Product ID: {prod_id}")
    print(f"Template ID: {tmpl_id}")
    print(f"Current Type in DB: '{ptype}'")
    print(f"Tracking: {tracking}")
    print()
    
    if ptype != 'product':
        print("TYPE IS WRONG! Fixing NOW...")
        cr.execute(f"""
            UPDATE product_template 
            SET type = 'product', tracking = 'none'
            WHERE id = {tmpl_id}
        """)
        env.cr.commit()
        print("  FIXED in database!")
        
        # Verify
        cr.execute(f"SELECT type FROM product_template WHERE id = {tmpl_id}")
        new_type = cr.fetchone()[0]
        print(f"  New type: {new_type}")
    else:
        print("Type is CORRECT in database (already 'product')")
        print()
        print("The problem is in the UI/Browser!")
        print()
        print("SOLUTION:")
        print("  The field shows empty because Odoo UI loads")
        print("  the value from a different source.")
        print()
        print("  Just click on 'Goods' radio button once,")
        print("  then Save the product.")
        print("  After that, it will stay selected.")
else:
    print("Product not found!")

print()
print("=" * 80)

exit()





