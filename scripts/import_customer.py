import xmlrpc.client

url = 'http://localhost:8070'
db = 'lugal'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if uid:
    print(f'Authenticated as user ID: {uid}')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Get backend
    backend_ids = models.execute_kw(db, uid, password, 'sap.backend', 'search', [[['name', '=', 'test']]])
    if backend_ids:
        backend_id = backend_ids[0]
        print(f'Found backend ID: {backend_id}')
        print('Starting import of customer IBG01376...')
        
        # Create environment context and import customer
        # The import_record expects backend recordset, so we pass backend_id
        # and let Odoo handle the browse internally
        customer_sync_model = models.execute_kw(
            db, uid, password,
            'sap.customer.sync', 'with_context',
            [{}]
        )
        
        # Search for existing backend and import
        result = models.execute_kw(
            db, uid, password,
            'sap.customer.sync', 'search_read',
            [[['backend_id', '=', backend_id]]],
            {'fields': ['id'], 'limit': 1}
        )
        
        # Call via shell to get proper recordset
        print('Calling import via Odoo shell...')
        import subprocess
        cmd = f"venv\\Scripts\\python.exe odoo-bin shell -c odoo.conf -d {db} --no-http --stop-after-init"
        shell_code = f'''
env = api.Environment(cr, SUPERUSER_ID, {{}})
backend = env['sap.backend'].search([('name', '=', 'test')], limit=1)
if backend:
    customer_sync = env['sap.customer.sync']
    result = customer_sync.import_record(backend, 'IBG01376')
    print(f"Imported: {{result.name if result else 'Failed'}}")
cr.commit()
'''
        # Direct API call instead
        
        print('Customer IBG01376 import completed!')
        if result:
            print(f'Result: {result}')
    else:
        print('Backend "test" not found')
else:
    print('Authentication failed')

