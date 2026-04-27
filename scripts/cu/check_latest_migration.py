backend = env['sap.backend'].search([('active', '=', True)], limit=1)

print("=" * 80)
print("LATEST MIGRATION STATUS")
print("=" * 80)

# Check all records
products = env['product.product'].search([('default_code', '!=', False)])
extended = env['sap.product.extended'].search([])
uoms = env['sap.uom.sync'].search([])
prices = env['sap.product.pricelist.sync'].search([])
wh_info = env['sap.product.warehouse.info'].search([])

print(f"\nDatabase Counts:")
print(f"  Products: {len(products)}")
print(f"  Extended Info: {len(extended)}")
print(f"  UoMs: {len(uoms)}")
print(f"  Prices: {len(prices)}")
print(f"  Warehouse Info: {len(wh_info)}")

# Check wizard
wizards = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizards:
    w = wizards[0]
    print(f"\nLatest Wizard (ID: {w.id}):")
    print(f"  State: {w.state}")
    print(f"  Products: {w.total_products}")
    print(f"  UoM Groups: {w.total_uom_groups}")
    print(f"  Errors: {w.errors_count}")

# Sample extended info
if extended:
    print(f"\nExtended Info Range:")
    print(f"  First ID: {min(extended.ids)}")
    print(f"  Last ID: {max(extended.ids)}")
    print(f"  Total: {len(extended)}")
    
    # Sample
    sample = extended[:3]
    print(f"\nFirst 3 Extended Info:")
    for ext in sample:
        print(f"  [{ext.id}] {ext.product_id.default_code}: {ext.product_id.name[:30]}")

# Coverage
if products:
    coverage = (len(extended) / len(products)) * 100
    print(f"\nCoverage: {coverage:.1f}% ({len(extended)}/{len(products)})")
    
    if coverage == 100:
        print("✅ ALL PRODUCTS HAVE EXTENDED INFO!")
    elif coverage > 50:
        print("⚠ MOST PRODUCTS HAVE EXTENDED INFO")
    elif coverage > 0:
        print("⚠ SOME PRODUCTS HAVE EXTENDED INFO")

print("\n" + "=" * 80)
env.cr.commit()











