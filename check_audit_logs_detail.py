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

print(f"🔍 Checking Recent Audit Logs\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get latest 10 audit logs
    logs = env['nbs.audit.log'].search([], order='timestamp desc', limit=10)
    
    print(f"📊 Latest 10 Audit Logs:\n")
    
    for i, log in enumerate(logs, 1):
        print(f"{i}. [{log.action}]")
        print(f"   ├─ User: {log.user_id.name}")
        print(f"   ├─ Time: {log.timestamp}")
        print(f"   └─ Metadata: {log.metadata or 'None'}")
        print()
    
    # Check for folder_updated logs
    folder_logs = env['nbs.audit.log'].search([
        ('action', '=', 'folder_updated')
    ], order='timestamp desc', limit=3)
    
    print(f"\n📁 Latest Folder Update Logs: {len(folder_logs)}")
    for log in folder_logs:
        print(f"   - {log.timestamp}: {log.metadata}")
    
    # Check for company logs
    company_logs = env['nbs.audit.log'].search([
        ('action', 'in', ['company_created', 'company_updated', 'company_deleted'])
    ], order='timestamp desc', limit=3)
    
    print(f"\n🏢 Latest Company Logs: {len(company_logs)}")
    for log in company_logs:
        print(f"   - {log.timestamp} [{log.action}]: {log.metadata}")
