#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص معالج الاستيراد من SAP والبيانات المستوردة
"""

import xmlrpc.client

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص معالج الاستيراد من SAP والبيانات")
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
    
    # 1. فحص SAP Backend Configuration
    print("=" * 80)
    print("1️⃣ فحص إعدادات SAP Backend")
    print("=" * 80)
    
    try:
        backends = models.execute_kw(db, uid, password,
            'sap.backend', 'search_read', [[]],
            {'fields': ['name', 'server', 'port', 'client', 'username', 'active']})
        
        if backends:
            print(f"عدد الـ Backends المعرفة: {len(backends)}\n")
            for backend in backends:
                active_emoji = "✅" if backend.get('active') else "❌"
                print(f"{active_emoji} {backend.get('name', 'N/A')}")
                print(f"   الخادم: {backend.get('server', 'N/A')}:{backend.get('port', 'N/A')}")
                print(f"   العميل: {backend.get('client', 'N/A')}")
                print(f"   المستخدم: {backend.get('username', 'N/A')}")
                print(f"   نشط: {backend.get('active', False)}\n")
        else:
            print("❌ لا توجد إعدادات SAP Backend معرفة!")
    except Exception as e:
        print(f"❌ خطأ في الوصول لـ sap.backend: {e}")
    
    # 2. فحص SAP Product Binding
    print("\n" + "=" * 80)
    print("2️⃣ فحص SAP Product Binding")
    print("=" * 80)
    
    try:
        binding_count = models.execute_kw(db, uid, password,
            'sap.product.product', 'search_count', [[]])
        print(f"عدد منتجات SAP المربوطة: {binding_count}\n")
        
        if binding_count > 0:
            bindings = models.execute_kw(db, uid, password,
                'sap.product.product', 'search_read', [[]],
                {'fields': ['product_id', 'external_id'], 'limit': 5})
            
            for binding in bindings:
                product_name = binding.get('product_id', ['N/A'])[1] if binding.get('product_id') else 'N/A'
                print(f"   📦 {product_name}")
                print(f"      SAP ID: {binding.get('external_id', 'N/A')}\n")
    except Exception as e:
        print(f"❌ خطأ في الوصول لـ sap.product.product: {e}")
    
    # 3. فحص SAP Import Wizard
    print("\n" + "=" * 80)
    print("3️⃣ فحص سجلات SAP Import Wizard")
    print("=" * 80)
    
    try:
        # فحص الحقول المتاحة أولاً
        wizard_fields = models.execute_kw(db, uid, password,
            'sap.import.wizard', 'fields_get', [],
            {'attributes': ['string', 'type']})
        
        print("الحقول المتاحة في sap.import.wizard:")
        for field_name in list(wizard_fields.keys())[:20]:
            print(f"   - {field_name}: {wizard_fields[field_name].get('string', 'N/A')}")
        print()
        
        # محاولة البحث عن سجلات
        wizard_count = models.execute_kw(db, uid, password,
            'sap.import.wizard', 'search_count', [[]])
        print(f"عدد سجلات SAP Import Wizard: {wizard_count}")
        
        if wizard_count > 0:
            wizards = models.execute_kw(db, uid, password,
                'sap.import.wizard', 'search_read', [[]],
                {'fields': ['state', 'create_date'], 'limit': 5})
            
            for wizard in wizards:
                print(f"\n   📅 {wizard.get('create_date', 'N/A')}")
                print(f"      الحالة: {wizard.get('state', 'N/A')}")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.import.wizard: {e}")
    
    # 4. فحص SAP Sync Logs
    print("\n" + "=" * 80)
    print("4️⃣ فحص سجلات المزامنة (SAP Sync Logs)")
    print("=" * 80)
    
    try:
        # فحص الحقول أولاً
        log_fields = models.execute_kw(db, uid, password,
            'sap.sync.log', 'fields_get', [],
            {'attributes': ['string', 'type']})
        
        print("الحقول المتاحة في sap.sync.log:")
        important_fields = ['model', 'operation', 'status', 'message', 'create_date', 'error_details']
        for field_name, field_info in log_fields.items():
            if any(keyword in field_name for keyword in ['status', 'message', 'model', 'operation', 'date', 'error']):
                print(f"   - {field_name}: {field_info.get('string', 'N/A')}")
        print()
        
        log_count = models.execute_kw(db, uid, password,
            'sap.sync.log', 'search_count', [[]])
        print(f"عدد سجلات المزامنة: {log_count}\n")
        
        if log_count > 0:
            # جلب آخر 5 سجلات
            logs = models.execute_kw(db, uid, password,
                'sap.sync.log', 'search_read', [[]],
                {'fields': ['model_name', 'operation_type', 'status', 'message', 'create_date'], 
                 'limit': 5, 'order': 'create_date desc'})
            
            print("آخر 5 عمليات مزامنة:")
            for log in logs:
                print(f"\n   📅 {log.get('create_date', 'N/A')}")
                print(f"      النموذج: {log.get('model_name', 'N/A')}")
                print(f"      العملية: {log.get('operation_type', 'N/A')}")
                print(f"      الحالة: {log.get('status', 'N/A')}")
                msg = log.get('message', 'N/A')
                if msg and len(msg) > 100:
                    msg = msg[:100] + "..."
                print(f"      الرسالة: {msg}")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.sync.log: {e}")
    
    # 5. فحص SAP Synced Data
    print("\n" + "=" * 80)
    print("5️⃣ فحص البيانات المتزامنة (SAP Synced Data)")
    print("=" * 80)
    
    try:
        synced_count = models.execute_kw(db, uid, password,
            'sap.synced.data', 'search_count', [[]])
        print(f"عدد البيانات المتزامنة: {synced_count}\n")
        
        if synced_count > 0:
            synced_data = models.execute_kw(db, uid, password,
                'sap.synced.data', 'search_read', [[]],
                {'fields': ['odoo_model', 'sap_id', 'sync_status', 'last_sync_date'], 
                 'limit': 5, 'order': 'last_sync_date desc'})
            
            print("آخر 5 بيانات متزامنة:")
            for data in synced_data:
                print(f"\n   📦 {data.get('odoo_model', 'N/A')}")
                print(f"      SAP ID: {data.get('sap_id', 'N/A')}")
                print(f"      الحالة: {data.get('sync_status', 'N/A')}")
                print(f"      آخر مزامنة: {data.get('last_sync_date', 'N/A')}")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.synced.data: {e}")
    
    # 6. فحص SAP Product UoM
    print("\n" + "=" * 80)
    print("6️⃣ فحص SAP Product UoM")
    print("=" * 80)
    
    try:
        uom_count = models.execute_kw(db, uid, password,
            'sap.product.uom', 'search_count', [[]])
        print(f"عدد سجلات SAP Product UoM: {uom_count}\n")
        
        if uom_count > 0:
            uoms = models.execute_kw(db, uid, password,
                'sap.product.uom', 'search_read', [[]],
                {'fields': ['product_id', 'uom_id', 'sap_uom_code'], 'limit': 10})
            
            for uom in uoms:
                product_name = uom.get('product_id', ['N/A'])[1] if uom.get('product_id') else 'N/A'
                uom_name = uom.get('uom_id', ['N/A'])[1] if uom.get('uom_id') else 'N/A'
                print(f"   📦 {product_name}")
                print(f"      UoM: {uom_name}")
                print(f"      SAP UoM Code: {uom.get('sap_uom_code', 'N/A')}\n")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.product.uom: {e}")
    
    # 7. فحص SAP UoM Groups
    print("\n" + "=" * 80)
    print("7️⃣ فحص SAP UoM Groups")
    print("=" * 80)
    
    try:
        group_count = models.execute_kw(db, uid, password,
            'sap.uom.group', 'search_count', [[]])
        print(f"عدد مجموعات UoM من SAP: {group_count}\n")
        
        if group_count > 0:
            groups = models.execute_kw(db, uid, password,
                'sap.uom.group', 'search_read', [[]],
                {'fields': ['name', 'sap_group_id', 'base_uom_id'], 'limit': 10})
            
            for group in groups:
                base_uom = group.get('base_uom_id', ['N/A'])[1] if group.get('base_uom_id') else 'N/A'
                print(f"   📏 {group.get('name', 'N/A')}")
                print(f"      SAP Group ID: {group.get('sap_group_id', 'N/A')}")
                print(f"      Base UoM: {base_uom}\n")
    except Exception as e:
        print(f"⚠️ خطأ في الوصول لـ sap.uom.group: {e}")
    
    # 8. فحص Pricelist Items مع التفاصيل
    print("\n" + "=" * 80)
    print("8️⃣ فحص عناصر قوائم الأسعار بالتفصيل")
    print("=" * 80)
    
    try:
        # جلب منتج عشوائي
        product_ids = models.execute_kw(db, uid, password,
            'product.product', 'search', [[]], {'limit': 1})
        
        if product_ids:
            product = models.execute_kw(db, uid, password,
                'product.product', 'read', [product_ids[0]],
                {'fields': ['name', 'default_code', 'product_tmpl_id']})[0]
            
            print(f"فحص الأسعار للمنتج: {product.get('name', 'N/A')} ({product.get('default_code', 'N/A')})\n")
            
            tmpl_id = product['product_tmpl_id'][0] if product.get('product_tmpl_id') else None
            if tmpl_id:
                # البحث عن عناصر الأسعار
                price_items = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'search_read',
                    [[['product_tmpl_id', '=', tmpl_id]]],
                    {'fields': ['pricelist_id', 'fixed_price', 'min_quantity', 'applied_on']})
                
                if price_items:
                    print(f"عدد عناصر الأسعار: {len(price_items)}\n")
                    for item in price_items[:3]:
                        pricelist_name = item.get('pricelist_id', ['N/A'])[1] if item.get('pricelist_id') else 'N/A'
                        print(f"   💰 {pricelist_name}")
                        print(f"      السعر: {item.get('fixed_price', 'N/A')}")
                        print(f"      الحد الأدنى: {item.get('min_quantity', 'N/A')}")
                        print(f"      التطبيق: {item.get('applied_on', 'N/A')}\n")
                else:
                    print("⚠️ لا توجد أسعار محددة لهذا المنتج")
    except Exception as e:
        print(f"⚠️ خطأ في فحص الأسعار: {e}")
    
    print("\n" + "=" * 80)
    print("✅ انتهى الفحص")
    print("=" * 80)

except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

