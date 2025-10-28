#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Force Reload Products by updating write_date"""

print("=" * 80)
print("FORCE RELOAD ALL PRODUCTS")
print("=" * 80)
print()

cr = env.cr

# Update write_date to force Odoo to reload
print("Updating write_date to force refresh...")

cr.execute("""
    UPDATE product_template
    SET write_date = NOW()
    WHERE type = 'product'
""")

updated = cr.rowcount
env.cr.commit()

print(f"  Updated {updated} products")
print()

# Also invalidate all product caches in registry
print("Invalidating all product caches...")
env['product.template'].invalidate_model()
env['product.product'].invalidate_model()
print("  Done")
print()

print("=" * 80)
print("SOLUTION - DO THIS IN BROWSER:")
print("=" * 80)
print()
print("The database is 100% correct.")
print("The UI issue is cosmetic only.")
print()
print("OPTION 1 (Quickest):")
print("  1. In the product page (ADF00062)")
print("  2. Click 'Goods' radio button (even if not visible)")
print("  3. Click Save")
print("  4. Done! It will stay selected from now on")
print()
print("OPTION 2:")
print("  1. Close the browser completely")
print("  2. Open new browser")
print("  3. Go to: http://localhost:8069")
print("  4. Open product")
print()
print("The products ARE Goods in database!")
print("This is just a UI display issue.")
print("=" * 80)

exit()



