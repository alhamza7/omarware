#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث سعر الصرف الحالي إلى 1510 مباشرة
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def change_rate_to_1510():
    """تحديث السعر الموجود إلى 1510"""
    
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
        db_name = 'nbs_lugalai'
    
    print(f"\n{'='*60}")
    print(f"تحديث سعر الصرف الحالي إلى 1510")
    print(f"قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. الحصول على عملة USD
            print("1. البحث عن عملة USD...")
            
            usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
            if not usd:
                print("   ❌ عملة USD غير موجودة!")
                return
            
            print(f"   ✅ وجدت عملة USD (ID: {usd.id})")
            
            # 2. البحث عن السعر الحالي
            print("\n2. البحث عن السعر الحالي...")
            
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                old_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   📊 السعر الحالي: 1 USD = {old_rate:.2f} IQD")
                print(f"   📅 التاريخ: {latest_rate.name}")
                print(f"   🔢 Rate في DB: {latest_rate.rate:.8f}")
            else:
                print("   ⚠️  لا يوجد سعر صرف محدد")
                latest_rate = None
                old_rate = 0
            
            # 3. تحديث السعر إلى 1510
            print(f"\n3. تحديث السعر إلى: 1 USD = 1510 IQD...")
            
            new_rate = 1510.0
            new_odoo_rate = 1.0 / new_rate
            today = datetime.now().date()
            
            if latest_rate:
                # تحديث السعر الموجود
                print(f"   🔄 تحديث السعر الموجود (ID: {latest_rate.id})...")
                latest_rate.write({
                    'rate': new_odoo_rate,
                    'name': today,
                })
                print(f"   ✅ تم التحديث!")
            else:
                # إنشاء سعر جديد
                print(f"   ➕ إنشاء سعر صرف جديد...")
                latest_rate = env['res.currency.rate'].create({
                    'currency_id': usd.id,
                    'name': today,
                    'rate': new_odoo_rate,
                    'company_id': env.company.id,
                })
                print(f"   ✅ تم الإنشاء (ID: {latest_rate.id})")
            
            # 4. التحقق من النتيجة
            print(f"\n4. التحقق من السعر الجديد...")
            
            # إعادة قراءة السعر من قاعدة البيانات
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   ✅ السعر الجديد: 1 USD = {current_rate:.2f} IQD")
                print(f"   ✅ التاريخ: {latest_rate.name}")
                print(f"   ✅ Rate في DB: {latest_rate.rate:.8f}")
            
            # 5. عرض مقارنة
            if old_rate != 0:
                print(f"\n5. المقارنة:")
                print(f"   قبل: 1 USD = {old_rate:.2f} IQD")
                print(f"   بعد: 1 USD = {current_rate:.2f} IQD")
                
                diff = current_rate - old_rate
                diff_percent = (diff / old_rate * 100) if old_rate != 0 else 0
                
                if diff > 0:
                    print(f"   📈 ارتفاع: +{diff:.2f} IQD ({diff_percent:+.2f}%)")
                elif diff < 0:
                    print(f"   📉 انخفاض: {diff:.2f} IQD ({diff_percent:+.2f}%)")
                else:
                    print(f"   ➡️  لم يتغير")
                
                # أمثلة عملية
                print(f"\n   أمثلة:")
                for amount in [100, 500, 1000]:
                    old_iqd = amount * old_rate
                    new_iqd = amount * current_rate
                    print(f"   • {amount} USD:")
                    print(f"     - قبل: {old_iqd:>10,.0f} IQD")
                    print(f"     - بعد: {new_iqd:>10,.0f} IQD")
            
            # 6. مسح الكاش
            print(f"\n6. مسح الكاش...")
            env['res.currency'].invalidate_model()
            env['res.currency.rate'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم تحديث سعر الصرف بنجاح!")
            print(f"{'='*60}\n")
            
            print("📋 الخطوات التالية:")
            print("")
            print("في المتصفح:")
            print("1. امسح كاش المتصفح: Ctrl+Shift+Delete")
            print("2. أعد تحميل الصفحة: F5")
            print("3. جميع الفواتير الجديدة ستستخدم السعر 1510")
            print("")
            print("لاختبار:")
            print("• أنشئ فاتورة جديدة بـ USD")
            print("• تحقق من القيمة بـ IQD")
            print("• يجب أن تكون: المبلغ × 1510")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    change_rate_to_1510()
