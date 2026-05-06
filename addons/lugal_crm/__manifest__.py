# -*- coding: utf-8 -*-
{
    'name': 'Lugal CRM',
    'version': '1.0.9',
    'category': 'CRM',
    'summary': 'Custom CRM module for Lugal platform',
    'description': """
Lugal CRM
=========

Custom CRM module: 360° customer card, call centre, omnichannel, knowledge base,
employee KPIs, supply chain. JWT auth via lugal_auth (centralized, independent).
POS bridge links "Create Invoice" in call dialog to pos_perfume_custom (optional).
Requirements and specifications are in addons/lugal_crm/requirements/
    """,
    'author': 'NBS IT Team',
    'website': 'https://nbs.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'contacts',
        'lugal_auth',   # centralized JWT (lugal.jwt.service) — NOT nbs_archive
        'product',      # product.product, product.pricelist
        'stock',        # stock.warehouse, stock.quant
        'lugal_supply', # حاويات + موردين (containers; vendors = res.partner)
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/crm_sequences.xml',
        'data/crm_cron.xml',
        'views/res_config_settings_supply_workflow_views.xml',
        'views/supply_chain_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
