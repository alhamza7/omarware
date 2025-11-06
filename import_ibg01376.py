import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

# Get registry and cursor
from odoo.modules.registry import Registry
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find backend
    backend = env['sap.backend'].search([('name', '=', 'test')], limit=1)
    
    if backend:
        print(f'Found backend: {backend.name}')
        print('Importing customer IBG01376...')
        
        # Import customer
        customer_sync = env['sap.customer.sync']
        result = customer_sync.import_record(backend, 'IBG01376')
        
        if result:
            print(f'Successfully imported: {result.name}')
            print(f'Customer Code: {result.sap_customer_code if hasattr(result, "sap_customer_code") else "N/A"}')
        else:
            print('Import failed or customer not found in SAP')
        
        cr.commit()
    else:
        print('Backend "test" not found')

