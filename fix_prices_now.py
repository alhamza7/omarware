#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث الأسعار فقط
"""

import psycopg2

DB_CONFIG = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("تحديث الأسعار")
print("=" * 80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ متصل!\n")
    
    # أولاً: فحص هيكل جدول product_pricelist
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'product_pricelist' 
        AND column_name = 'name'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"نوع حقل name: {result[1]}\n")
    
    # محاولة 1: البحث بـ ID مباشرة
    print("البحث عن قائمة الأسعار...")
    cur.execute("""
        SELECT id, name::text 
        FROM product_pricelist 
        WHERE name::text LIKE '%%SAP%%Price%%List%%1%%'
        LIMIT 5
    """)
    
    pricelists = cur.fetchall()
    if pricelists:
        print("قوائم الأسعار المتاحة:")
        for pl_id, pl_name in pricelists:
            print(f"   ID: {pl_id}, Name: {pl_name}")
        
        # استخدام أول واحدة
        pricelist_id = pricelists[0][0]
        print(f"\nاستخدام قائمة الأسعار ID: {pricelist_id}\n")
        
        print("تحديث الأسعار...")
        sql = """
            UPDATE product_product pp
            SET list_price = pli.fixed_price,
                write_date = NOW(),
                write_uid = 2
            FROM product_pricelist_item pli
            WHERE pli.product_id = pp.id
            AND pli.pricelist_id = %s
            AND pli.fixed_price > 0
        """
        
        cur.execute(sql, (pricelist_id,))
        count = cur.rowcount
        print(f"✅ تم تحديث {count} منتج\n")
        
        conn.commit()
        print("💾 تم الحفظ!\n")
    else:
        print("⚠️ لم يتم العثور على قائمة أسعار SAP\n")
    
    # الإحصائيات
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != ''),
            COUNT(*) FILTER (WHERE list_price > 0),
            COUNT(*)
        FROM product_product
    """)
    
    stats = cur.fetchone()
    print(f"\nإجمالي المنتجات: {stats[2]}")
    print(f"✅ لديها Foreign Name: {stats[0]}")
    print(f"✅ لديها سعر > 0: {stats[1]}\n")
    
    # عينة
    print("عينة من المنتجات:")
    cur.execute("""
        SELECT name, default_code, foreign_name, list_price
        FROM product_product
        WHERE foreign_name IS NOT NULL
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"\n📦 {row[0]} ({row[1]})")
        print(f"   Foreign: {row[2]}")
        print(f"   السعر: {row[3]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅✅✅ تم بنجاح! 🎉🎉🎉")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()

