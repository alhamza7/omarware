#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Adapter Component Registration
"""

import odoorpc

# Connect to Odoo
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('lugal', 'admin', 'admin')

print("=" * 60)
print("Testing Adapter Component Registration")
print("=" * 60)

# Get backend
backend = odoo.env['sap.backend'].search([('name', '=', 'test')], limit=1)
if not backend:
    print("\n[ERROR] Backend 'test' not found")
    exit(1)

backend_id = backend[0]
backend_record = odoo.env['sap.backend'].browse(backend_id)

print(f"\n[OK] Found backend: {backend_record.name}")
print(f"Backend ID: {backend_id}")

# Test WorkContext
print("\n1. Testing WorkContext creation...")
try:
    from odoo.addons.component.core import WorkContext
    
    # This would be done in server context
    print("   [INFO] WorkContext test requires server context")
    print("   [INFO] Testing through model import_batch method instead...")
except Exception as e:
    print(f"   [INFO] Cannot import WorkContext in RPC: {str(e)}")

# Test actual import
print("\n2. Testing actual import_batch...")
try:
    # Try to import partners
    partner_model = odoo.env['sap.res.partner']
    print(f"   [OK] Got partner model")
    
    # This will test if the adapter is registered
    print("   [INFO] Attempting batch import...")
    result = partner_model.import_batch(backend_id, filters=None)
    print(f"   [OK] Import completed: {result}")
    
except Exception as e:
    error_msg = str(e)
    if "No component found" in error_msg:
        print(f"   [ERROR] Component still not registered!")
        print(f"   Details: {error_msg}")
    else:
        print(f"   [ERROR] Other error: {error_msg}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

