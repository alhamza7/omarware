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
    action = env['ir.actions.client'].search([('id', '=', 1364)])
    
    if not action:
        # Try act_window
        action = env['ir.actions.act_window'].search([('id', '=', 1364)])
    
    if action:
        print(f"Action ID: {action.id}")
        print(f"Action Name: {action.name}")
        print(f"Model: {action._name}")
        print(f"Type: {action.type if hasattr(action, 'type') else 'N/A'}")
        
        if hasattr(action, 'tag'):
            print(f"Tag: {action.tag}")
        if hasattr(action, 'target'):
            print(f"Target: {action.target}")
            
        print("\nAll fields:")
        for field in action._fields:
            if hasattr(action, field):
                val = getattr(action, field)
                if val and not callable(val):
                    print(f"  {field}: {val}")

