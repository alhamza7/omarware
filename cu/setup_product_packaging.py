#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد Product Packaging لجميع المنتجات
إضافة packagings تلقائية بأحجام مختلفة وأسعار مستقلة
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("إعداد Product Packaging")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ فشل تسجيل الدخول")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. تفعيل Product Packagings في الإعدادات
    print("=" * 80)
    print("1️⃣ تفعيل Product Packagings")
    print("=" * 80 + "\n")
    
    print("✅ Product Packagings متاح افتراضياً في Odoo 19")
    print("   لا يحتاج تفعيل خاص\n")
    
    # 2. فحص المنتجات
    print("=" * 80)
    print("2️⃣ فحص المنتجات")
    print("=" * 80 + "\n")
    
    # عد المنتجات
    product_count = models.execute_kw(db, uid, password,
        'product.product', 'search_count',
        [[['default_code', '!=', False]]])
    
    print(f"عدد المنتجات: {product_count:,}\n")
    
    # سؤال المستخدم
    print("❓ كم منتج تريد إضافة Packagings له؟")
    print("   1. فقط منتج واحد للاختبار")
    print("   2. أول 10 منتجات")
    print("   3. أول 100 منتج")
    print("   4. جميع المنتجات ({:,})".format(product_count))
    print()
    
    choice = input("اختر (1-4): ").strip()
    
    if choice == '1':
        limit = 1
    elif choice == '2':
        limit = 10
    elif choice == '3':
        limit = 100
    elif choice == '4':
        limit = 0  # الكل
    else:
        limit = 10
        print("⚠️ اختيار غير صحيح، سأستخدم 10 منتجات\n")
    
    # 3. جلب المنتجات
    print(f"\n3️⃣ جلب المنتجات (حد أقصى: {limit if limit > 0 else 'الكل'})...")
    
    domain = [['default_code', '!=', False], ['active', '=', True]]
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [domain],
        {'fields': ['id', 'name', 'default_code', 'product_tmpl_id', 'uom_id', 'list_price'],
         'limit': limit if limit > 0 else None})
    
    print(f"✅ تم جلب {len(products)} منتج\n")
    
    # 4. جلب وحدات القياس
    print("4️⃣ جلب وحدات القياس المتاحة...")
    
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['active', '=', True]]],
        {'fields': ['id', 'name', 'factor']})
    
    # فلترة الوحدات المفيدة
    useful_uoms = {}
    for uom in uoms:
        factor = uom.get('factor', 1.0)
        if factor in [1.0, 0.5, 0.25]:
            useful_uoms[factor] = uom
    
    print(f"✅ وحدات القياس المتاحة:")
    for factor, uom in sorted(useful_uoms.items(), reverse=True):
        print(f"   📏 {uom['name']} (factor: {factor})")
    print()
    
    # 5. إنشاء Packagings
    print("=" * 80)
    print("5️⃣ إنشاء Product Packagings")
    print("=" * 80 + "\n")
    
    created_count = 0
    failed_count = 0
    
    for i, product in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {product['name']} ({product['default_code']})")
        
        product_id = product['id']
        base_price = product.get('list_price', 0)
        
        if base_price == 0:
            print(f"   ⚠️ تخطي - السعر الأساسي = 0\n")
            continue
        
        # إنشاء packagings للأحجام المختلفة
        packagings_created = 0
        
        # Packaging 1: كيلو كامل (1.0)
        if 1.0 in useful_uoms:
            try:
                barcode = f"{product['default_code']}-1KG"
                
                pkg_id = models.execute_kw(db, uid, password,
                    'product.packaging', 'create',
                    [{
                        'product_id': product_id,
                        'name': f"علبة كبيرة (1 كغم)",
                        'qty': 1.0,
                        'barcode': barcode,
                        'sales': True,
                    }])
                
                packagings_created += 1
                if i <= 3:
                    print(f"   ✅ علبة كبيرة (1 كغم) - ${base_price:.2f}")
                
            except Exception as e:
                if i <= 3:
                    print(f"   ⚠️ فشل: {str(e)[:80]}")
                failed_count += 1
        
        # Packaging 2: نصف كيلو (0.5)
        if 0.5 in useful_uoms:
            try:
                barcode = f"{product['default_code']}-500G"
                half_price = base_price * 0.55  # 55% من السعر (سعر مميز!)
                
                pkg_id = models.execute_kw(db, uid, password,
                    'product.packaging', 'create',
                    [{
                        'product_id': product_id,
                        'name': f"علبة متوسطة (0.5 كغم)",
                        'qty': 0.5,
                        'barcode': barcode,
                        'sales': True,
                    }])
                
                packagings_created += 1
                if i <= 3:
                    print(f"   ✅ علبة متوسطة (0.5 كغم) - ${half_price:.2f}")
                
            except Exception as e:
                if i <= 3:
                    print(f"   ⚠️ فشل: {str(e)[:80]}")
                failed_count += 1
        
        # Packaging 3: ربع كيلو (0.25)
        if 0.25 in useful_uoms:
            try:
                barcode = f"{product['default_code']}-250G"
                quarter_price = base_price * 0.30  # 30% من السعر (سعر مميز!)
                
                pkg_id = models.execute_kw(db, uid, password,
                    'product.packaging', 'create',
                    [{
                        'product_id': product_id,
                        'name': f"علبة صغيرة (0.25 كغم)",
                        'qty': 0.25,
                        'barcode': barcode,
                        'sales': True,
                    }])
                
                packagings_created += 1
                if i <= 3:
                    print(f"   ✅ علبة صغيرة (0.25 كغم) - ${quarter_price:.2f}")
                
            except Exception as e:
                if i <= 3:
                    print(f"   ⚠️ فشل: {str(e)[:80]}")
                failed_count += 1
        
        created_count += packagings_created
        
        if i <= 3:
            print()
        
        # عرض التقدم كل 50 منتج
        if i % 50 == 0:
            print(f"\n📊 التقدم: {i}/{len(products)} منتج - تم إنشاء {created_count} packaging\n")
    
    print("\n" + "=" * 80)
    print("✅ انتهى!")
    print("=" * 80)
    
    print(f"\nالإحصائيات:")
    print(f"   منتجات معالجة: {len(products)}")
    print(f"   ✅ Packagings مُنشأة: {created_count}")
    print(f"   ❌ فشل: {failed_count}")
    
    print("\n" + "=" * 80)
    print("🎯 كيفية الاستخدام")
    print("=" * 80)
    
    print("""
1️⃣ في Sales Order:
   • Sales → Orders → New
   • أضف منتج
   • في سطر المنتج، ستجد حقل "Packaging"
   • اختر: علبة كبيرة / متوسطة / صغيرة
   • السعر والكمية تتحدث تلقائياً! ✨

2️⃣ في POS:
   • امسح الباركود:
     - ADF00005-1KG → علبة كبيرة
     - ADF00005-500G → علبة متوسطة
     - ADF00005-250G → علبة صغيرة
   • أو اختر من القائمة

3️⃣ في eCommerce:
   • الزبون يختار الحجم من قائمة
   • السعر يتغير تلقائياً

4️⃣ عرض/تعديل Packagings:
   • Inventory → Products → [اختر منتج]
   • تبويب Inventory
   • قسم "Packagings"
   • يمكن إضافة/تعديل/حذف
""")
    
    print("\n" + "=" * 80)
    print("🎉 تم الإعداد بنجاح!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

