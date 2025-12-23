#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to setup admin user with NBS Archive permissions
"""

import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID

def setup_admin():
    """Add admin user to NBS Archive groups"""
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', 'odoo_simple.conf', '-d', 'lugal'])
    
    with odoo.api.Environment.manage():
        registry = odoo.registry('lugal')
        
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            
            try:
                # Get admin user
                admin_user = env.ref('base.user_admin')
                
                # Get NBS groups
                group_user = env.ref('nbs_archive.group_nbs_user', raise_if_not_found=False)
                group_manager = env.ref('nbs_archive.group_nbs_manager', raise_if_not_found=False)
                group_admin = env.ref('nbs_archive.group_nbs_admin', raise_if_not_found=False)
                
                # Add groups
                groups_to_add = []
                if group_user:
                    groups_to_add.append(group_user.id)
                if group_manager:
                    groups_to_add.append(group_manager.id)
                if group_admin:
                    groups_to_add.append(group_admin.id)
                
                if groups_to_add:
                    admin_user.write({
                        'groups_id': [(4, gid) for gid in groups_to_add]
                    })
                    print(f"✅ Added admin user to {len(groups_to_add)} NBS Archive groups")
                else:
                    print("❌ NBS Archive groups not found!")
                
                # Create some test data
                dept_sc = env.ref('nbs_archive.dept_supply_chain', raise_if_not_found=False)
                
                if dept_sc:
                    print(f"✅ Found department: {dept_sc.name}")
                
                cr.commit()
                print("✅ Setup completed successfully!")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                cr.rollback()
                return False
    
    return True

if __name__ == '__main__':
    setup_admin()








