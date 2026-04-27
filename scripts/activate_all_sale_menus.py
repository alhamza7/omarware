#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتفعيل جميع قوائم Sale وجميع التصنيفات الفرعية
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def activate_all_sale_menus():
    """تفعيل جميع قوائم Sale وجميع التصنيفات الفرعية"""
    
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
    print(f"تفعيل جميع قوائم Sale - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. البحث عن القائمة الرئيسية Sales
            print("1. البحث عن القائمة الرئيسية Sales...")
            main_sale_menus = env['ir.ui.menu'].search([
                ('name', 'in', ['Sales', 'المبيعات']),
                ('parent_id', '=', False)
            ])
            
            if not main_sale_menus:
                print("   ❌ القائمة الرئيسية Sales غير موجودة!")
                return
            
            for main_menu in main_sale_menus:
                print(f"   ✅ القائمة الرئيسية: {main_menu.name} (ID: {main_menu.id})")
            
            # 2. البحث عن جميع القوائم الفرعية (جميع المستويات)
            print("\n2. البحث عن جميع القوائم الفرعية...")
            
            all_sale_submenus = []
            for main_menu in main_sale_menus:
                # استخدام child_of للحصول على جميع المستويات
                submenus = env['ir.ui.menu'].search([
                    ('id', 'child_of', main_menu.id),
                    ('id', '!=', main_menu.id)
                ])
                all_sale_submenus.extend(submenus)
            
            print(f"   تم العثور على {len(all_sale_submenus)} قائمة فرعية (جميع المستويات)")
            
            # 3. تفعيل جميع القوائم المعطلة
            print("\n3. تفعيل القوائم المعطلة...")
            
            inactive_menus = [m for m in all_sale_submenus if not m.active]
            
            if inactive_menus:
                print(f"   تم العثور على {len(inactive_menus)} قائمة معطلة:")
                for menu in inactive_menus:
                    parent_name = menu.parent_id.name if menu.parent_id else "Root"
                    print(f"      ❌ {menu.name} (Parent: {parent_name})")
                    menu.active = True
                    print(f"         ✅ تم التفعيل")
            else:
                print("   ✅ جميع القوائم نشطة بالفعل!")
            
            # 4. التحقق من visibility groups
            print("\n4. التحقق من مجموعات الرؤية...")
            
            restricted_menus = []
            for menu in all_sale_submenus:
                if menu.groups_id:
                    restricted_menus.append(menu)
            
            if restricted_menus:
                print(f"   تم العثور على {len(restricted_menus)} قائمة لها قيود صلاحيات:")
                for menu in restricted_menus:
                    groups_names = ", ".join([g.name for g in menu.groups_id])
                    print(f"      🔒 {menu.name} - Groups: {groups_names}")
                
                print("\n   ℹ️  للسماح لجميع المستخدمين بالوصول، يمكن إزالة القيود")
                print("   (لكن هذا قد يكون له آثار أمنية)")
            else:
                print("   ✅ لا توجد قيود على القوائم")
            
            # 5. إصلاح sequence
            print("\n5. إعادة ترتيب القوائم...")
            
            for main_menu in main_sale_menus:
                # القوائم المباشرة فقط (المستوى الأول)
                direct_children = env['ir.ui.menu'].search([
                    ('parent_id', '=', main_menu.id),
                    ('active', '=', True)
                ], order='sequence,name')
                
                print(f"\n   القوائم الفرعية المباشرة لـ {main_menu.name}:")
                for idx, child in enumerate(direct_children):
                    child.sequence = (idx + 1) * 10
                    print(f"      {idx + 1}. {child.name} (Seq: {child.sequence})")
            
            # 6. مسح الكاش
            print("\n6. مسح الكاش...")
            env['ir.ui.menu'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print(f"✅ تم تفعيل {len(inactive_menus)} قائمة!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. في المتصفح:")
            print("   - امسح الكاش (Ctrl+Shift+R)")
            print("   - أو سجل خروج ودخول")
            print("")
            print("3. للتحقق من الشجرة الكاملة:")
            print("   venv/bin/python show_all_sale_menus_tree.py")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    activate_all_sale_menus()
