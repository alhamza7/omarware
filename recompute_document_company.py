#!/usr/bin/env python3
"""
Recompute company_id for all documents from their folders
"""
import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# Parse config
odoo.tools.config.parse_config(['-c', 'odoo_local.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal_local'
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"🔄 Recomputing company_id for all documents in database: {db_name}")

# Connect to database
with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get all documents
    documents = env['nbs.document'].search([])
    total = len(documents)
    print(f"📊 Found {total} documents")
    
    updated_count = 0
    null_count = 0
    
    for i, doc in enumerate(documents, 1):
        if i % 100 == 0:
            print(f"   Processing {i}/{total}...")
        
        # Get company from folder
        new_company_id = False
        if doc.folder_id and doc.folder_id.company_id:
            new_company_id = doc.folder_id.company_id.id
        
        # Update if different
        if doc.company_id.id != new_company_id:
            doc.write({'company_id': new_company_id})
            if new_company_id:
                updated_count += 1
            else:
                null_count += 1
    
    # Commit changes
    cr.commit()
    
    print(f"\n✅ Recomputation complete:")
    print(f"   📄 Total documents: {total}")
    print(f"   ✓ Updated with company: {updated_count}")
    print(f"   ∅ Set to null (no folder company): {null_count}")
    print(f"   = Unchanged: {total - updated_count - null_count}")
