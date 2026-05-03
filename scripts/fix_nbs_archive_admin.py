#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح صلاحيات نظام الأرشفة NBS Archive
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_nbs_archive_permissions():
    """إصلاح صلاحيات الأدمن في نظام الأرشفة"""
    
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
    print(f"إصلاح صلاحيات NBS Archive - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من وحدة nbs_archive
            print("1. التحقق من وحدة nbs_archive...")
            nbs_module = env['ir.module.module'].search([('name', '=', 'nbs_archive')])
            
            if not nbs_module:
                print("   ❌ وحدة nbs_archive غير موجودة!")
                print("   يرجى تثبيت الوحدة أولاً")
                return
            
            if nbs_module.state != 'installed':
                print(f"   ⚠️  وحدة nbs_archive في حالة: {nbs_module.state}")
                print("   يرجى تثبيت الوحدة أولاً")
                return
            
            print(f"   ✅ وحدة nbs_archive مثبتة")
            
            # 2. التحقق من المجموعات
            print("\n2. التحقق من مجموعات NBS Archive...")
            
            groups = {
                'user': env.ref('nbs_archive.group_nbs_user', raise_if_not_found=False),
                'manager': env.ref('nbs_archive.group_nbs_manager', raise_if_not_found=False),
                'admin': env.ref('nbs_archive.group_nbs_admin', raise_if_not_found=False),
            }
            
            for name, group in groups.items():
                if group:
                    print(f"   ✅ Group {name}: {group.name}")
                else:
                    print(f"   ❌ Group {name}: Not found!")
            
            # 3. إضافة الصلاحيات للأدمن
            print("\n3. إضافة صلاحيات NBS Archive للأدمن...")
            
            admin_user = env['res.users'].browse(odoo.SUPERUSER_ID)
            print(f"   المستخدم: {admin_user.name}")
            
            added_groups = []
            for name, group in groups.items():
                if group and group not in admin_user.group_ids:
                    admin_user.write({'group_ids': [(4, group.id)]})
                    added_groups.append(name)
                    print(f"   ✅ تم إضافة: {group.name}")
                elif group:
                    print(f"   ℹ️  موجود بالفعل: {group.name}")
            
            # 4. التحقق من البيانات الافتراضية
            print("\n4. التحقق من البيانات الافتراضية...")
            
            # الأقسام
            departments = env['nbs.department'].search([])
            print(f"   📁 الأقسام: {len(departments)}")
            for dept in departments:
                print(f"      - {dept.name} ({dept.code})")
            
            # أنواع المستندات
            doc_types = env['nbs.document.type'].search([])
            print(f"\n   📄 أنواع المستندات: {len(doc_types)}")
            for doctype in doc_types:
                print(f"      - {doctype.name} ({doctype.code}) - {doctype.department_id.name}")
            
            # 5. مسح الكاش
            print("\n5. مسح الكاش...")
            env['res.users'].invalidate_model()
            env['res.groups'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم إصلاح صلاحيات NBS Archive!")
            print(f"{'='*60}\n")
            
            if added_groups:
                print("تم إضافة الصلاحيات التالية للأدمن:")
                for group in added_groups:
                    print(f"   ✅ {group}")
            else:
                print("✅ الأدمن لديه جميع الصلاحيات بالفعل")
            
            print("\nالآن يمكنك:")
            print("1. تسجيل الدخول إلى Odoo")
            print("2. الذهاب إلى: NBS Archive")
            print("3. يجب أن ترى جميع القوائم والصلاحيات")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_nbs_archive_permissions()
