#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
import json

odoo.tools.config.parse_config(['-c', 'odoo_local.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal_local'
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"🧪 Testing /api/folders response - EXACT simulation\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Simulate the exact API logic from folder_controller.py
    domain = [('active', '=', True)]
    
    folder_ids = env['nbs.document.folder'].search(domain, order='sequence, name', limit=3).ids
    
    result = []
    for fid in folder_ids:
        try:
            folder = env['nbs.document.folder'].browse(fid)
            doc_count = 0
            all_doc_count = 0
            try:
                doc_count = folder.document_count
                all_doc_count = folder.all_document_count
            except Exception:
                pass
            
            # THIS IS THE EXACT CODE FROM THE CONTROLLER
            result.append({
                'id': folder.id,
                'name': folder.name,
                'code': folder.code,
                'description': folder.description,
                'parent_id': folder.parent_id.id if folder.parent_id else None,
                'parent_name': folder.parent_id.name if folder.parent_id else None,
                'level': folder.level,
                'full_path': folder.full_path,
                'child_count': folder.child_count,
                'document_count': doc_count,
                'all_document_count': all_doc_count,
                'department_id': folder.department_id.id,
                'department_name': folder.department_id.name,
                'company_id': folder.company_id.id if folder.company_id else None,
                'company_name': folder.company_id.name if folder.company_id else None,
                'restricted': folder.restricted,
                'color': folder.color,
                'icon': folder.icon,
                'sequence': folder.sequence,
                'created_at': folder.create_date.isoformat() if folder.create_date else None,
                'last_modified': folder.last_modified.isoformat() if folder.last_modified else None,
            })
        except Exception as e:
            print(f"Error with folder {fid}: {e}")
    
    print(f"📊 API Response Simulation:\n")
    print(json.dumps({'success': True, 'data': result, 'count': len(result)}, indent=2))
    
    # Check if last_modified is present
    if result:
        first_folder = result[0]
        if 'last_modified' in first_folder:
            print(f"\n✅ SUCCESS! last_modified is in the response")
            print(f"   └─ Value: {first_folder['last_modified']}")
        else:
            print(f"\n❌ FAIL! last_modified is NOT in the response")
