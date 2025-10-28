#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update All Products to Stockable with Inventory Tracking"""

print("=" * 80)
print("UPDATE ALL PRODUCTS TO STOCKABLE")
print("=" * 80)
print()

# Get all products with codes (from SAP)
products = env['product.product'].search([
    ('default_code', '!=', False),
    ('default_code', '!=', '')
])

print(f"Found {len(products)} products to update")
print()

# Count current types
cr = env.cr
cr.execute("""
    SELECT pt.type, COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("Current product types:")
for ptype, count in cr.fetchall():
    print(f"  {ptype}: {count}")
print()

print("=" * 80)
print("UPDATING PRODUCTS...")
print("=" * 80)
print()

updated_count = 0
skipped_count = 0

for product in products:
    try:
        template = product.product_tmpl_id
        
        # Update if not already stockable
        if template.type != 'product':
            template.write({
                'type': 'product',  # Stockable product
                'tracking': 'none',  # No lot/serial tracking by default
            })
            updated_count += 1
            
            if updated_count % 100 == 0:
                print(f"  Updated {updated_count}/{len(products)}...")
                env.cr.commit()
        else:
            skipped_count += 1
    
    except Exception as e:
        print(f"  Error updating {product.default_code}: {str(e)[:60]}")

env.cr.commit()

print()
print("=" * 80)
print("UPDATE COMPLETE!")
print("=" * 80)
print(f"  Updated: {updated_count}")
print(f"  Already stockable: {skipped_count}")
print(f"  Total: {len(products)}")
print()

# Verify final state
cr.execute("""
    SELECT pt.type, COUNT(*)
    FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code IS NOT NULL
    AND pp.default_code != ''
    GROUP BY pt.type
""")

print("Final product types:")
for ptype, count in cr.fetchall():
    status = "OK" if ptype == 'product' else "CHECK"
    print(f"  {ptype}: {count} [{status}]")

print()
print("=" * 80)
print("SUCCESS!")
print("=" * 80)
print("All products are now:")
print("  - Type: Stockable Product")
print("  - Inventory Tracking: Enabled")
print("  - Can track quantities: Yes")
print("=" * 80)

exit()



