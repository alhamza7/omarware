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

print(f"🔧 Fixing document 270\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get document 270
    doc = env['nbs.document'].browse(270)
    if not doc.exists():
        print("❌ Document 270 not found")
        sys.exit(1)
    
    print(f"📄 Document: {doc.name} (ID: {doc.id})")
    print(f"   └─ Current folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   └─ Current company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
    
    # Get folder 191
    folder = env['nbs.document.folder'].browse(191)
    
    if folder.exists():
        print(f"\n📁 Folder 191: {folder.name}")
        print(f"   └─ Company: {folder.company_id.name if folder.company_id else 'NULL'}")
        
        # Link document to folder
        print(f"\n🔗 Linking document to folder...")
        doc.write({
            'folder_id': folder.id,
            'folder_role': 'main'
        })
        cr.commit()
        
        # Reload
        doc = env['nbs.document'].browse(270)
        
        print(f"\n✅ Updated!")
        print(f"   └─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
        print(f"   └─ company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
        print(f"   └─ company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
    else:
        print(f"\n❌ Folder 191 not found!")
        print(f"Finding any folder with company_id...")
        
        folder = env['nbs.document.folder'].search([
            ('company_id', '!=', False),
            ('active', '=', True)
        ], limit=1)
        
        if folder:
            print(f"📁 Using folder: {folder.name} (ID: {folder.id})")
            doc.write({'folder_id': folder.id, 'folder_role': 'main'})
            cr.commit()
            
            doc = env['nbs.document'].browse(270)
            print(f"✅ Updated: company_id = {doc.company_id.id if doc.company_id else 'NULL'}")
