#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض المنتجات مع Foreign Names
Display Products with Foreign Names
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
print("📋 عرض المنتجات مع Foreign Names")
print("=" * 100)

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("✅ تم الاتصال بقاعدة البيانات\n")
    
    # عرض الإحصائيات
    print("📊 الإحصائيات السريعة:")
    print("-" * 100)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM product_product 
        WHERE foreign_name IS NOT NULL AND foreign_name != ''
    """)
    total_with_foreign = cur.fetchone()[0]
    print(f"   إجمالي المنتجات مع Foreign Name: {total_with_foreign:,}\n")
    
    # قائمة بالخيارات
    print("=" * 100)
    print("اختر طريقة العرض:")
    print("-" * 100)
    print("1. عرض أول 50 منتج")
    print("2. عرض آخر 50 منتج")
    print("3. البحث بكود المنتج (مثال: ADF00001)")
    print("4. البحث بالاسم الأجنبي (مثال: CK1)")
    print("5. عرض منتجات عشوائية (50 منتج)")
    print("6. عرض الكل (قد يستغرق وقتاً)")
    print("=" * 100)
    
    choice = input("\nاختر رقم (1-6): ").strip()
    
    print("\n" + "=" * 100)
    
    if choice == "1":
        print("📝 أول 50 منتج مع Foreign Name:")
        print("-" * 100)
        cur.execute("""
            SELECT 
                pp.default_code as "الكود",
                pt.name->>'en_US' as "اسم المنتج",
                pp.foreign_name as "Foreign Name",
                pt.list_price as "السعر"
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.foreign_name IS NOT NULL AND pp.foreign_name != ''
            ORDER BY pp.id
            LIMIT 50
        """)
        
    elif choice == "2":
        print("📝 آخر 50 منتج مع Foreign Name:")
        print("-" * 100)
        cur.execute("""
            SELECT 
                pp.default_code as "الكود",
                pt.name->>'en_US' as "اسم المنتج",
                pp.foreign_name as "Foreign Name",
                pt.list_price as "السعر"
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.foreign_name IS NOT NULL AND pp.foreign_name != ''
            ORDER BY pp.id DESC
            LIMIT 50
        """)
        
    elif choice == "3":
        code = input("أدخل كود المنتج (مثال: ADF00001): ").strip()
        print(f"\n🔍 البحث عن المنتج: {code}")
        print("-" * 100)
        cur.execute("""
            SELECT 
                pp.default_code as "الكود",
                pt.name->>'en_US' as "اسم المنتج",
                pp.foreign_name as "Foreign Name",
                pt.list_price as "السعر",
                pp.id as "Product ID"
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.default_code ILIKE %s
        """, (f"%{code}%",))
        
    elif choice == "4":
        foreign = input("أدخل الاسم الأجنبي (مثال: CK1): ").strip()
        print(f"\n🔍 البحث عن: {foreign}")
        print("-" * 100)
        cur.execute("""
            SELECT 
                pp.default_code as "الكود",
                pt.name->>'en_US' as "اسم المنتج",
                pp.foreign_name as "Foreign Name",
                pt.list_price as "السعر"
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.foreign_name ILIKE %s
            ORDER BY pp.id
            LIMIT 50
        """, (f"%{foreign}%",))
        
    elif choice == "5":
        print("📝 عينة عشوائية من 50 منتج:")
        print("-" * 100)
        cur.execute("""
            SELECT 
                pp.default_code as "الكود",
                pt.name->>'en_US' as "اسم المنتج",
                pp.foreign_name as "Foreign Name",
                pt.list_price as "السعر"
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.foreign_name IS NOT NULL AND pp.foreign_name != ''
            ORDER BY RANDOM()
            LIMIT 50
        """)
        
    elif choice == "6":
        confirm = input(f"⚠️  سيتم عرض {total_with_foreign:,} منتج. هل أنت متأكد؟ (yes/no): ").strip().lower()
        if confirm in ['yes', 'y', 'نعم']:
            print(f"\n📝 جميع المنتجات ({total_with_foreign:,}):")
            print("-" * 100)
            cur.execute("""
                SELECT 
                    pp.default_code as "الكود",
                    pt.name->>'en_US' as "اسم المنتج",
                    pp.foreign_name as "Foreign Name",
                    pt.list_price as "السعر"
                FROM product_product pp
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE pp.foreign_name IS NOT NULL AND pp.foreign_name != ''
                ORDER BY pp.id
            """)
        else:
            print("❌ تم الإلغاء")
            cur.close()
            conn.close()
            exit(0)
    else:
        print("❌ اختيار غير صحيح")
        cur.close()
        conn.close()
        exit(1)
    
    # عرض النتائج
    rows = cur.fetchall()
    if rows:
        headers = ["الكود", "اسم المنتج", "Foreign Name", "السعر"]
        
        # تحضير البيانات للعرض
        display_data = []
        for row in rows:
            code, name, foreign, price = row[:4]
            # تقصير الأسماء الطويلة
            name_display = (str(name)[:40] + '...') if name and len(str(name)) > 40 else (name or 'N/A')
            foreign_display = (str(foreign)[:30] + '...') if foreign and len(str(foreign)) > 30 else (foreign or 'N/A')
            
            display_data.append([
                code or 'N/A',
                name_display,
                foreign_display,
                f"{price:.2f}" if price else "0.00"
            ])
        
        print(f"\n✅ تم العثور على {len(rows):,} منتج:\n")
        print(tabulate(display_data, headers=headers, tablefmt="grid"))
        
        # حفظ في ملف إذا كانت النتائج كثيرة
        if len(rows) > 100:
            save = input(f"\n💾 هل تريد حفظ النتائج في ملف CSV؟ (yes/no): ").strip().lower()
            if save in ['yes', 'y', 'نعم']:
                import csv
                filename = "products_with_foreign_names.csv"
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in rows:
                        writer.writerow([
                            row[0] or 'N/A',
                            row[1] or 'N/A',
                            row[2] or 'N/A',
                            f"{row[3]:.2f}" if row[3] else "0.00"
                        ])
                print(f"✅ تم الحفظ في: {filename}")
    else:
        print("❌ لا توجد نتائج")
    
    print("\n" + "=" * 100)
    print("✅ انتهى العرض")
    print("=" * 100)
    
    # إغلاق الاتصال
    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"\n❌ خطأ في قاعدة البيانات:")
    print(f"   {e}")
    if 'conn' in locals():
        conn.close()
    
except KeyboardInterrupt:
    print("\n\n⚠️  تم الإلغاء بواسطة المستخدم")
    if 'conn' in locals():
        conn.close()
    
except Exception as e:
    print(f"\n❌ خطأ عام:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.close()

