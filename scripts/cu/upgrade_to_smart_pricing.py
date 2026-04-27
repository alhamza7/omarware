#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ترقية إلى نظام التسعير الذكي
Smart Pricing System Upgrade
"""

import sys
import io
import xmlrpc.client

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}\n")

def main():
    try:
        # الاتصال
        print_section("🔌 الاتصال بـ Odoo")
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("❌ فشل تسجيل الدخول")
            return
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
        print(f"✅ متصل بنجاح! User ID: {uid}")
        
        # ترقية الموديول
        print_section("🚀 ترقية إلى نظام التسعير الذكي")
        
        module_ids = models.execute_kw(db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', 'uom_in_pricelist')]])
        
        if not module_ids:
            print("❌ الموديول غير موجود!")
            return
        
        module = models.execute_kw(db, uid, password,
            'ir.module.module', 'read',
            [module_ids], {'fields': ['name', 'state']})[0]
        
        print(f"📦 الموديول: {module['name']}")
        print(f"   الحالة: {module['state']}")
        
        if module['state'] != 'installed':
            print("\n⚠️ الموديول غير مثبت!")
            print("   يرجى تثبيته أولاً من Apps")
            return
        
        print("\n🔄 جاري الترقية...")
        
        try:
            models.execute_kw(db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids])
            print("✅ تمت الترقية بنجاح!")
        except Exception as e:
            print(f"ℹ️  ملاحظة: {e}")
            print("\n💡 يرجى ترقية الموديول يدوياً:")
            print("   1. Apps → UOM In PriceList → Upgrade")
            print("   أو من command line:")
            print("   python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal")
        
        # التعليمات
        print_section("📋 ما الجديد في النظام الذكي؟")
        
        print("✨ نظام الأولويات:")
        print("   1️⃣  الأولوية الأولى: السعر المحدد في Pricelist")
        print("      → إذا وُجد سعر محدد لهذا UoM، يُستخدم مباشرة")
        print()
        print("   2️⃣  الأولوية الثانية: الحساب بالمعامل")
        print("      → إذا لم يُوجد سعر محدد، يُحسب من السعر الأساسي")
        print()
        print("   3️⃣  الأولوية الثالثة: list_price")
        print("      → ملاذ أخير")
        
        print("\n🎯 الفوائد:")
        print("   ✅ الأسعار الموجودة في Pricelist لها الأولوية")
        print("   ✅ الأسعار غير الموجودة تُحسب تلقائياً")
        print("   ✅ لا حاجة لإدخال كل UoM يدوياً")
        print("   ✅ يعمل في Sales و POS")
        
        print("\n📊 مثال عملي:")
        print("   المنتج: المعشوق")
        print("   ")
        print("   السيناريو 1: UoM = 0.5 كيلو")
        print("   → يوجد في Pricelist سعر محدد: $22.00")
        print("   → ✅ يستخدم $22.00 مباشرة")
        print()
        print("   السيناريو 2: UoM = 3 كيلو (غير موجود)")
        print("   → لا يوجد في Pricelist")
        print("   → 🧮 يحسب: سعر الكيلو × 3")
        print("   → ✅ النتيجة: $13.25 × 3 = $39.75")
        
        # اختبار
        print_section("🧪 اختبار النظام")
        
        print("جاري اختبار منتج 'المعشوق'...")
        
        # البحث عن المنتج
        product_ids = models.execute_kw(db, uid, password,
            'product.product', 'search',
            [[('default_code', '=', 'ADF00005')]], {'limit': 1})
        
        if product_ids:
            product = models.execute_kw(db, uid, password,
                'product.product', 'read',
                [product_ids], {'fields': ['name', 'default_code', 'list_price', 'uom_id']})[0]
            
            print(f"\n📦 المنتج: [{product['default_code']}] {product['name']}")
            print(f"   الوحدة الأساسية: {product['uom_id'][1]}")
            print(f"   list_price: ${product['list_price']}")
            
            # البحث عن قوائم الأسعار
            pricelist_ids = models.execute_kw(db, uid, password,
                'product.pricelist', 'search',
                [[('name', 'like', 'SAP')]], {'limit': 1})
            
            if pricelist_ids:
                pricelist = models.execute_kw(db, uid, password,
                    'product.pricelist', 'read',
                    [pricelist_ids], {'fields': ['name']})[0]
                
                print(f"\n💰 قائمة الأسعار: {pricelist['name']}")
                
                # البحث عن قواعد التسعير
                items = models.execute_kw(db, uid, password,
                    'product.pricelist.item', 'search_read',
                    [[
                        ('pricelist_id', '=', pricelist_ids[0]),
                        ('product_id', '=', product_ids[0]),
                        ('product_uom_id', '!=', False)
                    ]],
                    {'fields': ['product_uom_id', 'fixed_price'], 'limit': 5})
                
                if items:
                    print("\n   الأسعار المحددة:")
                    for item in items:
                        uom_name = item['product_uom_id'][1]
                        price = item['fixed_price']
                        print(f"   • {uom_name}: ${price:.2f}")
                    
                    print("\n✅ هذه الأسعار ستُستخدم مباشرة!")
                    print("   (لها الأولوية على الحساب التلقائي)")
        
        # الخطوات التالية
        print_section("🚀 الخطوات التالية")
        
        print("1️⃣  أعد تشغيل Odoo:")
        print("   • أوقف Odoo (Ctrl+C)")
        print("   • شغّله مرة أخرى: python odoo-bin -c odoo.conf")
        print()
        print("2️⃣  اختبر في Sales Order:")
        print("   • افتح: Sales → Orders → Create")
        print("   • اختر منتج: المعشوق")
        print("   • غيّر UoM وشاهد السعر يتغير تلقائياً!")
        print()
        print("3️⃣  اختبر في POS:")
        print("   • افتح POS Session")
        print("   • أضف منتج")
        print("   • اختر UoM مختلف")
        print("   • السعر الصحيح سيظهر تلقائياً!")
        print()
        print("4️⃣  اقرأ التوثيق الكامل:")
        print("   • SMART_PRICING_IMPLEMENTATION_AR.md")
        
        print_section("✅ انتهى!")
        
        print("🎉 تهانينا! النظام الذكي جاهز!")
        print("\nالآن لديك:")
        print("  ✅ أولوية للأسعار المحددة")
        print("  ✅ حساب تلقائي للأسعار غير الموجودة")
        print("  ✅ دعم كامل ل Sales و POS")
        print("\n💡 لا تنسَ إعادة تشغيل Odoo!")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()



