#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لعرض جميع قوائم Sale بشكل شجري مع جميع المستويات
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def print_menu_tree(menu, level=0, parent_active=True):
    """طباعة القائمة وجميع القوائم الفرعية بشكل شجري"""
    indent = "   " * level
    icon = "📂" if menu.child_id else "📄"
    status = "✅" if menu.active else "❌"
    parent_status = "🔒 (Parent inactive)" if not parent_active else ""
    
    print(f"{indent}{icon} [{status}] {menu.name} (ID: {menu.id}, Seq: {menu.sequence}) {parent_status}")
    
    if menu.action:
        print(f"{indent}   └─ Action: {menu.action.name}")
    
    # طباعة القوائم الفرعية
    for child in menu.child_id.sorted(key=lambda m: m.sequence):
        print_menu_tree(child, level + 1, menu.active)

def show_all_sale_menus():
    """عرض جميع قوائم Sale"""
    
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
    print(f"شجرة قوائم Sale الكاملة - قاعدة البيانات: {db_name}")
    print(f"{'='*70}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # البحث عن القائمة الرئيسية Sales
            main_sale_menus = env['ir.ui.menu'].search([
                ('name', 'in', ['Sales', 'المبيعات']),
                ('parent_id', '=', False)
            ])
            
            if not main_sale_menus:
                print("❌ لم يتم العثور على القائمة الرئيسية Sales!")
                print("\nجميع القوائم المتعلقة بـ sale:")
                all_sale_menus = env['ir.ui.menu'].search([
                    '|', ('name', 'ilike', 'sale'),
                    ('name', 'ilike', 'order')
                ])
                for menu in all_sale_menus:
                    parent_name = menu.parent_id.name if menu.parent_id else "Root"
                    status = "✅" if menu.active else "❌"
                    print(f"   [{status}] {menu.name} - Parent: {parent_name}")
                return
            
            # طباعة الشجرة الكاملة
            for main_menu in main_sale_menus:
                print_menu_tree(main_menu)
            
            # إحصائيات
            print(f"\n{'='*70}")
            print("إحصائيات:")
            print(f"{'='*70}")
            
            all_submenus = env['ir.ui.menu'].search([])
            
            def count_descendants(menu):
                """حساب جميع القوائم الفرعية"""
                count = len(menu.child_id)
                for child in menu.child_id:
                    count += count_descendants(child)
                return count
            
            for main_menu in main_sale_menus:
                total_submenus = count_descendants(main_menu)
                active_submenus = len(env['ir.ui.menu'].search([
                    ('id', 'child_of', main_menu.id),
                    ('id', '!=', main_menu.id),
                    ('active', '=', True)
                ]))
                inactive_submenus = total_submenus - active_submenus
                
                print(f"\nالقائمة الرئيسية: {main_menu.name}")
                print(f"   - إجمالي القوائم الفرعية: {total_submenus}")
                print(f"   - القوائم النشطة: {active_submenus} ✅")
                print(f"   - القوائم المعطلة: {inactive_submenus} ❌")
            
            # البحث عن قوائم معطلة
            print(f"\n{'='*70}")
            print("القوائم المعطلة في Sale:")
            print(f"{'='*70}")
            
            inactive_menus = []
            for main_menu in main_sale_menus:
                inactive = env['ir.ui.menu'].search([
                    ('id', 'child_of', main_menu.id),
                    ('id', '!=', main_menu.id),
                    ('active', '=', False)
                ])
                inactive_menus.extend(inactive)
            
            if inactive_menus:
                print("\n❌ القوائم التالية معطلة:")
                for menu in inactive_menus:
                    parent_name = menu.parent_id.name if menu.parent_id else "Root"
                    print(f"   - {menu.name} (ID: {menu.id}) - Parent: {parent_name}")
                print(f"\nلتفعيلها، شغل: venv/bin/python fix_sale_submenus.py")
            else:
                print("\n✅ جميع القوائم نشطة!")
            
            print(f"\n{'='*70}\n")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    show_all_sale_menus()
