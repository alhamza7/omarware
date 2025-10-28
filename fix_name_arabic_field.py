#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix name_arabic field issue"""

print("=" * 80)
print("Fixing name_arabic field")
print("=" * 80)

# Check if the field exists
print("\n1. Checking field definition:")
field_info = env['ir.model.fields'].search([
    ('model', '=', 'product.template'),
    ('name', '=', 'name_arabic')
], limit=1)

if field_info:
    print(f"   Field found: {field_info.name}")
    print(f"   Type: {field_info.ttype}")
    print(f"   Translate: {field_info.translate}")
    
    # Update field to remove translation if needed
    if field_info.translate:
        print("\n2. Removing translation flag...")
        field_info.write({'translate': False})
        env.cr.commit()
        print("   DONE")

# Test reading products
print("\n3. Testing product read:")
try:
    products = env['product.product'].search([], limit=5)
    for p in products:
        print(f"   - {p.default_code or 'N/A'}: {p.name}")
        if hasattr(p, 'name_arabic'):
            print(f"     Arabic: {p.name_arabic or 'N/A'}")
    print("\n   SUCCESS - Products can be read!")
except Exception as e:
    print(f"\n   ERROR: {str(e)}")

env.cr.commit()




