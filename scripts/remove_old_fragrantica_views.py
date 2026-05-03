#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لحذف جميع Views القديمة المتعلقة بـ Fragrantica من res.config.settings
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def remove_old_views():
    """حذف Views القديمة"""
    
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
    print(f"حذف Views القديمة - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # البحث عن جميع views المتعلقة بـ fragrantica في res.config.settings
            print("1. البحث عن Views القديمة...")
            
            old_views = env['ir.ui.view'].search([
                ('name', 'ilike', 'fragrantica'),
                ('model', '=', 'res.config.settings')
            ])
            
            if old_views:
                print(f"   تم العثور على {len(old_views)} view قديم:")
                for view in old_views:
                    print(f"      - ID: {view.id}, Name: {view.name}")
                
                print("\n2. حذف Views القديمة...")
                old_views.unlink()
                print(f"   ✅ تم حذف {len(old_views)} view")
            else:
                print("   ℹ️  لم يتم العثور على views قديمة")
            
            # مسح الكاش
            print("\n3. مسح الكاش...")
            env['ir.ui.view'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم حذف Views القديمة بنجاح!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. ترقية وحدة lugal_fragrantica (سيُنشئ views جديدة صحيحة)")
            print("   venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u lugal_fragrantica --stop-after-init")
            print("")
            print("2. إعادة تشغيل Odoo")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("3. مسح كاش المتصفح وإعادة التحميل")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    remove_old_views()
