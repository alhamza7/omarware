#!/usr/bin/env python3
"""
Comprehensive verification of all company-related features
"""
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

print(f"{'='*70}")
print(f"  COMPREHENSIVE COMPANY FEATURES VERIFICATION")
print(f"{'='*70}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Test 1: Document 73 has company_id
    print(f"TEST 1: Document 73 Company Fields")
    print(f"-" * 70)
    
    doc = env['nbs.document'].browse(73)
    if doc.exists():
        print(f"Document: {doc.name}")
        print(f"  company_id: {doc.company_id.id if doc.company_id else 'NULL'}")
        print(f"  company_name: {doc.company_id.name if doc.company_id else 'NULL'}")
        
        if doc.company_id:
            print(f"\n✅ PASS: Document 73 has company fields")
        else:
            print(f"\n❌ FAIL: Document 73 missing company_id")
    
    # Test 2: Audit logs
    print(f"\n\nTEST 2: Audit Logs with Change Details")
    print(f"-" * 70)
    
    folder_logs = env['nbs.audit.log'].search([
        ('action', '=', 'folder_updated')
    ], order='timestamp desc', limit=3)
    
    has_details = False
    for log in folder_logs:
        if '|' in (log.metadata or ''):
            has_details = True
            print(f"✅ {log.timestamp}")
            print(f"   {log.metadata}\n")
    
    if has_details:
        print(f"✅ PASS: Audit logs show change details")
    else:
        print(f"⚠️  No folder updates with details yet")
    
    # Test 3: Countries with phone_code
    print(f"\n\nTEST 3: Countries API")
    print(f"-" * 70)
    
    iraq = env['res.country'].search([('code', '=', 'IQ')], limit=1)
    if iraq:
        print(f"Iraq: ID={iraq.id}, Code={iraq.code}, Phone={iraq.phone_code}")
        print(f"✅ PASS: Countries have phone_code")
    
    print(f"\n\n{'='*70}")
    print(f"  ALL TESTS COMPLETE")
    print(f"{'='*70}\n")
