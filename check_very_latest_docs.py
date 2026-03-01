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

print(f"🔍 Checking VERY LATEST documents\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get latest 10 documents ordered by create_date
    docs = env['nbs.document'].search([('is_deleted', '=', False)], order='create_date desc, id desc', limit=10)
    
    print(f"📊 Latest 10 documents (newest first):\n")
    
    for i, doc in enumerate(docs, 1):
        has_company = bool(doc.company_id)
        has_folder = bool(doc.folder_id)
        status = "✅" if has_company else "❌"
        
        print(f"{i}. {status} ID {doc.id}: {doc.name}")
        print(f"   ├─ Created: {doc.create_date}")
        print(f"   ├─ folder_id: {doc.folder_id.id if has_folder else 'NULL'}")
        if has_folder:
            print(f"   ├─ folder_name: {doc.folder_id.name}")
            folder_has_company = bool(doc.folder_id.company_id)
            print(f"   ├─ folder.company_id: {doc.folder_id.company_id.id if folder_has_company else 'NULL'}")
            if folder_has_company:
                print(f"   ├─ folder.company_name: {doc.folder_id.company_id.name}")
        print(f"   ├─ doc.company_id: {doc.company_id.id if has_company else 'NULL'}")
        print(f"   └─ doc.company_name: {doc.company_id.name if has_company else 'NULL'}")
        print()
    
    # Count total
    total_docs = env['nbs.document'].search_count([('is_deleted', '=', False)])
    with_company = env['nbs.document'].search_count([('is_deleted', '=', False), ('company_id', '!=', False)])
    without_company = total_docs - with_company
    
    print(f"\n📈 Summary:")
    print(f"   Total documents: {total_docs}")
    print(f"   ✅ With company_id: {with_company}")
    print(f"   ❌ Without company_id: {without_company}")
