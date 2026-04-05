# -*- coding: utf-8 -*-
"""
List all available databases
"""

import psycopg2

print("=" * 60)
print("Listing PostgreSQL Databases")
print("=" * 60)

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='odoo_user',
        password='root',
        database='postgres'
    )
    
    cur = conn.cursor()
    
    # Get all databases
    cur.execute("""
        SELECT datname 
        FROM pg_database 
        WHERE datistemplate = false 
        AND datname NOT IN ('postgres')
        ORDER BY datname;
    """)
    
    databases = cur.fetchall()
    
    print(f"\nFound {len(databases)} database(s):\n")
    
    for idx, (db_name,) in enumerate(databases, 1):
        print(f"{idx}. {db_name}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Use one of these names in odoo.conf")
    print("=" * 60)
    
except Exception as e:
    print(f"\nError: {str(e)}")

