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

print(f"🔧 Fixing document 276\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    doc = env['nbs.document'].browse(276)
    if not doc.exists():
        print("❌ Document 276 not found")
        sys.exit(1)
    
    # Check if it's in folder_ids (Many2many)
    print(f"📄 Document: {doc.name}")
    print(f"   ├─ folder_id (Many2one): {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   ├─ folder_ids (Many2many): {doc.folder_ids.ids}")
    print(f"   └─ company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
    
    if doc.folder_ids and not doc.folder_id:
        folder = doc.folder_ids[0]
        print(f"\n📁 Found folder in Many2many: {folder.name} (ID: {folder.id})")
        print(f"   └─ Folder company: {folder.company_id.name if folder.company_id else 'NULL'}")
        
        print(f"\n🔄 Setting folder_id...")
        doc.write({'folder_id': folder.id})
        cr.commit()
        
        # Reload
        doc = env['nbs.document'].browse(276)
        
        print(f"\n✅ Fixed!")
        print(f"   ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
        print(f"   ├─ company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
        print(f"   └─ company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
