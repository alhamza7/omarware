#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تطبيق سعر الصرف على الفواتير
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def test_exchange_rate_on_invoices():
    """اختبار سعر الصرف على أنواع مختلفة من المستندات"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    # الحصول على اسم قاعدة البيانات
    db_name = odoo.tools.config.get('db_name', '')
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else ''
    
    if not db_name:
        dbfilter = odoo.tools.config.get('dbfilter', '')
        if dbfilter:
            import re
            match = re.match(r'\^?(\w+).*\$?', dbfilter)
            if match:
                db_name = match.group(1)
    
    if not db_name:
        db_name = 'lugal'
    
    print(f"\n{'='*70}")
    print(f"اختبار سعر الصرف على الفواتير - قاعدة البيانات: {db_name}")
    print(f"{'='*70}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. الحصول على العملات
            print("1. الحصول على العملات...")
            
            iqd = env['res.currency'].search([('name', '=', 'IQD')], limit=1)
            usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
            if not iqd or not usd:
                print("   ❌ العملات غير موجودة!")
                return
            
            print(f"   ✅ IQD (ID: {iqd.id})")
            print(f"   ✅ USD (ID: {usd.id})")
            
            # 2. عرض سعر الصرف الحالي
            print(f"\n2. سعر الصرف الحالي:")
            
            today = datetime.now().date()
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   التاريخ: {latest_rate.name}")
                print(f"   السعر: 1 USD = {current_rate:.2f} IQD")
            else:
                print("   ⚠️  لا يوجد سعر صرف!")
                return
            
            # 3. اختبار التحويل
            print(f"\n3. اختبار التحويل:")
            
            test_amounts = [100, 500, 1000, 50]
            
            for amount_usd in test_amounts:
                # استخدام دالة التحويل في Odoo
                amount_iqd = usd._convert(
                    amount_usd, 
                    iqd, 
                    env.company, 
                    today
                )
                print(f"   {amount_usd:>6.2f} USD = {amount_iqd:>10,.2f} IQD")
            
            # 4. التحقق من الفواتير الموجودة
            print(f"\n4. التحقق من الفواتير الموجودة بـ USD:")
            
            invoices = env['account.move'].search([
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('currency_id', '=', usd.id),
                ('state', '!=', 'cancel'),
            ], order='date desc', limit=5)
            
            if invoices:
                print(f"   وُجد {len(invoices)} فاتورة بـ USD (آخر 5):")
                print("")
                print(f"   {'التاريخ':<12} {'الحالة':<10} {'USD':<15} {'IQD':<15} {'السعر':<10}")
                print(f"   {'-'*70}")
                
                for inv in invoices:
                    status = {
                        'draft': 'مسودة',
                        'posted': 'محفوظة',
                        'cancel': 'ملغية',
                    }.get(inv.state, inv.state)
                    
                    amount_usd = inv.amount_total
                    amount_iqd = inv.amount_total_in_currency_signed
                    used_rate = amount_iqd / amount_usd if amount_usd != 0 else 0
                    
                    print(f"   {str(inv.date):<12} {status:<10} {amount_usd:>13,.2f} {amount_iqd:>13,.2f} {used_rate:>8.2f}")
            else:
                print(f"   ℹ️  لا توجد فواتير بـ USD")
            
            # 5. التحقق من أوامر البيع
            print(f"\n5. التحقق من أوامر البيع بـ USD:")
            
            sale_orders = env['sale.order'].search([
                ('currency_id', '=', usd.id),
                ('state', '!=', 'cancel'),
            ], order='date_order desc', limit=5)
            
            if sale_orders:
                print(f"   وُجد {len(sale_orders)} أمر بيع بـ USD (آخر 5):")
                print("")
                print(f"   {'التاريخ':<12} {'الحالة':<12} {'USD':<15} {'السعر المستخدم':<15}")
                print(f"   {'-'*70}")
                
                for order in sale_orders:
                    status = {
                        'draft': 'عرض سعر',
                        'sent': 'مُرسل',
                        'sale': 'أمر بيع',
                        'done': 'مكتمل',
                        'cancel': 'ملغي',
                    }.get(order.state, order.state)
                    
                    # الحصول على سعر الصرف المستخدم
                    order_date = order.date_order.date() if order.date_order else today
                    rate_on_order_date = env['res.currency.rate'].search([
                        ('currency_id', '=', usd.id),
                        ('name', '<=', order_date),
                    ], order='name desc', limit=1)
                    
                    if rate_on_order_date:
                        used_rate = 1.0 / rate_on_order_date.rate
                    else:
                        used_rate = 0
                    
                    print(f"   {str(order_date):<12} {status:<12} {order.amount_total:>13,.2f} {used_rate:>13.2f}")
            else:
                print(f"   ℹ️  لا توجد أوامر بيع بـ USD")
            
            # 6. شرح آلية التطبيق
            print(f"\n{'='*70}")
            print("📋 شرح آلية التطبيق:")
            print(f"{'='*70}\n")
            
            print("✅ المستندات الجديدة (بعد اليوم):")
            print("   - تستخدم سعر الصرف الحالي: 1 USD = {:.2f} IQD".format(current_rate))
            print("   - يُطبق تلقائياً على:")
            print("     • فواتير المبيعات الجديدة")
            print("     • فواتير الشراء الجديدة")
            print("     • أوامر البيع الجديدة")
            print("     • عروض الأسعار الجديدة")
            print("")
            
            print("⚠️  المستندات القديمة (قبل اليوم):")
            print("   - تحتفظ بسعر الصرف وقت إنشائها")
            print("   - لن تتأثر بالتحديث الجديد")
            print("   - إذا كانت 'مسودة'، يمكن إعادة حسابها")
            print("")
            
            print("🔄 إعادة حساب المسودات:")
            print("   1. افتح الفاتورة/الأمر")
            print("   2. إذا كانت الحالة 'Draft' (مسودة)")
            print("   3. اضغط على 'Recompute' أو عدّل أي حقل")
            print("   4. سيُطبق السعر الجديد")
            print("")
            
            # 7. سجل أسعار الصرف التاريخية
            print(f"\n7. سجل أسعار الصرف (آخر 10 تحديثات):")
            
            all_rates = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=10)
            
            if all_rates:
                print("")
                print(f"   {'التاريخ':<15} {'السعر (IQD لكل USD)':<25} {'Rate في DB':<15}")
                print(f"   {'-'*70}")
                
                for rate in all_rates:
                    actual_rate = 1.0 / rate.rate if rate.rate != 0 else 0
                    print(f"   {str(rate.name):<15} {actual_rate:>23,.2f} {rate.rate:>13.8f}")
            
            print(f"\n{'='*70}")
            print("✅ انتهى الاختبار")
            print(f"{'='*70}\n")
            
            # النصائح النهائية
            print("💡 نصائح:")
            print("")
            print("1. لتطبيق السعر على مسودة فاتورة:")
            print("   - افتح الفاتورة")
            print("   - عدّل أي حقل (مثل الوصف)")
            print("   - احفظ → سيُطبق السعر الجديد")
            print("")
            print("2. لإعادة حساب جميع المسودات:")
            print("   - Accounting → Customers → Invoices")
            print("   - فلتر: Status = Draft")
            print("   - اختر الكل → Action → Recompute Taxes")
            print("")
            print("3. لإنشاء فاتورة بسعر قديم:")
            print("   - أنشئ الفاتورة")
            print("   - غيّر تاريخ الفاتورة إلى تاريخ قديم")
            print("   - سيستخدم سعر ذلك التاريخ")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    test_exchange_rate_on_invoices()
