#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح القوائم الفرعية (Sub Menus) في Sale
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_sale_submenus():
    """إصلاح وتفعيل القوائم الفرعية في Sale"""
    
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
    print(f"إصلاح القوائم الفرعية في Sale - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. البحث عن القائمة الرئيسية Sales
            print("1. البحث عن القائمة الرئيسية Sales...")
            main_sale_menu = env['ir.ui.menu'].search([
                ('name', 'in', ['Sales', 'المبيعات']),
                ('parent_id', '=', False)
            ], limit=1)
            
            if not main_sale_menu:
                print("   ❌ القائمة الرئيسية Sales غير موجودة!")
                print("   يرجى تشغيل fix_sale_menu_remote.sh أولاً")
                return
            
            print(f"   ✅ القائمة الرئيسية موجودة (ID: {main_sale_menu.id})")
            
            # 2. البحث عن جميع القوائم الفرعية
            print("\n2. البحث عن القوائم الفرعية...")
            
            # البحث عن قوائم sale module
            sale_submenus = env['ir.ui.menu'].search([
                '|', 
                ('parent_id', '=', main_sale_menu.id),
                '&', ('parent_id', '!=', False),
                     '|', ('name', 'ilike', 'sale'),
                          '|', ('name', 'ilike', 'order'),
                               '|', ('name', 'ilike', 'quotation'),
                                    ('name', 'ilike', 'customer')
            ])
            
            print(f"   تم العثور على {len(sale_submenus)} قائمة فرعية")
            
            if sale_submenus:
                print("\n   القوائم الفرعية الموجودة:")
                for menu in sale_submenus:
                    status = "✅ نشط" if menu.active else "❌ معطل"
                    parent_name = menu.parent_id.name if menu.parent_id else "Root"
                    print(f"      - {menu.name} ({status}) - Parent: {parent_name}")
                    
                    # تفعيل القوائم المعطلة
                    if not menu.active:
                        menu.active = True
                        print(f"        ✅ تم تفعيل {menu.name}")
                    
                    # نقل القوائم التي ليست تحت Sales إلى Sales
                    if menu.parent_id and menu.parent_id.id != main_sale_menu.id:
                        # فقط القوائم المتعلقة بـ sale
                        if any(keyword in menu.name.lower() for keyword in ['sale', 'order', 'quotation']):
                            print(f"        📌 نقل {menu.name} إلى Sales...")
                            menu.parent_id = main_sale_menu.id
            
            # 3. التحقق من وجود القوائم الأساسية المطلوبة
            print("\n3. التحقق من القوائم الأساسية...")
            
            required_menus = [
                ('Orders', 'sale.order', 'tree,form', [('state', 'in', ['sale', 'done'])]),
                ('Quotations', 'sale.order', 'tree,form', [('state', 'in', ['draft', 'sent'])]),
                ('Customers', 'res.partner', 'kanban,tree,form', [('customer_rank', '>', 0)]),
                ('Products', 'product.template', 'kanban,tree,form', [('sale_ok', '=', True)]),
            ]
            
            created_count = 0
            for menu_name, model, view_mode, domain in required_menus:
                existing = env['ir.ui.menu'].search([
                    ('name', '=', menu_name),
                    ('parent_id', '=', main_sale_menu.id)
                ], limit=1)
                
                if not existing:
                    print(f"   ⚠️  القائمة '{menu_name}' مفقودة - جاري الإنشاء...")
                    
                    # إنشاء action
                    action = env['ir.actions.act_window'].create({
                        'name': menu_name,
                        'res_model': model,
                        'view_mode': view_mode,
                        'domain': str(domain),
                        'context': "{'default_user_id': uid}",
                    })
                    
                    # إنشاء القائمة
                    new_menu = env['ir.ui.menu'].create({
                        'name': menu_name,
                        'parent_id': main_sale_menu.id,
                        'action': f'ir.actions.act_window,{action.id}',
                        'sequence': 10 + created_count * 10,
                    })
                    
                    print(f"      ✅ تم إنشاء القائمة '{menu_name}' (ID: {new_menu.id})")
                    created_count += 1
                else:
                    status = "نشط ✅" if existing.active else "معطل ❌"
                    print(f"   ✅ القائمة '{menu_name}' موجودة ({status})")
                    if not existing.active:
                        existing.active = True
                        print(f"      ✅ تم تفعيل '{menu_name}'")
            
            # 4. إعادة ترتيب القوائم الفرعية
            print("\n4. إعادة ترتيب القوائم الفرعية...")
            all_submenus = env['ir.ui.menu'].search([
                ('parent_id', '=', main_sale_menu.id),
                ('active', '=', True)
            ], order='sequence,name')
            
            print(f"   عدد القوائم الفرعية النشطة: {len(all_submenus)}")
            for idx, menu in enumerate(all_submenus):
                menu.sequence = (idx + 1) * 10
                print(f"      {idx + 1}. {menu.name}")
            
            # 5. مسح الكاش
            print("\n5. مسح الكاش...")
            env['ir.ui.menu'].invalidate_model()
            env['ir.ui.view'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit
            cr.commit()
            
            print(f"\n{'='*60}")
            print(f"✅ تم إصلاح القوائم الفرعية! (تم إنشاء {created_count} قائمة جديدة)")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("   pkill -9 -f odoo-bin")
            print("   nohup venv/bin/python odoo-bin -c odoo.conf -d " + db_name + " --http-port=8069 > odoo.log 2>&1 &")
            print("")
            print("2. مسح كاش المتصفح (Ctrl+Shift+R)")
            print("3. إعادة تحميل الصفحة")
            print("")
            print("يجب أن تظهر القوائم الفرعية الآن داخل Sales:")
            print("   - Orders (الطلبات)")
            print("   - Quotations (عروض الأسعار)")
            print("   - Customers (العملاء)")
            print("   - Products (المنتجات)")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_sale_submenus()
