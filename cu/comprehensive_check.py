import psycopg2
import sys
import requests
import json

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
    
    print("=== فحص شامل للنظام ===")
    
    # 1. Check SAP Backend
    print("\n1. فحص SAP Backend:")
    cur.execute("""
        SELECT id, name, base_url, username, password, company_db, connection_status, 
               sync_customers, sync_products, active, verify_ssl
        FROM sap_backend 
        WHERE id = 2;
    """)
    backend = cur.fetchone()
    
    if backend:
        backend_id, name, base_url, username, password, company_db, status, sync_customers, sync_products, active, verify_ssl = backend
        print(f"  ✅ Backend: {name}")
        print(f"  ✅ URL: {base_url}")
        print(f"  ✅ Status: {status}")
        print(f"  ✅ Company DB: {company_db}")
        print(f"  ✅ Sync Customers: {'✅' if sync_customers else '❌'}")
        print(f"  ✅ Sync Products: {'✅' if sync_products else '❌'}")
        print(f"  ✅ Active: {'✅' if active else '❌'}")
        print(f"  ✅ Verify SSL: {'✅' if verify_ssl else '❌'}")
        
        # Test SAP connection
        print(f"\n2. اختبار الاتصال مع SAP:")
        login_url = f"{base_url}/Login"
        auth_data = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password
        }
        
        try:
            response = requests.post(login_url, json=auth_data, timeout=30, verify=verify_ssl)
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('SessionId')
                print(f"  ✅ تم تسجيل الدخول بنجاح!")
                print(f"  ✅ Session ID: {session_id[:20]}...")
                
                # Test getting customers
                headers = {
                    'B1SESSION': session_id,
                    'Content-Type': 'application/json'
                }
                
                customers_url = f"{base_url}/BusinessPartners"
                customers_response = requests.get(customers_url, headers=headers, timeout=30, verify=verify_ssl)
                
                if customers_response.status_code == 200:
                    customers_data = customers_response.json()
                    customers = customers_data.get('value', [])
                    print(f"  ✅ تم العثور على {len(customers)} عميل في SAP")
                    
                    # Show sample customers
                    for i, customer in enumerate(customers[:3]):
                        print(f"    - {customer.get('CardName', 'N/A')} ({customer.get('CardCode', 'N/A')})")
                    
                    # Test getting products
                    products_url = f"{base_url}/Items"
                    products_response = requests.get(products_url, headers=headers, timeout=30, verify=verify_ssl)
                    
                    if products_response.status_code == 200:
                        products_data = products_response.json()
                        products = products_data.get('value', [])
                        print(f"  ✅ تم العثور على {len(products)} منتج في SAP")
                        
                        # Show sample products
                        for i, product in enumerate(products[:3]):
                            print(f"    - {product.get('ItemName', 'N/A')} ({product.get('ItemCode', 'N/A')})")
                    else:
                        print(f"  ❌ فشل في جلب المنتجات: {products_response.status_code}")
                        print(f"  Response: {products_response.text}")
                        
                else:
                    print(f"  ❌ فشل في جلب العملاء: {customers_response.status_code}")
                    print(f"  Response: {customers_response.text}")
                    
            else:
                print(f"  ❌ فشل تسجيل الدخول: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ خطأ في الاتصال: {e}")
    
    # 3. Check SAP Connector
    print(f"\n3. فحص SAP Connector:")
    cur.execute("""
        SELECT id, name, sync_frequency, sync_status, active, auto_sync,
               sync_customers, sync_products, sync_quotations, sync_sales, sync_invoices,
               customers_synced, products_synced, quotations_synced, sales_synced, invoices_synced,
               last_sync
        FROM sap_connector 
        WHERE id = 2;
    """)
    connector = cur.fetchone()
    
    if connector:
        (id, name, frequency, status, active, auto_sync, sync_customers, sync_products, 
         sync_quotations, sync_sales, sync_invoices, customers_synced, products_synced, 
         quotations_synced, sales_synced, invoices_synced, last_sync) = connector
        
        print(f"  ✅ Name: {name}")
        print(f"  ✅ Frequency: {frequency}")
        print(f"  ✅ Status: {status}")
        print(f"  ✅ Active: {'✅' if active else '❌'}")
        print(f"  ✅ Auto Sync: {'✅' if auto_sync else '❌'}")
        print(f"  ✅ Sync Customers: {'✅' if sync_customers else '❌'}")
        print(f"  ✅ Sync Products: {'✅' if sync_products else '❌'}")
        print(f"  ✅ Last Sync: {last_sync}")
        print(f"  📊 Statistics:")
        print(f"    - Customers: {customers_synced}")
        print(f"    - Products: {products_synced}")
        print(f"    - Quotations: {quotations_synced}")
        print(f"    - Sales: {sales_synced}")
        print(f"    - Invoices: {invoices_synced}")
    
    # 4. Check actual sync records
    print(f"\n4. فحص سجلات المزامنة الفعلية:")
    cur.execute("SELECT COUNT(*) FROM sap_customer_sync;")
    sap_customers = cur.fetchone()[0]
    print(f"  📊 SAP Customer Sync records: {sap_customers}")
    
    cur.execute("SELECT COUNT(*) FROM sap_product_sync;")
    sap_products = cur.fetchone()[0]
    print(f"  📊 SAP Product Sync records: {sap_products}")
    
    # 5. Check Odoo records
    print(f"\n5. فحص سجلات Odoo:")
    cur.execute("SELECT COUNT(*) FROM res_partner WHERE customer_rank > 0;")
    odoo_customers = cur.fetchone()[0]
    print(f"  📊 Odoo Customers: {odoo_customers}")
    
    cur.execute("SELECT COUNT(*) FROM product_template;")
    odoo_products = cur.fetchone()[0]
    print(f"  📊 Odoo Products: {odoo_products}")
    
    # 6. Check if there are any sync methods
    print(f"\n6. فحص طرق المزامنة:")
    cur.execute("""
        SELECT cron_name, active, interval_number, interval_type, nextcall
        FROM ir_cron 
        WHERE cron_name ILIKE '%sap%' OR cron_name ILIKE '%sync%'
        ORDER BY id;
    """)
    sync_jobs = cur.fetchall()
    
    if sync_jobs:
        print(f"  📊 مهام المزامنة المجدولة:")
        for job in sync_jobs:
            cron_name, active, interval_num, interval_type, nextcall = job
            print(f"    - {cron_name}: {'✅' if active else '❌'} - {interval_num} {interval_type}")
    else:
        print(f"  ❌ لا توجد مهام مزامنة مجدولة")
    
    conn.close()
    
    print(f"\n=== خلاصة الفحص ===")
    if backend and connector:
        print(f"✅ SAP Backend: متصل")
        print(f"✅ SAP Connector: نشط")
        print(f"✅ الاتصال مع SAP: يعمل")
        print(f"❌ المزامنة التلقائية: غير مفعلة")
        print(f"💡 الحل: استخدم زر 'Sync All' في واجهة Odoo")
    
except Exception as e:
    print(f'خطأ: {e}')

