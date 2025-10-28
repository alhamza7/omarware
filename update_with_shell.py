#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للتشغيل عبر odoo shell - أسرع طريقة
"""

# هذا السكريبت يُشغل عبر: python odoo-bin shell -d lugal --no-http
# أو يمكن تشغيله مباشرة إذا كان env موجود

import logging
_logger = logging.getLogger(__name__)

def update_products_from_sap():
    """تحديث المنتجات من SAP Extended"""
    
    print("=" * 80)
    print("تحديث المنتجات من SAP")
    print("=" * 80)
    
    # الحصول على env
    from odoo import registry, SUPERUSER_ID
    from odoo.api import Environment
    
    db_name = 'lugal'
    
    with registry(db_name).cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        
        # 1. تحديث Foreign Name عبر SQL
        print("\n1️⃣ تحديث Foreign Name...")
        
        query1 = """
            UPDATE product_product pp
            SET foreign_name = spe.foreign_name,
                write_date = NOW(),
                write_uid = %s
            FROM sap_product_extended spe
            WHERE spe.product_id = pp.id
            AND spe.foreign_name IS NOT NULL
            AND spe.foreign_name != ''
        """
        
        cr.execute(query1, (SUPERUSER_ID,))
        count1 = cr.rowcount
        print(f"   ✅ تم تحديث {count1} منتج")
        
        # 2. تحديث الأسعار
        print("\n2️⃣ تحديث الأسعار...")
        
        query2 = """
            UPDATE product_product pp
            SET list_price = pli.fixed_price,
                write_date = NOW(),
                write_uid = %s
            FROM product_pricelist_item pli
            INNER JOIN product_pricelist pl ON pli.pricelist_id = pl.id
            WHERE pli.product_id = pp.id
            AND pl.name = 'SAP Price List 1'
            AND pli.fixed_price > 0
        """
        
        cr.execute(query2, (SUPERUSER_ID,))
        count2 = cr.rowcount
        print(f"   ✅ تم تحديث {count2} منتج")
        
        # حفظ
        cr.commit()
        print("\n💾 تم الحفظ!")
        
        # 3. عرض النتائج
        print("\n" + "=" * 80)
        print("النتائج")
        print("=" * 80)
        
        cr.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != ''),
                COUNT(*) FILTER (WHERE list_price > 0),
                COUNT(*)
            FROM product_product
        """)
        
        result = cr.fetchone()
        print(f"\nإجمالي المنتجات: {result[2]}")
        print(f"لديها Foreign Name: {result[0]}")
        print(f"لديها سعر > 0: {result[1]}")
        
        # عينة
        print("\nعينة:")
        cr.execute("""
            SELECT name, default_code, foreign_name, list_price
            FROM product_product
            WHERE foreign_name IS NOT NULL
            LIMIT 5
        """)
        
        for row in cr.fetchall():
            print(f"\n📦 {row[0]} ({row[1]})")
            print(f"   Foreign: {row[2]}")
            print(f"   السعر: {row[3]}")
        
        print("\n" + "=" * 80)
        print("✅ تم بنجاح!")
        print("=" * 80)

if __name__ == '__main__':
    update_products_from_sap()

