#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح خطأ UoM Transaction Failed
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def fix_uom_transaction_error():
    """إصلاح خطأ المعاملة في وحدات القياس"""
    
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
    print(f"إصلاح خطأ UoM Transaction - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # إنشاء registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # 1. التحقق من وحدات القياس المعطوبة
            print("1. التحقق من وحدات القياس...")
            
            cr.execute("""
                SELECT id, name, relative_factor, relative_uom_id, factor
                FROM uom_uom
                WHERE relative_uom_id IS NOT NULL
                ORDER BY id
            """)
            
            uoms = cr.fetchall()
            print(f"   وحدات القياس مع relative_uom_id: {len(uoms)}")
            
            # 2. البحث عن وحدات قياس بمراجع دائرية أو معطوبة
            print("\n2. البحث عن مشاكل في وحدات القياس...")
            
            problematic_uoms = []
            
            for uom_id, name, relative_factor, relative_uom_id, factor in uoms:
                # التحقق من أن relative_uom_id موجود
                cr.execute("SELECT id FROM uom_uom WHERE id = %s", (relative_uom_id,))
                if not cr.fetchone():
                    print(f"   ❌ {name} (ID: {uom_id}): relative_uom_id {relative_uom_id} غير موجود!")
                    problematic_uoms.append(uom_id)
                    continue
                
                # التحقق من أن relative_factor ليس null أو صفر
                if not relative_factor or relative_factor == 0:
                    print(f"   ❌ {name} (ID: {uom_id}): relative_factor غير صالح ({relative_factor})")
                    problematic_uoms.append(uom_id)
                    continue
                
                # التحقق من المراجع الدائرية
                visited = set([uom_id])
                current_id = relative_uom_id
                depth = 0
                circular = False
                
                while current_id and depth < 10:
                    if current_id in visited:
                        print(f"   ❌ {name} (ID: {uom_id}): مرجع دائري!")
                        problematic_uoms.append(uom_id)
                        circular = True
                        break
                    
                    visited.add(current_id)
                    cr.execute("SELECT relative_uom_id FROM uom_uom WHERE id = %s", (current_id,))
                    result = cr.fetchone()
                    current_id = result[0] if result else None
                    depth += 1
                
                if not circular and depth >= 10:
                    print(f"   ⚠️  {name} (ID: {uom_id}): سلسلة طويلة جداً (depth > 10)")
            
            # 3. إصلاح وحدات القياس المعطوبة
            if problematic_uoms:
                print(f"\n3. إصلاح {len(problematic_uoms)} وحدة قياس معطوبة...")
                
                for uom_id in problematic_uoms:
                    # إزالة relative_uom_id وجعلها reference uom
                    cr.execute("""
                        UPDATE uom_uom
                        SET relative_uom_id = NULL,
                            relative_factor = 1.0,
                            factor = 1.0
                        WHERE id = %s
                    """, (uom_id,))
                    print(f"   ✅ تم إصلاح UoM ID: {uom_id}")
                
                cr.commit()
            else:
                print("\n3. ✅ لا توجد وحدات قياس معطوبة")
            
            # 4. إعادة حساب العوامل باستخدام SQL مباشرة
            print("\n4. إعادة حساب عوامل وحدات القياس...")
            
            try:
                # تحديث factor لوحدات القياس المرجعية (بدون relative_uom_id)
                cr.execute("""
                    UPDATE uom_uom
                    SET factor = relative_factor
                    WHERE relative_uom_id IS NULL
                """)
                updated_refs = cr.rowcount
                print(f"   ✅ تم تحديث {updated_refs} وحدة مرجعية")
                
                # تحديث factor لوحدات القياس المشتقة (بطريقة متكررة)
                # نبدأ من المستوى الأول ونتقدم للأمام
                max_depth = 10
                for depth in range(max_depth):
                    cr.execute("""
                        UPDATE uom_uom u1
                        SET factor = u1.relative_factor * u2.factor
                        FROM uom_uom u2
                        WHERE u1.relative_uom_id = u2.id
                          AND u1.relative_uom_id IS NOT NULL
                          AND u2.factor IS NOT NULL
                          AND (u1.factor IS NULL OR u1.factor != u1.relative_factor * u2.factor)
                    """)
                    updated = cr.rowcount
                    if updated == 0:
                        break
                    print(f"   ✅ المستوى {depth + 1}: تم تحديث {updated} وحدة")
                
                cr.commit()
                print(f"   ✅ تم إعادة حساب جميع وحدات القياس")
                
            except Exception as e:
                print(f"   ⚠️  تعذر إعادة الحساب: {e}")
                cr.rollback()
            
            # 5. التحقق من النتائج
            print("\n5. التحقق من وحدات القياس بعد الإصلاح...")
            
            cr.execute("""
                SELECT COUNT(*) 
                FROM uom_uom
                WHERE relative_uom_id IS NOT NULL
                  AND (relative_factor IS NULL OR relative_factor = 0)
            """)
            
            bad_count = cr.fetchone()[0]
            
            if bad_count > 0:
                print(f"   ⚠️  لا يزال هناك {bad_count} وحدة قياس بها مشاكل")
            else:
                print("   ✅ جميع وحدات القياس صالحة")
            
            # 6. مسح الكاش
            print("\n6. مسح الكاش...")
            env['uom.uom'].invalidate_model()
            registry.clear_cache()
            print("   ✅ تم مسح الكاش")
            
            # Commit final changes
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ تم إصلاح خطأ UoM Transaction!")
            print(f"{'='*60}\n")
            
            print("الخطوات التالية:")
            print("1. إعادة تشغيل Odoo")
            print("2. مسح كاش المتصفح (Ctrl+Shift+Delete)")
            print("3. تسجيل الدخول مرة أخرى")
            print("")
            
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            sys.exit(1)

if __name__ == '__main__':
    fix_uom_transaction_error()
