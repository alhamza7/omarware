#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من اكتمال الترقية
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("التحقق من حالة الترقية")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. فحص حالة الوحدة
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if module_ids:
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['name', 'state', 'latest_version', 'installed_version']})[0]
        
        print("📦 الوحدة: uom_in_pricelist")
        print(f"   الحالة: {module['state']}")
        print(f"   الإصدار المثبت: {module.get('installed_version', 'N/A')}")
        print(f"   آخر إصدار: {module.get('latest_version', 'N/A')}\n")
        
        if module['state'] == 'installed':
            print("✅✅✅ الوحدة مثبتة ومحدثة!\n")
        elif module['state'] == 'to upgrade':
            print("⚠️ الوحدة بانتظار الترقية")
            print("   أعد تشغيل Odoo لإتمام الترقية\n")
        else:
            print(f"⚠️ الحالة: {module['state']}\n")
    
    # 2. فحص أن الحقل موجود
    fields_info = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'fields_get',
        [['product_uom_id']],
        {'attributes': ['string', 'type']})
    
    if 'product_uom_id' in fields_info:
        print("✅ حقل product_uom_id موجود ونشط\n")
    else:
        print("❌ حقل product_uom_id غير موجود!\n")
    
    # 3. اختبار سريع
    print("=" * 80)
    print("اختبار سريع")
    print("=" * 80 + "\n")
    
    print("البيانات التجريبية للمعشوق (ADF00005):\n")
    
    items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['product_id.default_code', '=', 'ADF00005']]],
        {'fields': ['product_id', 'product_uom_id', 'fixed_price'], 'limit': 5})
    
    for item in items:
        prod = item.get('product_id', ['N/A'])[1] if item.get('product_id') else 'N/A'
        uom = item.get('product_uom_id', ['N/A'])[1] if item.get('product_uom_id') else 'غير محدد'
        print(f"   📦 {prod}")
        print(f"      UoM: {uom}")
        print(f"      السعر: ${item.get('fixed_price', 0):.2f}\n")
    
    print("=" * 80)
    print("✅ التحقق اكتمل")
    print("=" * 80)
    
    print("""
الآن جرّب في Odoo:

1. Ctrl + Shift + R في المتصفح
2. Sales → Orders → New
3. Pricelist: SAP Price List 1
4. Add product: المعشوق
5. غيّر UoM وراقب السعر

المتوقع:
• Manual → $40
• 0.5 كيلو → $22
• 0.25 كغم → $12

إذا تغير السعر = نجح! 🎉
""")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

