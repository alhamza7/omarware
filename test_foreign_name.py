#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test ForeignName field"""

print("="*80)
print("ForeignName Field Test")
print("="*80)

# Check if foreign_name exists in extended model
ext_model = env['sap.product.extended']
print("\n1. Check foreign_name field in sap.product.extended:")
if 'foreign_name' in ext_model._fields:
    field = ext_model._fields['foreign_name']
    print(f"   EXISTS: {field.type} - {field.string}")
else:
    print("   NOT FOUND")

# Check existing extended records
extended = env['sap.product.extended'].search([], limit=5)
print(f"\n2. Sample Extended Info records: {len(extended)}")
for ext in extended:
    print(f"   Product: {ext.product_id.default_code if ext.product_id else 'N/A'}")
    if hasattr(ext, 'foreign_name'):
        print(f"   Foreign Name: {ext.foreign_name or 'Empty'}")

# Check how it will be used in migration
print("\n3. In Migration code:")
print("   - ForeignName from SAP -> foreign_name field")
print("   - If ItemName is empty -> use ForeignName as product name")
print("   - foreign_name stored in sap.product.extended")

print("\n" + "="*80)
print("ForeignName will be:")
print("  1. Stored in sap.product.extended.foreign_name")
print("  2. Used as product.name if ItemName is empty")
print("  3. Visible in Extended Info tab")
print("="*80)

env.cr.commit()




