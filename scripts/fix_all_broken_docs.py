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

print(f"🔧 Fixing all documents with folder_ids but no folder_id\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find docs with folder_ids but no folder_id
    all_docs = env['nbs.document'].search([('is_deleted', '=', False)])
    
    fixed_count = 0
    
    for doc in all_docs:
        if doc.folder_ids and not doc.folder_id:
            folder = doc.folder_ids[0]
            print(f"📄 Doc {doc.id}: {doc.name}")
            print(f"   ├─ Has folder_ids: {doc.folder_ids.ids}")
            print(f"   ├─ Missing folder_id")
            print(f"   └─ Setting folder_id to: {folder.id} ({folder.name})")
            
            doc.write({'folder_id': folder.id})
            
            # Check company_id
            doc = env['nbs.document'].browse(doc.id)
            print(f"   ✓ company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
            print()
            
            fixed_count += 1
    
    cr.commit()
    
    print(f"\n✅ Fixed {fixed_count} documents")
    
    # Final check
    without_company = env['nbs.document'].search_count([
        ('is_deleted', '=', False),
        ('company_id', '=', False)
    ])
    
    with_company = env['nbs.document'].search_count([
        ('is_deleted', '=', False),
        ('company_id', '!=', False)
    ])
    
    print(f"\n📊 Final Status:")
    print(f"   ✅ Documents with company_id: {with_company}")
    print(f"   ❌ Documents without company_id: {without_company}")
