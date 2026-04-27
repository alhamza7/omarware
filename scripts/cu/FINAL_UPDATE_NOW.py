#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحديث النهائي السريع - SQL مباشر
"""

import psycopg2

# معلومات الاتصال من odoo.conf
DB_CONFIG = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("تحديث Foreign Name والأسعار - SQL مباشر")
print("=" * 80)

try:
    # الاتصال
    print("الاتصال بقاعدة البيانات...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ متصل!\n")
    
    # 1. تحديث Foreign Name
    print("1️⃣ تحديث Foreign Name...")
    
    sql1 = """
        UPDATE product_product pp
        SET foreign_name = spe.foreign_name,
            write_date = NOW(),
            write_uid = 2
        FROM sap_product_extended spe
        WHERE spe.product_id = pp.id
        AND spe.foreign_name IS NOT NULL
        AND spe.foreign_name != ''
    """
    
    cur.execute(sql1)
    count1 = cur.rowcount
    print(f"   ✅ تم تحديث {count1} منتج\n")
    
    # 2. تحديث الأسعار
    print("2️⃣ تحديث الأسعار...")
    
    sql2 = """
        UPDATE product_product pp
        SET list_price = pli.fixed_price,
            write_date = NOW(),
            write_uid = 2
        FROM product_pricelist_item pli
        INNER JOIN product_pricelist pl ON pli.pricelist_id = pl.id
        WHERE pli.product_id = pp.id
        AND pl.name = 'SAP Price List 1'
        AND pli.fixed_price > 0
    """
    
    cur.execute(sql2)
    count2 = cur.rowcount
    print(f"   ✅ تم تحديث {count2} منتج\n")
    
    # حفظ
    conn.commit()
    print("💾 تم الحفظ!\n")
    
    # 3. الإحصائيات
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
    print(f"لديها Foreign Name: {stats[0]}")
    print(f"لديها سعر > 0: {stats[1]}\n")
    
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
    print("✅ تم بنجاح! 🎉")
    print("=" * 80)
    print("\nيمكنك الآن فتح Odoo والتحقق من:")
    print("  • Foreign Name في صفحة المنتج")
    print("  • الأسعار محدثة")
    print("  • وحدات القياس المتعددة في Pricelists")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()

