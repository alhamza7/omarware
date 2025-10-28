# -*- coding: utf-8 -*-
{
    'name': 'POS Perfume Design - Custom Interface',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'تصميم واجهة POS مخصصة لمتجر العطور مع جدول طلبات Excel-like',
    'description': """
        Point of Sale Custom Interface for Perfume Store
        =================================================
        * Excel-like order table with arrow key navigation
        * 50/50 split layout (Orders | Products)
        * Real-time calculations
        * Purple theme design
        * Multi-warehouse support
        * Dual currency (USD/IQD)
    """,
    'author': 'Lugal-AI',
    'website': 'https://lugal-ai.com',
    'depends': [
        'point_of_sale',
        'product',
        'stock',
        'sale',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_perfume_sequence.xml',
        'views/pos_perfume_views.xml',
        'views/pos_perfume_order_views.xml',
        'views/pos_perfume_session_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pos_perfume_custom/static/src/scss/perfume_pos.scss',
            'pos_perfume_custom/static/src/app/pos_perfume_app.js',
            'pos_perfume_custom/static/src/app/pos_perfume_screen.js',
            'pos_perfume_custom/static/src/xml/pos_perfume_screen.xml',
        ],
        'point_of_sale._assets_pos': [
            'pos_perfume_custom/static/src/app/pos_perfume_main.js',
            'pos_perfume_custom/static/src/app/total_iqd_widget.js',
            'pos_perfume_custom/static/src/xml/total_iqd_widget.xml',
            'pos_perfume_custom/static/src/xml/payment_screen_inherit.xml',
            'pos_perfume_custom/static/src/xml/product_screen_button.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

