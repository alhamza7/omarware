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

print(f"🧪 Testing Audit Logs for Folder and Company Updates\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Test 1: Folder Update
    print(f"📁 Test 1: Folder Update Audit Log")
    
    folder = env['nbs.document.folder'].search([('active', '=', True)], limit=1)
    if folder:
        print(f"   Folder: {folder.name} (ID: {folder.id})")
        print(f"   Old company: {folder.company_id.name if folder.company_id else 'None'}")
        
        # Get company
        company = env['res.partner'].search([('is_company', '=', True)], limit=1)
        
        # Update folder
        folder.write({
            'name': folder.name + ' - Updated',
            'description': 'Test description update',
            'company_id': company.id if company else False
        })
        
        # Check latest audit log
        latest_log = env['nbs.audit.log'].search([
            ('action', '=', 'folder_updated')
        ], order='timestamp desc', limit=1)
        
        if latest_log:
            print(f"\n   ✅ Audit Log Created:")
            print(f"      ├─ Action: {latest_log.action}")
            print(f"      ├─ User: {latest_log.user_id.name}")
            print(f"      ├─ Timestamp: {latest_log.timestamp}")
            print(f"      └─ Metadata: {latest_log.metadata}")
        else:
            print(f"\n   ❌ No audit log found!")
    
    # Test 2: Company Update
    print(f"\n\n🏢 Test 2: Company Update Audit Log")
    
    company = env['res.partner'].search([('is_company', '=', True)], limit=1)
    if company:
        print(f"   Company: {company.name} (ID: {company.id})")
        old_name = company.name
        
        # Update company
        company.write({
            'name': company.name + ' - Test Update',
            'phone': '+1234567890'
        })
        
        # Check latest audit log
        latest_log = env['nbs.audit.log'].search([
            ('action', '=', 'company_updated')
        ], order='timestamp desc', limit=1)
        
        if latest_log:
            print(f"\n   ✅ Audit Log Created:")
            print(f"      ├─ Action: {latest_log.action}")
            print(f"      ├─ User: {latest_log.user_id.name}")
            print(f"      ├─ Timestamp: {latest_log.timestamp}")
            print(f"      └─ Metadata: {latest_log.metadata}")
        else:
            print(f"\n   ❌ No audit log found!")
    
    # Rollback
    cr.rollback()
    print(f"\n(Test rolled back - no actual changes made)")
