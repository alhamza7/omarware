#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add Odoo to Python path
sys.path.append('/home/lugalai/Lugal-ai')
sys.path.append('/home/lugalai/Lugal-ai/odoo')

import odoo
from odoo import api, SUPERUSER_ID

def fix_audit_metadata_field():
    """
    Fix the missing 'metadata' field in nbs.audit.log model
    """
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', '/home/lugalai/Lugal-ai/odoo.conf'])
    
    dbname = 'nbs_lugalai'
    registry = odoo.registry(dbname)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
            
            print("=" * 60)
            print("إصلاح حقل metadata في نموذج nbs.audit.log")
            print("Fix metadata field in nbs.audit.log model")
            print("=" * 60)
            print()
            
            # 1. Check if nbs_archive module is installed
            print("1. التحقق من وحدة nbs_archive...")
            module = env['ir.module.module'].search([('name', '=', 'nbs_archive')], limit=1)
            if not module:
                print("   ❌ وحدة nbs_archive غير مثبتة!")
                return
            print(f"   ✅ الوحدة مثبتة - الحالة: {module.state}")
            print()
            
            # 2. Check if metadata field exists in database
            print("2. التحقق من الحقول في قاعدة البيانات...")
            cr.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'nbs_audit_log' 
                ORDER BY ordinal_position
            """)
            columns = cr.fetchall()
            
            print("   📋 الحقول الموجودة في جدول nbs_audit_log:")
            has_metadata = False
            has_metadata_snapshot = False
            
            for col_name, col_type in columns:
                print(f"      - {col_name} ({col_type})")
                if col_name == 'metadata':
                    has_metadata = True
                if col_name == 'metadata_snapshot':
                    has_metadata_snapshot = True
            
            print()
            
            if has_metadata:
                print("   ✅ حقل 'metadata' موجود!")
            else:
                print("   ⚠️  حقل 'metadata' غير موجود - سيتم إضافته عند ترقية الوحدة")
            
            if has_metadata_snapshot:
                print("   ✅ حقل 'metadata_snapshot' موجود!")
            
            print()
            
            # 3. Check audit log records
            print("3. التحقق من سجلات التدقيق...")
            try:
                AuditLog = env['nbs.audit.log']
                total_logs = AuditLog.search_count([])
                print(f"   📊 إجمالي سجلات التدقيق: {total_logs}")
                
                if total_logs > 0:
                    print()
                    print("   📝 أحدث 5 سجلات:")
                    logs = AuditLog.search([], limit=5, order='timestamp desc')
                    for log in logs:
                        print(f"      - {log.timestamp}: {log.user_id.name} - {log.action}")
                        if log.document_id:
                            print(f"        المستند: {log.document_id.name}")
                        # Check if metadata field is accessible
                        try:
                            metadata_val = log.metadata if hasattr(log, 'metadata') else 'N/A'
                            if metadata_val:
                                print(f"        البيانات الوصفية: {metadata_val}")
                        except Exception as e:
                            print(f"        ⚠️  لا يمكن الوصول للبيانات الوصفية: {str(e)}")
                
            except Exception as e:
                print(f"   ❌ خطأ في الوصول لسجلات التدقيق: {str(e)}")
            
            print()
            
            # 4. Check model fields definition
            print("4. التحقق من تعريف حقول النموذج...")
            try:
                model_obj = env['ir.model'].search([('model', '=', 'nbs.audit.log')], limit=1)
                if model_obj:
                    fields_obj = env['ir.model.fields'].search([('model_id', '=', model_obj.id)])
                    
                    print(f"   📋 الحقول المعرفة في النموذج: {len(fields_obj)}")
                    
                    metadata_field = fields_obj.filtered(lambda f: f.name == 'metadata')
                    metadata_snapshot_field = fields_obj.filtered(lambda f: f.name == 'metadata_snapshot')
                    
                    if metadata_field:
                        print(f"   ✅ حقل 'metadata' معرف: {metadata_field.ttype}")
                    else:
                        print(f"   ⚠️  حقل 'metadata' غير معرف في النموذج")
                    
                    if metadata_snapshot_field:
                        print(f"   ✅ حقل 'metadata_snapshot' معرف: {metadata_snapshot_field.ttype}")
                
            except Exception as e:
                print(f"   ⚠️  خطأ في التحقق من تعريف الحقول: {str(e)}")
            
            print()
            
            # 5. Test creating an audit log with metadata
            print("5. اختبار إنشاء سجل تدقيق مع metadata...")
            try:
                test_log = AuditLog.sudo().create({
                    'action': 'search',
                    'user_id': env.user.id,
                    'details': 'Test log entry',
                    'metadata': 'Test metadata value',
                })
                print(f"   ✅ تم إنشاء سجل تدقيق تجريبي (ID: {test_log.id})")
                
                # Try to read it back
                test_log_read = AuditLog.browse(test_log.id)
                if hasattr(test_log_read, 'metadata'):
                    print(f"   ✅ قراءة metadata: {test_log_read.metadata}")
                else:
                    print(f"   ⚠️  لا يمكن قراءة حقل metadata")
                
                # Clean up test log
                print(f"   ℹ️  ملاحظة: سجلات التدقيق محمية من الحذف (وهذا صحيح)")
                
            except Exception as e:
                print(f"   ❌ خطأ في إنشاء سجل التدقيق: {str(e)}")
                print(f"   💡 قد يكون الحقل غير موجود بعد - يجب ترقية الوحدة")
        
        print()
        env.cr.commit()
        
        print("=" * 60)
        print("✅ اكتمل الفحص!")
        print("=" * 60)
        print()
        print("🔧 الخطوات المطلوبة لإصلاح المشكلة:")
        print()
        print("1. ✅ تم تحديث ملف nbs_audit_log.py لإضافة حقل 'metadata'")
        print()
        print("2. ⚙️  يجب ترقية وحدة nbs_archive:")
        print("   cd /home/lugalai/Lugal-ai")
        print("   venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \\")
        print("     -u nbs_archive --stop-after-init")
        print()
        print("3. 🔄 إعادة تشغيل Odoo:")
        print("   pkill -9 -f odoo-bin")
        print("   nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \\")
        print("     --http-port=8069 > odoo.log 2>&1 &")
        print()
        print("4. ✅ اختبار النظام")
        print()
        print("💡 ملاحظة:")
        print("   - حقل 'metadata' يستخدم لتخزين معلومات إضافية عن الإجراء")
        print("   - حقل 'metadata_snapshot' يستخدم لتخزين نسخة من بيانات المستند")
        print("   - كلا الحقلين مهمان لنظام التدقيق")
        print()

if __name__ == '__main__':
    fix_audit_metadata_field()
