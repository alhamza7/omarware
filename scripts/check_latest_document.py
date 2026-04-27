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

print(f"🔍 التحقق من آخر المستندات المضافة\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get latest 5 documents
    docs = env['nbs.document'].search([('is_deleted', '=', False)], order='id desc', limit=5)
    
    print(f"📊 آخر 5 مستندات:\n")
    
    for doc in docs:
        has_company = bool(doc.company_id)
        status = "✅" if has_company else "❌"
        
        print(f"{status} ID {doc.id}: {doc.name}")
        print(f"   ├─ Created: {doc.create_date}")
        print(f"   ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
        if doc.folder_id:
            print(f"   ├─ folder_name: {doc.folder_id.name}")
            print(f"   ├─ folder.company_id: {doc.folder_id.company_id.id if doc.folder_id.company_id else 'NULL'}")
        print(f"   ├─ doc.company_id: {doc.company_id.id if has_company else 'NULL'}")
        print(f"   └─ doc.company_name: {doc.company_id.name if has_company else 'NULL'}")
        print()
