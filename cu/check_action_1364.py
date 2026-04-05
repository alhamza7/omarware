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
    
    # Get Action 1364
    action = env['ir.actions.act_window'].browse(1364)
    
    if action.exists():
        print(f"Action ID: {action.id}")
        print(f"Action Name: {action.name}")
        print(f"Model: {action.res_model}")
        print(f"View Mode: {action.view_mode}")
        print(f"Type: {action.type}")
        print(f"XML ID: {action.xml_id if hasattr(action, 'xml_id') else 'N/A'}")
        
        # Check if it's POS Perfume
        if 'perfume' in action.name.lower() or 'perfume' in action.res_model:
            print("\n✅ YES! This is POS PERFUME!")
        else:
            print(f"\n❌ NO, this is: {action.name}")
    else:
        print("Action 1364 not found!")

