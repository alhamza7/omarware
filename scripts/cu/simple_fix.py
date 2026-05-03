#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple fix for name_arabic"""

print("Fixing name_arabic field...")

# Update all products to have simple string name_arabic
try:
    # Use raw SQL to fix the issue
    env.cr.execute("""
        UPDATE product_template 
        SET name_arabic = NULL 
        WHERE name_arabic IS NOT NULL 
        AND name_arabic::text LIKE '%{%'
    """)
    
    env.cr.execute("""
        UPDATE product_product 
        SET name_arabic = NULL 
        WHERE name_arabic IS NOT NULL 
        AND name_arabic::text LIKE '%{%'
    """)
    
    env.cr.commit()
    print("DONE - Cleared problematic name_arabic values")
    
except Exception as e:
    print(f"Error: {e}")
    print("Trying alternative fix...")
    
    # Alternative: just clear all name_arabic
    env.cr.execute("UPDATE product_template SET name_arabic = NULL")
    env.cr.execute("UPDATE product_product SET name_arabic = NULL")
    env.cr.commit()
    print("DONE - Cleared all name_arabic values")

env.cr.commit()




