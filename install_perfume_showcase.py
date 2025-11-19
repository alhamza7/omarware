#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تثبيت مودول Perfume Showcase API
Install Perfume Showcase API Module
"""

import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.api import Environment

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

print("=" * 80)
print("Installing Perfume Showcase API Module")
print("=" * 80)

try:
    # Get registry
    registry = odoo.registry.Registry.new('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Find the module
        module = env['ir.module.module'].search([
            ('name', '=', 'perfume_showcase_api')
        ], limit=1)
        
        if not module:
            print("ERROR: Module not found in database!")
            print("\nPlease check:")
            print("   1. Module exists in addons/ folder")
            print("   2. Update Apps List in Odoo")
            sys.exit(1)
        
        print(f"\nModule: {module.name}")
        print(f"   Current State: {module.state}")
        print(f"   Version: {module.latest_version or 'N/A'}")
        
        if module.state == 'installed':
            print("\nModule is already installed!")
            
            # Try to upgrade if needed
            print("\nAttempting upgrade...")
            try:
                module.button_immediate_upgrade()
                cr.commit()
                print("Upgrade completed successfully!")
            except Exception as e:
                print(f"No upgrades available: {e}")
        else:
            print("\nInstalling...")
            try:
                module.button_immediate_install()
                cr.commit()
                print("Installation completed successfully!")
                print(f"\nNew State: {module.state}")
            except Exception as e:
                print(f"Installation error: {e}")
                import traceback
                traceback.print_exc()
                cr.rollback()
                sys.exit(1)
        
        # Verify installation
        print("\nVerifying installation...")
        
        # Check if models exist
        models_to_check = [
            'perfume.brand',
            'perfume.perfume',
            'perfume.note',
            'perfume.season',
            'perfume.occasion',
        ]
        
        all_ok = True
        for model_name in models_to_check:
            try:
                model = env[model_name]
                count = model.search_count([])
                print(f"   OK {model_name:25} : exists ({count} records)")
            except KeyError:
                print(f"   ERROR {model_name:25} : not found")
                all_ok = False
            except Exception as e:
                print(f"   WARNING {model_name:25} : error - {str(e)[:50]}")
                all_ok = False
        
        if all_ok:
            print("\nAll models exist! Installation successful!")
        else:
            print("\nSome models are missing. You may need to restart Odoo.")
        
        print("\n" + "=" * 80)
        print("Done!")
        print("=" * 80)
        print("\nNext steps:")
        print("   1. Reload Odoo page (Ctrl+F5)")
        print("   2. Look for 'Perfume Showcase' menu in sidebar")
        print("   3. Start adding data: Brands -> Perfumes")
        
except Exception as e:
    print(f"\nGeneral error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

