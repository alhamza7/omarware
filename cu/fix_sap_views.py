#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix SAP Integration views issue
This script will:
1. Delete old views with incorrect field names
2. Upgrade the module to load new views
"""

import sys
import odoo
from odoo import api, SUPERUSER_ID

def fix_views(dbname):
    """Fix SAP Integration views"""
    print("=" * 60)
    print("Fixing SAP Integration Views")
    print("=" * 60)
    
    # Initialize Odoo registry
    registry = odoo.registry(dbname)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("\nStep 1: Searching for old views...")
        
        # Find old views
        old_views = env['ir.ui.view'].search([
            '|',
            ('name', '=', 'sap.res.partner.list'),
            ('name', '=', 'sap.product.product.list')
        ])
        
        if old_views:
            print(f"   Found {len(old_views)} old view(s)")
            for view in old_views:
                print(f"   - {view.name} (ID: {view.id})")
            
            print("\nStep 2: Deleting old views...")
            old_views.unlink()
            print("   [OK] Old views deleted")
        else:
            print("   [INFO] No old views found")
        
        print("\nStep 3: Upgrading module...")
        
        # Find and upgrade module
        module = env['ir.module.module'].search([
            ('name', '=', 'sap_integration')
        ])
        
        if module:
            print(f"   Module state: {module.state}")
            
            if module.state == 'installed':
                # Mark for upgrade
                module.button_immediate_upgrade()
                print("   [OK] Module upgraded successfully")
            else:
                print(f"   [WARNING] Module is not installed (state: {module.state})")
        else:
            print("   [ERROR] Module not found!")
            return False
        
        # Commit changes
        cr.commit()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Fix completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("   1. Restart Odoo")
        print("   2. Test the import: env['sap.res.partner'].import_batch(backend)")
        print()
        
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_sap_views.py <database_name>")
        print("Example: python fix_sap_views.py odoo")
        sys.exit(1)
    
    dbname = sys.argv[1]
    print(f"Database: {dbname}\n")
    
    try:
        success = fix_views(dbname)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

