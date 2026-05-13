#!/usr/bin/env python3
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

print(f"🧪 اختبار: إنشاء مستند جديد بعد التحديث\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get folder with company
    folder = env['nbs.document.folder'].search([('company_id', '!=', False)], limit=1)
    
    if not folder:
        print("❌ لا يوجد فولدر بـ company_id")
        sys.exit(1)
    
    print(f"📁 الفولدر: {folder.name} (ID: {folder.id})")
    print(f"   └─ Company: {folder.company_id.name} (ID: {folder.company_id.id})")
    
    # Get required fields
    doc_type = env['nbs.document.type'].search([], limit=1)
    dept = folder.department_id
    
    print(f"\n📄 إنشاء مستند اختبار جديد...")
    
    # Create document - simulating what API does
    doc = env['nbs.document'].create({
        'name': 'مستند اختبار بعد التحديث - ' + str(env.context.get('tz')),
        'department_id': dept.id,
        'document_type_id': doc_type.id,
        'folder_id': folder.id,
        'folder_role': 'main',
        'uploader_id': 1,
    })
    
    cr.commit()
    
    # Reload to get computed values
    doc = env['nbs.document'].browse(doc.id)
    
    print(f"✅ تم إنشاء المستند: ID {doc.id}")
    print(f"\n📊 التفاصيل:")
    print(f"   ├─ Name: {doc.name}")
    print(f"   ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   ├─ folder_name: {doc.folder_id.name if doc.folder_id else 'NULL'}")
    print(f"   ├─ company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
    print(f"   └─ company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
    
    if doc.company_id and doc.company_id.id == folder.company_id.id:
        print(f"\n✅✅✅ نجح! المستند حصل على company_id من الفولدر!")
        print(f"\n🎯 الآن اختبر عبر API:")
        print(f"   POST /api/documents")
        print(f"   يجب أن ترى المستند {doc.id} مع:")
        print(f"     - company_id: {doc.company_id.id}")
        print(f"     - company_name: '{doc.company_id.name}'")
    else:
        print(f"\n❌ فشل! المستند لم يحصل على company_id")
        print(f"   Expected: {folder.company_id.id}")
        print(f"   Got: {doc.company_id.id if doc.company_id else 'NULL'}")
