#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص بنية uom_ids (Packagings) في Odoo 19
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
    
    print("=" * 80)
    print("فحص Packagings في Odoo 19")
    print("=" * 80 + "\n")
    
    # 1. فحص حقل uom_ids
    fields_info = models.execute_kw(db, uid, password,
        'product.product', 'fields_get',
        [['uom_ids']],
        {'attributes': ['string', 'type', 'relation', 'help']})
    
    if 'uom_ids' in fields_info:
        print("حقل uom_ids:")
        info = fields_info['uom_ids']
        print(f"   النوع: {info.get('type')}")
        print(f"   العنوان: {info.get('string')}")
        print(f"   العلاقة: {info.get('relation')}")
        print(f"   المساعدة: {info.get('help', 'N/A')}\n")
        
        # جلب معلومات عن الـ relation model
        if info.get('relation'):
            relation_model = info['relation']
            print(f"Model المرتبط: {relation_model}\n")
            
            # فحص حقول هذا الـ model
            try:
                relation_fields = models.execute_kw(db, uid, password,
                    relation_model, 'fields_get', [],
                    {'attributes': ['string', 'type']})
                
                print(f"حقول {relation_model}:\n")
                for field_name, field_info in list(relation_fields.items())[:20]:
                    print(f"   📌 {field_name}: {field_info.get('string')} ({field_info.get('type')})")
                
                # فحص إذا يوجد بيانات
                print(f"\n{'='*80}")
                count = models.execute_kw(db, uid, password,
                    relation_model, 'search_count', [[]])
                print(f"عدد السجلات في {relation_model}: {count}\n")
                
                if count > 0:
                    # جلب عينة
                    samples = models.execute_kw(db, uid, password,
                        relation_model, 'search_read', [[]],
                        {'fields': ['name', 'qty'], 'limit': 5})
                    
                    print("عينة من البيانات:")
                    for sample in samples:
                        print(f"   • {sample.get('name', 'N/A')} - Qty: {sample.get('qty', 'N/A')}")
                
            except Exception as e:
                print(f"⚠️ خطأ في فحص {relation_model}: {e}")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

