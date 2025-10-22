#!/usr/bin/env python3
"""
Direct test of SAP import to diagnose the issue
"""

import sys
import odoolib

# Connect to Odoo
connection = odoolib.get_connection(
    hostname="localhost",
    port=8069,
    database="lugal",
    login="admin",
    password="admin"
)

print("Connected to Odoo")

# Get backend
Backend = connection.get_model('sap.backend')
backends = Backend.search([('name', '=', 'test')])

if not backends:
    print("ERROR: Backend 'test' not found")
    sys.exit(1)

backend_id = backends[0]
print(f"Found backend ID: {backend_id}")

# Test customer import
print("\n=== Testing Customer Import ===")
CustomerSync = connection.get_model('sap.customer.sync')

try:
    # Test importing one customer
    result = CustomerSync.import_record(backend_id, 'IBG00001')
    print(f"SUCCESS: Customer imported: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test product import
print("\n=== Testing Product Import ===")
ProductSync = connection.get_model('sap.product.sync')

try:
    # Test importing one product
    result = ProductSync.import_record(backend_id, 'ADF00001')
    print(f"SUCCESS: Product imported: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")

