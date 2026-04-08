# -*- coding: utf-8 -*-
"""
Script to update existing customer label templates
Run this script to disable labels by default in existing templates
"""

def update_templates(env):
    """Update all customer label templates to disable labels"""
    templates = env['customer.label.template'].search([])
    templates.write({
        'show_phone_label': False,
        'show_mobile_label': False,
        'show_invoice_type_label': False,
        'show_note_label': False,
    })
    print(f"Updated {len(templates)} customer label template(s)")
    return True





