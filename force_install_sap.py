# -*- coding: utf-8 -*-
"""
Force install SAP Integration module
"""

print("=" * 60)
print("Force Installing SAP Integration")
print("=" * 60)

# Find module
module = env['ir.module.module'].search([('name', '=', 'sap_integration')])

if not module:
    print("[ERROR] Module not found!")
else:
    print(f"Module: {module.name}")
    print(f"State: {module.state}")
    
    # Reset state
    if module.state in ['to install', 'to upgrade', 'to remove']:
        print("\nResetting module state...")
        module.write({'state': 'uninstalled'})
        env.cr.commit()
        print("[OK] State reset to uninstalled")
    
    # Update module list first
    print("\nUpdating module list...")
    env['ir.module.module'].update_list()
    env.cr.commit()
    
    # Reinstall
    module = env['ir.module.module'].search([('name', '=', 'sap_integration')])
    print(f"\nCurrent state: {module.state}")
    
    if module.state == 'uninstalled':
        print("\nInstalling...")
        try:
            # Use button_install which is safer
            module.button_install()
            env.cr.commit()
            print("[SUCCESS] Module marked for installation")
            print("Please restart Odoo to complete installation")
        except Exception as e:
            print(f"[ERROR] {str(e)}")
    else:
        print(f"[INFO] State is: {module.state}")

print("\n" + "=" * 60)

