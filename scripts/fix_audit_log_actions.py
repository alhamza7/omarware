#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add Odoo to Python path
sys.path.append('/home/lugalai/Lugal-ai')
sys.path.append('/home/lugalai/Lugal-ai/odoo')

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

def fix_audit_log_actions():
    """
    Fix audit log actions that have invalid values
    """
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', '/home/lugalai/Lugal-ai/odoo.conf'])
    
    dbname = 'nbs_lugalai'
    registry = Registry(dbname)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 60)
        print("فحص وإصلاح قيم action في nbs.audit.log")
        print("=" * 60)
        print()
        
        # 1. Check current audit logs with invalid actions
        print("1. البحث عن سجلات التدقيق بقيم action غير صحيحة...")
        
        # Get all valid actions from the model
        AuditLog = env['nbs.audit.log']
        valid_actions = dict(AuditLog._fields['action'].selection)
        print(f"   📋 الإجراءات الصحيحة المتاحة ({len(valid_actions)}):")
        for key, value in valid_actions.items():
            print(f"      - {key}: {value}")
        
        print()
        
        # Query for logs with potentially invalid actions
        cr.execute("""
            SELECT DISTINCT action, COUNT(*) as count
            FROM nbs_audit_log
            GROUP BY action
            ORDER BY count DESC
        """)
        
        all_actions = cr.fetchall()
        print(f"   📊 الإجراءات المستخدمة في قاعدة البيانات ({len(all_actions)}):")
        
        invalid_actions = []
        for action, count in all_actions:
            if action in valid_actions:
                print(f"      ✅ {action}: {count} سجل")
            else:
                print(f"      ❌ {action}: {count} سجل (غير صحيح!)")
                invalid_actions.append((action, count))
        
        print()
        
        if not invalid_actions:
            print("   ✅ جميع الإجراءات صحيحة!")
            print()
        else:
            print(f"   ⚠️  وجدت {len(invalid_actions)} إجراء غير صحيح")
            print()
            
            # 2. Provide correction suggestions
            print("2. اقتراحات التصحيح:")
            
            corrections = {
                'atachment_upload': 'attachment_upload',
                'signed_version_upload': 'signed_version_uploaded',
                'new_version_upload': 'new_version_uploaded',
            }
            
            for invalid_action, count in invalid_actions:
                suggested = corrections.get(invalid_action, 'upload')
                print(f"   📝 {invalid_action} ({count} سجل)")
                print(f"      💡 التصحيح المقترح: {suggested}")
                
                # Ask for confirmation (in production, you might want to auto-correct)
                print(f"      ℹ️  يمكن تصحيحه يدوياً بـ SQL:")
                print(f"         UPDATE nbs_audit_log SET action = '{suggested}' WHERE action = '{invalid_action}';")
                print()
        
        # 3. Show recent audit logs
        print("3. أحدث 10 سجلات تدقيق:")
        logs = AuditLog.search([], limit=10, order='timestamp desc')
        for log in logs:
            action_display = dict(AuditLog._fields['action'].selection).get(log.action, log.action)
            print(f"   - {log.timestamp}: {log.user_id.name} - {log.action} ({action_display})")
            if log.document_id:
                print(f"     المستند: {log.document_id.name}")
            if log.metadata:
                print(f"     البيانات: {log.metadata[:50]}...")
        
        print()
        env.cr.commit()
    
    print("=" * 60)
    print("✅ اكتمل الفحص!")
    print("=" * 60)
    print()
    print("💡 ملاحظات:")
    print("1. تم تحديث نموذج nbs.audit.log لإضافة الإجراءات المفقودة")
    print("2. يجب ترقية وحدة nbs_archive لتطبيق التغييرات:")
    print("   bash upgrade_nbs_archive.sh")
    print()
    print("3. إذا وجدت قيم غير صحيحة، يمكن تصحيحها بـ SQL")
    print()

if __name__ == '__main__':
    fix_audit_log_actions()
