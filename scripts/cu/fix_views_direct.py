# -*- coding: utf-8 -*-
"""
Run this script from Odoo shell:
python odoo-bin shell -d odoo -c odoo.conf < fix_views_direct.py
"""

print("=" * 60)
print("Fixing SAP Integration Views")
print("=" * 60)

print("\nStep 1: Searching for old views...")

# Find old views
old_views = env['ir.ui.view'].search([
    '|',
    ('name', '=', 'sap.res.partner.list'),
    ('name', '=', 'sap.product.product.list')
])

if old_views:
    print(f"Found {len(old_views)} old view(s):")
    for view in old_views:
        print(f"  - {view.name} (ID: {view.id})")
    
    print("\nStep 2: Deleting old views...")
    old_views.unlink()
    print("[OK] Old views deleted")
else:
    print("[INFO] No old views found")

print("\nStep 3: Upgrading module...")

# Find and upgrade module
module = env['ir.module.module'].search([
    ('name', '=', 'sap_integration')
])

if module:
    print(f"Module state: {module.state}")
    
    if module.state == 'installed':
        module.button_immediate_upgrade()
        print("[OK] Module upgraded successfully")
    else:
        print(f"[WARNING] Module is not installed (state: {module.state})")
else:
    print("[ERROR] Module not found!")

print("\n" + "=" * 60)
print("[SUCCESS] Fix completed!")
print("=" * 60)
print("\nYou can now test the import.")

