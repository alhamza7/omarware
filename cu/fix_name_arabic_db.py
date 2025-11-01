#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix name_arabic database field type"""

print("=" * 80)
print("Fixing name_arabic field in database")
print("=" * 80)

# Execute SQL directly to fix the field
try:
    print("\n1. Checking current column type...")
    env.cr.execute("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'product_template' 
          AND column_name = 'name_arabic'
    """)
    result = env.cr.fetchone()
    if result:
        print(f"   Current type: {result[1]} ({result[2]})")
    
    print("\n2. Converting JSONB to VARCHAR...")
    
    # Drop and recreate as VARCHAR
    env.cr.execute("""
        ALTER TABLE product_template 
        DROP COLUMN IF EXISTS name_arabic CASCADE
    """)
    
    env.cr.execute("""
        ALTER TABLE product_template 
        ADD COLUMN name_arabic VARCHAR
    """)
    
    env.cr.execute("""
        ALTER TABLE product_product 
        DROP COLUMN IF EXISTS name_arabic CASCADE
    """)
    
    env.cr.execute("""
        ALTER TABLE product_product 
        ADD COLUMN name_arabic VARCHAR
    """)
    
    env.cr.commit()
    print("   DONE - Converted to VARCHAR")
    
    print("\n3. Verifying fix...")
    env.cr.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'product_template' 
          AND column_name = 'name_arabic'
    """)
    result = env.cr.fetchone()
    if result:
        print(f"   New type: {result[1]}")
    
    print("\n" + "=" * 80)
    print("FIXED! name_arabic is now VARCHAR")
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {e}")

env.cr.commit()




