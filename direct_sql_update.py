#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
import sys

print("=" * 80)
print("تحديث فوري - SQL مباشر")
print("=" * 80)

try:
    # محاولة كلمات مرور مختلفة
    passwords = ['odoo', 'admin', 'postgres', '']
    conn = None
    
    for pwd in passwords:
        try:
            print(f"محاولة الاتصال بكلمة المرور: {pwd if pwd else '(فارغة)'}...")
            conn = psycopg2.connect(
                dbname='lugal',
                user='odoo',
                password=pwd,
                host='localhost',
                port='5432'
            )
            print(f"✅ نجح الاتصال!\n")
            break
        except:
            continue
    
    if not conn:
        # محاولة مع postgres user
        try:
            print("محاولة الاتصال كمستخدم postgres...")
            conn = psycopg2.connect(
                dbname='lugal',
                user='postgres',
                password='postgres',
                host='localhost',
                port='5432'
            )
            print("✅ نجح الاتصال!\n")
        except Exception as e:
            print(f"❌ فشل الاتصال: {e}")
            sys.exit(1)
    
    cur = conn.cursor()
    
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
    print("💾 تم حفظ التغييرات!\n")
    
    # 3. عرض النتائج
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != '') as with_foreign,
            COUNT(*) FILTER (WHERE list_price > 0) as with_price,
            COUNT(*) as total
        FROM product_product
    """)
    
    result = cur.fetchone()
    print(f"إجمالي المنتجات: {result[2]}")
    print(f"لديها Foreign Name: {result[0]}")
    print(f"لديها سعر > 0: {result[1]}\n")
    
    # عينة
    print("عينة من المنتجات المحدثة:")
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
    print("✅ تم بنجاح!")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals() and conn:
        conn.rollback()

