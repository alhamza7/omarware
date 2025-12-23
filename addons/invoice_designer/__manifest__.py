# -*- coding: utf-8 -*-
{
    'name': 'Invoice Designer - Visual Template Builder',
    'version': '1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Professional Visual Invoice Designer with Drag & Drop',
    'description': """
Invoice Designer - Visual Template Builder
==========================================

Complete visual invoice designer with drag & drop interface.

Features:
---------
* Visual canvas editor with drag & drop
* 8+ element types (text, field, image, table, shape, line, barcode, qr)
* Complete control over fonts, colors, borders, backgrounds
* Table designer with full customization
* Data binding to all Odoo fields
* PDF generation
* Multi-page support
* Grid and snap-to-grid
* Zoom controls
* Layer management
* Copy/paste elements
* Undo/redo support
* Template library
* POS & Sale Order integration

Supported Document Types:
------------------------
* Sale Orders
* Quotations
* Invoices
* POS Receipts
* Delivery Notes
* Custom documents

    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'point_of_sale'],
    'data': [
        'security/invoice_designer_security.xml',
        'security/ir.model.access.csv',
        'views/invoice_template_designer_views.xml',
        'views/invoice_template_element_views.xml',
        'data/default_templates.xml',
        'data/available_fields.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'invoice_designer/static/src/js/invoice_designer.js',
            'invoice_designer/static/src/js/canvas_engine.js',
            'invoice_designer/static/src/js/element_handlers.js',
            'invoice_designer/static/src/xml/invoice_designer.xml',
            'invoice_designer/static/src/xml/toolbars.xml',
            'invoice_designer/static/src/xml/properties_panel.xml',
            'invoice_designer/static/src/css/invoice_designer.css',
            'invoice_designer/static/src/css/canvas.css',
            'invoice_designer/static/src/css/panels.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

