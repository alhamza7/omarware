#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إنشاء أسعار مرتبطة بوحدات القياس من بيانات SAP
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("إنشاء أسعار مرتبطة بوحدات القياس")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. فحص SAP Product UoM
    print("=" * 80)
    print("1️⃣ فحص بيانات وحدات القياس من SAP")
    print("=" * 80)
    
    try:
        sap_uom_count = models.execute_kw(db, uid, password,
            'sap.product.uom', 'search_count', [[]])
        print(f"عدد سجلات SAP Product UoM: {sap_uom_count}")
        
        if sap_uom_count > 0:
            sap_uoms = models.execute_kw(db, uid, password,
                'sap.product.uom', 'search_read', [[]],
                {'fields': ['product_id', 'uom_id', 'sap_uom_code'], 'limit': 10})
            
            print("\nعينة من البيانات:")
            for item in sap_uoms[:5]:
                prod = item.get('product_id', ['N/A'])[1] if item.get('product_id') else 'N/A'
                uom = item.get('uom_id', ['N/A'])[1] if item.get('uom_id') else 'N/A'
                print(f"   • {prod} → {uom}")
        else:
            print("⚠️ لا توجد بيانات في sap.product.uom")
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
    
    # 2. فحص وحدات القياس المتاحة
    print("\n" + "=" * 80)
    print("2️⃣ وحدات القياس المتاحة")
    print("=" * 80)
    
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['active', '=', True]]],
        {'fields': ['name', 'factor', 'uom_type'], 'limit': 20})
    
    print(f"عدد وحدات القياس: {len(uoms)}\n")
    
    # فلترة الوحدات المهمة (0.5، 0.25، إلخ)
    important_uoms = []
    for uom in uoms:
        factor = uom.get('factor', 1.0)
        if factor in [0.25, 0.5, 1.0, 2.0]:
            important_uoms.append(uom)
            print(f"   📏 {uom['name']} (معامل: {factor})")
    
    # 3. الحل المقترح
    print("\n" + "=" * 80)
    print("💡 الحل: إضافة Product Packaging")
    print("=" * 80)
    
    print("""
نظراً لأن:
• الأسعار الحالية كلها للكمية 1.0
• وحدات القياس موجودة (0.5، 0.25، إلخ)
• لا توجد بيانات ربط بينهما

الحل الأفضل: استخدام Product Packaging

════════════════════════════════════════════════════════════════════════════════

مثال عملي:

المنتج: "عطر X"
السعر الأساسي: $40 للكيلو

نضيف Packaging:
├─ 1 كيلو (Packaging) → السعر: $40
├─ 0.5 كيلو (Packaging) → السعر: $20 (نصف السعر)
└─ 0.25 كيلو (Packaging) → السعر: $10 (ربع السعر)

════════════════════════════════════════════════════════════════════════════════

الخطوات:
1. Settings → Inventory → فعّل "Product Packagings"
2. في كل منتج → Inventory → أضف Packagings
3. ربط كل packaging بسعره
""")
    
    # 4. سؤال المستخدم
    print("\n" + "=" * 80)
    print("❓ ماذا تريد أن نفعل؟")
    print("=" * 80)
    
    print("""
الخيارات المتاحة:

A) إنشاء Packagings تلقائياً لمنتجات مختارة
   • سريع
   • سهل الاستخدام
   • الأفضل للأحجام الثابتة (0.5، 1، إلخ)

B) استخدام نظام UoM الموجود
   • يتطلب تعديل Pricelist Items
   • أكثر مرونة
   • لكن أعقد

C) الحصول على البيانات الصحيحة من SAP
   • إعادة استيراد الأسعار من SAP
   • مع تحديد UoM لكل سعر

════════════════════════════════════════════════════════════════════════════════

📌 ملاحظة:
إذا كانت البيانات من SAP تحتوي على أسعار لوحدات مختلفة،
يجب إعادة استيرادها بشكل صحيح.
""")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

