#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Activate All SAP Products - حل سريع للمنتجات غير النشطة"""

print("=" * 80)
print("تفعيل جميع منتجات SAP")
print("=" * 80)

# البحث عن المنتجات غير النشطة
inactive_products = env['product.product'].with_context(active_test=False).search([
    ('default_code', '!=', False),
    ('active', '=', False)
])

print(f"\nوجدت {len(inactive_products)} منتج غير نشط")

if len(inactive_products) > 0:
    # عينة من المنتجات
    print("\nعينة من المنتجات التي سيتم تفعيلها:")
    for p in inactive_products[:10]:
        print(f"  - {p.default_code}: {p.name} (ID: {p.id})")
    
    if len(inactive_products) > 10:
        print(f"  ... و {len(inactive_products) - 10} منتج آخر")
    
    # تأكيد
    print(f"\n⚠️ سيتم تفعيل {len(inactive_products)} منتج")
    print("⏳ جاري التفعيل...")
    
    # التفعيل
    inactive_products.write({'active': True})
    env.cr.commit()
    
    print(f"\n✅ تم تفعيل {len(inactive_products)} منتج بنجاح!")
    
    # التحقق
    active_now = env['product.product'].search([('default_code', '!=', False)])
    all_products = env['product.product'].with_context(active_test=False).search([
        ('default_code', '!=', False)
    ])
    
    print(f"\n📊 الإحصائيات الجديدة:")
    print(f"   إجمالي منتجات SAP: {len(all_products)}")
    print(f"   منتجات نشطة: {len(active_now)}")
    print(f"   منتجات غير نشطة: {len(all_products) - len(active_now)}")
    
    # Extended Info
    extended = env['sap.product.extended'].search([])
    print(f"\n📝 Extended Info:")
    print(f"   إجمالي السجلات: {len(extended)}")
    print(f"   منتجات فريدة: {len(set(extended.mapped('product_id').ids))}")
else:
    print("\n✅ جميع المنتجات نشطة بالفعل!")

print("\n" + "=" * 80)
print("✅ اكتمل التفعيل بنجاح!")
print("=" * 80)

env.cr.commit()





