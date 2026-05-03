#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix product types using SQL"""

print("=" * 80)
print("FIX PRODUCT TYPES - SQL DIRECT")
print("=" * 80)
print()

cr = env.cr

# Check current types
cr.execute("""
    SELECT type, COUNT(*) 
    FROM product_template 
    GROUP BY type
""")

print("Current product types:")
for row in cr.fetchall():
    print(f"  {row[0]}: {row[1]} products")
print()

# Check what field controls stockable
cr.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'product_template' 
    AND column_name LIKE '%type%'
""")

print("Type-related fields in product_template:")
for row in cr.fetchall():
    print(f"  {row[0]}: {row[1]}")
print()

# Update using SQL - set detailed_type to 'product' for stockable
print("Updating product types using SQL...")

try:
    # First try detailed_type
    cr.execute("""
        UPDATE product_template 
        SET detailed_type = 'product'
        WHERE id IN (
            SELECT product_tmpl_id 
            FROM product_product 
            WHERE default_code IS NOT NULL 
            AND default_code != ''
        )
    """)
    count = cr.rowcount
    cr.commit()
    print(f"  Updated {count} products using detailed_type")
    
except Exception as e:
    print(f"  detailed_type update failed: {str(e)[:80]}")
    cr.rollback()
    
    # Try using type directly
    try:
        cr.execute("""
            UPDATE product_template 
            SET type = 'product'
            WHERE id IN (
                SELECT product_tmpl_id 
                FROM product_product 
                WHERE default_code IS NOT NULL 
                AND default_code != ''
            )
        """)
        count = cr.rowcount
        cr.commit()
        print(f"  Updated {count} products using type field")
    except Exception as e2:
        print(f"  type update also failed: {str(e2)[:80]}")
        cr.rollback()

# Verify
cr.execute("""
    SELECT type, COUNT(*) 
    FROM product_template 
    GROUP BY type
""")

print()
print("FINAL RESULT:")
for row in cr.fetchall():
    print(f"  {row[0]}: {row[1]} products")

print("=" * 80)

exit()






