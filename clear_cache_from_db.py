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
    # محاولة الحصول على اسم قاعدة البيانات من dbfilter أو استخدام القيمة الافتراضية
    dbfilter = odoo.tools.config.get('dbfilter', '')
    if dbfilter:
        # استخراج اسم قاعدة البيانات من dbfilter (مثل ^lugal_nbs.*$ -> lugal_nbs)
        import re
        match = re.match(r'\^?(\w+).*\$?', dbfilter)
        if match:
            db_name = match.group(1)
        else:
            db_name = odoo.tools.config.get('db_name') or 'lugal'
    else:
        db_name = odoo.tools.config.get('db_name') or 'lugal'
    
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
            
            # 5. حذف assets القديمة
            print("5. حذف assets القديمة...")
            assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', 'web.assets_%'),
                ('url', 'like', '/web/assets/%')
            ])
            if assets:
                count = len(assets)
                assets.unlink()
                print(f"   ✅ تم حذف {count} ملف assets")
            else:
                print("   ℹ️  لا توجد assets للحذف")
            
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

