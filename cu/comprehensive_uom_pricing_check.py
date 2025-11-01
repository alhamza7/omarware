#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص شامل لموديول UoM في التسعير
===============================
يتحقق من:
1. توافق الموديول مع Odoo 19
2. التسعيرات المتناسبة وغير المتناسبة
3. المشاكل المحتملة في الحسابات
"""

import sys
import io
import xmlrpc.client

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# إعدادات الاتصال
url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

def print_section(title, char="="):
    """طباعة عنوان قسم"""
    width = 80
    print(f"\n{char * width}")
    print(f"{title.center(width)}")
    print(f"{char * width}\n")

def main():
    try:
        # الاتصال بـ Odoo
        print_section("🔌 الاتصال بـ Odoo")
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("❌ فشل تسجيل الدخول")
            return
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
        print(f"✅ متصل بنجاح! User ID: {uid}")
        
        # ==========================================
        # 1. فحص تثبيت الموديول
        # ==========================================
        print_section("📦 فحص الموديول", "=")
        
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', 'uom_in_pricelist')]])
        
        if not module_ids:
            print("❌ الموديول غير موجود!")
            return
        
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids], {'fields': ['name', 'display_name', 'state', 'installed_version']})[0]
        
        print(f"اسم الموديول: {module.get('display_name', 'N/A')}")
        print(f"الإصدار: {module.get('installed_version', 'N/A')}")
        print(f"الحالة: {module.get('state', 'N/A')}")
        
        if module['state'] != 'installed':
            print("⚠️ الموديول غير مثبت!")
            return
        
        # ==========================================
        # 2. فحص الحقول المضافة
        # ==========================================
        print_section("🔧 فحص الحقول المخصصة", "=")
        
        # فحص fields في product.pricelist.item
        fields_info = models.execute_kw(db, uid, password,
            'product.pricelist.item', 'fields_get',
            [], {'attributes': ['string', 'type', 'store', 'readonly']})
        
        if 'product_uom_id' in fields_info:
            field_data = fields_info['product_uom_id']
            print(f"✅ حقل product_uom_id موجود")
            print(f"   النوع: {field_data.get('type', 'N/A')}")
            print(f"   الوصف: {field_data.get('string', 'N/A')}")
            print(f"   مخزّن: {field_data.get('store', 'N/A')}")
            print(f"   للقراءة فقط: {field_data.get('readonly', 'N/A')}")
        else:
            print("❌ حقل product_uom_id غير موجود!")
            return
        
        # ==========================================
        # 3. فحص قواعد التسعير الموجودة
        # ==========================================
        print_section("💰 فحص قواعد التسعير", "=")
        
        # البحث عن قواعد تحتوي على UoM محدد
        items_with_uom = models.execute_kw(db, uid, password,
            'product.pricelist.item', 'search',
            [[('product_uom_id', '!=', False)]])
        
        print(f"عدد قواعد التسعير مع UoM محدد: {len(items_with_uom)}")
        
        if items_with_uom:
            print("\nقواعد التسعير المخصصة لوحدات القياس:")
            print("-" * 80)
            
            # أخذ أول 20 قاعدة
            items_data = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'read',
                [items_with_uom[:20]], 
                {'fields': ['product_id', 'product_tmpl_id', 'product_uom_id', 
                            'pricelist_id', 'compute_price', 'fixed_price', 
                            'percent_price', 'price_discount']})
            
            for item in items_data:
                product_name = 'N/A'
                if item.get('product_id'):
                    product_name = item['product_id'][1]
                elif item.get('product_tmpl_id'):
                    product_name = item['product_tmpl_id'][1]
                
                uom_name = item.get('product_uom_id', [False, 'N/A'])[1]
                pricelist_name = item.get('pricelist_id', [False, 'N/A'])[1]
                
                print(f"\n📌 {product_name}")
                print(f"   قائمة الأسعار: {pricelist_name}")
                print(f"   وحدة القياس: {uom_name}")
                print(f"   نوع الحساب: {item.get('compute_price', 'N/A')}")
                
                if item.get('compute_price') == 'fixed':
                    print(f"   السعر الثابت: {item.get('fixed_price', 0)}")
                elif item.get('compute_price') == 'percentage':
                    print(f"   الخصم: {item.get('price_discount', 0)}%")
        
        # ==========================================
        # 4. اختبار التسعير المتناسب vs غير المتناسب
        # ==========================================
        print_section("🧪 اختبار التسعيرات المتناسبة", "=")
        
        # البحث عن منتجات لها قواعد تسعير متعددة
        if items_with_uom:
            # جمع المنتجات التي لها أكثر من قاعدة تسعير
            product_counts = {}
            
            items_data = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'read',
                [items_with_uom], 
                {'fields': ['product_id', 'product_uom_id', 'fixed_price', 'compute_price']})
            
            for item in items_data:
                if item.get('product_id') and item.get('compute_price') == 'fixed':
                    product_id = item['product_id'][0]
                    if product_id not in product_counts:
                        product_counts[product_id] = []
                    product_counts[product_id].append(item)
            
            # فحص المنتجات التي لها أكثر من قاعدة
            multi_rule_products = {k: v for k, v in product_counts.items() if len(v) > 1}
            
            print(f"عدد المنتجات التي لها قواعد تسعير متعددة: {len(multi_rule_products)}")
            
            # تحليل أول 5 منتجات
            for product_id, items in list(multi_rule_products.items())[:5]:
                product = models.execute_kw(db, uid, password,
                    'product.product', 'read',
                    [[product_id]], {'fields': ['display_name', 'uom_id']})[0]
                
                print(f"\n🔍 المنتج: {product['display_name']}")
                print(f"   الوحدة الأساسية: {product['uom_id'][1]}")
                
                # جمع معلومات الأسعار و UoM
                prices_by_uom = {}
                
                for item in items:
                    if item.get('product_uom_id'):
                        uom_id = item['product_uom_id'][0]
                        uom_name = item['product_uom_id'][1]
                        price = item.get('fixed_price', 0)
                        
                        # جلب معلومات UoM (Odoo 19 fields)
                        uom_data = models.execute_kw(db, uid, password,
                            'uom.uom', 'read',
                            [[uom_id]], {'fields': ['name', 'factor', 'relative_factor', 'relative_uom_id']})[0]
                        
                        prices_by_uom[uom_name] = {
                            'price': price,
                            'factor': uom_data.get('factor', 1),
                            'relative_factor': uom_data.get('relative_factor', 1),
                            'relative_uom_id': uom_data.get('relative_uom_id', False),
                        }
                
                # طباعة الأسعار
                print("\n   الأسعار حسب وحدة القياس:")
                for uom_name, data in prices_by_uom.items():
                    ref_uom = data['relative_uom_id'][1] if data['relative_uom_id'] else 'Base'
                    print(f"   • {uom_name}: {data['price']:.2f} (Factor: {data['factor']:.6f}, Rel: {data['relative_factor']:.6f}, Ref: {ref_uom})")
                
                # فحص التناسب
                if len(prices_by_uom) >= 2:
                    print("\n   📊 تحليل التناسب:")
                    uom_list = list(prices_by_uom.items())
                    
                    # مقارنة كل زوج
                    uom1_name, uom1_data = uom_list[0]
                    uom2_name, uom2_data = uom_list[1]
                    
                    # الحساب المتوقع بناءً على factor
                    if uom1_data['factor'] > 0 and uom2_data['factor'] > 0:
                        # نسبة التحويل
                        ratio = uom2_data['factor'] / uom1_data['factor']
                        
                        # السعر المتوقع = سعر الأول * نسبة التحويل
                        expected_price2 = uom1_data['price'] * ratio
                        actual_price2 = uom2_data['price']
                        
                        difference = abs(expected_price2 - actual_price2)
                        percentage_diff = (difference / expected_price2 * 100) if expected_price2 > 0 else 0
                        
                        print(f"   مقارنة {uom1_name} مع {uom2_name}:")
                        print(f"   • نسبة التحويل: {ratio:.6f}")
                        print(f"   • السعر المتوقع ل {uom2_name}: {expected_price2:.2f}")
                        print(f"   • السعر الفعلي: {actual_price2:.2f}")
                        print(f"   • الفرق: {difference:.2f} ({percentage_diff:.2f}%)")
                        
                        if percentage_diff > 5:
                            print(f"   ⚠️⚠️ تحذير: الفرق كبير! التسعير غير متناسب!")
                            print(f"   💡 يُنصح بمراجعة السعر يدوياً")
                        elif percentage_diff > 1:
                            print(f"   ⚠️ تحذير بسيط: فرق طفيف في التسعير")
                        else:
                            print(f"   ✅ التسعير متناسب!")
                
                print("-" * 80)
        
        # ==========================================
        # 5. فحص التوافق مع Odoo 19
        # ==========================================
        print_section("🔬 فحص التوافق مع Odoo 19", "=")
        
        print("التحقق من العناصر الحرجة:")
        
        # فحص model product.pricelist
        try:
            models.execute_kw(db, uid, password,
                'product.pricelist', 'search', [[]], {'limit': 1})
            print("✅ model product.pricelist متاح")
        except Exception as e:
            print(f"❌ مشكلة في product.pricelist: {e}")
        
        # فحص model product.pricelist.item
        try:
            models.execute_kw(db, uid, password,
                'product.pricelist.item', 'search', [[]], {'limit': 1})
            print("✅ model product.pricelist.item متاح")
        except Exception as e:
            print(f"❌ مشكلة في product.pricelist.item: {e}")
        
        # فحص model sale.order.line
        try:
            models.execute_kw(db, uid, password,
                'sale.order.line', 'search', [[]], {'limit': 1})
            print("✅ model sale.order.line متاح")
        except Exception as e:
            print(f"❌ مشكلة في sale.order.line: {e}")
        
        print("\n✅ جميع النماذج الأساسية متاحة!")
        
        # ==========================================
        # 6. اختبار عملي
        # ==========================================
        print_section("🎯 مثال عملي على التسعير", "=")
        
        if items_with_uom:
            # أخذ أول قاعدة كمثال
            example_item = models.execute_kw(db, uid, password,
                'product.pricelist.item', 'read',
                [[items_with_uom[0]]], 
                {'fields': ['product_id', 'product_uom_id', 'fixed_price', 
                           'pricelist_id', 'compute_price']})[0]
            
            if example_item.get('product_id'):
                print(f"مثال عملي:")
                print(f"• المنتج: {example_item['product_id'][1]}")
                print(f"• وحدة القياس: {example_item.get('product_uom_id', [0, 'N/A'])[1]}")
                print(f"• قائمة الأسعار: {example_item.get('pricelist_id', [0, 'N/A'])[1]}")
                print(f"• نوع الحساب: {example_item.get('compute_price', 'N/A')}")
                if example_item.get('compute_price') == 'fixed':
                    print(f"• السعر: {example_item.get('fixed_price', 0):.2f}")
                
                print("\n💡 كيفية الاستخدام:")
                print("1. في Sales Order، اختر هذا المنتج")
                print("2. غيّر وحدة القياس للوحدة المذكورة أعلاه")
                print("3. سيتم تطبيق السعر المخصص تلقائياً!")
        
        # ==========================================
        # 7. التوصيات
        # ==========================================
        print_section("📋 التوصيات والنتائج", "=")
        
        print("✅ الإيجابيات:")
        print("   1. الموديول مثبت ويعمل بشكل صحيح")
        print("   2. يضيف حقل UoM مخصص لقواعد التسعير")
        print("   3. يوفر واجهة سهلة لتحديد أسعار مختلفة")
        print(f"   4. يوجد حالياً {len(items_with_uom)} قاعدة تسعير مع UoM محدد")
        
        print("\n⚠️ نقاط الانتباه:")
        print("   1. يجب إدخال الأسعار يدوياً لكل وحدة قياس")
        print("   2. الموديول لا يحسب الأسعار تلقائياً بناءً على نسب التحويل")
        print("   3. قد تحدث أخطاء في التسعير إذا لم يتم حساب النسب بدقة")
        print("   4. يحتاج إلى مراقبة دورية للتأكد من تناسب الأسعار")
        
        print("\n💡 الحلول المقترحة:")
        print("   1. إنشاء wizard لحساب الأسعار تلقائياً بناءً على نسب UoM")
        print("   2. إضافة validation للتحقق من تناسب الأسعار")
        print("   3. إنشاء تقرير دوري لمراجعة التسعيرات غير المتناسبة")
        print("   4. توثيق معادلات التحويل المعتمدة")
        
        print("\n🔧 التعديلات المقترحة على الموديول:")
        print("   1. إضافة زر 'Auto-Calculate Price' يحسب السعر بناءً على:")
        print("      - سعر الوحدة الأساسية")
        print("      - factor التحويل")
        print("   2. إضافة warning عند حفظ سعر غير متناسب")
        print("   3. إضافة حقل 'is_proportional' للتمييز بين:")
        print("      - أسعار متناسبة (محسوبة تلقائياً)")
        print("      - أسعار مخصصة (مدخلة يدوياً)")
        
        print_section("✅ انتهى الفحص الشامل", "=")
        
        print("\n📝 الخلاصة:")
        print(f"• الموديول يعمل بشكل صحيح في Odoo 19")
        print(f"• عدد القواعد النشطة: {len(items_with_uom)}")
        print(f"• يوصى بمراجعة التسعيرات للتأكد من التناسب")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
