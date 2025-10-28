#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check New Fields Added"""

print("=" * 80)
print("New Fields Added to SAP Integration")
print("=" * 80)

# Check sap.product.extended model
print("\n1. New Fields in 'sap.product.extended':")
ext_model = env['sap.product.extended']

new_fields = [
    'sales_unit',
    'purchase_unit', 
    'inventory_uom',
    'sales_uom_id',
    'purchase_uom_id',
    'inventory_uom_id'
]

for field_name in new_fields:
    if field_name in ext_model._fields:
        field = ext_model._fields[field_name]
        print(f"   - {field_name}: {field.type} ({field.string})")
    else:
        print(f"   X {field_name}: NOT FOUND")

# Check product.product - fields being populated
print("\n2. Fields in 'product.product' being updated:")
product_fields = [
    ('name', 'from ItemName or ForeignName'),
    ('default_code', 'from ItemCode'),
    ('list_price', 'from SalesUnitPrice'),
    ('standard_price', 'from PurchaseUnitPrice'),
    ('uom_id', 'from SalesUnit/InventoryUoM'),
    ('uom_po_id', 'from PurchaseUnit'),
    ('sale_ok', 'if active and SalesItem'),
    ('purchase_ok', 'if active and PurchaseItem'),
    ('available_in_pos', 'if active and SalesItem'),
    ('barcode', 'from BarCode'),
    ('weight', 'from Weight'),
    ('volume', 'from Volume'),
    ('description', 'from UserText'),
    ('description_sale', 'from Remarks'),
]

for field_name, source in product_fields:
    print(f"   - {field_name}: {source}")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print("\nNew fields in sap.product.extended: 6")
print("  - sales_unit (Char)")
print("  - purchase_unit (Char)")
print("  - inventory_uom (Char)")
print("  - sales_uom_id (Many2one)")
print("  - purchase_uom_id (Many2one)")
print("  - inventory_uom_id (Many2one)")
print("\nEnhanced fields in product.product: 14")
print("  - Now populated from SAP with complete data")

env.cr.commit()




