#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشخيص مشكلة عدم ظهور UoM في Pricelist
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("تشخيص مشكلة UoM في Pricelist")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. فحص حالة الوحدة
    print("=" * 80)
    print("1️⃣ فحص حالة الوحدة")
    print("=" * 80 + "\n")
    
    module_ids = models.execute_kw(db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'uom_in_pricelist']]])
    
    if module_ids:
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['name', 'state', 'latest_version']})[0]
        
        print(f"الوحدة: {module['name']}")
        print(f"الحالة: {module['state']}")
        print(f"الإصدار: {module.get('latest_version', 'N/A')}\n")
        
        if module['state'] != 'installed':
            print(f"❌ المشكلة: الوحدة {module['state']} وليست installed!")
            print("   الحل: يجب إتمام التثبيت\n")
    else:
        print("❌ الوحدة غير موجودة!\n")
    
    # 2. فحص الحقول في product.pricelist.item
    print("=" * 80)
    print("2️⃣ فحص حقول product.pricelist.item")
    print("=" * 80 + "\n")
    
    fields_info = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'fields_get', [],
        {'attributes': ['string', 'type']})
    
    if 'product_uom_id' in fields_info:
        print("✅ حقل product_uom_id موجود!")
        print(f"   النوع: {fields_info['product_uom_id'].get('type')}")
        print(f"   العنوان: {fields_info['product_uom_id'].get('string')}\n")
    else:
        print("❌ حقل product_uom_id غير موجود!")
        print("   المشكلة: الوحدة لم تُحمّل بشكل صحيح\n")
        print("الحقول المتاحة:")
        for field_name in list(fields_info.keys())[:20]:
            print(f"   - {field_name}")
        print()
    
    # 3. فحص الـ Views
    print("=" * 80)
    print("3️⃣ فحص Views")
    print("=" * 80 + "\n")
    
    views = models.execute_kw(db, uid, password,
        'ir.ui.view', 'search_read',
        [[['model', '=', 'product.pricelist.item'], 
          ['name', 'ilike', 'uom']]],
        {'fields': ['name', 'active', 'mode']})
    
    if views:
        print("Views المتعلقة بـ UoM:")
        for view in views:
            active = "✅" if view.get('active') else "❌"
            print(f"   {active} {view['name']} (mode: {view.get('mode', 'N/A')})")
        print()
    else:
        print("⚠️ لا توجد views UoM!\n")
    
    # 4. فحص البيانات المُنشأة
    print("=" * 80)
    print("4️⃣ فحص البيانات المُنشأة")
    print("=" * 80 + "\n")
    
    # البحث عن pricelist items للمعشوق
    items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['product_id.default_code', '=', 'ADF00005']]],
        {'fields': ['product_id', 'product_uom_id', 'fixed_price', 'pricelist_id']})
    
    if items:
        print(f"عدد Price Items للمعشوق: {len(items)}\n")
        for item in items:
            prod = item.get('product_id', ['N/A'])[1] if item.get('product_id') else 'N/A'
            uom = item.get('product_uom_id', ['N/A'])[1] if item.get('product_uom_id') else '❌ غير موجود'
            pricelist = item.get('pricelist_id', ['N/A'])[1] if item.get('pricelist_id') else 'N/A'
            
            print(f"   📦 {prod}")
            print(f"      Pricelist: {pricelist}")
            print(f"      UoM: {uom}")
            print(f"      السعر: ${item.get('fixed_price', 0):.2f}\n")
    else:
        print("⚠️ لا توجد price items للمعشوق!\n")
    
    # 5. التشخيص والحل
    print("=" * 80)
    print("5️⃣ التشخيص والحل")
    print("=" * 80 + "\n")
    
    # التحقق من السبب
    if module_ids:
        module_state = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['state']})[0]['state']
        
        if module_state != 'installed':
            print("❌ المشكلة: الوحدة غير مثبتة بالكامل")
            print(f"   الحالة: {module_state}")
            print("\n✅ الحل:")
            print("   1. أعد تشغيل Odoo")
            print("   2. أو اذهب لـ Apps → Update Apps List")
            print("   3. ثم Install من الواجهة\n")
        
        elif 'product_uom_id' not in fields_info:
            print("❌ المشكلة: الحقل لم يُضف للـ model")
            print("\n✅ الحل:")
            print("   1. أعد تشغيل Odoo (مهم!)")
            print("   2. Apps → Upgrade 'UOM In PriceList'\n")
        
        elif not views:
            print("❌ المشكلة: الـ View لم يُحمّل")
            print("\n✅ الحل:")
            print("   1. أعد تشغيل Odoo")
            print("   2. أو: Apps → Upgrade Module\n")
        
        else:
            print("✅ كل شيء يبدو صحيح تقنياً!")
            print("\n⚠️ المشكلة قد تكون:")
            print("   1. Cache في المتصفح → Ctrl+F5")
            print("   2. View غير صحيح → أعد تشغيل Odoo")
            print("   3. خطأ في xpath → نحتاج تعديل الـ View\n")

except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

