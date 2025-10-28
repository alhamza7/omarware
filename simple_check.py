backend = env['sap.backend'].search([('active', '=', True)], limit=1)
products = env['product.product'].search([('default_code', '!=', False)])
extended = env['sap.product.extended'].search([])
uoms = env['sap.uom.sync'].search([])
prices = env['sap.product.pricelist.sync'].search([])
wh_info = env['sap.product.warehouse.info'].search([])

print("MIGRATION STATUS:")
print(f"  UoMs: {len(uoms)}")
print(f"  Products: {len(products)}")
print(f"  Extended: {len(extended)}")
print(f"  Prices: {len(prices)}")
print(f"  Warehouse: {len(wh_info)}")

if len(extended) > 0:
    print("\nEXTENDED INFO EXISTS!")
    print(f"Sample: Product {extended[0].product_id.default_code}")
else:
    print("\nNO EXTENDED INFO - Need to run complete migration")

env.cr.commit()









