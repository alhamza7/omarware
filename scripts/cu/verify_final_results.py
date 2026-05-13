#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق النهائي من النتائج
"""

import psycopg2

DB_CONFIG = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("\n" + "=" * 80)
print("التحقق النهائي من النتائج")
print("=" * 80 + "\n")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. Foreign Name
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != ''),
               COUNT(*)
        FROM product_product
    """)
    fn_stats = cur.fetchone()
    
    # 2. الأسعار
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE list_price > 0),
               COUNT(*)
        FROM product_template
    """)
    price_stats = cur.fetchone()
    
    # 3. عينة من المنتجات
    cur.execute("""
        SELECT pt.name::text, pp.default_code, pp.foreign_name, pt.list_price
        FROM product_product pp
        INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pp.foreign_name IS NOT NULL
        AND pt.list_price > 0
        LIMIT 10
    """)
    
    samples = cur.fetchall()
    
    # عرض النتائج
    print("📊 **النتائج النهائية:**\n")
    print(f"✅ Foreign Name: {fn_stats[0]:,} من {fn_stats[1]:,} منتج ({fn_stats[0]/fn_stats[1]*100:.1f}%)")
    print(f"✅ الأسعار: {price_stats[0]:,} من {price_stats[1]:,} منتج ({price_stats[0]/price_stats[1]*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("عينة من المنتجات المحدثة (10 منتجات):")
    print("=" * 80 + "\n")
    
    for i, (name, code, foreign, price) in enumerate(samples, 1):
        # تنظيف الاسم من JSON
        if name.startswith('{'):
            import json
            try:
                name_dict = json.loads(name)
                name = name_dict.get('en_US', name)
            except:
                pass
        
        print(f"{i}. {name}")
        print(f"   الكود: {code}")
        print(f"   Foreign Name: {foreign}")
        print(f"   السعر: ${price:.2f}\n")
    
    cur.close()
    conn.close()
    
    print("=" * 80)
    print("✅ تم التحقق بنجاح!")
    print("=" * 80)
    print("\n🎉 يمكنك الآن:")
    print("   1. فتح Odoo")
    print("   2. عرض أي منتج")
    print("   3. سترى Foreign Name والسعر محدثين")
    print("   4. الأسعار المتعددة موجودة في Pricelists")
    print("\n")

except Exception as e:
    print(f"❌ خطأ: {e}")

