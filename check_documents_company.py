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

print(f"🔍 التحقق من company_id في المستندات - قاعدة البيانات: {db_name}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get all active documents
    documents = env['nbs.document'].search([('is_deleted', '=', False)])
    
    print(f"📊 إجمالي المستندات: {len(documents)}\n")
    
    docs_with_company = 0
    docs_without_company = 0
    
    for doc in documents:
        has_company = bool(doc.company_id)
        has_folder = bool(doc.folder_id)
        folder_has_company = bool(doc.folder_id and doc.folder_id.company_id) if has_folder else False
        
        if has_company:
            docs_with_company += 1
        else:
            docs_without_company += 1
        
        status = "✅" if has_company else "❌"
        print(f"{status} Doc {doc.id}: {doc.name}")
        print(f"   └─ folder_id: {doc.folder_id.id if has_folder else 'لا يوجد'}")
        if has_folder:
            print(f"   └─ folder.company_id: {doc.folder_id.company_id.id if folder_has_company else 'لا يوجد'}")
        print(f"   └─ doc.company_id: {doc.company_id.id if has_company else 'NULL'}")
        print(f"   └─ doc.company_name: {doc.company_id.name if has_company else 'NULL'}")
        print()
    
    print(f"\n📈 الملخص:")
    print(f"   ✅ مستندات لديها company_id: {docs_with_company}")
    print(f"   ❌ مستندات بدون company_id: {docs_without_company}")
    
    # Check folders with company
    print(f"\n📁 الفولدرات التي لديها company_id:")
    folders = env['nbs.document.folder'].search([('company_id', '!=', False)])
    for folder in folders:
        print(f"   - {folder.name} (ID: {folder.id})")
        print(f"     └─ Company: {folder.company_id.name} (ID: {folder.company_id.id})")
        docs_in_folder = env['nbs.document'].search([('folder_id', '=', folder.id)])
        print(f"     └─ عدد المستندات: {len(docs_in_folder)}")
