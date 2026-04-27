# SAP Integration Module for Odoo 17.0

## Overview

This module provides a complete integration between Odoo and SAP using the **OCA Connector Framework** and **SAP Service Layer API**.

### Version 2.0.0

## Features

✅ **OCA Connector Framework Integration**
- Uses connector, component, and component_event modules
- Backend Adapters for SAP Service Layer communication
- Binders for linking Odoo and SAP records
- Mappers for data transformation
- Import/Export Components
- Event Listeners for automatic synchronization

✅ **Binding Models**
- `sap.res.partner` - SAP Business Partners (Customers/Suppliers)
- `sap.product.product` - SAP Items (Products)
- `sap.sale.order` - SAP Orders/Quotations
- `sap.account.move` - SAP Invoices

✅ **Synchronization Features**
- Batch import from SAP
- Individual record import/export
- Bidirectional synchronization
- Error handling and retry mechanism
- Sync status tracking

✅ **Components Architecture**
- **Adapters**: Communicate with SAP Service Layer API
- **Binders**: Link Odoo IDs with SAP external IDs
- **Mappers**: Transform data between Odoo and SAP formats
- **Importers**: Import data from SAP to Odoo
- **Exporters**: Export data from Odoo to SAP
- **Listeners**: Auto-sync on record create/update events

## Requirements

### Dependencies

```python
'depends': [
    'base',
    'sale',
    'purchase',
    'account',
    'stock',
    'product',
    'connector',         # OCA Connector Framework
    'component',         # Component System
    'component_event',   # Event System
    # 'queue_job',       # TODO: Install from OCA
]
```

### Install queue_job (Optional but Recommended)

```bash
# Install from OCA repository
pip install odoo-addon-queue-job==17.0.*
```

**Without queue_job:**
- Synchronization runs directly (blocking)
- No background jobs
- No job queue management

**With queue_job:**
- Asynchronous background synchronization
- Job queue with retry mechanism
- Better performance for large datasets

## Installation

1. **Clone or copy the module** to your Odoo addons directory:
   ```bash
   cp -r sap_integration /path/to/odoo/addons/
   ```

2. **Install dependencies**:
   ```bash
   # Install OCA modules (already in your addons/)
   # - connector
   # - component
   # - component_event
   
   # Optional: Install queue_job
   pip install odoo-addon-queue-job==17.0.*
   ```

3. **Update Odoo apps list**:
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "SAP Integration"
   - Click Install

## Configuration

### 1. Configure SAP Backend

Go to: **Settings > SAP Integration > Backends**

Create a new SAP Backend:
- **Name**: Your backend name (e.g., "SAP Production")
- **Service Layer URL**: Your SAP B1 Service Layer URL
  - Example: `https://sap-server.com:50000/b1s/v1`
- **Username**: SAP username
- **Password**: SAP password
- **Company Database**: SAP company database name
- **Batch Size**: Number of records per batch (default: 100)
- **Timeout**: Request timeout in seconds (default: 30)
- **Retry Attempts**: Number of retries on failure (default: 3)

Click "Test Connection" to verify.

### 2. Import Data from SAP

#### Import Business Partners (Customers)
```python
# From Python code or Shell
backend = env['sap.backend'].browse(1)
result = env['sap.res.partner'].import_batch(backend, filters=None)
```

Or use the UI:
- Go to SAP Integration > Partners
- Click "Import from SAP"

#### Import Products (Items)
```python
backend = env['sap.backend'].browse(1)
result = env['sap.product.product'].import_batch(backend, filters=None)
```

#### Import Orders
```python
backend = env['sap.backend'].browse(1)
result = env['sap.sale.order'].import_batch(backend, filters=None)
```

### 3. Export Data to SAP

#### Export Partner
```python
# Create a binding first
partner = env['res.partner'].browse(1)
binding = env['sap.res.partner'].create({
    'odoo_id': partner.id,
    'backend_id': backend.id,
})

# Export to SAP
binding.export_record()
```

#### Export Product
```python
product = env['product.product'].browse(1)
binding = env['sap.product.product'].create({
    'odoo_id': product.id,
    'backend_id': backend.id,
})

binding.export_record()
```

### 4. Automatic Synchronization

Enable event listeners for automatic sync:

```python
# In context when creating/updating records
partner = env['res.partner'].with_context(
    sap_auto_bind=True,
    sap_backend=backend
).create({
    'name': 'New Customer',
    # ...
})
# This will auto-create a SAP binding and export to SAP
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Odoo Models                          │
│  res.partner | product.product | sale.order | account.move  │
└─────────────────────┬───────────────────────────────────────┘
                      │ _inherits
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                     Binding Models                           │
│  sap.res.partner | sap.product.product | sap.sale.order    │
│  + external_id (SAP ID)                                     │
│  + backend_id (SAP Backend)                                 │
│  + sync_date                                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                   OCA Components                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Adapter    │  │    Binder    │  │    Mapper    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Importer    │  │   Exporter   │  │   Listener   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              SAP Service Layer Connection                    │
│                    (REST API)                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
                ┌──────────┐
                │   SAP    │
                │ Business │
                │   One    │
                └──────────┘
```

## Components Explained

### 1. Adapters (adapter.py)

Communicate with SAP Service Layer API:
- `SapPartnerAdapter`: Get/Create/Update Business Partners
- `SapProductAdapter`: Get/Create/Update Items
- `SapSaleOrderAdapter`: Get/Create/Update Orders
- `SapInvoiceAdapter`: Get/Create/Update Invoices

### 2. Binders (binder.py)

Link Odoo records with SAP records:
- `to_internal(external_id)`: Get Odoo record from SAP ID
- `to_external(binding)`: Get SAP ID from Odoo record
- `bind(external_id, binding)`: Create the link

### 3. Mappers (mapper.py)

Transform data between formats:
- **Import Mappers**: SAP → Odoo
- **Export Mappers**: Odoo → SAP

### 4. Importers (importer.py)

Import data from SAP:
- `run(external_id)`: Import single record
- `import_batch(filters)`: Import multiple records

### 5. Exporters (exporter.py)

Export data to SAP:
- `run(binding)`: Export single record

### 6. Listeners (listener.py)

Auto-sync on events:
- `on_record_create`: Triggered when record created
- `on_record_write`: Triggered when record updated

## Usage Examples

### Example 1: Import All Customers

```python
# Get backend
backend = self.env['sap.backend'].search([('active', '=', True)], limit=1)

# Import all customers
result = self.env['sap.res.partner'].import_batch(backend)

print(f"Imported: {result['imported']}, Errors: {result['errors']}")
```

### Example 2: Export a Product

```python
# Get product
product = self.env['product.product'].search([('default_code', '=', 'PROD001')])

# Create binding
binding = self.env['sap.product.product'].create({
    'odoo_id': product.id,
    'backend_id': backend.id,
    'default_code': 'PROD001',  # SAP ItemCode
})

# Export to SAP
binding.export_record()

print(f"Product exported with SAP ItemCode: {binding.external_id}")
```

### Example 3: Sync Order to SAP When Confirmed

```python
# This happens automatically with listeners enabled

# Confirm order
order.action_confirm()

# A listener will automatically:
# 1. Create sap.sale.order binding
# 2. Export order to SAP
# 3. Store SAP DocEntry in binding.external_id
```

## Troubleshooting

### Connection Issues

1. **Test Connection Failed**
   - Verify SAP Service Layer URL
   - Check username/password
   - Ensure SAP server is accessible
   - Check firewall/network settings

2. **Authentication Error**
   - Verify Company Database name
   - Check user permissions in SAP

### Import/Export Issues

1. **Record Not Found**
   - Check if external_id exists in SAP
   - Verify filters in batch import

2. **Mapping Errors**
   - Check mapper components
   - Verify field mappings match SAP structure

3. **Constraint Violations**
   - Ensure unique external_ids
   - Check required fields are mapped

### Performance

1. **Slow Imports**
   - Reduce batch_size in backend settings
   - Install queue_job for async processing
   - Use filters to import specific records

2. **Timeout Errors**
   - Increase timeout in backend settings
   - Check network latency to SAP server

## Advanced Configuration

### Custom Mappers

Create custom mapper for specific fields:

```python
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

class CustomPartnerMapper(Component):
    _inherit = 'sap.partner.import.mapper'
    
    @mapping
    def custom_field(self, record):
        # Your custom mapping logic
        return {'custom_field': record.get('CustomField')}
```

### Custom Filters

Filter records during import:

```python
# Import only active customers
filters = "Valid eq 'Y'"
result = env['sap.res.partner'].import_batch(backend, filters=filters)

# Import products from specific group
filters = "ItemsGroupCode eq 100"
result = env['sap.product.product'].import_batch(backend, filters=filters)
```

## TODO / Future Enhancements

- [ ] Install and integrate queue_job for background processing
- [ ] Add support for SAP Purchase Orders
- [ ] Add support for SAP Delivery Notes
- [ ] Implement incremental sync (delta sync)
- [ ] Add SAP webhook support for real-time sync
- [ ] Create wizard for easy bulk import/export
- [ ] Add sync dashboard with statistics
- [ ] Implement conflict resolution strategies

## Support

For issues and questions:
- Check the logs: Settings > Technical > Logging
- Review SAP Service Layer documentation
- Check OCA Connector documentation: https://github.com/OCA/connector

## License

LGPL-3

## Credits

- **Author**: Your Company
- **OCA Connector Framework**: Camptocamp, Odoo Community Association (OCA)
- **SAP Service Layer API**: SAP SE

---

**Version**: 2.0.0  
**Last Updated**: 2024

