#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أسرع طريقة لنقل Foreign Name من SAP إلى المنتجات
Fast transfer of Foreign Name from SAP to Products
"""

import psycopg2
import time

# إعدادات قاعدة البيانات
db_config = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("🚀 نقل Foreign Name من SAP إلى المنتجات - أسرع طريقة")
print("=" * 80)

try:
    start_time = time.time()
    
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ تم الاتصال بقاعدة البيانات\n")
    
    # 1. فحص البيانات قبل التحديث
    print("📊 فحص البيانات الحالية:")
    print("-" * 80)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NOT NULL AND foreign_name != ''
    """)
    before_count = cur.fetchone()[0]
    print(f"   المنتجات التي لديها Foreign Name حالياً: {before_count}")
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM sap_product_extended 
        WHERE product_id IS NOT NULL 
        AND foreign_name IS NOT NULL 
        AND foreign_name != ''
    """)
    sap_count = cur.fetchone()[0]
    print(f"   سجلات SAP التي تحتوي Foreign Name: {sap_count}")
    
    # حساب المنتجات القابلة للتحديث
    cur.execute("""
        SELECT COUNT(DISTINCT pp.id)
        FROM product_product pp
        JOIN sap_product_extended spe ON spe.product_id = pp.id
        WHERE spe.foreign_name IS NOT NULL 
        AND spe.foreign_name != ''
        AND (pp.foreign_name IS NULL OR pp.foreign_name = '' OR pp.foreign_name != spe.foreign_name)
    """)
    can_update = cur.fetchone()[0]
    print(f"   المنتجات القابلة للتحديث: {can_update}\n")
    
    if can_update == 0:
        print("✅ جميع المنتجات محدثة بالفعل! لا حاجة لأي تحديث.")
        cur.close()
        conn.close()
        exit(0)
    
    # 2. تنفيذ التحديث بأقصى سرعة
    print("⚡ بدء نقل البيانات...")
    print("-" * 80)
    
    update_query = """
        UPDATE product_product pp
        SET 
            foreign_name = spe.foreign_name,
            write_date = NOW(),
            write_uid = 2
        FROM sap_product_extended spe
        WHERE spe.product_id = pp.id
        AND spe.foreign_name IS NOT NULL
        AND spe.foreign_name != ''
    """
    
    cur.execute(update_query)
    updated_count = cur.rowcount
    
    # حفظ التغييرات
    conn.commit()
    
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ تم التحديث بنجاح!")
    print("=" * 80)
    print(f"   📦 عدد المنتجات المحدثة: {updated_count}")
    print(f"   ⏱️  الوقت المستغرق: {elapsed_time:.2f} ثانية")
    print(f"   ⚡ السرعة: {updated_count/elapsed_time:.0f} منتج/ثانية")
    print("=" * 80)
    
    # 3. التحقق من النتائج
    print("\n📊 التحقق من النتائج:")
    print("-" * 80)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NOT NULL AND foreign_name != ''
    """)
    after_count = cur.fetchone()[0]
    print(f"   المنتجات التي لديها Foreign Name الآن: {after_count}")
    print(f"   الزيادة: {after_count - before_count} منتج\n")
    
    # 4. عرض عينة من المنتجات المحدثة
    print("📝 عينة من المنتجات المحدثة:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            pp.default_code,
            pt.name,
            pp.foreign_name,
            spe.foreign_name as sap_foreign_name
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        JOIN sap_product_extended spe ON spe.product_id = pp.id
        WHERE pp.foreign_name IS NOT NULL 
        AND pp.foreign_name != ''
        ORDER BY pp.id
        LIMIT 10
    """)
    
    for row in cur.fetchall():
        code, name, foreign, sap_foreign = row
        status = "✅" if foreign == sap_foreign else "⚠️"
        print(f"\n{status} [{code or 'N/A'}] {name[:40]}")
        print(f"   Foreign Name: {foreign}")
    
    print("\n" + "=" * 80)
    print("✅ اكتمل النقل بنجاح!")
    print("=" * 80)
    
    # إغلاق الاتصال
    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"\n❌ خطأ في قاعدة البيانات:")
    print(f"   {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    exit(1)
    
except Exception as e:
    print(f"\n❌ خطأ عام:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    exit(1)

