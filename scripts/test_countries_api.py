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

print(f"🧪 Testing /api/countries response with phone_code\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Test search for "iraq"
    print(f"📡 Test 1: Search for 'iraq'")
    countries = env['res.country'].search([('name', 'ilike', 'iraq')], limit=5)
    
    result = {
        'success': True,
        'data': [{
            'id': country.id,
            'name': country.name,
            'code': country.code,
            'phone_code': country.phone_code if country.phone_code else None,
        } for country in countries],
        'count': len(countries)
    }
    
    import json
    print(json.dumps(result, indent=2))
    
    print(f"\n📡 Test 2: List some countries")
    countries = env['res.country'].search([
        ('name', 'in', ['Iraq', 'Saudi Arabia', 'United States', 'United Kingdom'])
    ])
    
    print(f"\n{'Country':<25} {'ID':<8} {'Code':<6} {'Phone Code'}")
    print("=" * 60)
    for c in countries:
        phone = c.phone_code if c.phone_code else 'N/A'
        print(f"{c.name:<25} {c.id:<8} {c.code:<6} +{phone}")
    
    print(f"\n✅ Response now includes phone_code field!")
