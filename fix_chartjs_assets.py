#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت خاص لحل مشكلة تحميل web.chartjs_lib.min.js
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_chartjs_assets():
    """حل مشكلة Chart.js Assets"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    # الحصول على اسم قاعدة البيانات
    db_name = odoo.tools.config.get('db_name', '')
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
    print(f"حل مشكلة Chart.js Assets - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            print("1. البحث عن Assets المتعلقة بـ Chart.js...")
            
            # حذف جميع assets المتعلقة بـ chartjs
            chartjs_assets = env['ir.attachment'].search([
                '|',
                '|',
                ('name', 'ilike', '%chartjs%'),
                ('name', 'ilike', '%chart.js%'),
                ('url', 'ilike', '%chartjs%')
            ])
            
            if chartjs_assets:
                print(f"   تم العثور على {len(chartjs_assets)} ملف chart.js assets")
                for asset in chartjs_assets[:5]:
                    print(f"      - {asset.name}")
                chartjs_assets.unlink()
                print(f"   ✅ تم حذف جميع Chart.js assets")
            else:
                print("   ℹ️  لم يتم العثور على chart.js assets")
            
            print("\n2. حذف جميع Web Assets...")
            
            # حذف جميع web assets
            web_assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', 'web.assets_%'),
                ('url', 'like', '/web/assets/%')
            ])
            
            if web_assets:
                count = len(web_assets)
                web_assets.unlink()
                print(f"   ✅ تم حذف {count} ملف web assets")
            
            print("\n3. مسح جميع أنواع الكاش...")
            
            # مسح الكاش
            env['ir.ui.view'].invalidate_model()
            print("   ✅ تم مسح ir.ui.view cache")
            
            try:
                env['ir.qweb'].invalidate_model()
            except:
                pass
            print("   ✅ تم مسح ir.qweb cache")
            
            try:
                env['ir.http'].invalidate_model()
            except:
                pass
            print("   ✅ تم مسح ir.http cache")
            
            env['ir.actions.actions'].invalidate_model()
            print("   ✅ تم مسح ir.actions cache")
            
            # مسح registry cache
            registry.clear_cache()
            print("   ✅ تم مسح registry cache")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم حل مشكلة Chart.js بنجاح!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("2. مسح كاش المتصفح تماماً (Ctrl+Shift+Delete)")
            print("3. إغلاق المتصفح وفتحه من جديد")
            print("4. الدخول على الموقع")
            print("")
            print("ملاحظة: عند أول تحميل، سيستغرق إعادة بناء Assets بضع ثوانٍ")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_chartjs_assets()
