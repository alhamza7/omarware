# -*- coding: utf-8 -*-
{
    'name': 'Custom Pricelist Packaging',
    'version': '19.0.1.0.0',
    'category': 'Sales/Pricing',
    'summary': 'Add packaging-based pricing support to pricelist items',
    'description': """
Custom Pricelist Packaging
==========================
This module extends Odoo's pricelist items to support packaging-based pricing.

Features:
---------
* Add "Product Packaging" field to pricelist items
* Set fixed prices for specific product packaging types
* Automatically apply packaging prices in sales orders
* Fallback to default price × packaging quantity factor if no packaging price is defined

Technical:
----------
* Built using Odoo inheritance (no core modifications)
* Compatible with Odoo 19
* Follows Odoo coding standards and conventions
    """,
    'author': 'Custom Development',
    'website': 'https://www.odoo.com',
    'depends': [
        'product',
        'sale_management',
    ],
    'data': [
        'views/product_pricelist_item_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

