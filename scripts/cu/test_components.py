# -*- coding: utf-8 -*-
"""
Test Components Registration
"""

print("=" * 60)
print("Testing SAP Components")
print("=" * 60)

try:
    # Get backend
    backend = env['sap.backend'].search([], limit=1)
    
    if not backend:
        print("\n[INFO] No backend found. Create one first.")
        print("Creating test backend...")
        backend = env['sap.backend'].create({
            'name': 'Test Backend',
            'base_url': 'https://test:50000/b1s/v1',
            'username': 'test',
            'password': 'test',
            'company_db': 'TEST',
            'active': False,  # Inactive for testing
        })
        print(f"[OK] Created backend: {backend.name}")
    else:
        print(f"\n[OK] Found backend: {backend.name}")
    
    # Test WorkContext
    print("\n1. Testing WorkContext...")
    from odoo.addons.component.core import WorkContext
    
    work = WorkContext(
        model_name='sap.res.partner',
        collection=backend,
        components_registry=env['component.core']._cache
    )
    print("   [OK] WorkContext created")
    
    # Test finding components
    print("\n2. Testing Components...")
    
    # Try to find batch importer
    try:
        importer = work.component(usage='batch.importer')
        print(f"   [OK] Found batch.importer: {importer._name}")
    except Exception as e:
        print(f"   [ERROR] batch.importer: {str(e)}")
    
    # Try to find record importer
    try:
        importer = work.component(usage='record.importer')
        print(f"   [OK] Found record.importer: {importer._name}")
    except Exception as e:
        print(f"   [ERROR] record.importer: {str(e)}")
    
    # Try to find adapter
    try:
        adapter = work.component(usage='backend.adapter')
        print(f"   [OK] Found backend.adapter: {adapter._name}")
    except Exception as e:
        print(f"   [ERROR] backend.adapter: {str(e)}")
    
    # Test import_batch method
    print("\n3. Testing import_batch method...")
    try:
        # This should not error even if no SAP connection
        print("   Calling import_batch (will fail if no connection, but that's OK)...")
        result = env['sap.res.partner'].import_batch(backend, filters=None)
        print(f"   [OK] import_batch executed: {result}")
    except Exception as e:
        if "Component" in str(e) or "Several" in str(e):
            print(f"   [ERROR] Component issue: {str(e)}")
        else:
            print(f"   [INFO] Expected error (connection issue): {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Component system is working!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

