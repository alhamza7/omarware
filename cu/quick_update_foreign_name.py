#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث سريع للـ Foreign Name والأسعار باستخدام SQL المباشر
"""

import psycopg2
from psycopg2.extras import execute_batch

# إعدادات قاعدة البيانات
db_config = {
    'dbname': 'lugal',
    'user': 'odoo',
    'password': 'odoo',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("تحديث سريع للـ Foreign Name والأسعار")
print("=" * 80)

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ تم الاتصال بقاعدة البيانات\n")
    
    # 1. فحص البيانات الحالية
    print("=" * 80)
    print("1️⃣ فحص البيانات الحالية")
    print("=" * 80)
    
    cur.execute("SELECT COUNT(*) FROM product_product")
    total_products = cur.fetchone()[0]
    print(f"إجمالي المنتجات: {total_products}")
    
    cur.execute("SELECT COUNT(*) FROM product_product WHERE foreign_name IS NOT NULL AND foreign_name != ''")
    with_foreign = cur.fetchone()[0]
    print(f"منتجات لديها Foreign Name: {with_foreign}")
    
    cur.execute("SELECT COUNT(*) FROM sap_product_extended")
    sap_extended_count = cur.fetchone()[0]
    print(f"سجلات SAP Extended: {sap_extended_count}")
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM sap_product_extended 
        WHERE product_id IS NOT NULL 
        AND foreign_name IS NOT NULL 
        AND foreign_name != ''
    """)
    sap_with_foreign = cur.fetchone()[0]
    print(f"سجلات SAP Extended لديها Foreign Name ومربوطة بمنتج: {sap_with_foreign}\n")
    
    # 2. تحديث Foreign Name
    print("=" * 80)
    print("2️⃣ تحديث Foreign Name من SAP Extended")
    print("=" * 80)
    
    update_query = """
        UPDATE product_product pp
        SET foreign_name = spe.foreign_name,
            write_date = NOW(),
            write_uid = 2
        FROM sap_product_extended spe
        WHERE spe.product_id = pp.id
        AND spe.foreign_name IS NOT NULL
        AND spe.foreign_name != ''
        AND (pp.foreign_name IS NULL OR pp.foreign_name = '')
    """
    
    print("تنفيذ التحديث...")
    cur.execute(update_query)
    updated_foreign = cur.rowcount
    print(f"✅ تم تحديث {updated_foreign} منتج بـ Foreign Name")
    
    # 3. تحديث الأسعار من Pricelist
    print("\n" + "=" * 80)
    print("3️⃣ تحديث الأسعار من SAP Price List 1")
    print("=" * 80)
    
    # الحصول على ID قائمة الأسعار
    cur.execute("SELECT id FROM product_pricelist WHERE name = 'SAP Price List 1'")
    pricelist_result = cur.fetchone()
    
    if pricelist_result:
        pricelist_id = pricelist_result[0]
        print(f"تم العثور على SAP Price List 1 (ID: {pricelist_id})")
        
        price_update_query = """
            UPDATE product_product pp
            SET list_price = pli.fixed_price,
                write_date = NOW(),
                write_uid = 2
            FROM product_pricelist_item pli
            WHERE pli.product_id = pp.id
            AND pli.pricelist_id = %s
            AND pli.fixed_price > 0
            AND (pp.list_price = 0 OR pp.list_price IS NULL)
        """
        
        print("تنفيذ تحديث الأسعار...")
        cur.execute(price_update_query, (pricelist_id,))
        updated_prices = cur.rowcount
        print(f"✅ تم تحديث {updated_prices} منتج بأسعار من Pricelist")
    else:
        print("⚠️ لم يتم العثور على SAP Price List 1")
    
    # حفظ التغييرات
    conn.commit()
    print("\n✅ تم حفظ جميع التغييرات")
    
    # 4. التحقق من النتائج
    print("\n" + "=" * 80)
    print("4️⃣ التحقق من النتائج")
    print("=" * 80)
    
    cur.execute("SELECT COUNT(*) FROM product_product WHERE foreign_name IS NOT NULL AND foreign_name != ''")
    final_with_foreign = cur.fetchone()[0]
    print(f"منتجات لديها Foreign Name الآن: {final_with_foreign} (كان: {with_foreign})")
    
    cur.execute("SELECT COUNT(*) FROM product_product WHERE list_price > 0")
    final_with_price = cur.fetchone()[0]
    print(f"منتجات لديها سعر > 0 الآن: {final_with_price}")
    
    # عينة من المنتجات المحدثة
    print("\nعينة من المنتجات بعد التحديث:")
    cur.execute("""
        SELECT name, default_code, foreign_name, list_price
        FROM product_product
        WHERE foreign_name IS NOT NULL
        ORDER BY id
        LIMIT 10
    """)
    
    for row in cur.fetchall():
        name, code, foreign, price = row
        print(f"\n📦 {name} ({code})")
        print(f"   Foreign Name: ✅ {foreign}")
        print(f"   السعر: {price}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى التحديث بنجاح")
    print("=" * 80)
    
    # إغلاق الاتصال
    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ خطأ في قاعدة البيانات: {e}")
    if conn:
        conn.rollback()
except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.rollback()

