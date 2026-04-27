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

print(f"🔍 Testing company_id computation in database: {db_name}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get folders with company_id
    folders = env['nbs.document.folder'].search([('company_id', '!=', False)], limit=5)
    print(f"📁 Found {len(folders)} folders with company_id set\n")
    
    for folder in folders:
        print(f"Folder: {folder.name} (ID: {folder.id})")
        print(f"  └─ Folder company_id: {folder.company_id.id if folder.company_id else 'NULL'}")
        print(f"  └─ Folder company_name: {folder.company_id.name if folder.company_id else 'NULL'}")
        
        # Get documents in this folder
        docs = env['nbs.document'].search([('folder_id', '=', folder.id)])
        print(f"  └─ Documents in folder: {len(docs)}")
        
        for doc in docs:
            print(f"     📄 Doc: {doc.name} (ID: {doc.id})")
            print(f"        ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
            print(f"        ├─ folder.company_id: {doc.folder_id.company_id.id if doc.folder_id and doc.folder_id.company_id else 'NULL'}")
            print(f"        ├─ doc.company_id (computed): {doc.company_id.id if doc.company_id else 'NULL'}")
            print(f"        └─ doc.company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
        print()
    
    # Get documents with folder but no company
    docs_no_company = env['nbs.document'].search([
        ('folder_id', '!=', False),
        ('company_id', '=', False)
    ], limit=10)
    
    if docs_no_company:
        print(f"\n⚠️  Found {len(docs_no_company)} documents with folder but no company_id:")
        for doc in docs_no_company:
            print(f"  - Doc {doc.id}: {doc.name}")
            print(f"    Folder: {doc.folder_id.name if doc.folder_id else 'None'}")
            print(f"    Folder has company: {doc.folder_id.company_id.name if doc.folder_id and doc.folder_id.company_id else 'No'}")
