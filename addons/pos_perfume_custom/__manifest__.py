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
        'uom',                        # ⭐ دعم وحدات القياس
        'uom_in_pricelist',          # ⭐ أسعار حسب UoM
        'sap_integration',           # ⭐ معلومات SAP
        'ultramsg_integration',      # ⭐ WhatsApp Integration
        # 'invoice_designer',          # ⭐ معطل: استخدام الفاتورة الأصلية من Odoo
    ],
    'data': [
        'security/pos_perfume_security.xml',  # ✅ Record rules (must be first!)
        'security/ir.model.access.csv',
        'data/pos_perfume_sequence.xml',
        'data/default_exchange_rate.xml',  # ✅ Default exchange rate configuration
        # 'data/invoice_templates.xml',  # ⛔ معطل: استخدام الفاتورة الأصلية
        'views/pos_perfume_views.xml',
        'views/pos_perfume_order_views.xml',
        'views/pos_perfume_session_views.xml',
        'views/res_config_settings_views.xml',  # ✅ Sales settings for exchange rate
        # 'reports/pos_order_arabic_report.xml',  # ⛔ معطل: استخدام التقرير الأساسي
        'reports/pos_perfume_order_report.xml',  # ✅ تقرير أساسي يرث من sale.order
        'reports/pos_perfume_report_action.xml',  # ✅ إجراء الطباعة
        # 'reports/pos_perfume_order_report_gold.xml',  # ⛔ تصاميم بديلة معطلة
        # 'reports/pos_perfume_order_report_nbs.xml',  # ⛔ تصاميم بديلة معطلة
    ],
    'assets': {
        'web.assets_backend': [
            'pos_perfume_custom/static/src/scss/perfume_pos.scss',
            # Enhanced table navigation
            'pos_perfume_custom/static/src/js/pos_perfume_order_line_list.js',
            # Components (يجب أن تُحمَّل أولاً)
            'pos_perfume_custom/static/src/app/product_search_uom.js',
            'pos_perfume_custom/static/src/app/customer_search.js',
            'pos_perfume_custom/static/src/app/location_selector.js',
            # Screen (يستخدم الـ Components)
            'pos_perfume_custom/static/src/app/pos_perfume_screen.js',
            # App (آخر شيء - يُسجل الـ action)
            'pos_perfume_custom/static/src/app/pos_perfume_app.js',
            # Templates
            'pos_perfume_custom/static/src/xml/product_search_uom.xml',
            'pos_perfume_custom/static/src/xml/customer_search.xml',
            'pos_perfume_custom/static/src/xml/location_selector.xml',
            'pos_perfume_custom/static/src/xml/pos_perfume_screen.xml',
        ],
        'point_of_sale._assets_pos': [
            'pos_perfume_custom/static/src/app/pos_perfume_main.js',
            'pos_perfume_custom/static/src/app/total_iqd_widget.js',
            'pos_perfume_custom/static/src/xml/total_iqd_widget.xml',
            'pos_perfume_custom/static/src/xml/payment_screen_inherit.xml',
            'pos_perfume_custom/static/src/xml/product_screen_button.xml',
        ],
        'web.report_assets_common': [
            'pos_perfume_custom/static/src/css/pos_report_arabic.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

