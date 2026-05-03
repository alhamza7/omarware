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

print(f"🧪 Testing document creation with company_id in: {db_name}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get a folder with company_id
    folder = env['nbs.document.folder'].search([('company_id', '!=', False)], limit=1)
    
    if not folder:
        print("❌ No folder with company_id found. Creating one...")
        # Get first company
        company = env['res.partner'].search([('is_company', '=', True)], limit=1)
        dept = env['nbs.department'].search([], limit=1)
        if not company or not dept:
            print("❌ No company or department found. Cannot test.")
            sys.exit(1)
        
        folder = env['nbs.document.folder'].create({
            'name': 'Test Folder with Company',
            'department_id': dept.id,
            'company_id': company.id,
            'owner_id': 1
        })
        print(f"✓ Created folder: {folder.name} with company: {company.name}")
    
    print(f"📁 Using folder: {folder.name} (ID: {folder.id})")
    print(f"   Company: {folder.company_id.name} (ID: {folder.company_id.id})")
    
    # Get document type and department
    doc_type = env['nbs.document.type'].search([], limit=1)
    dept = folder.department_id
    
    # Create a test document
    print(f"\n📄 Creating test document...")
    doc = env['nbs.document'].create({
        'name': 'Test Document for Company Check',
        'department_id': dept.id,
        'document_type_id': doc_type.id,
        'folder_id': folder.id,
        'folder_role': 'main',
        'uploader_id': 1,
    })
    
    print(f"✓ Created document: {doc.name} (ID: {doc.id})")
    print(f"   folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
    print(f"   company_id: {doc.company_id.id if doc.company_id else 'NULL'} ← Should be {folder.company_id.id}")
    print(f"   company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
    
    if doc.company_id and doc.company_id.id == folder.company_id.id:
        print(f"\n✅ SUCCESS! Document got company_id from folder!")
    else:
        print(f"\n❌ FAIL! Document company_id is NULL or wrong!")
    
    # Don't commit - this is just a test
    cr.rollback()
    print(f"\n(Test rolled back - no actual data created)")
