#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لمسح الكاش من قاعدة البيانات مباشرة
يمكن تشغيله من Odoo shell أو منفصلاً
"""

import sys
import os

# إضافة مسار Odoo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def clear_all_cache():
    """مسح جميع أنواع الكاش"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    # محاولة الحصول على اسم قاعدة البيانات
    # أولاً من db_name، ثم من dbfilter
    db_name = odoo.tools.config.get('db_name', '')
    if not db_name:
        dbfilter = odoo.tools.config.get('dbfilter', '')
        if dbfilter:
            # استخراج اسم قاعدة البيانات من dbfilter (مثل ^lugal_nbs.*$ -> lugal_nbs)
            import re
            match = re.match(r'\^?(\w+).*\$?', dbfilter)
            if match:
                db_name = match.group(1)
    
    # القيمة الافتراضية
    if not db_name:
        db_name = 'lugal'
    
    print(f"\n{'='*60}")
    print(f"مسح الكاش من قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. مسح ir.ui.view cache
            print("1. مسح ir.ui.view cache...")
            env['ir.ui.view'].invalidate_model()
            print("   ✅ تم")
            
            # 2. مسح ir.qweb cache
            print("2. مسح ir.qweb cache...")
            try:
                env['ir.qweb'].invalidate_model()
            except:
                pass
            print("   ✅ تم")
            
            # 3. مسح ir.http cache
            print("3. مسح ir.http cache...")
            try:
                env['ir.http'].invalidate_model()
            except:
                pass
            print("   ✅ تم")
            
            # 4. مسح ir.actions cache
            print("4. مسح ir.actions cache...")
            env['ir.actions.actions'].invalidate_model()
            print("   ✅ تم")
            
            # 5. حذف assets القديمة (جميع أنواع Assets)
            print("5. حذف assets القديمة...")
            
            # حذف جميع assets المتعلقة بـ web
            web_assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', 'web.assets_%'),
                ('url', 'like', '/web/assets/%')
            ])
            
            # حذف assets المتعلقة بـ web_tour
            web_tour_assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', 'web_tour.%'),
                ('name', 'ilike', '%web_tour%')
            ])
            
            # حذف جميع assets الأخرى
            all_assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', '%.assets_%'),
                ('url', 'like', '/web/assets/%')
            ])
            
            total_count = 0
            if web_assets:
                count = len(web_assets)
                web_assets.unlink()
                total_count += count
                print(f"   ✅ تم حذف {count} ملف web assets")
            
            if web_tour_assets:
                count = len(web_tour_assets)
                web_tour_assets.unlink()
                total_count += count
                print(f"   ✅ تم حذف {count} ملف web_tour assets")
            
            if all_assets and total_count == 0:
                count = len(all_assets)
                all_assets.unlink()
                total_count = count
                print(f"   ✅ تم حذف {count} ملف assets")
            
            if total_count == 0:
                print("   ℹ️  لا توجد assets للحذف")
            else:
                print(f"   ✅ إجمالي الملفات المحذوفة: {total_count}")
            
            # 6. مسح registry cache
            print("6. مسح registry cache...")
            registry.clear_cache()
            print("   ✅ تم")
            
            # 7. مسح cache من sale.order و pos.perfume.order
            print("7. مسح cache من sale.order و pos.perfume.order...")
            try:
                env['sale.order'].invalidate_model()
                print("   ✅ تم مسح sale.order cache")
            except (KeyError, AttributeError) as e:
                print(f"   ⚠️  sale.order غير متوفر (قد تكون وحدة sale غير مثبتة)")
            
            try:
                env['pos.perfume.order'].invalidate_model()
                print("   ✅ تم مسح pos.perfume.order cache")
            except (KeyError, AttributeError) as e:
                print(f"   ⚠️  pos.perfume.order غير متوفر (قد تكون وحدة pos_perfume_custom غير مثبتة)")
            
            print("   ✅ تم")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم مسح جميع أنواع الكاش بنجاح!")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    clear_all_cache()

