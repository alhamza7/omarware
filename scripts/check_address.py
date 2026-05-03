import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

# Get registry and cursor
from odoo.modules.registry import Registry
registry = Registry('lugal')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find customer IBG01376 through binding
    binding = env['sap.res.partner'].search([('external_id', '=', 'IBG01376')], limit=1)
    
    if binding and binding.odoo_id:
        partner = binding.odoo_id
        print(f'Customer: {partner.name}')
        print(f'SAP Code: {binding.external_id}')
        print(f'Street: {partner.street or "N/A"}')
        print(f'City: {partner.city or "N/A"}')
        print(f'Zip: {partner.zip or "N/A"}')
        print(f'Country: {partner.country_id.name if partner.country_id else "N/A"}')
        print(f'Phone: {partner.phone or "N/A"}')
    else:
        print('Customer binding not found!')

