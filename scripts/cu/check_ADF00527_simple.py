#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check ADF00527 - Simple"""

cr = env.cr

print("=" * 80)
print("PRODUCT ADF00527 CHECK")
print("=" * 80)
print()

# Check product
cr.execute("""
    SELECT id, type 
    FROM product_product 
    WHERE default_code = 'ADF00527'
""")
result = cr.fetchone()

if result:
    prod_id, prod_type = result
    print(f"Product ID: {prod_id}")
    print(f"Type: {prod_type}")
    print()
    
    # Check quantities
    product = env['product.product'].browse(prod_id)
    print(f"Available Qty: {product.qty_available}")
    print(f"Virtual Qty: {product.virtual_available}")
    print()
    
    # Check stock quants
    cr.execute(f"""
        SELECT 
            sq.quantity,
            sl.complete_name
        FROM stock_quant sq
        JOIN stock_location sl ON sq.location_id = sl.id
        WHERE sq.product_id = {prod_id}
        AND sq.quantity != 0
    """)
    
    quants = cr.fetchall()
    if quants:
        print(f"Stock in {len(quants)} locations:")
        for qty, loc in quants:
            print(f"  {loc}: {qty}")
    else:
        print("NO stock quants")
    
    print()
    
    # Check warehouse info
    cr.execute(f"""
        SELECT 
            sap_warehouse_name,
            last_in_stock,
            last_available
        FROM sap_product_warehouse_info
        WHERE product_code = 'ADF00527'
        LIMIT 10
    """)
    
    warehouses = cr.fetchall()
    if warehouses:
        print(f"SAP Warehouse Info ({len(warehouses)} warehouses):")
        for wh_name, in_stock, available in warehouses:
            if in_stock != 0 or available != 0:
                print(f"  {wh_name}: Stock={in_stock}, Available={available}")
    else:
        print("NO warehouse info from SAP")
else:
    print("Product not found")

print()
print("=" * 80)
print("To view in Odoo:")
print("  1. Click 'Inventory' tab (in the product page)")
print("  2. Or click the On Hand button if visible")
print("=" * 80)

exit()






