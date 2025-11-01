#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Inventory Check - Safe"""

print("=" * 80)
print("FINAL INVENTORY CHECK")
print("=" * 80)
print()

# 1. Stock quants
quants = env['stock.quant'].search([('quantity', '>', 0)])
print(f"Stock Quants (qty > 0): {len(quants)}")
print()

# 2. Warehouses
warehouses = env['stock.warehouse'].search([])
print(f"Warehouses: {len(warehouses)}")
for wh in warehouses:
    quant_count = env['stock.quant'].search_count([
        ('location_id', 'child_of', wh.view_location_id.id),
        ('quantity', '>', 0)
    ])
    print(f"  - {wh.name}: {quant_count} products")
print()

# 3. Sample products with quantities
print("Sample products with stock:")
products_with_stock = env['product.product'].search([
    ('default_code', '!=', False),
    ('qty_available', '>', 0)
], limit=10)

for prod in products_with_stock:
    print(f"  {prod.default_code}: Qty = {prod.qty_available}")
print()

# 4. Check total quantities
cr = env.cr
cr.execute("SELECT SUM(quantity) FROM stock_quant WHERE quantity > 0")
total_qty = cr.fetchone()[0]
print(f"Total quantity in stock: {total_qty}")
print()

print("=" * 80)
print("RESULT:")
print("=" * 80)
if len(quants) > 0:
    print("  SUCCESS! Inventory data is available!")
    print("  You can view it in: Inventory > Operations > On Hand")
else:
    print("  NO STOCK FOUND")
print("=" * 80)

exit()






