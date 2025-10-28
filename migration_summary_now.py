print("=" * 60)
print("MIGRATION SUMMARY - CURRENT STATUS")
print("=" * 60)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# Database counts
products = env['product.product'].search_count([('default_code', '!=', False)])
extended = env['sap.product.extended'].search_count([('backend_id', '=', backend.id)])
uoms = env['sap.uom.sync'].search_count([('backend_id', '=', backend.id)])
prices = env['sap.product.pricelist.sync'].search_count([('backend_id', '=', backend.id)])
wh_info = env['sap.product.warehouse.info'].search_count([('backend_id', '=', backend.id)])

print(f"\nDatabase:")
print(f"  Products (basic): {products}")
print(f"  Extended Info: {extended}")
print(f"  UoMs: {uoms}")
print(f"  Prices: {prices}")
print(f"  Warehouse: {wh_info}")

# Coverage
if products > 0:
    coverage = (extended / products) * 100 if extended <= products else (products / extended) * 100
    print(f"\nCoverage: {extended}/{products}")
    if extended > products:
        print(f"  Migration imported {extended - products} NEW products from SAP!")

# Wizard status
wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
if wizard:
    print(f"\nLatest Wizard:")
    print(f"  ID: {wizard.id}")
    print(f"  State: {wizard.state}")
    print(f"  Products: {wizard.total_products}")
    print(f"  UoM Groups: {wizard.total_uom_groups}")
    
    if wizard.state == 'running':
        print(f"\n  STATUS: STILL WORKING!")
        print(f"  Be patient - processing thousands of products")
    elif wizard.state == 'done':
        print(f"\n  STATUS: COMPLETE!")
    else:
        print(f"\n  STATUS: {wizard.state}")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)

if wizard and wizard.state == 'running':
    print("Migration is WORKING - just takes time.")
    print("Options:")
    print("  1. Wait (recommended)")
    print("  2. Watch progress with: watch_migration.py")
    print("  3. Check Extended Info count every 5 min")
elif extended > 0:
    print("Migration completed successfully!")
    print(f"  {extended} products with extended info")
else:
    print("Ready to run migration")

print("=" * 60)
env.cr.commit()









