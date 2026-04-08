# -*- coding: utf-8 -*-
"""
مثال عملي لاستيراد البيانات من SAP إلى Odoo

استخدم هذا الكود من Python Shell في Odoo:
    من القائمة: Settings > Technical > Python Code
    أو من Terminal: odoo-bin shell -d your_database
"""

def example_1_simple_import(env):
    """
    مثال 1: استيراد بسيط للعملاء
    """
    print("=" * 60)
    print("مثال 1: استيراد العملاء من SAP")
    print("=" * 60)
    
    # الحصول على Backend
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    if not backend:
        print("❌ لم يتم العثور على SAP Backend نشط")
        return
    
    print(f"✅ Backend: {backend.name}")
    
    # استيراد العملاء
    print("\n📥 جاري استيراد العملاء...")
    result = env['sap.res.partner'].import_batch(backend)
    
    print(f"\n✅ تم الاستيراد!")
    print(f"   - تم استيراد: {result.get('imported', 0)} عميل")
    print(f"   - أخطاء: {result.get('errors', 0)}")
    
    # عرض العملاء
    partners = env['res.partner'].search([('ref', 'like', 'C%')], limit=5)
    print(f"\n👥 عينة من العملاء المستوردين:")
    for partner in partners:
        print(f"   - {partner.name} (SAP: {partner.ref})")


def example_2_import_specific_customer(env):
    """
    مثال 2: استيراد عميل محدد
    """
    print("=" * 60)
    print("مثال 2: استيراد عميل محدد")
    print("=" * 60)
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    # استيراد عميل محدد بـ CardCode
    card_code = 'C00001'  # غيّر هذا للعميل الذي تريده
    
    print(f"\n📥 استيراد العميل: {card_code}")
    
    try:
        binding = env['sap.res.partner'].import_record(backend, card_code)
        partner = binding.odoo_id
        
        print(f"\n✅ تم الاستيراد بنجاح!")
        print(f"   الاسم: {partner.name}")
        print(f"   البريد: {partner.email or 'غير متوفر'}")
        print(f"   الهاتف: {partner.phone or 'غير متوفر'}")
        print(f"   SAP CardCode: {binding.external_id}")
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")


def example_3_import_with_filter(env):
    """
    مثال 3: استيراد مع فلتر
    """
    print("=" * 60)
    print("مثال 3: استيراد العملاء النشطين فقط")
    print("=" * 60)
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    # استيراد العملاء النشطين فقط
    filters = "Valid eq 'Y'"
    
    print(f"\n📥 استيراد العملاء النشطين...")
    print(f"   Filter: {filters}")
    
    result = env['sap.res.partner'].import_batch(backend, filters=filters)
    
    print(f"\n✅ تم!")
    print(f"   - مستورد: {result.get('imported', 0)}")


def example_4_import_products(env):
    """
    مثال 4: استيراد المنتجات
    """
    print("=" * 60)
    print("مثال 4: استيراد المنتجات من SAP")
    print("=" * 60)
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    print("\n📥 استيراد المنتجات...")
    result = env['sap.product.product'].import_batch(backend)
    
    print(f"\n✅ تم!")
    print(f"   - مستورد: {result.get('imported', 0)}")
    
    # عرض عينة
    products = env['product.product'].search([
        ('default_code', '!=', False)
    ], limit=5)
    
    print(f"\n📦 عينة من المنتجات:")
    for product in products:
        print(f"   - {product.name}")
        print(f"     الكود: {product.default_code}")
        print(f"     السعر: {product.list_price}")


def example_5_check_imported_data(env):
    """
    مثال 5: التحقق من البيانات المستوردة
    """
    print("=" * 60)
    print("مثال 5: التحقق من البيانات المستوردة")
    print("=" * 60)
    
    # عد العملاء
    partner_count = env['res.partner'].search_count([('ref', '!=', False)])
    binding_count = env['sap.res.partner'].search_count([])
    
    print(f"\n📊 الإحصائيات:")
    print(f"   - عملاء في res.partner: {partner_count}")
    print(f"   - bindings في sap.res.partner: {binding_count}")
    
    # التحقق من سلامة البيانات
    bindings_without_partner = env['sap.res.partner'].search([
        ('odoo_id', '=', False)
    ])
    
    if bindings_without_partner:
        print(f"\n⚠️  تحذير: {len(bindings_without_partner)} binding بدون odoo_id")
    else:
        print(f"\n✅ جميع bindings لديها odoo_id")
    
    # عرض عينة مع التفاصيل
    print(f"\n📋 عينة من البيانات:")
    bindings = env['sap.res.partner'].search([], limit=3)
    
    for i, binding in enumerate(bindings, 1):
        partner = binding.odoo_id
        print(f"\n   {i}. {partner.name if partner else 'N/A'}")
        print(f"      SAP CardCode: {binding.external_id}")
        print(f"      Odoo ID: {partner.id if partner else 'N/A'}")
        print(f"      Email: {binding.email or 'N/A'}")
        print(f"      Phone: {binding.phone or 'N/A'}")


def example_6_incremental_sync(env):
    """
    مثال 6: المزامنة التدريجية
    """
    print("=" * 60)
    print("مثال 6: المزامنة التدريجية (Incremental Sync)")
    print("=" * 60)
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    print("\n📅 آخر مزامنة:")
    print(f"   - العملاء: {backend.last_partner_sync or 'لم يتم بعد'}")
    print(f"   - المنتجات: {backend.last_product_sync or 'لم يتم بعد'}")
    
    # مزامنة العملاء المعدلين فقط
    print("\n🔄 مزامنة العملاء المعدلين...")
    result = backend.sync_incremental_partners()
    
    print(f"✅ تمت المزامنة التدريجية")


def example_7_error_handling(env):
    """
    مثال 7: معالجة الأخطاء
    """
    print("=" * 60)
    print("مثال 7: معالجة الأخطاء")
    print("=" * 60)
    
    # البحث عن سجلات بها أخطاء
    failed_bindings = env['sap.res.partner'].search([
        ('sync_error', '!=', False)
    ])
    
    if not failed_bindings:
        print("\n✅ لا توجد أخطاء في المزامنة")
        return
    
    print(f"\n⚠️  وجد {len(failed_bindings)} سجل به أخطاء:")
    
    for binding in failed_bindings[:5]:
        print(f"\n   - SAP CardCode: {binding.external_id}")
        print(f"     الخطأ: {binding.sync_error}")
        print(f"     عدد المحاولات: {binding.sync_retry_count}")


def run_all_examples(env):
    """
    تشغيل جميع الأمثلة
    """
    print("\n" + "=" * 60)
    print("🚀 تشغيل جميع الأمثلة")
    print("=" * 60 + "\n")
    
    examples = [
        ("استيراد بسيط", example_1_simple_import),
        ("استيراد عميل محدد", example_2_import_specific_customer),
        ("استيراد مع فلتر", example_3_import_with_filter),
        ("استيراد المنتجات", example_4_import_products),
        ("التحقق من البيانات", example_5_check_imported_data),
        ("المزامنة التدريجية", example_6_incremental_sync),
        ("معالجة الأخطاء", example_7_error_handling),
    ]
    
    for name, func in examples:
        print(f"\n{'='*60}")
        print(f"▶️  {name}")
        print('='*60)
        try:
            func(env)
        except Exception as e:
            print(f"❌ خطأ: {str(e)}")
        
        input("\nاضغط Enter للمتابعة...")


# للاستخدام من Odoo Shell:
# 
# from odoo.addons.sap_integration.examples import import_example
# 
# # تشغيل مثال واحد:
# import_example.example_1_simple_import(env)
# 
# # تشغيل جميع الأمثلة:
# import_example.run_all_examples(env)

