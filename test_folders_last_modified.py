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

print(f"🧪 Testing Folders API - last_modified field\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get a folder
    folder = env['nbs.document.folder'].search([('active', '=', True)], limit=1)
    
    if not folder:
        print("❌ No folders found")
        sys.exit(1)
    
    print(f"📁 Folder: {folder.name} (ID: {folder.id})")
    print(f"   ├─ create_date: {folder.create_date}")
    print(f"   ├─ write_date: {folder.write_date}")
    print(f"   └─ last_modified: {folder.last_modified}")
    
    # Simulate API response
    print(f"\n📡 Simulated API Response:")
    print(f"{{")
    print(f'  "id": {folder.id},')
    print(f'  "name": "{folder.name}",')
    print(f'  "created_at": "{folder.create_date.isoformat() if folder.create_date else None}",')
    print(f'  "last_modified": "{folder.last_modified.isoformat() if folder.last_modified else None}"')
    print(f"}}")
    
    if folder.last_modified:
        print(f"\n✅ SUCCESS! last_modified is computed and available")
    else:
        print(f"\n⚠️  last_modified is None (may need documents/notes in folder)")
