products = env['product.product'].search([('default_code', '!=', False)])
extended = env['sap.product.extended'].search([])
prices = env['sap.product.pricelist.sync'].search([])
wh = env['sap.product.warehouse.info'].search([])

print(f"Products: {len(products)}")
print(f"Extended: {len(extended)}")
print(f"Prices: {len(prices)}")
print(f"Warehouse: {len(wh)}")

wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizard:
    print(f"\nWizard State: {wizard.state}")
    print(f"Total Products: {wizard.total_products}")
    print(f"Total Prices: {wizard.total_prices}")
    print(f"Total Warehouses: {wizard.total_warehouses}")

if len(extended) > 0:
    coverage = (len(extended) / max(len(products), len(extended))) * 100
    print(f"\nCoverage: {coverage:.0f}%")

env.cr.commit()









