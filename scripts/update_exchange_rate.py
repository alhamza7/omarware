#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث سعر الصرف في Odoo
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def update_exchange_rate(new_rate=1510.0):
    """تحديث سعر الصرف"""
    
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
    
    print(f"\n{'='*60}")
    print(f"تحديث سعر الصرف - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من العملات
            print("1. التحقق من العملات...")
            
            # العملة الأساسية (IQD)
            iqd = env['res.currency'].search([('name', '=', 'IQD')], limit=1)
            if not iqd:
                print("   ⚠️  عملة IQD غير موجودة! جاري الإنشاء...")
                iqd = env['res.currency'].create({
                    'name': 'IQD',
                    'symbol': 'د.ع',
                    'rounding': 0.01,
                    'position': 'after',
                    'active': True,
                })
                print(f"   ✅ تم إنشاء عملة IQD (ID: {iqd.id})")
            else:
                print(f"   ✅ عملة IQD موجودة (ID: {iqd.id})")
            
            # العملة الثانوية (USD)
            usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
            if not usd:
                print("   ⚠️  عملة USD غير موجودة!")
                usd = env.ref('base.USD', raise_if_not_found=False)
            
            if usd:
                print(f"   ✅ عملة USD موجودة (ID: {usd.id})")
            else:
                print("   ❌ عملة USD غير موجودة!")
                return
            
            # 2. عرض سعر الصرف الحالي
            print(f"\n2. سعر الصرف الحالي...")
            
            # البحث عن آخر سعر صرف
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   التاريخ: {latest_rate.name}")
                print(f"   السعر: 1 USD = {current_rate:.2f} IQD")
                print(f"   (rate في قاعدة البيانات: {latest_rate.rate})")
            else:
                print("   ⚠️  لا يوجد سعر صرف محدد!")
            
            # 3. تحديث سعر الصرف
            print(f"\n3. تحديث سعر الصرف إلى: 1 USD = {new_rate} IQD...")
            
            today = datetime.now().date()
            
            # حذف أي سعر صرف لنفس اليوم
            existing_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
                ('name', '=', today),
            ])
            
            if existing_rate:
                print(f"   ⚠️  يوجد سعر صرف لليوم، سيتم تحديثه...")
                # في Odoo، rate = 1 / السعر الفعلي
                # إذا كان 1 USD = 1510 IQD، فإن rate = 1/1510
                odoo_rate = 1.0 / new_rate
                existing_rate.write({'rate': odoo_rate})
                print(f"   ✅ تم تحديث السعر")
            else:
                print(f"   إنشاء سعر صرف جديد...")
                odoo_rate = 1.0 / new_rate
                env['res.currency.rate'].create({
                    'currency_id': usd.id,
                    'name': today,
                    'rate': odoo_rate,
                    'company_id': env.company.id,
                })
                print(f"   ✅ تم إنشاء السعر الجديد")
            
            # 4. تفعيل إعدادات العملات المتعددة
            print(f"\n4. تفعيل إعدادات العملات...")
            
            # تفعيل multi-currency في الشركة
            company = env.company
            if not company.currency_exchange_journal_id:
                # البحث عن journal مناسب
                journal = env['account.journal'].search([
                    ('type', '=', 'general'),
                    ('company_id', '=', company.id),
                ], limit=1)
                
                if journal:
                    company.write({'currency_exchange_journal_id': journal.id})
                    print(f"   ✅ تم ربط journal لتبادل العملات")
            
            # تفعيل USD
            if not usd.active:
                usd.write({'active': True})
                print(f"   ✅ تم تفعيل عملة USD")
            
            # 5. إضافة صلاحيات للأدمن
            print(f"\n5. التحقق من صلاحيات إدارة العملات...")
            
            admin_user = env['res.users'].browse(odoo.SUPERUSER_ID)
            
            # مجموعة إدارة العملات
            currency_group = env.ref('base.group_multi_currency', raise_if_not_found=False)
            if currency_group:
                if currency_group not in admin_user.group_ids:
                    admin_user.write({'group_ids': [(4, currency_group.id)]})
                    print(f"   ✅ تم إضافة صلاحية Multi-Currency")
                else:
                    print(f"   ✅ الأدمن لديه صلاحية Multi-Currency")
            
            # مجموعة الإعدادات
            settings_group = env.ref('base.group_system', raise_if_not_found=False)
            if settings_group:
                if settings_group not in admin_user.group_ids:
                    admin_user.write({'group_ids': [(4, settings_group.id)]})
                    print(f"   ✅ تم إضافة صلاحية Settings")
                else:
                    print(f"   ✅ الأدمن لديه صلاحية Settings")
            
            # 6. التحقق من النتيجة
            print(f"\n6. التحقق من النتيجة النهائية...")
            
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   ✅ التاريخ: {latest_rate.name}")
                print(f"   ✅ السعر: 1 USD = {current_rate:.2f} IQD")
            
            # 7. مسح الكاش
            print(f"\n7. مسح الكاش...")
            env['res.currency'].invalidate_model()
            env['res.currency.rate'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم تحديث سعر الصرف بنجاح!")
            print(f"{'='*60}\n")
            
            print("للوصول إلى إعدادات العملات:")
            print("1. الإعدادات (Settings)")
            print("2. General Settings")
            print("3. قسم Multi-Currencies")
            print("4. اضغط على 'Currencies' لرؤية جميع العملات")
            print("5. اختر USD وعدّل السعر")
            print("")
            print("أو:")
            print("المحاسبة (Accounting) → الإعدادات (Configuration) → العملات (Currencies)")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    # قراءة السعر من المستخدم أو استخدام القيمة الافتراضية
    if len(sys.argv) > 1:
        try:
            new_rate = float(sys.argv[1])
        except ValueError:
            print("خطأ: يجب إدخال رقم صحيح لسعر الصرف")
            print("مثال: python update_exchange_rate.py 1510")
            sys.exit(1)
    else:
        new_rate = 1510.0
    
    update_exchange_rate(new_rate)
