# -*- coding: utf-8 -*-
"""
Odoo Script to activate all existing products in Sales and POS
سكربت Odoo لتفعيل جميع المنتجات الموجودة في المبيعات ونقطة البيع
"""

import xmlrpc.client
import sys

# Odoo connection settings - تعديل هذه القيم حسب نظامك
url = "http://localhost:8070"  # أو IP النظام الجديد
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("تفعيل جميع المنتجات في Sales و Point of Sale")
print("=" * 80)
print()

try:
    # Connect to Odoo
    print("🔄 جاري الاتصال بـ Odoo...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل الاتصال! تحقق من بيانات الاتصال.")
        sys.exit(1)
    
    print(f"✅ تم الاتصال بنجاح! (User ID: {uid})")
    print()
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Search for all active products
    print("🔍 جاري البحث عن المنتجات...")
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[('active', '=', True)]]
    )
    
    print(f"📦 تم العثور على {len(product_ids)} منتج نشط")
    print()
    
    if not product_ids:
        print("⚠️  لم يتم العثور على منتجات نشطة")
        sys.exit(0)
    
    # Update all products to enable Sales and POS
    print("🔄 جاري تفعيل المنتجات...")
    print()
    
    # Update in batches to avoid timeout
    batch_size = 500
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
            progress = (total_updated / len(product_ids)) * 100
            print(f"  ✓ تم تفعيل {total_updated}/{len(product_ids)} منتج ({progress:.1f}%)")
        except Exception as e:
            print(f"  ❌ خطأ في الدفعة {i//batch_size + 1}: {str(e)}")
            continue
    
    print()
    print("=" * 80)
    print(f"✅ تم تفعيل {total_updated} منتج بنجاح!")
    print("=" * 80)
    print()
    print("الآن جميع المنتجات متاحة في:")
    print("  ✅ Sales (المبيعات)")
    print("  ✅ Point of Sale (نقطة البيع)")
    print()
    
except xmlrpc.client.Fault as e:
    print(f"❌ خطأ في Odoo: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"❌ خطأ عام: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

