#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create Server Action for Mass Update"""

print("=" * 80)
print("CREATE MASS UPDATE ACTION")
print("=" * 80)
print()

# Create a server action
action = env['ir.actions.server'].create({
    'name': 'Set All Products to Goods',
    'model_id': env['ir.model'].search([('model', '=', 'product.template')], limit=1).id,
    'binding_model_id': env['ir.model'].search([('model', '=', 'product.template')], limit=1).id,
    'binding_view_types': 'list',
    'state': 'code',
    'code': """
for record in records:
    if record.type != 'product':
        record.write({'type': 'product', 'tracking': 'none'})
    """
})

env.cr.commit()

print(f"Action created: {action.name} (ID: {action.id})")
print()
print("=" * 80)
print("HOW TO USE:")
print("=" * 80)
print("1. Go to: Inventory > Products > Products")
print("2. Select ALL products (checkbox at top)")
print("3. Click: Action > Set All Products to Goods")
print("4. All products will be updated!")
print()
print("This action is now available in the Products list view")
print("=" * 80)

exit()



