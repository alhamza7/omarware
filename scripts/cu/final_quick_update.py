#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحديث النهائي السريع - استخدام ORM بطريقة ذكية
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"  
password = "admin"

print("=" * 80)
print("التحديث السريع للـ Foreign Name والأسعار")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # استخدام execute_kw مع raw SQL عبر model method
    # سنستخدم ir.model لتنفيذ SQL
    
    print("تنفيذ التحديثات...")
    
    # استدعاء method مباشرة على sap.product.extended
    # لتحديث المنتجات
    
    try:
        # نستخدم طريقة مختلفة - البحث عن جميع السجلات ثم التحديث الجماعي
        print("\n1️⃣ جلب البيانات...")
        
        # جلب IDs فقط لتسريع العملية
        sap_ids = models.execute_kw(db, uid, password,
            'sap.product.extended', 'search',
            [[['product_id', '!=', False], ['foreign_name', '!=', False]]])
        
        print(f"   عدد السجلات: {len(sap_ids)}")
        
        # جلب البيانات بدفعات كبيرة
        print("\n2️⃣ جلب البيانات بالتفصيل...")
        batch_size = 1000
        all_data = []
        
        for i in range(0, len(sap_ids), batch_size):
            batch_ids = sap_ids[i:i+batch_size]
            batch_data = models.execute_kw(db, uid, password,
                'sap.product.extended', 'read',
                [batch_ids],
                {'fields': ['product_id', 'foreign_name']})
            all_data.extend(batch_data)
            print(f"   جُلب {len(all_data)}/{len(sap_ids)}")
        
        # التحديث بدفعات كبيرة
        print("\n3️⃣ تحديث المنتجات...")
        updated = 0
        
        for i in range(0, len(all_data), batch_size):
            batch = all_data[i:i+batch_size]
            
            # تحديث كل منتج
            updates = []
            for item in batch:
                product_id = item['product_id'][0]
                foreign_name = item['foreign_name']
                updates.append((product_id, foreign_name))
            
            # تحديث جماعي
            for prod_id, fname in updates:
                try:
                    models.execute_kw(db, uid, password,
                        'product.product', 'write',
                        [[prod_id], {'foreign_name': fname}])
                    updated += 1
                except:
                    pass
            
            print(f"   تم تحديث {updated}/{len(all_data)}")
        
        print(f"\n✅ تم تحديث {updated} منتج بـ Foreign Name")
        
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
    
    # تحديث الأسعار
    print("\n4️⃣ تحديث الأسعار...")
    
    try:
        # جلب عناصر قائمة الأسعار
        items = models.execute_kw(db, uid, password,
            'product.pricelist.item', 'search_read',
            [[['pricelist_id.name', '=', 'SAP Price List 1'], 
              ['product_id', '!=', False],
              ['fixed_price', '>', 0]]],
            {'fields': ['product_id', 'fixed_price']})
        
        print(f"   عدد الأسعار: {len(items)}")
        
        price_updated = 0
        batch_size = 1000
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            for item in batch:
                product_id = item['product_id'][0]
                price = item['fixed_price']
                
                try:
                    models.execute_kw(db, uid, password,
                        'product.product', 'write',
                        [[product_id], {'list_price': price}])
                    price_updated += 1
                except:
                    pass
            
            print(f"   تم تحديث {price_updated}/{len(items)}")
        
        print(f"\n✅ تم تحديث {price_updated} سعر")
        
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
    
    # النتائج
    print("\n" + "=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    
    with_foreign = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['foreign_name', '!=', False]]])
    
    with_price = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['list_price', '>', 0]]])
    
    print(f"\nمنتجات لديها Foreign Name: {with_foreign}")
    print(f"منتجات لديها سعر > 0: {with_price}")
    
    print("\n✅ تم!")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

