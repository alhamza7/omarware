# -*- coding: utf-8 -*-
"""
Script to activate all products in Sales and POS
تفعيل جميع المنتجات في المبيعات ونقطة البيع
"""

import xmlrpc.client
import sys

# Odoo connection settings
url = "http://localhost:8070"
db = "lugal"
username = "admin"
password = "admin"

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("❌ Failed to authenticate!")
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("=" * 80)
print("تفعيل جميع المنتجات في Sales و Point of Sale")
print("=" * 80)
print()

# Search for all products
product_ids = models.execute_kw(
    db, uid, password,
    'product.product', 'search',
    [[('active', '=', True)]]
)

print(f"📦 تم العثور على {len(product_ids)} منتج نشط")
print()

# Update all products to enable Sales and POS
if product_ids:
    print("🔄 جاري تفعيل المنتجات...")
    
    # Update in batches to avoid timeout
    batch_size = 100
    total_updated = 0
    
    for i in range(0, len(product_ids), batch_size):
        batch = product_ids[i:i + batch_size]
        
        try:
            models.execute_kw(
                db, uid, password,
                'product.product', 'write',
                [batch, {
                    'sale_ok': True,
                    'available_in_pos': True,
                }]
            )
            total_updated += len(batch)
            print(f"  ✓ تم تفعيل {total_updated}/{len(product_ids)} منتج")
        except Exception as e:
            print(f"  ❌ خطأ في الدفعة {i//batch_size + 1}: {str(e)}")
            continue
    
    print()
    print("=" * 80)
    print(f"✅ تم تفعيل {total_updated} منتج بنجاح!")
    print("=" * 80)
    print()
    print("الآن جميع المنتجات متاحة في:")
    print("  - Sales (المبيعات)")
    print("  - Point of Sale (نقطة البيع)")
else:
    print("⚠️  لم يتم العثور على منتجات نشطة")

