#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تفعيل قوائم العملات في Odoo
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def activate_currency_menu():
    """تفعيل قوائم العملات"""
    
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
    print(f"تفعيل قوائم العملات - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. تفعيل Multi-Currency
            print("1. تفعيل Multi-Currency في الإعدادات...")
            
            # تفعيل group_multi_currency
            group = env.ref('base.group_multi_currency', raise_if_not_found=False)
            if group:
                # إضافة جميع المستخدمين لهذه المجموعة
                users = env['res.users'].search([('active', '=', True)])
                for user in users:
                    if group not in user.group_ids:
                        user.write({'group_ids': [(4, group.id)]})
                print(f"   ✅ تم تفعيل Multi-Currency لـ {len(users)} مستخدم")
            
            # 2. تفعيل قوائم العملات
            print("\n2. تفعيل قوائم العملات...")
            
            # البحث عن قوائم العملات
            currency_menus = env['ir.ui.menu'].search([
                '|', '|', '|',
                ('name', 'ilike', 'currency'),
                ('name', 'ilike', 'currencies'),
                ('name', 'ilike', 'عملة'),
                ('name', 'ilike', 'عملات'),
            ])
            
            activated = 0
            for menu in currency_menus:
                if not menu.active:
                    menu.write({'active': True})
                    activated += 1
                    print(f"   ✅ تم تفعيل: {menu.name}")
            
            if activated == 0:
                print(f"   ℹ️  جميع القوائم ({len(currency_menus)}) مفعلة بالفعل")
            else:
                print(f"   ✅ تم تفعيل {activated} قائمة")
            
            # 3. التحقق من action للعملات
            print("\n3. التحقق من Actions للعملات...")
            
            currency_action = env.ref('base.action_currency_form', raise_if_not_found=False)
            if currency_action:
                print(f"   ✅ Action للعملات موجود (ID: {currency_action.id})")
                
                # التحقق من القائمة المرتبطة
                menus = env['ir.ui.menu'].search([
                    ('action', '=', f'ir.actions.act_window,{currency_action.id}')
                ])
                
                if menus:
                    print(f"   ✅ القائمة مربوطة: {menus[0].name}")
                    if not menus[0].active:
                        menus[0].write({'active': True})
                        print(f"   ✅ تم تفعيل القائمة")
                else:
                    print(f"   ⚠️  القائمة غير مربوطة!")
            
            # 4. التحقق من أسعار الصرف
            print("\n4. التحقق من Actions لأسعار الصرف...")
            
            rate_action = env.ref('base.act_view_currency_rates', raise_if_not_found=False)
            if rate_action:
                print(f"   ✅ Action لأسعار الصرف موجود (ID: {rate_action.id})")
            
            # 5. إنشاء قائمة مخصصة إذا لزم الأمر
            print("\n5. التحقق من قائمة Accounting/Configuration/Currencies...")
            
            # البحث عن قائمة Configuration في Accounting
            accounting_menu = env.ref('account.menu_finance', raise_if_not_found=False)
            config_menu = env.ref('account.menu_finance_configuration', raise_if_not_found=False)
            
            if accounting_menu and config_menu:
                # البحث عن قائمة العملات تحت Configuration
                currency_menu = env['ir.ui.menu'].search([
                    ('name', '=', 'Currencies'),
                    ('parent_id', '=', config_menu.id),
                ], limit=1)
                
                if not currency_menu and currency_action:
                    # إنشاء القائمة
                    currency_menu = env['ir.ui.menu'].create({
                        'name': 'Currencies',
                        'parent_id': config_menu.id,
                        'action': f'ir.actions.act_window,{currency_action.id}',
                        'sequence': 50,
                    })
                    print(f"   ✅ تم إنشاء قائمة Currencies في Accounting")
                elif currency_menu:
                    if not currency_menu.active:
                        currency_menu.write({'active': True})
                        print(f"   ✅ تم تفعيل قائمة Currencies في Accounting")
                    else:
                        print(f"   ✅ قائمة Currencies موجودة ومفعلة")
            
            # 6. عرض جميع القوائم المتعلقة بالعملات
            print("\n6. جميع قوائم العملات المتاحة:")
            
            all_currency_menus = env['ir.ui.menu'].search([
                '|', '|',
                ('name', 'ilike', 'currency'),
                ('name', 'ilike', 'currencies'),
                ('name', 'ilike', 'rate'),
            ])
            
            for menu in all_currency_menus:
                status = "✅ مفعل" if menu.active else "❌ معطل"
                parent = menu.parent_id.name if menu.parent_id else "Root"
                print(f"   {status} | {menu.name} (Parent: {parent})")
            
            # 7. مسح الكاش
            print(f"\n7. مسح الكاش...")
            env['ir.ui.menu'].invalidate_model()
            env['ir.actions.act_window'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم تفعيل قوائم العملات!")
            print(f"{'='*60}\n")
            
            print("للوصول إلى إعدادات العملات:")
            print("")
            print("الطريقة 1 (الإعدادات):")
            print("   Settings → General Settings → Multi-Currencies → Currencies")
            print("")
            print("الطريقة 2 (المحاسبة):")
            print("   Accounting → Configuration → Currencies")
            print("")
            print("لتحديث سعر الصرف:")
            print("   1. اذهب إلى Currencies")
            print("   2. افتح عملة USD")
            print("   3. اذهب إلى تبويب 'Rates'")
            print("   4. أضف/عدّل السعر")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    activate_currency_menu()
