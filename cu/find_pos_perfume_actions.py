#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("=" * 80)
    print("البحث عن POS PERFUME ACTIONS")
    print("=" * 80)
    
    # Search for POS Perfume actions
    actions = env['ir.actions.act_window'].search([
        '|', '|',
        ('name', 'ilike', 'perfume'),
        ('res_model', 'ilike', 'perfume'),
        ('res_model', '=', 'pos.perfume.order'),
    ])
    
    print(f"\n✅ وجدت {len(actions)} Actions")
    
    for action in actions:
        print(f"\n{'='*60}")
        print(f"ID: {action.id}")
        print(f"Name: {action.name}")
        print(f"Model: {action.res_model}")
        print(f"View Mode: {action.view_mode}")
        print(f"🔗 URL: http://192.168.116.181:8070/odoo/action-{action.id}")
        
    # Also check menu items
    print(f"\n{'='*80}")
    print("القوائم المتعلقة بـ POS PERFUME")
    print("=" * 80)
    
    menus = env['ir.ui.menu'].search([
        '|',
        ('name', 'ilike', 'perfume'),
        ('action', 'in', [f'ir.actions.act_window,{a.id}' for a in actions]),
    ])
    
    for menu in menus:
        print(f"\n📋 Menu: {menu.complete_name}")
        print(f"   ID: {menu.id}")
        if menu.action:
            action_id = menu.action.id if hasattr(menu.action, 'id') else 'N/A'
            print(f"   Action ID: {action_id}")

