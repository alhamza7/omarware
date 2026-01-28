#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للتحقق من حالة وحدة Sale وإصلاح مشاكل القائمة
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def check_sale_module():
    """التحقق من وحدة Sale وإصلاحها"""
    
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
    print(f"فحص وحدة Sale - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من وحدة sale
            print("1. التحقق من وحدة sale...")
            sale_module = env['ir.module.module'].search([('name', '=', 'sale')])
            
            if not sale_module:
                print("   ❌ وحدة sale غير موجودة!")
                return
            
            print(f"   الحالة: {sale_module.state}")
            print(f"   النسخة: {sale_module.installed_version or 'غير مثبتة'}")
            
            if sale_module.state != 'installed':
                print("\n   ⚠️  وحدة sale غير مثبتة!")
                print("   تثبيت الوحدة...")
                sale_module.button_immediate_install()
                print("   ✅ تم تثبيت وحدة sale")
            else:
                print("   ✅ وحدة sale مثبتة")
            
            # 2. التحقق من القوائم
            print("\n2. التحقق من قوائم Sale...")
            sale_menus = env['ir.ui.menu'].search([
                ('name', 'ilike', 'sale'),
                '|', ('parent_id', '=', False),
                ('name', '=', 'Sales')
            ])
            
            if sale_menus:
                print(f"   تم العثور على {len(sale_menus)} قائمة:")
                for menu in sale_menus:
                    print(f"      - ID: {menu.id}, Name: {menu.name}, Active: {menu.active}, Parent: {menu.parent_id.name if menu.parent_id else 'Root'}")
                    if not menu.active:
                        print(f"        ⚠️  تفعيل القائمة...")
                        menu.active = True
            else:
                print("   ❌ لم يتم العثور على قوائم Sale!")
            
            # 3. التحقق من صلاحيات المستخدم الحالي
            print("\n3. التحقق من صلاحيات المستخدم...")
            admin_user = env['res.users'].browse(odoo.SUPERUSER_ID)
            sale_groups = env['ir.model.data'].search([
                ('module', '=', 'sale'),
                ('model', '=', 'res.groups')
            ])
            
            print(f"   المستخدم: {admin_user.name} (ID: {admin_user.id})")
            print(f"   المجموعات: {len(admin_user.groups_id)}")
            
            # إضافة المستخدم لمجموعات Sale إذا لزم الأمر
            sale_manager_group = env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
            if sale_manager_group and sale_manager_group not in admin_user.groups_id:
                print("   إضافة صلاحيات Sale Manager...")
                admin_user.write({'groups_id': [(4, sale_manager_group.id)]})
                print("   ✅ تم إضافة صلاحيات Sale Manager")
            
            # 4. مسح الكاش
            print("\n4. مسح الكاش...")
            env['ir.ui.menu'].invalidate_model()
            env['ir.ui.view'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم الفحص والإصلاح!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. مسح كاش المتصفح (Ctrl+Shift+Delete)")
            print("3. تسجيل الخروج وإعادة تسجيل الدخول")
            print("4. يجب أن تظهر قائمة Sales في القائمة الرئيسية")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    check_sale_module()
