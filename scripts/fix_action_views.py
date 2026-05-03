#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح مشكلة View types not defined في actions
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_action_views():
    """إصلاح actions التي لديها view types غير معرّفة"""
    
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
    print(f"إصلاح Action Views - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. البحث عن الـ action 715
            print("1. البحث عن Action 715...")
            action = env['ir.actions.act_window'].browse(715)
            
            if not action.exists():
                print("   ❌ Action 715 غير موجود!")
                print("\n   البحث عن جميع actions المتعلقة بـ Sale...")
                sale_actions = env['ir.actions.act_window'].search([
                    ('res_model', 'ilike', 'sale')
                ])
                print(f"   تم العثور على {len(sale_actions)} action")
                for act in sale_actions[:10]:
                    print(f"      - ID: {act.id}, Name: {act.name}, Model: {act.res_model}, View Mode: {act.view_mode}")
            else:
                print(f"   ✅ تم العثور على Action: {action.name}")
                print(f"      Model: {action.res_model}")
                print(f"      View Mode: {action.view_mode}")
                print(f"      Domain: {action.domain}")
                
                # التحقق من views المتاحة
                print("\n2. التحقق من Views المتاحة...")
                model = action.res_model
                
                available_views = env['ir.ui.view'].search([
                    ('model', '=', model),
                    ('type', 'in', ['tree', 'list', 'form', 'kanban'])
                ])
                
                print(f"   Views المتاحة لـ {model}:")
                view_types = []
                for view in available_views:
                    print(f"      - Type: {view.type}, Name: {view.name}")
                    view_types.append(view.type)
                
                # 3. إصلاح view_mode
                print("\n3. إصلاح View Mode...")
                current_modes = action.view_mode.split(',')
                print(f"   View modes الحالية: {current_modes}")
                
                # استبدال tree بـ list إذا كانت tree غير موجودة
                fixed_modes = []
                for mode in current_modes:
                    mode = mode.strip()
                    if mode == 'tree':
                        if 'tree' not in view_types and 'list' not in view_types:
                            # إنشاء list view بسيط
                            print(f"   ⚠️  لا يوجد tree أو list view - جاري الإنشاء...")
                            env['ir.ui.view'].create({
                                'name': f'{model}.view.tree',
                                'model': model,
                                'type': 'tree',
                                'arch': f'''<?xml version="1.0"?>
                                    <tree string="{action.name}">
                                        <field name="name"/>
                                    </tree>
                                '''
                            })
                            print(f"      ✅ تم إنشاء tree view")
                        fixed_modes.append('tree')
                    else:
                        fixed_modes.append(mode)
                
                new_view_mode = ','.join(fixed_modes)
                print(f"   View modes الجديدة: {new_view_mode}")
                
                if new_view_mode != action.view_mode:
                    action.view_mode = new_view_mode
                    print("   ✅ تم تحديث view_mode")
                else:
                    print("   ℹ️  لا حاجة لتحديث view_mode")
            
            # 4. البحث عن جميع Sale actions ذات المشاكل المحتملة
            print("\n4. فحص جميع Sale Actions...")
            sale_actions = env['ir.actions.act_window'].search([
                '|', ('res_model', 'ilike', 'sale'),
                     ('name', 'ilike', 'sale')
            ])
            
            problematic_actions = []
            for act in sale_actions:
                if 'tree' in act.view_mode:
                    model = act.res_model
                    # التحقق من وجود tree view
                    tree_view = env['ir.ui.view'].search([
                        ('model', '=', model),
                        ('type', 'in', ['tree', 'list'])
                    ], limit=1)
                    
                    if not tree_view:
                        problematic_actions.append(act)
            
            if problematic_actions:
                print(f"   تم العثور على {len(problematic_actions)} action بمشاكل محتملة:")
                for act in problematic_actions:
                    print(f"      ❌ ID: {act.id}, Name: {act.name}, Model: {act.res_model}")
                    
                    # إنشاء tree view بسيط
                    print(f"         جاري إنشاء tree view...")
                    try:
                        # الحصول على حقول الـ model
                        model_obj = env[act.res_model]
                        fields = []
                        
                        # إضافة بعض الحقول الشائعة
                        common_fields = ['name', 'date', 'state', 'partner_id', 'user_id']
                        for field_name in common_fields:
                            if field_name in model_obj._fields:
                                fields.append(field_name)
                        
                        if not fields:
                            fields = ['name']  # على الأقل name
                        
                        fields_xml = '\n'.join([f'                        <field name="{f}"/>' for f in fields])
                        
                        env['ir.ui.view'].create({
                            'name': f'{act.res_model}.view.tree.generated',
                            'model': act.res_model,
                            'type': 'tree',
                            'arch': f'''<?xml version="1.0"?>
                                <tree string="{act.name}">
{fields_xml}
                                </tree>
                            '''
                        })
                        print(f"         ✅ تم إنشاء tree view لـ {act.res_model}")
                    except Exception as e:
                        print(f"         ❌ خطأ في إنشاء tree view: {e}")
            else:
                print("   ✅ جميع Actions صحيحة!")
            
            # 5. مسح الكاش
            print("\n5. مسح الكاش...")
            env['ir.actions.act_window'].invalidate_model()
            env['ir.ui.view'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم إصلاح Action Views!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. مسح كاش المتصفح (Ctrl+Shift+R)")
            print("3. إعادة المحاولة")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_action_views()
