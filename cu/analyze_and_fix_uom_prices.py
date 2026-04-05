#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحليل وإصلاح: ربط الأسعار بوحدات القياس بدلاً من الكميات
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
print("تحليل الأسعار ووحدات القياس")
print("=" * 80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ متصل\n")
    
    # 1. فحص البيانات الحالية في pricelist items
    print("=" * 80)
    print("1️⃣ فحص عناصر الأسعار الحالية")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*),
            COUNT(DISTINCT product_id),
            MIN(min_quantity),
            MAX(min_quantity)
        FROM product_pricelist_item
        WHERE pricelist_id IN (
            SELECT id FROM product_pricelist 
            WHERE name::text LIKE '%SAP%Price%List%1%'
        )
        AND product_id IS NOT NULL
    """)
    
    stats = cur.fetchone()
    print(f"إجمالي عناصر الأسعار: {stats[0]}")
    print(f"عدد المنتجات الفريدة: {stats[1]}")
    print(f"أصغر كمية: {stats[2]}")
    print(f"أكبر كمية: {stats[3]}\n")
    
    # 2. فحص منتج له أسعار متعددة
    print("=" * 80)
    print("2️⃣ أمثلة على منتجات لها أسعار متعددة")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            pp.default_code,
            pt.name::text,
            pli.min_quantity,
            pli.fixed_price
        FROM product_pricelist_item pli
        INNER JOIN product_product pp ON pli.product_id = pp.id
        INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pli.pricelist_id IN (
            SELECT id FROM product_pricelist 
            WHERE name::text LIKE '%SAP%Price%List%1%'
        )
        AND pli.product_id IN (
            SELECT product_id
            FROM product_pricelist_item
            WHERE pricelist_id IN (
                SELECT id FROM product_pricelist 
                WHERE name::text LIKE '%SAP%Price%List%1%'
            )
            GROUP BY product_id
            HAVING COUNT(*) > 1
        )
        ORDER BY pp.default_code, pli.min_quantity
        LIMIT 20
    """)
    
    products = cur.fetchall()
    
    if products:
        current_code = None
        for code, name, min_qty, price in products:
            if current_code != code:
                if name.startswith('{'):
                    import json
                    try:
                        name_dict = json.loads(name)
                        name = name_dict.get('en_US', name)
                    except:
                        pass
                
                print(f"\n📦 {code} - {name[:50]}")
                current_code = code
            print(f"   الكمية {min_qty} → ${price:.2f}")
    
    # 3. فحص وحدات القياس المتاحة
    print("\n" + "=" * 80)
    print("3️⃣ وحدات القياس المتاحة")
    print("=" * 80)
    
    cur.execute("""
        SELECT name, factor, active
        FROM uom_uom
        WHERE active = true
        ORDER BY name
        LIMIT 20
    """)
    
    uoms = cur.fetchall()
    print(f"\nعدد وحدات القياس النشطة: {len(uoms)}\n")
    for uom_name, factor, active in uoms[:10]:
        print(f"   📏 {uom_name} (معامل: {factor})")
    
    # 4. الحل المقترح
    print("\n" + "=" * 80)
    print("💡 الحل المقترح")
    print("=" * 80)
    
    print("""
المشكلة الحالية:
─────────────────
• الأسعار مرتبطة بـ min_quantity (الكمية الأدنى)
• مثال: الكمية 1 → $42، الكمية 0.5 → $22
• Odoo يفهمها كـ "عتبات سعر" وليس "وحدات قياس"

الحل:
──────
لربط الأسعار بوحدات القياس، نحتاج:

1️⃣ إنشاء وحدات قياس جديدة:
   • "كيلو كامل" (1.0 من الوحدة الأساسية)
   • "نصف كيلو" (0.5 من الوحدة الأساسية)
   • إلخ...

2️⃣ تحديث pricelist_item:
   • بدلاً من min_quantity
   • نضيف product variants أو نستخدم نظام packaging

3️⃣ أو استخدام Product Variants:
   • كل variant = حجم مختلف
   • كل variant له سعره الخاص

════════════════════════════════════════════════════════════════════════════════

هل تريد:
A) إنشاء وحدات قياس جديدة وربط الأسعار بها؟
B) استخدام Product Variants (الأفضل للأحجام الثابتة)؟
C) استخدام Product Packaging (الأسرع والأبسط)؟
""")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

