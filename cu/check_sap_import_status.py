#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص حالة استيراد البيانات من SAP
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص حالة استيراد البيانات من SAP")
print("=" * 80)

try:
    # الاتصال بـ Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ تم الاتصال بنجاح\n")
    
    # 1. فحص بيانات SAP Products
    print("=" * 80)
    print("1️⃣ فحص جدول SAP Products")
    print("=" * 80)
    
    try:
        # عدد السجلات
        sap_product_count = models.execute_kw(db, uid, password,
            'sap.product', 'search_count', [[]])
        print(f"عدد منتجات SAP في الجدول: {sap_product_count}\n")
        
        if sap_product_count > 0:
            # جلب عينة من البيانات
            sap_products = models.execute_kw(db, uid, password,
                'sap.product', 'search_read', [[]],
                {'fields': ['material_number', 'material_description', 'foreign_name', 
                           'base_unit', 'material_group'], 'limit': 5})
            
            for sap_prod in sap_products:
                print(f"\n📦 SAP Material: {sap_prod.get('material_number', 'N/A')}")
                print(f"   Description: {sap_prod.get('material_description', 'N/A')}")
                print(f"   Foreign Name: {sap_prod.get('foreign_name', 'غير موجود')}")
                print(f"   Base Unit: {sap_prod.get('base_unit', 'N/A')}")
                print(f"   Material Group: {sap_prod.get('material_group', 'N/A')}")
                
            # فحص كم منتج لديه foreign_name
            sap_with_foreign = models.execute_kw(db, uid, password,
                'sap.product', 'search_count', 
                [[['foreign_name', '!=', False], ['foreign_name', '!=', '']]])
            print(f"\n📊 منتجات SAP لديها Foreign Name: {sap_with_foreign} من {sap_product_count}")
    except Exception as e:
        print(f"❌ خطأ في الوصول لجدول sap.product: {e}")
    
    # 2. فحص الربط بين SAP ومنتجات Odoo
    print("\n" + "=" * 80)
    print("2️⃣ فحص الربط بين SAP ومنتجات Odoo")
    print("=" * 80)
    
    try:
        # فحص منتجات Odoo التي لديها رابط SAP
        products_with_sap = models.execute_kw(db, uid, password,
            'product.product', 'search_read',
            [[['default_code', '!=', False]]],
            {'fields': ['name', 'default_code', 'foreign_name'], 'limit': 5})
        
        print(f"عينة من منتجات Odoo:\n")
        for prod in products_with_sap:
            code = prod.get('default_code', 'N/A')
            print(f"\n📦 Odoo Product: {prod.get('name', 'N/A')}")
            print(f"   Code: {code}")
            print(f"   Foreign Name: {prod.get('foreign_name', 'غير موجود')}")
            
            # البحث عن المنتج المقابل في SAP
            try:
                sap_match = models.execute_kw(db, uid, password,
                    'sap.product', 'search_read',
                    [[['material_number', '=', code]]],
                    {'fields': ['material_number', 'foreign_name', 'material_description']})
                
                if sap_match:
                    print(f"   ✅ تم العثور في SAP:")
                    print(f"      Foreign Name في SAP: {sap_match[0].get('foreign_name', 'غير موجود')}")
                    print(f"      Description في SAP: {sap_match[0].get('material_description', 'N/A')}")
                else:
                    print(f"   ❌ لم يتم العثور على مطابقة في SAP")
            except Exception as e:
                print(f"   ⚠️ خطأ في البحث عن SAP: {e}")
    except Exception as e:
        print(f"❌ خطأ في فحص الربط: {e}")
    
    # 3. فحص SAP UOM Prices
    print("\n" + "=" * 80)
    print("3️⃣ فحص أسعار وحدات القياس من SAP")
    print("=" * 80)
    
    try:
        uom_price_count = models.execute_kw(db, uid, password,
            'sap.uom.price', 'search_count', [[]])
        print(f"عدد أسعار وحدات القياس في SAP: {uom_price_count}\n")
        
        if uom_price_count > 0:
            uom_prices = models.execute_kw(db, uid, password,
                'sap.uom.price', 'search_read', [[]],
                {'fields': ['material_number', 'uom_code', 'uom_name', 'price', 
                           'currency', 'price_list'], 'limit': 10})
            
            for price in uom_prices:
                print(f"\n💵 Material: {price.get('material_number', 'N/A')}")
                print(f"   UoM Code: {price.get('uom_code', 'N/A')}")
                print(f"   UoM Name: {price.get('uom_name', 'N/A')}")
                print(f"   السعر: {price.get('price', 'N/A')} {price.get('currency', 'N/A')}")
                print(f"   قائمة الأسعار: {price.get('price_list', 'N/A')}")
    except Exception as e:
        print(f"❌ خطأ في الوصول لجدول sap.uom.price: {e}")
    
    # 4. فحص SAP UoM (وحدات القياس)
    print("\n" + "=" * 80)
    print("4️⃣ فحص وحدات القياس من SAP")
    print("=" * 80)
    
    try:
        sap_uom_count = models.execute_kw(db, uid, password,
            'sap.uom', 'search_count', [[]])
        print(f"عدد وحدات القياس في SAP: {sap_uom_count}\n")
        
        if sap_uom_count > 0:
            sap_uoms = models.execute_kw(db, uid, password,
                'sap.uom', 'search_read', [[]],
                {'fields': ['uom_code', 'uom_name', 'uom_group_id'], 'limit': 10})
            
            for uom in sap_uoms:
                group = uom.get('uom_group_id', False)
                group_str = f"{group[1]}" if group else "لا توجد مجموعة"
                print(f"   📏 {uom.get('uom_code', 'N/A')} - {uom.get('uom_name', 'N/A')} ({group_str})")
    except Exception as e:
        print(f"❌ خطأ في الوصول لجدول sap.uom: {e}")
    
    # 5. فحص حالة المزامنة
    print("\n" + "=" * 80)
    print("5️⃣ فحص حالة آخر مزامنة")
    print("=" * 80)
    
    try:
        # البحث عن سجلات المزامنة
        sync_logs = models.execute_kw(db, uid, password,
            'sap.sync.log', 'search_read', [[]],
            {'fields': ['sync_type', 'status', 'create_date', 'message'], 
             'limit': 5, 'order': 'create_date desc'})
        
        if sync_logs:
            print(f"آخر {len(sync_logs)} عمليات مزامنة:\n")
            for log in sync_logs:
                print(f"   📅 {log.get('create_date', 'N/A')}")
                print(f"      النوع: {log.get('sync_type', 'N/A')}")
                print(f"      الحالة: {log.get('status', 'N/A')}")
                print(f"      الرسالة: {log.get('message', 'N/A')}\n")
        else:
            print("⚠️ لا توجد سجلات مزامنة")
    except Exception as e:
        print(f"⚠️ لا يمكن الوصول لسجلات المزامنة: {e}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

