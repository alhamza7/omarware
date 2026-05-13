#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check PK00075 Details"""

cr = env.cr

print("=" * 80)
print("PRODUCT: PK00075")
print("=" * 80)
print()

# Get product
product = env['product.product'].search([('default_code', '=', 'PK00075')], limit=1)

print(f"Available Qty in Odoo: {product.qty_available}")
print(f"Virtual Qty: {product.virtual_available}")
print()

# Get stock locations
cr.execute("""
    SELECT 
        sl.complete_name,
        sq.quantity,
        sq.reserved_quantity,
        sq.quantity - sq.reserved_quantity as available
    FROM stock_quant sq
    JOIN stock_location sl ON sq.location_id = sl.id
    WHERE sq.product_id = %s
    AND sq.quantity != 0
    ORDER BY sq.quantity DESC
""", (product.id,))

quants = cr.fetchall()
print(f"Stock in {len(quants)} locations:")
print("-" * 80)
for loc, qty, reserved, available in quants:
    print(f"  {loc}")
    print(f"    Quantity: {qty}")
    print(f"    Reserved: {reserved}")
    print(f"    Available: {available}")
    print()

# Get SAP warehouse info
cr.execute("""
    SELECT 
        sap_warehouse_code,
        sap_warehouse_name,
        last_in_stock,
        last_available
    FROM sap_product_warehouse_info
    WHERE product_code = 'PK00075'
    AND last_in_stock > 0
    ORDER BY last_in_stock DESC
""")

sap_data = cr.fetchall()
if sap_data:
    print("SAP Warehouse Data:")
    print("-" * 80)
    for code, name, stock, available in sap_data:
        print(f"  Warehouse {code}: {name}")
        print(f"    Stock: {stock}, Available: {available}")
        print()

print("=" * 80)
print("HOW TO VIEW IN ODOO:")
print("=" * 80)
print("In the product page you have open now:")
print("  1. Click 'Inventory' tab (next to Sales)")
print("  2. You will see: On Hand Quantity = 998,588")
print("  3. Click the blue button/number to see details")
print("=" * 80)

exit()






