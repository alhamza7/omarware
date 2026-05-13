#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Apps List and Install Perfume Showcase API module
"""

import xmlrpc.client

url = "http://localhost:8070"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("Updating Apps List and Installing Perfume Showcase API")
print("=" * 80)

try:
    # Connect
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("ERROR: Authentication failed!")
        exit(1)
    
    print(f"Connected! User ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Step 1: Update Apps List
    print("\nStep 1: Updating Apps List...")
    try:
        update_wizard = models.execute_kw(
            db, uid, password,
            'base.module.update', 'create',
            [{}]
        )
        
        models.execute_kw(
            db, uid, password,
            'base.module.update', 'update_module',
            [[update_wizard]]
        )
        print("Apps List updated!")
    except Exception as e:
        print(f"Update warning: {e}")
    
    # Step 2: Find module
    print("\nStep 2: Finding module...")
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'perfume_showcase_api')]]
    )
    
    if not module_ids:
        print("ERROR: Module not found after update!")
        exit(1)
    
    # Get module info
    module = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['name', 'state', 'latest_version']}
    )[0]
    
    print(f"Module: {module['name']}")
    print(f"State: {module['state']}")
    print(f"Version: {module.get('latest_version', 'N/A')}")
    
    if module['state'] == 'uninstallable':
        print("\nWARNING: Module is uninstallable!")
        print("This usually means version incompatibility.")
        print("Please check the module version in __manifest__.py (should be 19.0.x.x.x)")
    
    # Step 3: Install
    if module['state'] == 'installed':
        print("\nModule is already installed!")
        print("Attempting upgrade...")
        try:
            models.execute_kw(
                db, uid, password,
                'ir.module.module', 'button_immediate_upgrade',
                [module_ids]
            )
            print("Upgrade completed!")
        except Exception as e:
            print(f"No upgrades available: {e}")
    else:
        print("\nInstalling module...")
        try:
            models.execute_kw(
                db, uid, password,
                'ir.module.module', 'button_immediate_install',
                [module_ids]
            )
            print("Installation completed successfully!")
        except Exception as e:
            print(f"Installation error: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    # Verify
    print("\nVerifying installation...")
    module_after = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['state']}
    )[0]
    
    print(f"New State: {module_after['state']}")
    
    if module_after['state'] == 'installed':
        print("\n" + "=" * 80)
        print("SUCCESS! Module installed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Reload Odoo page (Ctrl+F5)")
        print("2. Look for 'Perfume Showcase' menu in sidebar")
        print("3. Start adding data: Brands -> Perfumes")
    else:
        print(f"\nWARNING: Module state is '{module_after['state']}'")
        print("You may need to restart Odoo server")
        
except xmlrpc.client.ProtocolError as e:
    print(f"\nConnection Error: {e}")
    print("Make sure Odoo is running on http://localhost:8070")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

