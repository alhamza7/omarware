#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to install Perfume Showcase API module using XML-RPC
"""

import xmlrpc.client

url = "http://localhost:8070"
db = "lugal"
username = "admin"
password = "admin"

print("=" * 80)
print("Installing Perfume Showcase API Module")
print("=" * 80)

try:
    # Connect
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("ERROR: Authentication failed!")
        print("Please check username and password")
        exit(1)
    
    print(f"Connected! User ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Find module
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'perfume_showcase_api')]]
    )
    
    if not module_ids:
        print("\nERROR: Module not found!")
        print("Please update Apps List first in Odoo")
        exit(1)
    
    # Get module info
    module = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [module_ids],
        {'fields': ['name', 'state', 'latest_version']}
    )[0]
    
    print(f"\nModule: {module['name']}")
    print(f"State: {module['state']}")
    print(f"Version: {module.get('latest_version', 'N/A')}")
    
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
        print("\nWARNING: Module state is not 'installed'")
        print(f"Current state: {module_after['state']}")
        
except xmlrpc.client.ProtocolError as e:
    print(f"\nConnection Error: {e}")
    print("Make sure Odoo is running on http://localhost:8070")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

