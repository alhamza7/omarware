print("FINAL CHECK AFTER PROGRAM ENDED")
print("=" * 70)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# Counts
products = env['product.product'].search_count([('default_code', '!=', False)])
extended = env['sap.product.extended'].search_count([])
uoms = env['sap.uom.sync'].search_count([])
prices = env['sap.product.pricelist.sync'].search_count([])
wh_info = env['sap.product.warehouse.info'].search_count([])

print(f"\nDATABASE TOTALS:")
print(f"  Products: {products}")
print(f"  Extended Info: {extended}")
print(f"  UoMs: {uoms}")
print(f"  Prices: {prices}")
print(f"  Warehouse Info: {wh_info}")

# Check wizards
wizards = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizards:
    w = wizards[0]
    print(f"\nLAST WIZARD:")
    print(f"  ID: {w.id}")
    print(f"  State: {w.state}")
    print(f"  Products: {w.total_products}")
    print(f"  UoM Groups: {w.total_uom_groups}")
    print(f"  Pricelists: {w.total_pricelists}")
    print(f"  Prices: {w.total_prices}")
    print(f"  Warehouses: {w.total_warehouses}")
    print(f"  Errors: {w.errors_count}")
    
    if w.start_time and w.end_time:
        duration = (w.end_time - w.start_time).total_seconds()
        print(f"  Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")
    elif w.start_time:
        from datetime import datetime
        duration = (datetime.now() - w.start_time).total_seconds()
        print(f"  Running time: {duration:.0f} seconds ({duration/60:.1f} minutes)")

# Success check
print("\n" + "=" * 70)
print("MIGRATION RESULTS:")
print("=" * 70)

if extended > 2000:
    print(f"SUCCESS! {extended} products with extended info!")
    print(f"Migration imported {extended - products} NEW products from SAP")
elif extended > 100:
    print(f"PARTIAL SUCCESS: {extended} products with extended info")
elif extended > 0:
    print(f"STARTED: {extended} products with extended info")
else:
    print(f"NOT STARTED: No extended info")

print("=" * 70)
env.cr.commit()









