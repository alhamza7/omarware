#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Set Default Product Type to 'product' in ir.default"""

print("=" * 80)
print("SET DEFAULT PRODUCT TYPE TO 'PRODUCT'")
print("=" * 80)
print()

# Remove any existing default for product.template type
existing_defaults = env['ir.default'].search([
    ('field_id.name', '=', 'type'),
    ('field_id.model', '=', 'product.template')
])

if existing_defaults:
    print(f"Removing {len(existing_defaults)} existing defaults...")
    existing_defaults.unlink()
    print("  Done")
    print()

# Create new default value
print("Setting default type to 'product' (Goods)...")

# Get the field
field = env['ir.model.fields'].search([
    ('model', '=', 'product.template'),
    ('name', '=', 'type')
], limit=1)

if field:
    # Create default value
    env['ir.default'].create({
        'field_id': field.id,
        'json_value': '"product"',  # JSON encoded string
        'company_id': False,  # Apply to all companies
        'user_id': False,  # Apply to all users
    })
    print("  Default created!")
else:
    print("  Field not found, using alternative method...")
    
    # Alternative: set directly in ir_default table
    cr = env.cr
    cr.execute("""
        INSERT INTO ir_default (field_id, json_value, company_id, user_id)
        SELECT 
            imf.id,
            '"product"'::jsonb,
            NULL,
            NULL
        FROM ir_model_fields imf
        WHERE imf.model = 'product.template'
        AND imf.name = 'type'
        ON CONFLICT DO NOTHING
    """)
    env.cr.commit()
    print("  Default set via SQL!")

env.cr.commit()

print()
print("=" * 80)
print("SUCCESS!")
print("=" * 80)
print("Default product type is now: Goods (product)")
print()
print("When creating new products:")
print("  - Type will be 'Goods' by default")
print("  - No manual selection needed")
print()
print("IMPORTANT: Clear browser cache or use Incognito mode")
print("  Ctrl+Shift+Delete > Clear cached images and files")
print("=" * 80)

exit()



