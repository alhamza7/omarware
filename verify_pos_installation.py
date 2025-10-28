#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="lugal",
        user="odoo_user",
        password="root",
        host="localhost",
        port="5432"
    )
    
    cursor = conn.cursor()
    
    # Check module state
    cursor.execute("""
        SELECT name, state, latest_version
        FROM ir_module_module
        WHERE name = 'pos_perfume_custom'
    """)
    
    result = cursor.fetchone()
    
    print("=" * 70)
    print("POS Perfume Custom - Installation Check")
    print("=" * 70)
    
    if result:
        name, state, version = result
        print(f"Module Name: {name}")
        print(f"State: {state}")
        print(f"Version: {version}")
        print()
        
        if state == 'installed':
            print("SUCCESS! Module is INSTALLED")
            print()
            print("What was added to POS:")
            print("  1. Arabic product names (name_arabic field)")
            print("  2. IQD price display (1 USD = 1,300 IQD)")
            print("  3. Purple theme colors")
            print()
            print("To see changes:")
            print("  1. Add products with Arabic names")
            print("  2. Open POS")
            print("  3. You'll see prices in both USD and IQD")
            print("  4. Arabic names will appear for products")
            
        elif state == 'uninstalled':
            print("Module is uninstalled. Installing...")
            cursor.execute("""
                UPDATE ir_module_module
                SET state = 'to install'
                WHERE name = 'pos_perfume_custom'
            """)
            conn.commit()
            print("Module marked for installation.")
            print("Restart Odoo to complete installation.")
            
        else:
            print(f"Module state: {state}")
            print("Please check Odoo and try to install manually")
    else:
        print("Module not found!")
        print("Please update app list in Odoo")
    
    print("=" * 70)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

