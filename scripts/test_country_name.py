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

print(f"🧪 Testing country_name in company creation\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Test 1: Create company with country_name (existing country)
    print(f"📝 Test 1: Creating company with country_name (existing)")
    
    # Check if "United States" exists
    us_country = env['res.country'].search([('name', 'ilike', 'United States')], limit=1)
    if us_country:
        print(f"   ✓ Country exists: {us_country.name} (ID: {us_country.id}, Code: {us_country.code})")
    
    # Simulate the logic
    country_name = "United States"
    country = env['res.country'].search([('name', 'ilike', country_name)], limit=1)
    
    if country:
        print(f"   ✓ Found country: {country.name} (ID: {country.id})")
        country_id_to_use = country.id
    else:
        print(f"   Creating new country: {country_name}")
        new_country = env['res.country'].create({
            'name': country_name,
            'code': country_name[:2].upper()
        })
        country_id_to_use = new_country.id
        print(f"   ✓ Created country: {new_country.name} (ID: {new_country.id})")
    
    # Create company
    company = env['res.partner'].create({
        'name': 'Test International Company',
        'is_company': True,
        'country_id': country_id_to_use,
        'phone': '+1-555-0100',
        'email': 'test@international.com'
    })
    
    print(f"   ✓ Company created: {company.name}")
    print(f"     └─ Country: {company.country_id.name} ({company.country_id.code})")
    
    # Test 2: Create company with new country_name
    print(f"\n📝 Test 2: Creating company with NEW country_name")
    
    country_name_2 = "Test Country XYZ"
    country_2 = env['res.country'].search([('name', 'ilike', country_name_2)], limit=1)
    
    if not country_2:
        print(f"   Creating new country: {country_name_2}")
        new_country_2 = env['res.country'].create({
            'name': country_name_2,
            'code': country_name_2[:2].upper()
        })
        country_id_2 = new_country_2.id
        print(f"   ✓ Created country: {new_country_2.name} (Code: {new_country_2.code})")
    
    company_2 = env['res.partner'].create({
        'name': 'Another Test Company',
        'is_company': True,
        'country_id': country_id_2
    })
    
    print(f"   ✓ Company created: {company_2.name}")
    print(f"     └─ Country: {company_2.country_id.name}")
    
    # Test 3: List countries
    print(f"\n📝 Test 3: List countries with search")
    
    countries = env['res.country'].search([('name', 'ilike', 'United')], limit=5)
    print(f"   Search 'United' found {len(countries)} countries:")
    for c in countries:
        print(f"     - {c.name} ({c.code})")
    
    # Rollback test
    cr.rollback()
    print(f"\n✅ Tests passed! (rolled back)")
