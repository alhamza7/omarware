#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إنشاء أمثلة لأسعار UoM للاختبار
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("إنشاء أمثلة لأسعار UoM")
print("=" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    print(f"✅ متصل\n")
    
    # 1. البحث عن منتج للاختبار
    print("1️⃣ البحث عن منتج للاختبار...")
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['default_code', '=', 'ADF00005']]],
        {'fields': ['id', 'name', 'default_code', 'product_tmpl_id', 'uom_id'], 'limit': 1})
    
    if not products:
        print("⚠️ لم يتم العثور على المنتج ADF00005")
        print("سأستخدم أول منتج متاح...\n")
        products = models.execute_kw(db, uid, password,
            'product.product', 'search_read', [[]],
            {'fields': ['id', 'name', 'default_code', 'product_tmpl_id', 'uom_id'], 'limit': 1})
    
    if not products:
        print("❌ لا توجد منتجات!")
        exit(1)
    
    product = products[0]
    product_tmpl_id = product['product_tmpl_id'][0]
    base_uom = product.get('uom_id', [False, 'كغم'])[1]
    
    print(f"✅ المنتج: {product['name']} ({product['default_code']})")
    print(f"   الوحدة الأساسية: {base_uom}\n")
    
    # 2. البحث عن وحدات قياس
    print("2️⃣ البحث عن وحدات القياس...")
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'search_read',
        [[['active', '=', True]]],
        {'fields': ['id', 'name', 'factor'], 'limit': 20})
    
    # فلترة الوحدات المهمة
    important_uoms = []
    for uom in uoms:
        factor = uom.get('factor', 1.0)
        if factor in [0.25, 0.5, 1.0]:
            important_uoms.append(uom)
            print(f"   📏 {uom['name']} (factor: {factor})")
    
    if len(important_uoms) < 2:
        print("\n⚠️ لا توجد وحدات قياس متنوعة كافية")
        print("   سنستخدم ما هو متاح\n")
    
    # 3. البحث عن SAP Price List 1
    print("\n3️⃣ البحث عن SAP Price List 1...")
    pricelists = models.execute_kw(db, uid, password,
        'product.pricelist', 'search_read',
        [[['name', 'ilike', 'SAP%Price%List%1']]],
        {'fields': ['id', 'name'], 'limit': 1})
    
    if not pricelists:
        print("⚠️ لم يتم العثور على SAP Price List 1")
        # استخدام أول pricelist
        pricelists = models.execute_kw(db, uid, password,
            'product.pricelist', 'search_read', [[]],
            {'fields': ['id', 'name'], 'limit': 1})
    
    if not pricelists:
        print("❌ لا توجد pricelists!")
        exit(1)
    
    pricelist = pricelists[0]
    print(f"✅ Pricelist: {pricelist['name']}\n")
    
    # 4. إنشاء أمثلة لأسعار UoM
    print("=" * 80)
    print("4️⃣ إنشاء أمثلة لأسعار UoM")
    print("=" * 80 + "\n")
    
    created_count = 0
    
    # مثال 1: السعر الأساسي (1.0)
    base_price = 40.0
    if len(important_uoms) > 0:
        base_uom = [u for u in important_uoms if u['factor'] == 1.0][0] if any(u['factor'] == 1.0 for u in important_uoms) else important_uoms[0]
        
        try:
            item_id = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'create',
                [{
                    'pricelist_id': pricelist['id'],
                    'applied_on': '0_product_variant',
                    'product_tmpl_id': product_tmpl_id,
                    'product_id': product['id'],  # إضافة product_id
                    'product_uom_id': base_uom['id'],
                    'fixed_price': base_price,
                    'min_quantity': 1,
                }])
            
            print(f"✅ أُنشئ: {base_uom['name']} → ${base_price}")
            created_count += 1
        except Exception as e:
            print(f"⚠️ فشل: {str(e)[:100]}")
    
    # مثال 2: نصف الوحدة (0.5)
    if len(important_uoms) > 1:
        half_uom = [u for u in important_uoms if u['factor'] == 0.5][0] if any(u['factor'] == 0.5 for u in important_uoms) else None
        
        if half_uom:
            try:
                item_id = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'create',
                    [{
                        'pricelist_id': pricelist['id'],
                        'applied_on': '0_product_variant',
                        'product_tmpl_id': product_tmpl_id,
                        'product_id': product['id'],  # إضافة product_id
                        'product_uom_id': half_uom['id'],
                        'fixed_price': 22.0,  # سعر مستقل (ليس $20)
                        'min_quantity': 1,
                    }])
                
                print(f"✅ أُنشئ: {half_uom['name']} → $22.00")
                created_count += 1
            except Exception as e:
                print(f"⚠️ فشل: {str(e)[:100]}")
    
    # مثال 3: ربع الوحدة (0.25)
    if len(important_uoms) > 2:
        quarter_uom = [u for u in important_uoms if u['factor'] == 0.25][0] if any(u['factor'] == 0.25 for u in important_uoms) else None
        
        if quarter_uom:
            try:
                item_id = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'create',
                    [{
                        'pricelist_id': pricelist['id'],
                        'applied_on': '0_product_variant',
                        'product_tmpl_id': product_tmpl_id,
                        'product_id': product['id'],  # إضافة product_id
                        'product_uom_id': quarter_uom['id'],
                        'fixed_price': 12.0,  # سعر مستقل (ليس $10)
                        'min_quantity': 1,
                    }])
                
                print(f"✅ أُنشئ: {quarter_uom['name']} → $12.00")
                created_count += 1
            except Exception as e:
                print(f"⚠️ فشل: {str(e)[:100]}")
    
    print(f"\n✅ تم إنشاء {created_count} قاعدة سعر\n")
    
    print("=" * 80)
    print("🧪 اختبر الآن!")
    print("=" * 80)
    print(f"""
المنتج التجريبي: {product['name']}

الخطوات:
1. افتح Odoo → Sales → Orders → New
2. اختر Pricelist: {pricelist['name']}
3. أضف المنتج: {product['name']}
4. غيّر UoM في سطر المنتج:
   • كيلو → السعر يجب أن يكون $40
   • نصف كيلو → السعر يجب أن يكون $22 ✨
   • ربع كيلو → السعر يجب أن يكون $12 ✨

إذا تغير السعر → 🎉 نجح!
إذا لم يتغير → نحتاج تعديلات إضافية
""")

except Exception as e:
    print(f"❌ خطأ: {e}")

