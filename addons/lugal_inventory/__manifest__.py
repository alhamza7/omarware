{
    'name': 'Lugal Inventory',
    'version': '19.0.1.0.0',
    'summary': 'Inventory counting system with mobile/web API',
    'description': """
        Smart inventory management module that allows:
        - Multi-warehouse inventory sessions
        - Barcode scanning for product lookup
        - User management per warehouse
        - Audit trail for all inventory counts
        - REST API for web and mobile app integration
    """,
    'category': 'Inventory',
    'author': 'NBS',
    'depends': ['stock', 'product', 'base', 'sap_integration'],
    'data': [
        'security/ir.model.access.csv',
        'security/lugal_inventory_security.xml',
        'data/lugal_inventory_data.xml',
        'views/lugal_inventory_views.xml',
        'views/lugal_inventory_menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
