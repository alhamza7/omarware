#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث فوري باستخدام SQL فقط - بدون حلقات
"""

import psycopg2

# إعدادات قاعدة البيانات
db_config = {
    'dbname': 'lugal',
    'user': 'odoo',
    'password': 'odoo',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("تحديث فوري للـ Foreign Name والأسعار")
print("=" * 80)

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ متصل بقاعدة البيانات\n")
    
    # 1. التحديث الفوري للـ Foreign Name
    print("تحديث Foreign Name...")
    cur.execute("""
        UPDATE product_product pp
        SET foreign_name = spe.foreign_name,
            write_date = NOW(),
            write_uid = 2
        FROM sap_product_extended spe
        WHERE spe.product_id = pp.id
        AND spe.foreign_name IS NOT NULL
        AND spe.foreign_name != ''
    """)
    count1 = cur.rowcount
    print(f"✅ تم تحديث {count1} منتج")
    
    # 2. التحديث الفوري للأسعار
    print("\nتحديث الأسعار من Pricelist...")
    cur.execute("""
        UPDATE product_product pp
        SET list_price = pli.fixed_price,
            write_date = NOW(),
            write_uid = 2
        FROM product_pricelist_item pli
        INNER JOIN product_pricelist pl ON pli.pricelist_id = pl.id
        WHERE pli.product_id = pp.id
        AND pl.name = 'SAP Price List 1'
        AND pli.fixed_price > 0
    """)
    count2 = cur.rowcount
    print(f"✅ تم تحديث {count2} منتج")
    
    # حفظ
    conn.commit()
    print("\n✅ تم الحفظ!")
    
    # عرض عينة
    print("\nعينة من النتائج:")
    cur.execute("""
        SELECT name, default_code, foreign_name, list_price
        FROM product_product
        WHERE foreign_name IS NOT NULL
        LIMIT 5
    """)
    
    for name, code, foreign, price in cur.fetchall():
        print(f"\n📦 {name} ({code})")
        print(f"   Foreign: {foreign}")
        print(f"   السعر: {price}")
    
    cur.close()
    conn.close()
    print("\n" + "=" * 80)
    print("✅ انتهى!")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ: {e}")
    if 'conn' in locals():
        conn.rollback()

