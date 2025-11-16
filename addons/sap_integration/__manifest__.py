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
        # OCA Connector modules are not compatible with Odoo 19.0, removed for now
        # 'connector',  # OCA Connector framework
        # 'component',  # OCA Component framework
        # 'component_event',  # OCA Component Event framework
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
        
        # Views (Actions & Forms)
        'views/sap_menus_minimal.xml',      # Minimal menus: defines menu_sap_integration and menu_sap_tools only
        # 'views/sap_dashboard_views.xml',  # Full dashboard + menus (temporarily disabled due to XML schema issues on server)
        # 'views/sap_menu_structure.xml',   # Old menu structure file (disabled)
        
        # Wizards - Load AFTER menus so they can reference menu items
        'wizard/sap_import_wizard_views.xml',  # Main import wizard (used by other views)
        'wizard/sap_conflict_resolution_wizard_views.xml',  # Conflict Resolution Wizard
        'wizard/sap_uom_conversion_test_wizard_views.xml',  # UoM Conversion Test Wizard
        'wizard/sap_user_permission_wizard_views.xml',  # User Permission Wizard
        'wizard/sap_product_complete_migration_views.xml',  # Complete Product Migration Wizard
        'wizard/quick_product_update_views.xml',  # Quick Product Update Wizard
        'wizard/clear_pricelist_wizard_views.xml',  # Clear Pricelist Wizard
        'wizard/stock_duplicate_cleaner_views.xml',  # Stock Duplicate Cleaner Wizard
        
        # Views (Actions & Forms)
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
        'views/sap_uom_group_views.xml',  # UoM Group Views
        'views/sap_dashboard_control_views.xml',  # Dashboard Control Views
        'views/sap_customer_views.xml',
        'views/sap_product_views.xml',
        'views/sap_quotation_views.xml',
        'views/sap_sale_views.xml',
        'views/sale_order_sap_views.xml',  # SAP integration for sale orders
        'views/sap_warehouse_views.xml',
        
        # Reports
        'report/sale_report_inherit.xml',  # Add SAP Document Number to sale order PDF
        
        # New: Complete Product Migration Views
        'views/sap_product_extended_views.xml',  # Extended product information
        'views/sap_product_pricelist_sync_views.xml',  # Pricelist synchronization
        'views/sap_product_warehouse_info_views.xml',  # Warehouse information
        'views/product_uom_group_views.xml',  # UoM Group restriction in products/sales
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
