#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من نقل Foreign Name
Verify Foreign Name Transfer
"""

import psycopg2

# إعدادات قاعدة البيانات
db_config = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 80)
print("📊 التحقق من نقل Foreign Name من SAP إلى المنتجات")
print("=" * 80)

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ تم الاتصال بقاعدة البيانات\n")
    
    # 1. إحصائيات عامة
    print("📊 الإحصائيات العامة:")
    print("-" * 80)
    
    cur.execute("SELECT COUNT(*) FROM product_product")
    total_products = cur.fetchone()[0]
    print(f"   إجمالي المنتجات: {total_products:,}")
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NOT NULL AND foreign_name != ''
    """)
    with_foreign = cur.fetchone()[0]
    print(f"   المنتجات مع Foreign Name: {with_foreign:,}")
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NULL OR foreign_name = ''
    """)
    without_foreign = cur.fetchone()[0]
    print(f"   المنتجات بدون Foreign Name: {without_foreign:,}")
    
    percentage = (with_foreign / total_products * 100) if total_products > 0 else 0
    print(f"   النسبة المئوية: {percentage:.1f}%\n")
    
    # 2. التحقق من التطابق مع SAP
    print("🔍 التحقق من التطابق مع SAP:")
    print("-" * 80)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product pp
        JOIN sap_product_extended spe ON spe.product_id = pp.id
        WHERE pp.foreign_name = spe.foreign_name
    """)
    matching = cur.fetchone()[0]
    print(f"   المنتجات المتطابقة مع SAP: {matching:,}")
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product pp
        JOIN sap_product_extended spe ON spe.product_id = pp.id
        WHERE pp.foreign_name != spe.foreign_name 
        OR (pp.foreign_name IS NULL AND spe.foreign_name IS NOT NULL)
        OR (pp.foreign_name IS NOT NULL AND spe.foreign_name IS NULL)
    """)
    not_matching = cur.fetchone()[0]
    print(f"   المنتجات غير المتطابقة: {not_matching:,}\n")
    
    # 3. عرض عينة من المنتجات
    print("📝 عينة من المنتجات (أول 15 منتج):")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            pp.default_code,
            pt.name,
            pp.foreign_name,
            CASE 
                WHEN pp.foreign_name IS NOT NULL AND pp.foreign_name != '' THEN '✅'
                ELSE '❌'
            END as status
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        ORDER BY pp.id
        LIMIT 15
    """)
    
    for i, row in enumerate(cur.fetchall(), 1):
        code, name, foreign, status = row
        name_str = str(name)[:50] if name else 'N/A'
        print(f"\n{i}. {status} [{code or 'N/A'}] {name_str}")
        if foreign:
            print(f"   Foreign Name: {foreign}")
        else:
            print(f"   Foreign Name: (غير موجود)")
    
    # 4. عينة من المنتجات مع SAP
    print("\n\n📋 عينة مع مقارنة SAP (أول 10):")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            pp.default_code,
            pt.name,
            pp.foreign_name as product_foreign,
            spe.foreign_name as sap_foreign,
            CASE 
                WHEN pp.foreign_name = spe.foreign_name THEN '✅ متطابق'
                ELSE '⚠️ مختلف'
            END as match_status
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        JOIN sap_product_extended spe ON spe.product_id = pp.id
        WHERE spe.foreign_name IS NOT NULL
        ORDER BY pp.id
        LIMIT 10
    """)
    
    for i, row in enumerate(cur.fetchall(), 1):
        code, name, product_foreign, sap_foreign, match = row
        name_str = str(name)[:40] if name else 'N/A'
        print(f"\n{i}. [{code or 'N/A'}] {name_str}")
        print(f"   المنتج: {product_foreign or 'N/A'}")
        print(f"   SAP: {sap_foreign or 'N/A'}")
        print(f"   الحالة: {match}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى التحقق")
    print("=" * 80)
    
    # إغلاق الاتصال
    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"\n❌ خطأ في قاعدة البيانات:")
    print(f"   {e}")
    if 'conn' in locals():
        conn.close()
    
except Exception as e:
    print(f"\n❌ خطأ عام:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.close()

