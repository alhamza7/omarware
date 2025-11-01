#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اكتشاف البنية الصحيحة لـ Packaging في Odoo 19
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print("✅ متصل\n")
    
    # فحص الحقول الكاملة لـ product.uom
    print("=" * 80)
    print("جميع حقول product.uom بالتفصيل:")
    print("=" * 80 + "\n")
    
    uom_fields = models.execute_kw(db, uid, password,
        'product.uom', 'fields_get', [],
        {'attributes': ['string', 'type', 'relation', 'required', 'help']})
    
    for field_name, field_info in sorted(uom_fields.items()):
        required = " [مطلوب]" if field_info.get('required') else ""
        relation = f" → {field_info.get('relation')}" if field_info.get('relation') else ""
        print(f"📌 {field_name}: {field_info.get('string')}{required}")
        print(f"   النوع: {field_info.get('type')}{relation}")
        if field_info.get('help'):
            print(f"   المساعدة: {field_info['help'][:100]}")
        print()
    
    # محاولة إنشاء بيانات صحيحة
    print("\n" + "=" * 80)
    print("محاولة إنشاء Packaging بالحقول الصحيحة")
    print("=" * 80 + "\n")
    
    # جلب منتج
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    if products:
        product_id = products[0]['id']
        
        # جلب UoM
        uoms = models.execute_kw(db, uid, password,
            'uom.uom', 'search_read',
            [[['name', 'ilike', '0.5']]],
            {'fields': ['id', 'name'], 'limit': 1})
        
        if uoms:
            uom_id = uoms[0]['id']
            
            # البيانات الصحيحة (حسب الحقول المتاحة)
            pkg_data = {
                'product_id': product_id,
                'uom_id': uom_id,
                'name': "علبة متوسطة (0.5 كغم)",
                'barcode': "TEST-500G",
            }
            
            print("البيانات:")
            for key, value in pkg_data.items():
                print(f"   {key}: {value}")
            print()
            
            try:
                pkg_id = models.execute_kw(db, uid, password,
                    'product.uom', 'create',
                    [pkg_data])
                
                print(f"✅✅✅ نجح إنشاء Packaging!")
                print(f"   ID: {pkg_id}\n")
                
                # قراءة ما تم إنشاؤه
                created = models.execute_kw(db, uid, password,
                    'product.uom', 'read',
                    [[pkg_id]])
                
                print("تفاصيل Packaging:")
                for field, value in created[0].items():
                    print(f"   {field}: {value}")
                
            except Exception as e:
                print(f"❌ فشل: {e}")

except Exception as e:
    print(f"❌ خطأ: {e}")

