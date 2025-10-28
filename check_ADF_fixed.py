#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check ADF00527"""

cr = env.cr

# Check product
cr.execute("""
    SELECT pp.id, pt.type, pt.name
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = 'ADF00527'
""")
result = cr.fetchone()

if result:
    prod_id, prod_type, prod_name = result
    print(f"Product: ADF00527")
    print(f"  Type: {prod_type}")
    print()
    
    # Check quantities via ORM
    product = env['product.product'].browse(prod_id)
    print(f"  Qty Available: {product.qty_available}")
    print()
    
    # Check stock quants
    cr.execute(f"""
        SELECT sl.complete_name, sq.quantity
        FROM stock_quant sq
        JOIN stock_location sl ON sq.location_id = sl.id
        WHERE sq.product_id = {prod_id}
        AND sq.quantity != 0
    """)
    
    quants = cr.fetchall()
    if quants:
        print(f"  Stock Locations:")
        for loc, qty in quants:
            print(f"    {loc}: {qty}")
    else:
        print("  NO stock (quantity = 0)")
    
    print()
    print("INSTRUCTIONS:")
    print("  1. In the product page you have open")
    print("  2. Click 'Inventory' tab (top of the page)")
    print("  3. You will see quantity fields there")
    print("  4. Or click the button with number if visible at top")
else:
    print("Product not found")

exit()




