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
    
    # Check SAP Backend configuration
    cur.execute('SELECT * FROM sap_backend;')
    backend_details = cur.fetchall()
    print(f'SAP Backend details: {backend_details}')
    
    # Check if there are any sync logs or errors
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%log%' OR table_name LIKE '%error%'
        ORDER BY table_name;
    """)
    log_tables = cur.fetchall()
    print(f'Log/Error tables: {[table[0] for table in log_tables]}')
    
    # Check connector configuration details
    cur.execute("""
        SELECT 
            c.id, c.name, c.backend_id, c.active, c.auto_sync,
            c.sync_frequency, c.last_sync, c.status,
            b.name as backend_name, b.host, b.port, b.username
        FROM sap_connector c
        LEFT JOIN sap_backend b ON c.backend_id = b.id;
    """)
    connector_config = cur.fetchall()
    print(f'Connector configuration: {connector_config}')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')

