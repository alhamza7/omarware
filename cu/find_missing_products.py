#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find Missing Products - Where did they go?"""

print("=" * 80)
print("البحث عن المنتجات المفقودة")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# Check product.template
print("\n1. فحص Product Templates:")
templates = env['product.template'].search([('default_code', '!=', False)])
print(f"   Product Templates مع كود: {len(templates)}")

# Check product.product
products = env['product.product'].search([('default_code', '!=', False)])
print(f"   Product Products مع كود: {len(products)}")

# Check recent creates
recent_templates = env['product.template'].search([
    ('create_date', '>=', '2025-10-22 00:00:00')
], order='create_date desc')
print(f"\n2. Templates تم إنشاؤها اليوم: {len(recent_templates)}")

recent_products = env['product.product'].search([
    ('create_date', '>=', '2025-10-22 00:00:00')
], order='create_date desc')
print(f"   Products تم إنشاؤها اليوم: {len(recent_products)}")

# Check Extended Info connections
extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
print(f"\n3. Extended Info: {len(extended)}")

# Count unique products
unique_product_ids = set(extended.mapped('product_id').ids)
print(f"   منتجات فريدة في Extended: {len(unique_product_ids)}")

# Check if products exist
existing_products = env['product.product'].browse(list(unique_product_ids)).exists()
print(f"   منتجات موجودة فعلياً: {len(existing_products)}")

# Find deleted products
deleted_count = len(unique_product_ids) - len(existing_products)
if deleted_count > 0:
    print(f"\n   ⚠️ منتجات محذوفة: {deleted_count}")

# Sample Extended Info
print(f"\n4. عينة من Extended Info:")
for ext in extended[:5]:
    if ext.product_id:
        print(f"   • Product ID {ext.product_id.id}: {ext.product_id.default_code}")
        print(f"     Exists: {ext.product_id.exists()}")
        print(f"     Active: {ext.product_id.active if ext.product_id.exists() else 'N/A'}")
    else:
        print(f"   • No product_id")

# Check all products (including inactive)
all_products = env['product.product'].with_context(active_test=False).search([
    ('default_code', '!=', False)
])
print(f"\n5. جميع المنتجات (بما فيها غير النشطة): {len(all_products)}")

inactive_products = env['product.product'].with_context(active_test=False).search([
    ('default_code', '!=', False),
    ('active', '=', False)
])
print(f"   منتجات غير نشطة: {len(inactive_products)}")

# Check if Extended Info points to templates or products
print(f"\n6. تحليل Extended Info:")
ext_with_products = extended.filtered(lambda e: e.product_id)
print(f"   Extended Info مع product_id: {len(ext_with_products)}")

# Get the model of product_id
if ext_with_products:
    sample_ext = ext_with_products[0]
    print(f"   نوع product_id: {sample_ext.product_id._name}")

print("\n" + "=" * 80)

env.cr.commit()





