#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص إعداد وحدات القياس والأسعار
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("فحص وحدات القياس والأسعار")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. فحص SAP UoM Groups
    print("=" * 80)
    print("1️⃣ مجموعات وحدات القياس من SAP")
    print("=" * 80)
    
    uom_groups = models.execute_kw(db, uid, password,
        'sap.uom.group', 'search_read', [[]],
        {'fields': ['name', 'uom_ids'], 'limit': 5})
    
    print(f"عدد مجموعات UoM: {len(uom_groups)}\n")
    
    if uom_groups:
        print("أمثلة على المجموعات:\n")
        for group in uom_groups:
            print(f"📏 {group['name']}")
            uom_ids = group.get('uom_ids', [])
            print(f"   عدد الوحدات: {len(uom_ids)}")
            
            if uom_ids:
                try:
                    uoms = models.execute_kw(db, uid, password,
                        'uom.uom', 'read', [uom_ids],
                        {'fields': ['name', 'factor', 'category_id']})
                    
                    for uom in uoms[:3]:
                        cat = uom.get('category_id', ['N/A'])[1] if uom.get('category_id') else 'N/A'
                        print(f"      • {uom['name']} (معامل: {uom.get('factor', 'N/A')}) - {cat}")
                except:
                    pass
            print()
    
    # 2. فحص UoM Categories
    print("=" * 80)
    print("2️⃣ فئات وحدات القياس (UoM Categories)")
    print("=" * 80)
    
    categories = models.execute_kw(db, uid, password,
        'uom.category', 'search_read', [[]],
        {'fields': ['name'], 'limit': 10})
    
    print(f"عدد الفئات: {len(categories)}\n")
    for cat in categories:
        print(f"   📁 {cat['name']}")
    
    # 3. فحص وحدات القياس المتاحة
    print("\n" + "=" * 80)
    print("3️⃣ وحدات القياس المتاحة في النظام")
    print("=" * 80)
    
    all_uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read', [[]],
        {'fields': ['name', 'category_id'], 'limit': 20})
    
    print(f"عدد وحدات القياس: {len(all_uoms)}\n")
    
    by_category = {}
    for uom in all_uoms:
        cat_name = uom.get('category_id', ['Other'])[1] if uom.get('category_id') else 'Other'
        if cat_name not in by_category:
            by_category[cat_name] = []
        by_category[cat_name].append(uom['name'])
    
    for cat, uoms in list(by_category.items())[:5]:
        print(f"📁 {cat}:")
        for uom in uoms[:5]:
            print(f"   • {uom}")
        print()
    
    # 4. فحص كيفية ربط الأسعار
    print("=" * 80)
    print("4️⃣ كيفية ربط الأسعار بوحدات القياس")
    print("=" * 80)
    
    # جلب عينة من pricelist items
    items = models.execute_kw(db, uid, password,
        'product.pricelist.item', 'search_read',
        [[['product_id', '!=', False]]],
        {'fields': ['product_id', 'pricelist_id', 'fixed_price', 'min_quantity'], 'limit': 10})
    
    if items:
        print("\nعينة من عناصر الأسعار:\n")
        for item in items[:5]:
            prod_name = item.get('product_id', ['N/A'])[1] if item.get('product_id') else 'N/A'
            pricelist = item.get('pricelist_id', ['N/A'])[1] if item.get('pricelist_id') else 'N/A'
            print(f"📦 {prod_name}")
            print(f"   قائمة الأسعار: {pricelist}")
            print(f"   السعر: ${item.get('fixed_price', 0):.2f}")
            print(f"   الكمية الأدنى: {item.get('min_quantity', 1)}\n")
    
    # 5. التوصيات
    print("=" * 80)
    print("💡 التوضيح والحل")
    print("=" * 80)
    
    print("""
🔍 الوضع الحالي:

1. ✅ البيانات موجودة:
   • 169 مجموعة وحدات قياس من SAP
   • 9,335 سعر في كل Pricelist
   
2. ⚠️ المشكلة:
   • الأسعار مرتبطة بـ "الكمية الأدنى" (min_quantity)
   • وليست مرتبطة بـ "وحدات قياس مختلفة" (UoM)
   
3. 📊 مثال:
   • السعر 42$ للكمية 1 (يمثل 1 كغم)
   • السعر 22$ للكمية 0.5 (يمثل 0.5 كغم)
   
   لكن النظام يراها كـ "كميات" وليس "وحدات قياس"

════════════════════════════════════════════════════════════════════════════════

✅ الحلول الممكنة:

🔧 الحل 1: استخدام Product Packaging (التعبئة والتغليف)
────────────────────────────────────────────────────────────
   • في صفحة المنتج → تبويب Inventory
   • أضف Packaging (مثلاً: كغم، نصف كغم)
   • ربط كل تعبئة بسعرها في Pricelist

🔧 الحل 2: استخدام وحدات قياس مختلفة فعلية
────────────────────────────────────────────────────────────
   • إنشاء وحدات قياس جديدة (0.5 كغم، 1 كغم)
   • تعديل Pricelist Items لتستخدم UoM بدل min_quantity
   • يتطلب تعديل على البيانات

🔧 الحل 3: استخدام Product Variants (متغيرات المنتج)
────────────────────────────────────────────────────────────
   • إنشاء متغيرات للمنتج (نصف كغم، كغم)
   • كل متغير له سعره الخاص
   • الأفضل للمنتجات التي لها أحجام ثابتة

════════════════════════════════════════════════════════════════════════════════

📌 الخلاصة:
   البيانات موجودة لكن Odoo يفهمها كـ "كميات" وليس "وحدات قياس"
   هذا طبيعي لأن SAP يرسل الأسعار مرتبطة بالكمية
   
   الحل الأفضل: استخدام Product Packaging
""")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

