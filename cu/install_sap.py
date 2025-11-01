# -*- coding: utf-8 -*-
"""
Install SAP Integration module
"""

print("=" * 60)
print("Installing SAP Integration Module")
print("=" * 60)

# Find module
module = env['ir.module.module'].search([
    ('name', '=', 'sap_integration')
])

if not module:
    print("[ERROR] Module 'sap_integration' not found!")
    print("Make sure the module is in addons folder.")
else:
    print(f"Module found: {module.name}")
    print(f"Current state: {module.state}")
    
    if module.state == 'uninstalled':
        print("\nInstalling module...")
        module.button_immediate_install()
        print("[SUCCESS] Module installed!")
    elif module.state == 'installed':
        print("\n[INFO] Module already installed")
        print("Upgrading...")
        module.button_immediate_upgrade()
        print("[SUCCESS] Module upgraded!")
    else:
        print(f"\n[INFO] Module state: {module.state}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

