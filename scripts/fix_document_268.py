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

print(f"🔧 إصلاح المستند 268\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get document 268
    doc = env['nbs.document'].browse(268)
    
    if not doc.exists():
        print("❌ المستند 268 غير موجود")
        sys.exit(1)
    
    print(f"📄 المستند: {doc.name} (ID: {doc.id})")
    print(f"   └─ folder_id قبل: {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   └─ company_id قبل: {doc.company_id.id if doc.company_id else 'NULL'}")
    
    # Find the folder that was supposed to be for this document
    # Looking for folder "testymainnnnn" or similar
    folder = env['nbs.document.folder'].search([
        ('name', 'ilike', 'testymainnnnn'),
        ('active', '=', True)
    ], limit=1)
    
    if not folder:
        # Use any folder with company_id
        folder = env['nbs.document.folder'].search([
            ('company_id', '!=', False),
            ('active', '=', True)
        ], limit=1)
    
    if not folder:
        print("❌ لا يوجد فولدر مناسب")
        sys.exit(1)
    
    print(f"\n📁 الفولدر المختار: {folder.name} (ID: {folder.id})")
    print(f"   └─ Company: {folder.company_id.name if folder.company_id else 'لا توجد'}")
    
    # Update document
    print(f"\n🔄 تحديث المستند...")
    doc.write({
        'folder_id': folder.id,
        'folder_role': 'main'
    })
    
    cr.commit()
    
    # Reload
    doc = env['nbs.document'].browse(268)
    
    print(f"\n✅ تم التحديث!")
    print(f"   └─ folder_id بعد: {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   └─ company_id بعد: {doc.company_id.id if doc.company_id else 'NULL'}")
    print(f"   └─ company_name بعد: {doc.company_id.name if doc.company_id else 'NULL'}")
    
    if doc.company_id:
        print(f"\n🎉 نجح! الآن المستند لديه company_id")
    else:
        print(f"\n⚠️ لم يتم تعيين company_id - ربما الفولدر ليس لديه شركة")
