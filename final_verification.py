backend = env['sap.backend'].search([('active','=',True)],limit=1)
products = env['product.product'].search([('default_code','!=',False)])
extended = env['sap.product.extended'].search([])
prices = env['sap.product.pricelist.sync'].search([])
wh_info = env['sap.product.warehouse.info'].search([])
uoms = env['sap.uom.sync'].search([('sync_status','=','success')])

print("FINAL RESULTS:")
print(f"Products: {len(products)}")
print(f"Extended Info: {len(extended)}")
print(f"UoMs: {len(uoms)}")
print(f"Prices: {len(prices)}")
print(f"Warehouse: {len(wh_info)}")

if extended:
    print(f"\nExtended Info IDs: {extended.ids[:10]}")
    ext = extended[0]
    print(f"Sample: {ext.product_id.default_code}")
    print(f"  Foreign: {ext.foreign_name or 'N/A'}")
    print(f"  Group: {ext.items_group_name or 'N/A'}")

env.cr.commit()









