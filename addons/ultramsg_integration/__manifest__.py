# -*- coding: utf-8 -*-
{
    'name': 'ULTRAMSG WhatsApp Integration',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Send WhatsApp messages via ULTRAMSG API',
    'description': """
        ULTRAMSG WhatsApp Integration
        ==============================
        * Send WhatsApp messages via ULTRAMSG API
        * Message logging and tracking
        * Support for text, documents, and images
        * Phone number formatting (Iraqi format)
        * Integration with POS and other modules
        
        Features:
        ---------
        - Send documents (PDF invoices)
        - Send text messages
        - Send images
        - Message status tracking
        - Error handling and logging
        - Phone number auto-formatting
    """,
    'author': 'Lugal-AI',
    'website': 'https://lugal-ai.com',
    'depends': [
        'base',
        'mail',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ultramsg_sequence.xml',
        'views/ultramsg_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ultramsg_integration/static/src/js/ultramsg_test_interface.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

