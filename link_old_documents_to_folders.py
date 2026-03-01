#!/usr/bin/env python3
"""
ربط المستندات القديمة بفولدرات لكي ترث company_id
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', 'odoo_local.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal_local'
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"🔗 ربط المستندات القديمة بفولدرات - قاعدة البيانات: {db_name}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get documents without folder
    docs_without_folder = env['nbs.document'].search([
        ('folder_id', '=', False),
        ('is_deleted', '=', False)
    ])
    
    print(f"📊 عدد المستندات بدون فولدر: {len(docs_without_folder)}\n")
    
    if not docs_without_folder:
        print("✅ جميع المستندات مربوطة بفولدرات!")
        sys.exit(0)
    
    # Get or create a default folder for each department/company combination
    updated_count = 0
    
    for doc in docs_without_folder:
        print(f"📄 معالجة: {doc.name} (ID: {doc.id})")
        
        # Find or create a folder for this document
        dept = doc.department_id
        
        if not dept:
            print(f"   ⚠️  المستند بدون قسم - تخطي")
            continue
        
        # Look for existing folder in same department
        # You can modify this logic based on your needs
        folder = env['nbs.document.folder'].search([
            ('department_id', '=', dept.id),
            ('active', '=', True)
        ], limit=1)
        
        if not folder:
            # Create a default folder
            print(f"   📁 إنشاء فولدر جديد للقسم: {dept.name}")
            folder = env['nbs.document.folder'].create({
                'name': f'مستندات {dept.name}',
                'code': f'{dept.code or "DOC"}',
                'department_id': dept.id,
                'owner_id': 1,
            })
        
        # Link document to folder
        doc.write({
            'folder_id': folder.id,
            'folder_role': 'main' if not doc.parent_document_id else 'sub'
        })
        
        # Check if company_id was inherited
        doc.invalidate_recordset()
        doc_after = env['nbs.document'].browse(doc.id)
        
        company_status = f"company_id = {doc_after.company_id.id}" if doc_after.company_id else "لا توجد شركة"
        print(f"   ✓ تم الربط بالفولدر: {folder.name} ({company_status})")
        updated_count += 1
    
    # Commit changes
    cr.commit()
    
    print(f"\n✅ اكتمل!")
    print(f"   📄 تم تحديث {updated_count} مستند")
    print(f"\n💡 ملاحظة: إذا كنت تريد تعيين شركة معينة للفولدرات،")
    print(f"   يمكنك تحديث الفولدرات عبر: POST /api/folders/<id>/update")
    print(f"   مع company_id في الـ body")
