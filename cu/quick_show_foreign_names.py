#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض سريع للمنتجات مع Foreign Names
Quick Show Products with Foreign Names
"""

import psycopg2
from tabulate import tabulate

# إعدادات قاعدة البيانات
db_config = {
    'dbname': 'lugal',
    'user': 'odoo_user',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

print("=" * 100)
print("📋 عرض سريع للمنتجات مع Foreign Names")
print("=" * 100)

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ تم الاتصال بقاعدة البيانات\n")
    
    # عرض الإحصائيات
    print("📊 الإحصائيات:")
    print("-" * 100)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NOT NULL AND foreign_name != ''
    """)
    total_with_foreign = cur.fetchone()[0]
    print(f"   ✅ إجمالي المنتجات مع Foreign Name: {total_with_foreign:,}\n")
    
    # عرض أول 30 منتج
    print("📝 أول 30 منتج مع Foreign Name:")
    print("-" * 100)
    
    cur.execute("""
        SELECT 
            pp.default_code,
            pt.name->>'en_US',
            pp.foreign_name,
            pt.list_price
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE pp.foreign_name IS NOT NULL AND pp.foreign_name != ''
        ORDER BY pp.id
        LIMIT 30
    """)
    
    rows = cur.fetchall()
    
    if rows:
        # تحضير البيانات للعرض
        display_data = []
        for i, row in enumerate(rows, 1):
            code, name, foreign, price = row
            # تقصير الأسماء الطويلة
            name_display = (str(name)[:35] + '...') if name and len(str(name)) > 35 else (name or 'N/A')
            foreign_display = (str(foreign)[:25] + '...') if foreign and len(str(foreign)) > 25 else (foreign or 'N/A')
            
            display_data.append([
                i,
                code or 'N/A',
                name_display,
                foreign_display,
                f"{price:.2f}" if price else "0.00"
            ])
        
        headers = ["#", "الكود", "اسم المنتج", "Foreign Name", "السعر"]
        print()
        print(tabulate(display_data, headers=headers, tablefmt="grid"))
    
    print("\n" + "=" * 100)
    print("💡 نصائح:")
    print("-" * 100)
    print("   📱 في Odoo: Inventory → Products → Products")
    print("   🔍 للبحث التفاعلي: python show_foreign_names.py")
    print("   📊 للإحصائيات الكاملة: python verify_foreign_name_transfer.py")
    print("   📖 للدليل الكامل: راجع ملف HOW_TO_VIEW_FOREIGN_NAMES_AR.md")
    print("=" * 100)
    
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

