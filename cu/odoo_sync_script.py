
import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.cli.server.report_configuration()
env = api.Environment(odoo.registry('lugal'), SUPERUSER_ID, {})

# Get SAP Connector
connector = env['sap.connector'].browse(2)
print(f"Connector: {connector.name}")
print(f"Status: {connector.sync_status}")

# Try to trigger sync
try:
    # Check if there's a sync method
    if hasattr(connector, 'sync_all'):
        print("Triggering sync_all...")
        connector.sync_all()
    elif hasattr(connector, 'sync_from_sap'):
        print("Triggering sync_from_sap...")
        connector.sync_from_sap()
    else:
        print("No sync method found")
        
    # Check results
    print(f"Customers synced: {connector.customers_synced}")
    print(f"Products synced: {connector.products_synced}")
    
except Exception as e:
    print(f"Error: {e}")
