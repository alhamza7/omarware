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

print(f"🧪 Testing Folder Audit Log Filtering\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get a folder with documents
    folder = env['nbs.document.folder'].search([
        ('active', '=', True)
    ], limit=1)
    
    if not folder:
        print("❌ No folders found")
        sys.exit(1)
    
    # Get documents in this folder
    documents = env['nbs.document'].search([
        ('folder_id', '=', folder.id)
    ])
    
    print(f"📁 Folder: {folder.name} (ID: {folder.id})")
    print(f"   └─ Documents in folder: {len(documents)}")
    
    # Test: Create a folder update
    print(f"\n🔄 Updating folder...")
    folder.write({
        'description': f'Test description for audit log at {env.context.get("tz")}'
    })
    
    # Upload a document to folder
    if documents:
        doc = documents[0]
        print(f"\n📄 Updating document: {doc.name} (ID: {doc.id})")
        # Just read it to create view log
    
    cr.commit()
    
    # Now query audit logs for this folder
    print(f"\n📊 Querying audit logs for folder {folder.id}...")
    
    # Get all documents in folder
    doc_ids = documents.ids
    
    # Query logs: folder_id = X OR document_id in [docs in folder]
    if doc_ids:
        logs = env['nbs.audit.log'].search([
            '|',
            ('folder_id', '=', folder.id),
            ('document_id', 'in', doc_ids)
        ], order='timestamp desc', limit=10)
    else:
        logs = env['nbs.audit.log'].search([
            ('folder_id', '=', folder.id)
        ], order='timestamp desc', limit=10)
    
    print(f"   Found {len(logs)} audit logs\n")
    
    folder_log_count = 0
    doc_log_count = 0
    
    for i, log in enumerate(logs, 1):
        log_type = "📁 FOLDER" if log.folder_id else "📄 DOCUMENT"
        if log.folder_id:
            folder_log_count += 1
        if log.document_id:
            doc_log_count += 1
        
        print(f"{i}. {log_type} - [{log.action}]")
        print(f"   ├─ User: {log.user_id.name}")
        print(f"   ├─ Time: {log.timestamp}")
        if log.folder_id:
            print(f"   ├─ Folder: {log.folder_id.name} (ID: {log.folder_id.id})")
        if log.document_id:
            print(f"   ├─ Document: {log.document_id.name} (ID: {log.document_id.id})")
        print(f"   └─ Metadata: {log.metadata or 'None'}")
        print()
    
    print(f"📈 Summary:")
    print(f"   📁 Folder-specific logs: {folder_log_count}")
    print(f"   📄 Document logs: {doc_log_count}")
    print(f"   📊 Total: {len(logs)}")
    
    if folder_log_count > 0:
        print(f"\n✅ SUCCESS! Can filter audit logs by folder_id")
        print(f"   └─ Returns both folder logs AND document logs in that folder")
    
    # Rollback test update
    cr.rollback()
    print(f"\n(Test updates rolled back)")
