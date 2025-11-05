# -*- coding: utf-8 -*-
"""
Script to activate all products in Sales and POS using SQL
تفعيل جميع المنتجات في المبيعات ونقطة البيع باستخدام SQL
"""

import psycopg2
from psycopg2 import sql

# Database connection settings
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'lugal',
    'user': 'odoo_user',
    'password': 'root'
}

try:
    # Connect to database
    print("=" * 80)
    print("تفعيل جميع المنتجات في Sales و Point of Sale")
    print("=" * 80)
    print()
    print("🔄 جاري الاتصال بقاعدة البيانات...")
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Count active products
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE active = TRUE
    """)
    total_products = cur.fetchone()[0]
    
    print(f"📦 تم العثور على {total_products} منتج نشط")
    print()
    
    if total_products > 0:
        print("🔄 جاري تفعيل المنتجات...")
        
        # Update all active products
        cur.execute("""
            UPDATE product_product
            SET sale_ok = TRUE,
                available_in_pos = TRUE
            WHERE active = TRUE
        """)
        
        rows_updated = cur.rowcount
        conn.commit()
        
        print(f"  ✓ تم تحديث {rows_updated} منتج")
        print()
        print("=" * 80)
        print(f"✅ تم تفعيل {rows_updated} منتج بنجاح!")
        print("=" * 80)
        print()
        print("الآن جميع المنتجات متاحة في:")
        print("  - Sales (المبيعات)")
        print("  - Point of Sale (نقطة البيع)")
    else:
        print("⚠️  لم يتم العثور على منتجات نشطة")
    
    # Close connection
    cur.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"❌ خطأ في قاعدة البيانات: {str(e)}")
except Exception as e:
    print(f"❌ خطأ عام: {str(e)}")

