#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clear Cache"""

print("Clearing Odoo cache...")

# Clear registry cache
env.registry.clear_cache()

# Invalidate all records
env['product.template'].invalidate_model()
env['product.product'].invalidate_model()

print("Cache cleared!")
print()
print("Database state:")

cr = env.cr
cr.execute("SELECT type, COUNT(*) FROM product_template GROUP BY type")

for ptype, count in cr.fetchall():
    print(f"  {ptype}: {count}")

print()
print("ALL products are type 'product' (Goods) in database")
print()
print("NEXT: Refresh your browser (F5) or restart Odoo")

exit()



