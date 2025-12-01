#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix customer label templates
Run this from Odoo shell or as a standalone script
"""

import sys
import os

# Add Odoo to path if running standalone
if __name__ == '__main__':
    # This script should be run from Odoo shell:
    # python odoo-bin shell -d lugal
    # Then: exec(open('addons/product_label_designer/scripts/fix_customer_labels.py').read())
    pass

def fix_customer_labels(env):
    """Fix all customer label templates"""
    templates = env['customer.label.template'].search([])
    
    updated_count = 0
    for template in templates:
        needs_update = False
        updates = {}
        
        if template.show_phone_label:
            updates['show_phone_label'] = False
            needs_update = True
        
        if template.show_mobile_label:
            updates['show_mobile_label'] = False
            needs_update = True
        
        if template.show_invoice_type_label:
            updates['show_invoice_type_label'] = False
            needs_update = True
        
        if template.show_note_label:
            updates['show_note_label'] = False
            needs_update = True
        
        if needs_update:
            template.write(updates)
            updated_count += 1
            print(f"Updated template: {template.name}")
    
    print(f"\n✅ تم تحديث {updated_count} من أصل {len(templates)} قالب")
    return True

# Auto-run if in Odoo shell
if 'env' in globals():
    fix_customer_labels(env)


