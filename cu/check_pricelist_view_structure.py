#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص هيكل view الأصلي لـ product.pricelist.item
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
    print("فحص هيكل View الأصلي")
    print("=" * 80 + "\n")
    
    # البحث عن الـ view الأصلي
    view_ids = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search',
        [[['model', '=', 'product.pricelist.item'], 
          ['type', '=', 'form'],
          ['name', 'ilike', 'product_pricelist_item']]])
    
    if view_ids:
        views = models.execute_kw(db, uid, password,
            'ir.ui.view', 'read',
            [view_ids],
            {'fields': ['name', 'arch', 'inherit_id']})
        
        print(f"عدد الـ Views: {len(views)}\n")
        
        for view in views[:3]:
            print(f"View: {view['name']}")
            print(f"ID: {view['id']}")
            parent = view.get('inherit_id')
            if parent:
                print(f"Parent: {parent[1]}")
            
            # عرض جزء من الـ arch
            arch = view.get('arch', '')
            if arch and len(arch) > 0:
                print("\nأول 1000 حرف من الـ arch:")
                print("-" * 80)
                print(arch[:1000])
                print("-" * 80)
            print("\n")

except Exception as e:
    print(f"❌ خطأ: {e}")

