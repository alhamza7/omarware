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

print(f"🔍 Checking Document 276 and Folder 197\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check folder 197
    folder = env['nbs.document.folder'].browse(197)
    if folder.exists():
        print(f"📁 Folder 197: {folder.name}")
        print(f"   ├─ company_id: {folder.company_id.id if folder.company_id else 'NULL'}")
        print(f"   ├─ company_name: {folder.company_id.name if folder.company_id else 'NULL'}")
        print(f"   └─ created: {folder.create_date}")
    else:
        print(f"❌ Folder 197 not found!")
    
    print()
    
    # Check document 276
    doc = env['nbs.document'].browse(276)
    if doc.exists():
        print(f"📄 Document 276: {doc.name}")
        print(f"   ├─ created: {doc.create_date}")
        print(f"   ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
        print(f"   ├─ folder_name: {doc.folder_id.name if doc.folder_id else 'NULL'}")
        if doc.folder_id:
            print(f"   ├─ folder.company_id: {doc.folder_id.company_id.id if doc.folder_id.company_id else 'NULL'}")
        print(f"   ├─ doc.company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
        print(f"   └─ doc.company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
        
        # Check the actual field value
        print(f"\n🔬 Database field check:")
        cr.execute("SELECT folder_id, company_id FROM nbs_document WHERE id = 276")
        result = cr.fetchone()
        print(f"   ├─ Raw folder_id: {result[0]}")
        print(f"   └─ Raw company_id: {result[1]}")
        
        if doc.folder_id and doc.folder_id.company_id and not doc.company_id:
            print(f"\n❌ PROBLEM FOUND!")
            print(f"   Folder HAS company_id but document DOESN'T have it")
            print(f"   This means the create() logic didn't run or failed")
    else:
        print(f"❌ Document 276 not found!")
