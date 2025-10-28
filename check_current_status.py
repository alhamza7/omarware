print("CURRENT STATUS:")
print("=" * 60)

# Check wizards
wizards = env['sap.product.complete.migration'].search([], order='id desc')
print(f"Total Wizards: {len(wizards)}")

if wizards:
    for w in wizards[:3]:
        print(f"\nWizard ID: {w.id}")
        print(f"  State: {w.state}")
        print(f"  Start: {w.start_time}")
        print(f"  End: {w.end_time}")
        print(f"  Products: {w.total_products}")
        print(f"  Errors: {w.errors_count}")

# Check database
products = env['product.product'].search([('default_code', '!=', False)])
extended = env['sap.product.extended'].search([])
uoms = env['sap.uom.sync'].search([])

print(f"\nDatabase:")
print(f"  Products: {len(products)}")
print(f"  Extended: {len(extended)}")
print(f"  UoMs: {len(uoms)}")

print("=" * 60)
env.cr.commit()









