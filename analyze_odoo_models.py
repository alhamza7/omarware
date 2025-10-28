#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Odoo Models - Pricing, Stock, UoM"""

print("=" * 80)
print("تحليل نماذج Odoo - التسعير والمخازن ووحدات القياس")
print("=" * 80)

# 1. Product Fields
print("\n📦 حقول المنتج (product.product):")
product_fields = env['product.product']._fields
important_fields = [
    'name', 'default_code', 'barcode', 'list_price', 'standard_price',
    'uom_id', 'uom_po_id', 'weight', 'volume',
    'categ_id', 'description', 'description_sale', 'description_purchase'
]
for field in important_fields:
    if field in product_fields:
        f = product_fields[field]
        print(f"  ✓ {field}: {f.type} - {f.string}")

# 2. UoM System
print("\n📏 نظام وحدات القياس:")
try:
    # Try different model names
    if 'uom.category' in env:
        uom_groups = env['uom.category'].search([])
        print(f"  إجمالي UoM Categories: {len(uom_groups)}")
    else:
        print("  ⚠️ uom.category غير موجود")
        uom_groups = []
except:
    uom_groups = []

uoms = env['uom.uom'].search([])
print(f"  إجمالي UoM: {len(uoms)}")

if uom_groups:
    print("\n  عينة من UoM Categories:")
    for cat in uom_groups[:5]:
        uoms_in_cat = env['uom.uom'].search([('category_id', '=', cat.id)])
        print(f"    - {cat.name}: {len(uoms_in_cat)} وحدات")
else:
    print("\n  عينة من UoM:")
    for uom in uoms[:10]:
        print(f"    - {uom.name} ({uom.uom_type if hasattr(uom, 'uom_type') else 'N/A'})")

# 3. Pricing System
print("\n💰 نظام التسعير:")
pricelists = env['product.pricelist'].search([])
print(f"  إجمالي Pricelists: {len(pricelists)}")

print("\n  عينة من Pricelists:")
for pl in pricelists[:5]:
    items = env['product.pricelist.item'].search([('pricelist_id', '=', pl.id)])
    print(f"    - {pl.name}: {len(items)} items")

# Check pricelist item fields
pricelist_item_fields = env['product.pricelist.item']._fields
print("\n  حقول Pricelist Item:")
pl_important = ['product_tmpl_id', 'product_id', 'min_quantity', 'fixed_price', 
                'price', 'base', 'compute_price']
for field in pl_important:
    if field in pricelist_item_fields:
        print(f"    ✓ {field}")

# 4. Stock/Warehouse System
print("\n🏭 نظام المخازن:")
warehouses = env['stock.warehouse'].search([])
print(f"  إجمالي Warehouses: {len(warehouses)}")
for wh in warehouses:
    print(f"    - {wh.name} ({wh.code})")

locations = env['stock.location'].search([('usage', '=', 'internal')])
print(f"  إجمالي Stock Locations: {len(locations)}")

# Check stock.quant fields
quant_fields = env['stock.quant']._fields
print("\n  حقول Stock Quant:")
quant_important = ['product_id', 'location_id', 'quantity', 'reserved_quantity', 
                   'available_quantity']
for field in quant_important:
    if field in quant_fields:
        f = quant_fields[field]
        print(f"    ✓ {field}: {f.type}")

# 5. SAP Extended Info
print("\n📝 SAP Extended Info Fields:")
ext_fields = env['sap.product.extended']._fields
print(f"  إجمالي الحقول: {len(ext_fields)}")
ext_important = ['foreign_name', 'items_group_name', 'manufacturer', 
                 'sales_unit', 'purchase_unit', 'inventory_uom']
for field in ext_important:
    if field in ext_fields:
        f = ext_fields[field]
        print(f"    ✓ {field}: {f.type}")
    else:
        print(f"    ✗ {field}: غير موجود")

# 6. Check SAP data structure
print("\n🔍 فحص بيانات SAP الموجودة:")
backend = env['sap.backend'].search([('active', '=', True)], limit=1)
if backend:
    print(f"  Backend: {backend.name}")
    
    # Check UoM sync
    uom_syncs = env['sap.uom.sync'].search([('backend_id', '=', backend.id)])
    print(f"  SAP UoM Syncs: {len(uom_syncs)}")
    
    # Check extended info
    extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
    print(f"  SAP Extended Info: {len(extended)}")
    
    if extended:
        sample = extended[0]
        print(f"\n  عينة Extended Info:")
        print(f"    Product: {sample.product_id.default_code if sample.product_id else 'N/A'}")
        print(f"    Foreign Name: {sample.foreign_name or 'N/A'}")
        print(f"    Manufacturer: {sample.manufacturer or 'N/A'}")

env.cr.commit()

