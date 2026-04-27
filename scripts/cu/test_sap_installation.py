# -*- coding: utf-8 -*-
"""
Test SAP Integration installation
"""

print("=" * 60)
print("Testing SAP Integration Installation")
print("=" * 60)

# Check module
print("\n1. Checking module status...")
module = env['ir.module.module'].search([('name', '=', 'sap_integration')])
if module:
    print(f"   Module: {module.name}")
    print(f"   State: {module.state}")
    print(f"   [OK]" if module.state == 'installed' else f"   [WARNING] Not installed")
else:
    print("   [ERROR] Module not found!")

# Check models
print("\n2. Checking models...")
models_to_check = [
    'sap.backend',
    'sap.res.partner',
    'sap.product.product',
]

for model_name in models_to_check:
    try:
        model = env[model_name]
        count = model.search_count([])
        print(f"   [{model_name}] OK - {count} records")
    except Exception as e:
        print(f"   [{model_name}] ERROR: {str(e)}")

# Check backend
print("\n3. Checking SAP backend...")
backends = env['sap.backend'].search([])
if backends:
    for backend in backends:
        print(f"   Backend: {backend.name}")
        print(f"   URL: {backend.base_url}")
        print(f"   Active: {backend.active}")
        print(f"   Status: {backend.connection_status}")
else:
    print("   [INFO] No backends configured yet")
    print("   Create one at: Settings > SAP Integration > Backends")

# Check views
print("\n4. Checking views...")
views = env['ir.ui.view'].search([
    ('model', 'in', ['sap.res.partner', 'sap.product.product'])
])
print(f"   Found {len(views)} view(s)")
for view in views:
    print(f"   - {view.name} ({view.model})")

print("\n" + "=" * 60)
print("[SUCCESS] Installation check complete!")
print("=" * 60)

print("\nNext steps:")
print("1. Configure SAP Backend at: Settings > SAP Integration > Backends")
print("2. Test connection: backend.test_connection()")
print("3. Import data: env['sap.res.partner'].import_batch(backend)")

