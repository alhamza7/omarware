# -*- coding: utf-8 -*-
{
    'name': 'Lugal AI',
    'version': '1.0.0',
    'category': 'Artificial Intelligence',
    'summary': 'Enterprise AI Control Layer for Odoo × Gemini',
    'description': """
        Lugal AI - Enterprise-Grade AI Integration
        ==========================================
        
        Complete AI solution with:
        - Gemini API Integration
        - Role-Based Permissions (Admin/Employee/Customer)
        - Question Indexing & Classification
        - Token Optimization & Caching
        - POS-Style Product Search Interface
        - SAP Integration Support
        - Bilingual Support (Arabic/English)
        - Conversation History & Analytics
        
        Designed for operational clarity, data protection, and fast business answers.
    """,
    'author': 'Capo Development',
    'website': 'https://lugal-ai.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'product',
        'sale',
        'stock',
        'account',
    ],
    'data': [
        # Security
        'security/lugal_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/lugal_default_questions.xml',
        
        # Views
        'views/lugal_config_views.xml',
        'views/lugal_conversation_views.xml',
        'views/lugal_question_index_views.xml',
        'views/lugal_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lugal_ai/static/src/css/lugal_ai.css',
            'lugal_ai/static/src/js/lugal_chat.js',
            'lugal_ai/static/src/js/lugal_product_search.js',
            'lugal_ai/static/src/js/lugal_admin.js',
            'lugal_ai/static/src/xml/lugal_chat.xml',
            'lugal_ai/static/src/xml/lugal_product_search.xml',
            'lugal_ai/static/src/xml/lugal_admin.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

