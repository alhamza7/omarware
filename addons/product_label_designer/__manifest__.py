# -*- coding: utf-8 -*-
{
    'name': 'Product Label Designer',
    'version': '19.0.1.0.1',
    'category': 'Inventory/Inventory',
    'summary': 'Design and print professional product labels with custom backgrounds',
    'description': """
Product Label Designer
======================
* Create custom label templates
* Add background images and logos
* Print labels with barcode support
* Multiple label sizes
* Full Arabic support
    """,
    'author': 'Lugal AI',
    'website': 'https://www.lugal-ai.com',
    'license': 'LGPL-3',
    'depends': ['product', 'stock', 'web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'security/customer_label_access.xml',
        'views/product_label_views.xml',
        'views/customer_label_views.xml',
        'views/label_designer_template.xml',
        'views/customer_label_designer_template.xml',
        'wizard/print_label_wizard_views.xml',
        'wizard/print_customer_label_wizard_views.xml',
        'wizard/quick_print_wizard_views.xml',
        'reports/label_reports.xml',
        'reports/customer_label_reports.xml',
        'reports/label_html_reports.xml',
        'reports/label_templates.xml',
        'reports/customer_label_templates.xml',
        'reports/label_simple_report.xml',
        'reports/label_templates_simple.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_label_designer/static/src/css/label_designer.css',
            'product_label_designer/static/src/js/label_designer.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
