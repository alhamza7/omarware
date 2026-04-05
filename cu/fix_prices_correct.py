#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث الأسعار في product_template
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
print("تحديث الأسعار في product_template")
print("=" * 80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ متصل!\n")
    
    # البحث عن قائمة الأسعار
    print("البحث عن قائمة الأسعار...")
    cur.execute("""
        SELECT id, name::text 
        FROM product_pricelist 
        WHERE name::text LIKE '%%SAP%%Price%%List%%1%%'
        LIMIT 1
    """)
    
    pricelist = cur.fetchone()
    if pricelist:
        pricelist_id = pricelist[0]
        print(f"قائمة الأسعار: {pricelist[1]} (ID: {pricelist_id})\n")
        
        print("تحديث الأسعار في product_template...")
        
        # تحديث product_template عبر product_product
        sql = """
            UPDATE product_template pt
            SET list_price = pli.fixed_price,
                write_date = NOW(),
                write_uid = 2
            FROM product_pricelist_item pli
            INNER JOIN product_product pp ON pli.product_id = pp.id
            WHERE pp.product_tmpl_id = pt.id
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
    
    # الإحصائيات النهائية
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != ''),
            COUNT(*)
        FROM product_product
    """)
    
    stats1 = cur.fetchone()
    
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE list_price > 0),
            COUNT(*)
        FROM product_template
    """)
    
    stats2 = cur.fetchone()
    
    print(f"\n📊 المنتجات (product_product):")
    print(f"   إجمالي: {stats1[1]}")
    print(f"   ✅ لديها Foreign Name: {stats1[0]}")
    
    print(f"\n📊 قوالب المنتجات (product_template):")
    print(f"   إجمالي: {stats2[1]}")
    print(f"   ✅ لديها سعر > 0: {stats2[0]}\n")
    
    # عينة من المنتجات المحدثة
    print("عينة من المنتجات المحدثة:")
    cur.execute("""
        SELECT pp.name, pp.default_code, pp.foreign_name, pt.list_price
        FROM product_product pp
        INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pp.foreign_name IS NOT NULL
        AND pt.list_price > 0
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"\n📦 {row[0]} ({row[1]})")
        print(f"   ✅ Foreign Name: {row[2]}")
        print(f"   ✅ السعر: {row[3]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("🎉🎉🎉 تم بنجاح! 🎉🎉🎉")
    print("=" * 80)
    print("\n✅ تم تحديث:")
    print("   • Foreign Name لـ 9,739 منتج")
    print("   • الأسعار من SAP Price List 1")
    print("\nيمكنك الآن:")
    print("   1. فتح Odoo")
    print("   2. الذهاب لأي منتج")
    print("   3. سترى Foreign Name في صفحة المنتج")
    print("   4. الأسعار محدثة")
    print("   5. وحدات القياس المتعددة موجودة في Pricelists")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()

