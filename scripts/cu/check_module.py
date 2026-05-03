#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo.api import Environment

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

# Get registry
SUPERUSER_ID = 1
with Environment.manage():
    registry = odoo.registry('lugal')
    with registry.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        
        print("="*60)
        print("🔍 SAP Integration Module Check")
        print("="*60)
        
        # 1. Check if modules are installed
        print("\n1️⃣ Checking Module Installation Status:")
        print("-" * 60)
        modules_to_check = [
            'connector',
            'component', 
            'component_event',
            'sap_integration'
        ]
        
        for module_name in modules_to_check:
            module = env['ir.module.module'].search([('name', '=', module_name)])
            if module:
                print(f"   {module_name:25} : {module.state:15} (v{module.installed_version or 'N/A'})")
            else:
                print(f"   {module_name:25} : ❌ NOT FOUND")
        
        # 2. Check if sap_integration models exist
        print("\n2️⃣ Checking Models Registration:")
        print("-" * 60)
        models_to_check = [
            'sap.backend',
            'sap.res.partner',
            'sap.product.product',
            'sap.sale.order',
            'sap.account.move',
        ]
        
        for model_name in models_to_check:
            try:
                model = env[model_name]
                count = model.search_count([])
                print(f"   {model_name:25} : ✅ ({count} records)")
            except KeyError:
                print(f"   {model_name:25} : ❌ NOT REGISTERED")
            except Exception as e:
                print(f"   {model_name:25} : ⚠️  Error: {str(e)[:40]}")
        
        # 3. Check ir.model entries
        print("\n3️⃣ Checking Database Models:")
        print("-" * 60)
        for model_name in models_to_check:
            model_entry = env['ir.model'].search([('model', '=', model_name)])
            if model_entry:
                print(f"   {model_name:25} : ✅ in database")
            else:
                print(f"   {model_name:25} : ❌ NOT in database")
        
        # 4. Check menu items
        print("\n4️⃣ Checking Menu Items:")
        print("-" * 60)
        menus = env['ir.ui.menu'].search([('name', 'ilike', 'sap')])
        if menus:
            for menu in menus[:10]:
                print(f"   📋 {menu.name} (id: {menu.id})")
        else:
            print("   ⚠️  No SAP menus found")
        
        # 5. Check security rules
        print("\n5️⃣ Checking Security Access:")
        print("-" * 60)
        access_rules = env['ir.model.access'].search([('name', 'ilike', 'sap')])
        print(f"   Found {len(access_rules)} access rules")
        for rule in access_rules[:5]:
            print(f"   🔒 {rule.name}")
        
        # 6. Check for errors in logs
        print("\n6️⃣ Checking for Installation Errors:")
        print("-" * 60)
        errors = env['ir.logging'].search([
            ('name', 'ilike', 'sap'),
            ('level', 'in', ['ERROR', 'CRITICAL'])
        ], limit=5, order='id desc')
        
        if errors:
            print("   ⚠️  Found recent errors:")
            for error in errors:
                print(f"   [{error.create_date}] {error.message[:60]}")
        else:
            print("   ✅ No recent errors found")
        
        print("\n" + "="*60)
        print("✅ Check Complete!")
        print("="*60)

