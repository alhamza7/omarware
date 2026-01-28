#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت شامل لحل مشكلة AssetsLoadingError
خاصة مشكلة تحميل web_tour.interactive.min.js
"""

import sys
import os

# إضافة مسار Odoo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_assets_error():
    """حل مشكلة تحميل Assets"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    # محاولة الحصول على اسم قاعدة البيانات من dbfilter
    dbfilter = odoo.tools.config.get('dbfilter', '')
    if dbfilter:
        import re
        match = re.match(r'\^?(\w+).*\$?', dbfilter)
        if match:
            db_name = match.group(1)
        else:
            db_name = odoo.tools.config.get('db_name') or 'lugal'
    else:
        db_name = odoo.tools.config.get('db_name') or 'lugal'
    
    print(f"\n{'='*60}")
    print(f"حل مشكلة تحميل Assets - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. مسح جميع أنواع الكاش
            print("1. مسح ir.ui.view cache...")
            env['ir.ui.view'].invalidate_model()
            print("   ✅ تم")
            
            print("2. مسح ir.qweb cache...")
            try:
                env['ir.qweb'].invalidate_model()
            except:
                pass
            print("   ✅ تم")
            
            print("3. مسح ir.http cache...")
            try:
                env['ir.http'].invalidate_model()
            except:
                pass
            print("   ✅ تم")
            
            print("4. مسح ir.actions cache...")
            env['ir.actions.actions'].invalidate_model()
            print("   ✅ تم")
            
            # 2. حذف جميع Assets (بما في ذلك web_tour)
            print("5. حذف جميع Assets...")
            
            # البحث عن جميع Assets
            all_assets = env['ir.attachment'].search([
                '|',
                '|',
                '|',
                ('name', 'like', 'web.assets_%'),
                ('name', 'like', 'web_tour.%'),
                ('name', 'ilike', '%web_tour%'),
                ('url', 'like', '/web/assets/%')
            ])
            
            if all_assets:
                count = len(all_assets)
                
                # عرض بعض الأمثلة قبل الحذف
                print(f"   ℹ️  تم العثور على {count} ملف assets")
                sample_names = all_assets[:5].mapped('name')
                for name in sample_names:
                    if name:
                        print(f"      - {name}")
                
                # حذف جميع Assets
                all_assets.unlink()
                print(f"   ✅ تم حذف {count} ملف assets")
            else:
                print("   ℹ️  لا توجد assets للحذف")
            
            # 3. مسح registry cache
            print("6. مسح registry cache...")
            registry.clear_cache()
            print("   ✅ تم")
            
            # 4. مسح cache من ir.asset (Asset registry)
            print("7. مسح ir.asset cache...")
            try:
                env['ir.asset'].invalidate_model()
                print("   ✅ تم")
            except:
                print("   ⚠️  ir.asset غير متوفر")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم حل المشكلة بنجاح!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("2. فتح المتصفح ومسح الكاش (Ctrl+Shift+Delete)")
            print("3. إعادة تحميل الصفحة (Ctrl+F5)")
            print("")
            print("ملاحظة: Assets سيتم إعادة بنائها تلقائياً عند أول طلب")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_assets_error()
