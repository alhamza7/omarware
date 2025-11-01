#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ترقية uom_in_pricelist لتحميل Tree View الجديد
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("ترقية uom_in_pricelist Module")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # البحث عن الوحدة
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if module_ids:
        print("ترقية الوحدة...")
        
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            
            print("✅ تمت الترقية!\n")
            
            print("=" * 80)
            print("الآن:")
            print("=" * 80)
            print("""
1. في المتصفح: Ctrl + Shift + R
2. افتح Pricelist مرة أخرى
3. يجب أن تشاهد عمود "Unit of Measure" ✨

إذا لم يظهر:
→ أعد تشغيل Odoo كاملاً
→ ثم حاول مرة أخرى
""")
            
        except Exception as e:
            print(f"❌ خطأ: {e}\n")
            print("⚠️ قد تحتاج إعادة تشغيل Odoo لإتمام الترقية")
    else:
        print("❌ الوحدة غير موجودة!")

except Exception as e:
    print(f"❌ خطأ: {e}")

