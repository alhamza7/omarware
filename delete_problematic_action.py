#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لحذف واستبدال Action 715 المشكل
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def delete_problematic_action():
    """حذف واستبدال Action 715"""
    
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
    print(f"حذف Action 715 المشكل - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. البحث عن Action 715
            print("1. البحث عن Action 715...")
            action = env['ir.actions.act_window'].browse(715)
            
            if not action.exists():
                print("   ℹ️  Action 715 غير موجود (ربما تم حذفه)")
            else:
                print(f"   ✅ تم العثور على Action:")
                print(f"      Name: {action.name}")
                print(f"      Model: {action.res_model}")
                print(f"      View Mode: {action.view_mode}")
                
                # البحث عن القوائم المرتبطة بهذا الـ action
                print("\n2. البحث عن القوائم المرتبطة...")
                menus = env['ir.ui.menu'].search([
                    ('action', '=', f'ir.actions.act_window,{action.id}')
                ])
                
                if menus:
                    print(f"   تم العثور على {len(menus)} قائمة:")
                    for menu in menus:
                        parent_name = menu.parent_id.name if menu.parent_id else "Root"
                        print(f"      - {menu.name} (Parent: {parent_name})")
                    
                    # إنشاء action جديد بسيط وصحيح
                    print("\n3. إنشاء Action جديد صحيح...")
                    
                    # تحديد الـ model
                    model = action.res_model or 'sale.order'
                    
                    new_action = env['ir.actions.act_window'].create({
                        'name': action.name or 'Sales Orders',
                        'res_model': model,
                        'view_mode': 'tree,form',  # بسيط وواضح
                        'domain': [],
                        'context': "{'default_user_id': uid}",
                        'help': 'Click to create a quotation or sales order.',
                    })
                    
                    print(f"   ✅ تم إنشاء Action جديد (ID: {new_action.id})")
                    
                    # تحديث القوائم لتستخدم الـ action الجديد
                    print("\n4. تحديث القوائم...")
                    for menu in menus:
                        menu.action = f'ir.actions.act_window,{new_action.id}'
                        print(f"   ✅ تم تحديث القائمة: {menu.name}")
                    
                    # حذف الـ action القديم
                    print("\n5. حذف Action 715 القديم...")
                    action.unlink()
                    print("   ✅ تم حذف Action 715")
                else:
                    print("   ℹ️  لا توجد قوائم مرتبطة - حذف Action مباشرة")
                    action.unlink()
                    print("   ✅ تم حذف Action 715")
            
            # 6. البحث عن جميع actions المشكلة في Sale
            print("\n6. فحص جميع Sale Actions...")
            
            # البحث عن actions مرتبطة بـ sale
            sale_actions = env['ir.actions.act_window'].search([
                '|', ('res_model', 'ilike', 'sale'),
                     ('name', 'ilike', 'sale')
            ])
            
            print(f"   تم العثور على {len(sale_actions)} action")
            
            fixed_count = 0
            for act in sale_actions:
                # التحقق من view_mode
                if not act.view_mode:
                    print(f"   ⚠️  Action {act.id} ({act.name}) ليس له view_mode")
                    act.view_mode = 'tree,form'
                    print(f"      ✅ تم تعيين view_mode")
                    fixed_count += 1
                elif 'tree' in act.view_mode and act.res_model:
                    # التحقق من وجود tree view
                    tree_view = env['ir.ui.view'].search([
                        ('model', '=', act.res_model),
                        ('type', 'in', ['tree', 'list'])
                    ], limit=1)
                    
                    if not tree_view:
                        print(f"   ⚠️  Action {act.id} ({act.name}) يحتاج tree view")
                        # تغيير tree إلى list أو kanban,form
                        if 'form' in act.view_mode:
                            act.view_mode = act.view_mode.replace('tree', 'kanban')
                            print(f"      ✅ تم تغيير view_mode إلى: {act.view_mode}")
                            fixed_count += 1
            
            print(f"\n   ✅ تم إصلاح {fixed_count} action")
            
            # 7. مسح الكاش
            print("\n7. مسح الكاش...")
            env['ir.actions.act_window'].invalidate_model()
            env['ir.ui.menu'].invalidate_model()
            env['ir.ui.view'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم حذف واستبدال Actions المشكلة!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. مسح كاش المتصفح (Ctrl+Shift+Delete)")
            print("3. إعادة تحميل الصفحة")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    delete_problematic_action()
