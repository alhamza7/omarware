#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح active_id error في قائمة Sales
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_sale_menu_action():
    """إصلاح action في قائمة Sales"""
    
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
    print(f"إصلاح active_id error - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. البحث عن جميع قوائم Sales
            print("1. البحث عن قوائم Sales...")
            sale_menus = env['ir.ui.menu'].search([
                '|', ('name', '=', 'Sales'),
                ('name', '=', 'المبيعات')
            ])
            
            print(f"   تم العثور على {len(sale_menus)} قائمة")
            
            fixed_count = 0
            for menu in sale_menus:
                print(f"\n   فحص القائمة: {menu.name} (ID: {menu.id})")
                print(f"   Parent: {menu.parent_id.name if menu.parent_id else 'Root'}")
                
                if menu.action:
                    action = menu.action
                    print(f"   Action: {action.name} (Type: {action._name})")
                    
                    if hasattr(action, 'context') and action.context:
                        print(f"   Context: {action.context[:100]}...")
                        
                        if 'active_id' in action.context:
                            print("   ⚠️  يحتوي على active_id - جاري الإصلاح...")
                            
                            # تنظيف context
                            try:
                                context = eval(action.context)
                                # إزالة أي مفتاح يحتوي على active_id
                                cleaned_context = {}
                                for key, value in context.items():
                                    if 'active_id' not in key and 'active_id' not in str(value):
                                        cleaned_context[key] = value
                                
                                action.write({'context': str(cleaned_context)})
                                print("   ✅ تم تنظيف context")
                                fixed_count += 1
                            except Exception as e:
                                print(f"   ❌ خطأ في تنظيف context: {e}")
                                # إذا فشل التنظيف، نزيل الـ context تماماً
                                action.write({'context': '{}'})
                                print("   ✅ تم إزالة context تماماً")
                                fixed_count += 1
                else:
                    print("   ℹ️  القائمة بدون action")
            
            # 2. التأكد من وجود قائمة رئيسية صحيحة
            print("\n2. التأكد من القائمة الرئيسية...")
            main_menu = env['ir.ui.menu'].search([
                ('name', 'in', ['Sales', 'المبيعات']),
                ('parent_id', '=', False),
                ('active', '=', True)
            ], limit=1)
            
            if not main_menu:
                print("   إنشاء قائمة رئيسية جديدة...")
                
                # إنشاء action بسيط بدون context
                sale_action = env['ir.actions.act_window'].create({
                    'name': 'Sales Orders',
                    'res_model': 'sale.order',
                    'view_mode': 'tree,form',
                    'context': "{'default_user_id': uid}",
                    'domain': [],
                })
                
                main_menu = env['ir.ui.menu'].create({
                    'name': 'Sales',
                    'sequence': 20,
                    'parent_id': False,
                    'action': f'ir.actions.act_window,{sale_action.id}',
                })
                print(f"   ✅ تم إنشاء القائمة الرئيسية (ID: {main_menu.id})")
            else:
                print(f"   ✅ القائمة الرئيسية موجودة (ID: {main_menu.id})")
            
            # 3. مسح الكاش
            print("\n3. مسح الكاش...")
            env['ir.ui.menu'].invalidate_model()
            env['ir.actions.act_window'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print(f"✅ تم إصلاح {fixed_count} قائمة!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. مسح كاش المتصفح (Ctrl+Shift+Delete)")
            print("3. إعادة تحميل الصفحة (F5)")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_sale_menu_action()
