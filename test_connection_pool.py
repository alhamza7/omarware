#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Connection Pool Performance"""

import odoorpc
import time

# Connect to Odoo
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('lugal', 'admin', 'admin')

print("=" * 60)
print("Testing SAP Connection Pool Performance")
print("=" * 60)

# Get backend
backend_model = odoo.env['sap.backend']
backends = backend_model.search([('active', '=', True)], limit=1)

if not backends:
    print("\n[ERROR] No active backend found")
    exit(1)

backend_id = backends[0]
backend = backend_model.browse(backend_id)

print(f"\n[OK] Found backend: {backend.name}")
print(f"Backend ID: {backend_id}")

# Test connection pool statistics
print("\n" + "=" * 60)
print("Connection Pool Test")
print("=" * 60)

try:
    # Import 10 partners to test
    print("\n1. Testing Partner Import (10 records)...")
    start = time.time()
    
    partner_model = odoo.env['sap.res.partner']
    result = partner_model.import_batch(backend_id, filters="startswith(CardCode, 'C')")
    
    end = time.time()
    duration = end - start
    
    print(f"   Time taken: {duration:.2f} seconds")
    print(f"   Imported: {result.get('imported', 0)}")
    print(f"   Skipped: {result.get('skipped', 0)}")
    
except Exception as e:
    print(f"   [ERROR] {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

