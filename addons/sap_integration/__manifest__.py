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
        'connector',  # OCA Connector framework - Now activated!
        'component',  # OCA Component framework - Now activated!
        'component_event',  # OCA Component Event framework - Now activated!
        # 'queue_job',  # TODO: Install queue_job module from OCA if needed for background jobs
    ],
    'external_dependencies': {
        'python': ['requests', 'cachetools'],
    },
    'data': [
        'security/sap_security.xml',
        'security/ir.model.access.csv',
        'data/sap_backend_data.xml',
        # 'data/sap_cron_data.xml',  # Disabled - uses advanced models not yet enabled
        
        # Wizards - Load FIRST so their actions are available
        'wizard/sap_import_wizard_views.xml',  # Main import wizard (used by other views)
        'wizard/sap_conflict_resolution_wizard_views.xml',  # Conflict Resolution Wizard
        'wizard/sap_uom_conversion_test_wizard_views.xml',  # UoM Conversion Test Wizard
        'wizard/sap_user_permission_wizard_views.xml',  # User Permission Wizard
        
        # Views (Actions & Forms)
        'views/sap_dashboard_views.xml',  # Dashboard views and actions
        'views/sap_backend_views.xml',
        'views/sap_connector_views.xml',
        'views/sap_mapper_views.xml',  # UOM & Pricelist Mapping
        'views/sap_binding_views.xml',  # Customer & Product Bindings
        'views/sap_sync_log_views.xml',  # Sync Log Views
        'views/sap_analysis_views.xml',  # Analysis & Monitoring Views
        'views/sap_synced_data_views.xml',  # Synced Data Views
        'views/sap_synced_data_dashboard.xml',  # Synced Data Dashboard
        'views/sap_sync_management_views.xml',  # Sync Management Views
        'views/sap_uom_management_views.xml',  # UoM Management Views
        'views/sap_dashboard_control_views.xml',  # Dashboard Control Views
        'views/sap_customer_views.xml',
        'views/sap_product_views.xml',
        'views/sap_quotation_views.xml',
        'views/sap_sale_views.xml',
        'views/sap_warehouse_views.xml',
        
        # Menu Structure - Load LAST to organize all menu items
        'views/sap_menu_structure.xml',  # ⭐ New: Organized menu structure
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
