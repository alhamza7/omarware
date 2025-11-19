# -*- coding: utf-8 -*-
{
    'name': 'Perfume Showcase API',
    'version': '19.0.1.0.1',
    'category': 'Website',
    'summary': 'إدارة موقع عرض العطور عبر API - Perfume Showcase Website Management via API',
    'description': """
        Perfume Showcase API Module
        ===========================
        * إدارة العطور والعلامات التجارية من Odoo
        * REST API endpoints لعرض البيانات
        * دعم كامل لتفاصيل العطور (Notes, Seasons, Occasions)
        * إدارة ديناميكية للموقع
        
        Features:
        - Brand Management (إدارة العلامات التجارية)
        - Perfume Management (إدارة العطور)
        - Notes Management (إدارة النوتات)
        - REST API for Frontend (API للواجهة الأمامية)
    """,
    'author': 'Lugal-AI',
    'website': 'https://lugal-ai.com',
    'depends': [
        'base',
        'product',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/demo_data.xml',
        'views/perfume_brand_views.xml',
        'views/perfume_perfume_views.xml',
        'views/perfume_tag_views.xml',
        'views/perfume_menu_views.xml',
    ],
    # NOTE: we previously used a post_init_hook to create a PostgreSQL
    # compatibility function. This is no longer needed because the
    # wrapper function has been created directly in the database.
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

