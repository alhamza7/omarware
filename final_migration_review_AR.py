#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Migration Review - Arabic Report"""

print("=" * 80)
print("تقرير شامل لحالة نظام SAP Migration")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if backend:
    print(f"\n🔌 Backend: {backend.name}")
    print(f"   Status: {'✅ Active' if backend.active else '❌ Inactive'}")
    
    # ========== Products Analysis ==========
    print("\n" + "=" * 80)
    print("📦 تحليل المنتجات")
    print("=" * 80)
    
    all_products = env['product.product'].search([])
    sap_products = env['product.product'].search([('default_code', '!=', False)])
    
    print(f"\nإجمالي المنتجات في النظام: {len(all_products)}")
    print(f"منتجات SAP (مع كود): {len(sap_products)}")
    
    # Get products created in last migration
    recent_products = env['product.product'].search(
        [('create_date', '>=', '2025-10-22 00:00:00')],
        order='create_date desc'
    )
    print(f"منتجات تم إنشاؤها اليوم: {len(recent_products)}")
    
    # ========== Extended Info Analysis ==========
    print("\n" + "=" * 80)
    print("📝 تحليل البيانات الموسعة (Extended Info)")
    print("=" * 80)
    
    extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
    print(f"\nإجمالي سجلات Extended Info: {len(extended)}")
    
    # Count products with extended info
    products_with_ext = extended.mapped('product_id')
    unique_products = len(set(products_with_ext.ids))
    print(f"منتجات لديها Extended Info: {unique_products}")
    
    # Check duplicates
    duplicates = len(extended) - unique_products
    if duplicates > 0:
        print(f"⚠️ سجلات مكررة: {duplicates}")
    
    # ========== UoM Analysis ==========
    print("\n" + "=" * 80)
    print("📏 تحليل وحدات القياس (UoM)")
    print("=" * 80)
    
    uoms = env['sap.uom.sync'].search([('backend_id', '=', backend.id)])
    successful_uoms = uoms.filtered(lambda u: u.sync_status == 'success')
    
    print(f"\nإجمالي وحدات القياس: {len(uoms)}")
    print(f"وحدات ناجحة: {len(successful_uoms)}")
    
    # ========== Pricelists Analysis ==========
    print("\n" + "=" * 80)
    print("💰 تحليل قوائم الأسعار (Pricelists)")
    print("=" * 80)
    
    price_syncs = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
    print(f"\nسجلات الأسعار: {len(price_syncs)}")
    
    # ========== Warehouse Analysis ==========
    print("\n" + "=" * 80)
    print("🏭 تحليل معلومات المخازن")
    print("=" * 80)
    
    warehouse_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
    print(f"\nسجلات المخازن: {len(warehouse_info)}")
    
    # ========== Migration Wizard Status ==========
    print("\n" + "=" * 80)
    print("⚙️ حالة آخر عملية Migration")
    print("=" * 80)
    
    wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)
    if wizard:
        status_icon = {
            'draft': '📝',
            'running': '⏳',
            'done': '✅',
            'error': '❌'
        }.get(wizard.state, '❓')
        
        print(f"\n{status_icon} الحالة: {wizard.state}")
        print(f"\n📊 الإحصائيات:")
        print(f"   • وحدات القياس: {wizard.total_uom_groups}")
        print(f"   • المنتجات: {wizard.total_products}")
        print(f"   • قوائم الأسعار: {wizard.total_pricelists}")
        print(f"   • سجلات الأسعار: {wizard.total_prices}")
        print(f"   • سجلات المخازن: {wizard.total_warehouses}")
        print(f"   • الأخطاء: {wizard.errors_count}")
        
        if wizard.start_time and wizard.end_time:
            duration_minutes = wizard.duration_seconds // 60
            print(f"\n⏱️ المدة: {duration_minutes} دقيقة ({wizard.duration_seconds} ثانية)")
            print(f"   بدأت: {wizard.start_time}")
            print(f"   انتهت: {wizard.end_time}")
    
    # ========== Summary & Issues ==========
    print("\n" + "=" * 80)
    print("📋 الملخص والمشاكل")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # Check issues
    if len(extended) > len(sap_products) * 2:
        issues.append(f"⚠️ عدد Extended Info ({len(extended)}) أكبر بكثير من المنتجات ({len(sap_products)})")
    
    if len(price_syncs) == 0 and wizard and wizard.total_prices == 0:
        warnings.append("⚠️ لم يتم استيراد أي أسعار")
    
    if len(warehouse_info) == 0 and wizard and wizard.total_warehouses == 0:
        warnings.append("⚠️ لم يتم استيراد معلومات المخازن")
    
    if duplicates > 1000:
        issues.append(f"⚠️ يوجد عدد كبير من السجلات المكررة: {duplicates}")
    
    if issues:
        print("\n❌ مشاكل يجب حلها:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if warnings:
        print("\n⚠️ تحذيرات:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not issues and not warnings:
        print("\n✅ لا توجد مشاكل كبيرة")
    
    # ========== Recommendations ==========
    print("\n" + "=" * 80)
    print("💡 التوصيات")
    print("=" * 80)
    
    print("""
الخطوات المقترحة:

1. تنظيف البيانات المكررة:
   • احذف سجلات Extended Info المكررة
   • قم بفحص المنتجات المستوردة للتأكد من عدم التكرار

2. استكمال استيراد البيانات:
   • قم بتفعيل Stage 3 (Pricelists) إذا كنت تحتاجها
   • قم بتفعيل Stage 4 (Warehouse Info) إذا كنت تحتاجها

3. مراجعة السجلات (Logs):
   • افحص SAP Sync Logs للأخطاء
   • راجع Odoo logs (odoo.log) للمشاكل التقنية

4. اختبار الاتصال:
   • تأكد من أن SAP Backend متصل بشكل صحيح
   • اختبر استيراد منتج واحد للتأكد من الاتصال
""")
    
    # ========== Error Logs from Latest Migration ==========
    if wizard and wizard.migration_log:
        print("\n" + "=" * 80)
        print("📜 سجل آخر عملية Migration")
        print("=" * 80)
        
        # Show last 30 lines
        log_lines = wizard.migration_log.split('\n')
        if len(log_lines) > 30:
            print("\n... (showing last 30 lines) ...\n")
            print('\n'.join(log_lines[-30:]))
        else:
            print(f"\n{wizard.migration_log}")

env.cr.commit()





