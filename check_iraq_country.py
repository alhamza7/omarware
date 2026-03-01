#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', 'odoo_local.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal_local'
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"🔍 Searching for Iraq in countries\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Search for Iraq
    iraq = env['res.country'].search([('name', 'ilike', 'iraq')], limit=1)
    
    if iraq:
        print(f"✅ Iraq found in database:")
        print(f"   ├─ ID: {iraq.id} ← This is country_id (NOT 964!)")
        print(f"   ├─ Name: {iraq.name}")
        print(f"   ├─ Code: {iraq.code}")
        print(f"   └─ Phone Code: {iraq.phone_code}")
        
        print(f"\n📝 Correct usage:")
        print(f'   country_id: {iraq.id}  (database ID)')
        print(f'   OR')
        print(f'   country_name: "Iraq"  (recommended)')
    else:
        print(f"❌ Iraq NOT found in database")
        print(f"\n✅ Solution: Use country_name")
        print(f'   country_name: "Iraq"')
        print(f"   Backend will create it automatically")
    
    # Show some example countries with their IDs
    print(f"\n📊 Example country IDs (database IDs, not phone codes):")
    examples = env['res.country'].search([
        ('name', 'in', ['United States', 'Saudi Arabia', 'United Kingdom', 'Iraq'])
    ])
    for c in examples:
        print(f"   - {c.name}: country_id = {c.id}, phone_code = +{c.phone_code}, ISO = {c.code}")
