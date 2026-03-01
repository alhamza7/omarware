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

print(f"🧪 Testing bulk upload with company_id\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get company
    company = env['res.partner'].search([('is_company', '=', True)], limit=1)
    dept = env['nbs.department'].search([], limit=1)
    doc_type = env['nbs.document.type'].search([], limit=1)
    
    print(f"🏢 Company: {company.name} (ID: {company.id})")
    print(f"📂 Department: {dept.name} (ID: {dept.id})")
    print(f"📋 Doc Type: {doc_type.name} (ID: {doc_type.id})")
    
    print(f"\n📥 Creating bulk upload job with company_id...")
    
    # Create job
    job = env['nbs.bulk.upload.job'].create({
        'department_id': dept.id,
        'document_type_id': doc_type.id,
        'create_folder_per_file': True,
        'company_id': company.id,
        'confidentiality_level': 'internal',
        'uploader_id': 1,
        'status': 'pending'
    })
    
    print(f"✓ Job created: {job.job_id}")
    print(f"  └─ company_id: {job.company_id.id if job.company_id else 'NULL'}")
    
    # Process upload
    print(f"\n📤 Processing test files...")
    
    files_data = [
        {
            'file_name': 'test_bulk_1.pdf',
            'file_data': 'JVBERi0xLjQKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgaHR0cDovL3d3dy5yZXBvcnRsYWIuY29tCg==',
            'name': 'Bulk Test 1',
            'description': 'Test bulk upload with company'
        }
    ]
    
    result = job.process_upload(files_data)
    cr.commit()
    
    print(f"✓ Upload processed: {result}")
    
    # Check created documents and folders
    print(f"\n📊 Checking created items...")
    
    if job.created_document_ids:
        doc = job.created_document_ids[0]
        print(f"\n📄 Document: {doc.name} (ID: {doc.id})")
        print(f"   ├─ folder_id: {doc.folder_id.id if doc.folder_id else 'NULL'}")
        print(f"   ├─ folder_name: {doc.folder_id.name if doc.folder_id else 'NULL'}")
        
        if doc.folder_id:
            print(f"   ├─ folder.company_id: {doc.folder_id.company_id.id if doc.folder_id.company_id else 'NULL'}")
            print(f"   ├─ folder.company_name: {doc.folder_id.company_id.name if doc.folder_id.company_id else 'NULL'}")
        
        print(f"   ├─ doc.company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
        print(f"   └─ doc.company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
        
        if doc.company_id and doc.company_id.id == company.id:
            print(f"\n✅✅✅ SUCCESS! Bulk upload creates documents with company_id!")
        else:
            print(f"\n❌ FAILED! Document has no company_id")
    
    # Rollback test
    cr.rollback()
    print(f"\n(Test data rolled back)")
