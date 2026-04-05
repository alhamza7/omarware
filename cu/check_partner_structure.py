import psycopg2
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

try:
    conn = psycopg2.connect(
        host='localhost',
        database='lugal',
        user='odoo_user',
        password='root'
    )
    cur = conn.cursor()
    
    print("=== فحص هيكل جدول res_partner ===")
    
    # Check res_partner table structure
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' 
        AND column_name IN ('group_rfq', 'group_supplier', 'autopost_bills', 'customer_rank', 'supplier_rank')
        ORDER BY ordinal_position;
    """)
    partner_columns = cur.fetchall()
    print("الحقول المطلوبة:")
    for col_name, col_type, is_nullable, col_default in partner_columns:
        print(f"  {col_name}: {col_type} - Nullable: {is_nullable} - Default: {col_default}")
    
    # Check all columns that are NOT NULL
    cur.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' 
        AND is_nullable = 'NO'
        AND column_name NOT IN ('id', 'create_date', 'write_date', 'create_uid', 'write_uid')
        ORDER BY ordinal_position;
    """)
    required_columns = cur.fetchall()
    print(f"\nجميع الحقول المطلوبة (NOT NULL):")
    for col_name, col_type, col_default in required_columns:
        print(f"  {col_name}: {col_type} - Default: {col_default}")
    
    # Check existing partner to see what fields are set
    cur.execute("""
        SELECT name, customer_rank, supplier_rank, autopost_bills, group_rfq
        FROM res_partner 
        WHERE customer_rank > 0
        LIMIT 1;
    """)
    existing_partner = cur.fetchone()
    if existing_partner:
        print(f"\nعينة من العميل الموجود:")
        print(f"  Name: {existing_partner[0]}")
        print(f"  Customer Rank: {existing_partner[1]}")
        print(f"  Supplier Rank: {existing_partner[2]}")
        print(f"  Autopost Bills: {existing_partner[3]}")
        print(f"  Group RFQ: {existing_partner[4]}")
    
    conn.close()
except Exception as e:
    print(f'خطأ: {e}')

