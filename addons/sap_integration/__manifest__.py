{
    'name': 'SAP Integration',
    'version': '2.0.0',
    'summary': 'SAP Integration using OCA Connectors and Service Layer',
    'description': '''
        SAP Integration Module
        =====================
        
        This module provides integration between Odoo and SAP using:
        - OCA Connector framework
        - SAP Service Layer API
        - REST API communication
        - Background job queue for asynchronous synchronization
        
        Features:
        - Customer synchronization with binding records
        - Product synchronization with binding records
        - Quotation synchronization
        - Sales Order synchronization
        - Invoice synchronization
        - Unit of Measure mapping
        - Pricelist management
        - Error handling and monitoring
        - Event-based synchronization
        - Retry mechanism for failed jobs
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Connector',
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'stock',
        'product',
        'uom',
        'connector',
        'component',
        'component_event',
        # 'queue_job',  # TODO: Install queue_job module from OCA
    ],
    'external_dependencies': {
        'python': ['requests', 'cachetools'],
    },
    'data': [
        'security/sap_security.xml',
        'security/ir.model.access.csv',
        'data/sap_backend_data.xml',
        'views/sap_dashboard_views.xml',  # Must be loaded first to define main menu
        'views/sap_backend_views.xml',
        'views/sap_connector_views.xml',
        'views/sap_mapper_views.xml',  # UOM & Pricelist Mapping
        'views/sap_binding_views.xml',  # Customer & Product Bindings
        # Temporarily disabled views with issues
        # 'views/sap_customer_views.xml',
        # 'views/sap_product_views.xml',
        # 'views/sap_quotation_views.xml',
        # 'views/sap_sale_views.xml',
        # 'wizard/sap_import_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
