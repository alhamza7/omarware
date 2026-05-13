#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فرض تحديث الـ View
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
    print("فرض تحديث View")
    print("=" * 80 + "\n")
    
    # البحث عن الـ View
    view_ids = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search',
        [[['name', '=', 'product.pricelist.item.form.uom']]])
    
    if view_ids:
        print(f"تم العثور على View (ID: {view_ids[0]})")
        
        # قراءة الـ View
        view = models.execute_kw(db, uid, password,
            'ir.ui.view', 'read',
            [view_ids],
            {'fields': ['name', 'active', 'arch_db']})[0]
        
        print(f"الاسم: {view['name']}")
        print(f"نشط: {view['active']}")
        print(f"\nالـ arch:\n{view.get('arch_db', 'N/A')}\n")
        
        # فرض إعادة الكتابة
        print("فرض تحديث الـ View...")
        models.execute_kw(db, uid, password,
            'ir.ui.view', 'write',
            [view_ids, {'active': True}])
        
        print("✅ تم\n")
        print("الآن:")
        print("   1. Ctrl + Shift + R في المتصفح")
        print("   2. افتح Pricelist مرة أخرى")
        print("   3. يجب أن يظهر!\n")
    else:
        print("❌ الـ View غير موجود!")

except Exception as e:
    print(f"❌ خطأ: {e}")

