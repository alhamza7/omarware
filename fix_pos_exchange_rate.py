#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح سعر الصرف في POS (نقطة البيع)
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_pos_exchange_rate():
    """إصلاح سعر الصرف في POS"""
    
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
    
    print(f"\n{'='*70}")
    print(f"إصلاح سعر الصرف في POS - قاعدة البيانات: {db_name}")
    print(f"{'='*70}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من سعر الصرف
            print("1. التحقق من سعر الصرف في النظام...")
            
            usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
            iqd = env['res.currency'].search([('name', '=', 'IQD')], limit=1)
            
            if not usd:
                print("   ❌ عملة USD غير موجودة!")
                return
            
            latest_rate = env['res.currency.rate'].search([
                ('currency_id', '=', usd.id),
            ], order='name desc', limit=1)
            
            if latest_rate:
                current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
                print(f"   ✅ السعر في النظام: 1 USD = {current_rate:.2f} IQD")
            else:
                print("   ⚠️  لا يوجد سعر صرف!")
                current_rate = 1510.0
            
            # 2. التحقق من جلسات POS المفتوحة
            print("\n2. التحقق من جلسات POS المفتوحة...")
            
            open_sessions = env['pos.session'].search([
                ('state', '!=', 'closed'),
            ])
            
            if open_sessions:
                print(f"   ⚠️  وجدت {len(open_sessions)} جلسة POS مفتوحة:")
                for session in open_sessions:
                    print(f"      - {session.name} (الحالة: {session.state})")
                    print(f"        POS Config: {session.config_id.name}")
                
                print("\n   ⚠️  تحذير: جلسات POS المفتوحة تستخدم الكاش القديم!")
                print("   يجب إغلاقها وإعادة فتحها لتطبيق السعر الجديد.")
            else:
                print("   ✅ لا توجد جلسات POS مفتوحة")
            
            # 3. التحقق من إعدادات POS
            print("\n3. التحقق من إعدادات POS...")
            
            pos_configs = env['pos.config'].search([
                ('active', '=', True),
            ])
            
            if pos_configs:
                print(f"   وجدت {len(pos_configs)} نقطة بيع مفعلة:")
                for config in pos_configs:
                    currency = config.currency_id or env.company.currency_id
                    print(f"      ✅ {config.name}")
                    print(f"         العملة: {currency.name}")
                    
                    # التحقق من إعدادات العملة
                    if config.currency_id and config.currency_id != env.company.currency_id:
                        print(f"         ⚠️  POS تستخدم عملة مختلفة عن الشركة!")
            else:
                print("   ⚠️  لا توجد نقاط بيع مفعلة!")
            
            # 4. التحقق من أسعار المنتجات بـ USD
            print("\n4. التحقق من أسعار المنتجات...")
            
            # البحث عن منتجات متوفرة في POS
            products = env['product.product'].search([
                ('available_in_pos', '=', True),
            ], limit=10)
            
            if products:
                print(f"   وجدت {len(products)} منتج في POS (عرض أول 10):")
                print(f"\n   {'المنتج':<30} {'السعر':<15} {'العملة':<10}")
                print(f"   {'-'*60}")
                
                for product in products[:10]:
                    price = product.lst_price
                    currency = product.currency_id or env.company.currency_id
                    print(f"   {product.name[:28]:<30} {price:>13,.2f} {currency.name:<10}")
            
            # 5. إغلاق الجلسات المفتوحة تلقائياً (اختياري)
            if open_sessions:
                print(f"\n5. إغلاق جلسات POS المفتوحة...")
                
                for session in open_sessions:
                    if session.state == 'opened':
                        try:
                            print(f"   ⚠️  محاولة إغلاق: {session.name}...")
                            
                            # التحقق من عدم وجود أوامر مفتوحة
                            open_orders = env['pos.order'].search([
                                ('session_id', '=', session.id),
                                ('state', '=', 'draft'),
                            ])
                            
                            if open_orders:
                                print(f"      ❌ لا يمكن الإغلاق: يوجد {len(open_orders)} أمر مفتوح")
                            else:
                                # إغلاق الجلسة
                                # session.action_pos_session_closing_control()
                                print(f"      ⚠️  يُنصح بإغلاقها يدوياً من الواجهة")
                        except Exception as e:
                            print(f"      ❌ خطأ: {e}")
                    else:
                        print(f"   ℹ️  {session.name} في حالة: {session.state}")
            
            # 6. مسح الكاش
            print(f"\n6. مسح الكاش...")
            
            env['res.currency'].invalidate_model()
            env['res.currency.rate'].invalidate_model()
            env['pos.session'].invalidate_model()
            env['pos.config'].invalidate_model()
            env['product.product'].invalidate_model()
            
            registry.clear_cache()
            print("   ✅ تم مسح كاش الخادم")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*70}")
            print("✅ تم إصلاح إعدادات سعر الصرف!")
            print(f"{'='*70}\n")
            
            # التعليمات النهائية
            print("📋 الخطوات المطلوبة لإصلاح POS:")
            print("")
            
            if open_sessions:
                print("⚠️  1. إغلاق جلسات POS المفتوحة:")
                for session in open_sessions:
                    print(f"      - اذهب إلى: Point of Sale → Sessions → {session.name}")
                    print(f"        اضغط 'Close Session' (إغلاق الجلسة)")
                print("")
            
            print("2. مسح كاش المتصفح:")
            print("   - اضغط: Ctrl+Shift+Delete")
            print("   - احذف: Cached images and files")
            print("   - الفترة: All time")
            print("")
            
            print("3. في واجهة POS:")
            print("   - اذهب إلى: Point of Sale")
            print("   - افتح نقطة بيع جديدة (New Session)")
            print("   - في إعدادات POS (⚙️):")
            print("     • تأكد من السعر: 1 USD = 1510 IQD")
            print("")
            
            print("4. اختبار:")
            print("   - امسح باركود منتج")
            print("   - تحقق من السعر المعروض")
            print("   - يجب أن يكون صحيحاً (السعر × 1510)")
            print("")
            
            print("💡 ملاحظة مهمة:")
            print("   POS يخزن البيانات محلياً في المتصفح (LocalStorage)")
            print("   لذلك يجب:")
            print("   ✓ إغلاق الجلسات القديمة")
            print("   ✓ مسح كاش المتصفح")
            print("   ✓ فتح جلسة جديدة")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_pos_exchange_rate()
