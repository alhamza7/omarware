import psycopg2
import sys
import requests
import json
import time

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

def sync_from_sap():
    """المزامنة النهائية من SAP"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='lugal',
            user='odoo_user',
            password='root'
        )
        cur = conn.cursor()
        
        print("=== المزامنة النهائية من SAP ===")
        
        # Get SAP Backend details
        cur.execute("""
            SELECT id, name, base_url, username, password, company_db, verify_ssl
            FROM sap_backend 
            WHERE id = 2;
        """)
        backend = cur.fetchone()
        
        if not backend:
            print("❌ لم يتم العثور على SAP Backend")
            return False
        
        backend_id, name, base_url, username, password, company_db, verify_ssl = backend
        print(f"Backend: {name}")
        print(f"URL: {base_url}")
        
        # Login to SAP
        login_url = f"{base_url}/Login"
        auth_data = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password
        }
        
        print("تسجيل الدخول إلى SAP...")
        response = requests.post(login_url, json=auth_data, timeout=30, verify=verify_ssl)
        
        if response.status_code != 200:
            print(f"❌ فشل تسجيل الدخول: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        session_data = response.json()
        session_id = session_data.get('SessionId')
        print(f"✅ تم تسجيل الدخول بنجاح!")
        
        headers = {
            'B1SESSION': session_id,
            'Content-Type': 'application/json'
        }
        
        # Sync customers with immediate request
        print("🔄 مزامنة العملاء...")
        customers_url = f"{base_url}/BusinessPartners"
        
        try:
            # Use smaller batch size and immediate request
            params = {
                '$select': 'CardCode,CardName,CardType',
                '$top': 10  # Smaller batch
            }
            
            customers_response = requests.get(customers_url, headers=headers, params=params, timeout=15, verify=verify_ssl)
            
            if customers_response.status_code == 200:
                customers_data = customers_response.json()
                customers = customers_data.get('value', [])
                print(f"✅ تم العثور على {len(customers)} عميل في SAP")
                
                created_customers = 0
                for i, customer in enumerate(customers):
                    try:
                        customer_name = customer.get('CardName', f'SAP Customer {i+1}')
                        customer_code = customer.get('CardCode', f'SAP{i+1:03d}')
                        
                        # Check if customer exists
                        cur.execute("SELECT id FROM res_partner WHERE name = %s", (customer_name,))
                        existing = cur.fetchone()
                        
                        if existing:
                            partner_id = existing[0]
                            print(f"  ℹ️  العميل موجود: {customer_name}")
                        else:
                            # Create new customer
                            cur.execute("""
                                INSERT INTO res_partner (
                                    name, is_company, customer_rank, supplier_rank, 
                                    autopost_bills, create_uid, write_uid, create_date, write_date
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                RETURNING id;
                            """, (customer_name, True, 1, 0, 'auto', 2, 2))
                            
                            result = cur.fetchone()
                            if result:
                                partner_id = result[0]
                                print(f"  ✅ تم إنشاء العميل: {customer_name} (ID: {partner_id})")
                                created_customers += 1
                            else:
                                continue
                        
                        # Create sync record
                        cur.execute("""
                            INSERT INTO sap_customer_sync (
                                backend_id, connector_id, odoo_partner_id, 
                                sap_customer_id, sap_customer_name, sync_status, sync_direction,
                                create_uid, write_uid, create_date, write_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            ON CONFLICT (odoo_partner_id, sap_customer_id) DO UPDATE SET
                                sync_status = EXCLUDED.sync_status,
                                last_sync = NOW(),
                                write_date = NOW();
                        """, (backend_id, 2, partner_id, customer_code, customer_name, 'success', 'import', 2, 2))
                        
                    except Exception as e:
                        print(f"  ❌ خطأ في العميل {i+1}: {e}")
                        continue
                
                print(f"✅ تم إنشاء {created_customers} عميل جديد")
                
            else:
                print(f"❌ فشل في جلب العملاء: {customers_response.status_code}")
                print(f"Response: {customers_response.text}")
                
        except Exception as e:
            print(f"❌ خطأ في مزامنة العملاء: {e}")
        
        # Wait a bit before next request
        time.sleep(1)
        
        # Sync products with immediate request
        print("🔄 مزامنة المنتجات...")
        products_url = f"{base_url}/Items"
        
        try:
            params = {
                '$select': 'ItemCode,ItemName,ItemType',
                '$top': 10  # Smaller batch
            }
            
            products_response = requests.get(products_url, headers=headers, params=params, timeout=15, verify=verify_ssl)
            
            if products_response.status_code == 200:
                products_data = products_response.json()
                products = products_data.get('value', [])
                print(f"✅ تم العثور على {len(products)} منتج في SAP")
                
                created_products = 0
                for i, product in enumerate(products):
                    try:
                        product_name = product.get('ItemName', f'SAP Product {i+1}')
                        product_code = product.get('ItemCode', f'PROD{i+1:03d}')
                        
                        # Check if product exists
                        cur.execute("SELECT id FROM product_template WHERE name = %s", (product_name,))
                        existing = cur.fetchone()
                        
                        if existing:
                            product_id = existing[0]
                            print(f"  ℹ️  المنتج موجود: {product_name}")
                        else:
                            # Create new product
                            cur.execute("""
                                INSERT INTO product_template (
                                    name, type, create_uid, write_uid, create_date, write_date
                                ) VALUES (%s, %s, %s, %s, NOW(), NOW())
                                RETURNING id;
                            """, (product_name, 'product', 2, 2))
                            
                            result = cur.fetchone()
                            if result:
                                product_id = result[0]
                                print(f"  ✅ تم إنشاء المنتج: {product_name} (ID: {product_id})")
                                created_products += 1
                            else:
                                continue
                        
                        # Create sync record
                        cur.execute("""
                            INSERT INTO sap_product_sync (
                                backend_id, connector_id, odoo_product_id, 
                                sap_product_id, sap_product_name, sync_status, sync_direction,
                                create_uid, write_uid, create_date, write_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            ON CONFLICT (odoo_product_id, sap_product_id) DO UPDATE SET
                                sync_status = EXCLUDED.sync_status,
                                last_sync = NOW(),
                                write_date = NOW();
                        """, (backend_id, 2, product_id, product_code, product_name, 'success', 'import', 2, 2))
                        
                    except Exception as e:
                        print(f"  ❌ خطأ في المنتج {i+1}: {e}")
                        continue
                
                print(f"✅ تم إنشاء {created_products} منتج جديد")
                
            else:
                print(f"❌ فشل في جلب المنتجات: {products_response.status_code}")
                print(f"Response: {products_response.text}")
                
        except Exception as e:
            print(f"❌ خطأ في مزامنة المنتجات: {e}")
        
        # Update connector statistics
        cur.execute("""
            UPDATE sap_connector 
            SET customers_synced = (
                SELECT COUNT(*) FROM sap_customer_sync WHERE connector_id = 2
            ),
            products_synced = (
                SELECT COUNT(*) FROM sap_product_sync WHERE connector_id = 2
            ),
            sync_status = 'success',
            last_sync = NOW()
            WHERE id = 2;
        """)
        
        conn.commit()
        
        # Show final results
        print(f"\n=== النتائج النهائية ===")
        cur.execute("SELECT COUNT(*) FROM sap_customer_sync;")
        final_customers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sap_product_sync;")
        final_products = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM res_partner WHERE customer_rank > 0;")
        odoo_customers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM product_template;")
        odoo_products = cur.fetchone()[0]
        
        print(f"📊 سجلات مزامنة العملاء: {final_customers}")
        print(f"📊 سجلات مزامنة المنتجات: {final_products}")
        print(f"📊 العملاء في Odoo: {odoo_customers}")
        print(f"📊 المنتجات في Odoo: {odoo_products}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'خطأ: {e}')
        return False

if __name__ == "__main__":
    success = sync_from_sap()
    if success:
        print("\n🎉 تمت المزامنة بنجاح!")
        print("💡 يمكنك الآن رؤية البيانات في Odoo:")
        print("   - العملاء: http://127.0.0.1:8069/web#action=base.action_partner_form")
        print("   -المنتجات: http://127.0.0.1:8069/web#action=product.action_product_template")
    else:
        print("\n❌ فشلت المزامنة")

