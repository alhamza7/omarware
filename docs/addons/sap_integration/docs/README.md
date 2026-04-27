# SAP Integration Module

## Overview

The SAP Integration module provides comprehensive integration capabilities between Odoo and SAP Business One Service Layer API. It offers bidirectional synchronization, data mapping, error handling, monitoring, and extensibility features.

## Features

### Core Features
- **Bidirectional Synchronization** - Sync data between SAP and Odoo in both directions
- **Data Mapping** - Flexible mapping between SAP and Odoo data formats
- **Error Handling** - Comprehensive error handling with logging and alerts
- **Monitoring** - Real-time monitoring with dashboards and statistics
- **UoM Management** - Unit of Measure conversion and management
- **User Management** - Role-based access control and permissions

### Advanced Features
- **Plugin Architecture** - Extensible plugin system for custom functionality
- **API Framework** - RESTful API for external integrations
- **Webhook System** - Real-time event notifications
- **Customization Engine** - Business-specific rule engine
- **Migration Tools** - Data and configuration migration utilities
- **Testing Framework** - Comprehensive testing suite

## Installation

### Prerequisites
- Odoo 16.0 or later
- Python 3.8 or later
- SAP Business One Service Layer API access
- Required Python packages (see requirements.txt)

### Installation Steps

1. **Clone the module**
   ```bash
   git clone <repository-url>
   cd sap_integration
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install in Odoo**
   - Copy the module to your Odoo addons directory
   - Update the module list in Odoo
   - Install the module

4. **Configure SAP Backend**
   - Go to SAP Integration > Configuration > SAP Backends
   - Create a new backend configuration
   - Enter your SAP Service Layer details
   - Test the connection

## Configuration

### SAP Backend Configuration

1. **Basic Settings**
   - Name: Descriptive name for the backend
   - Host: SAP Service Layer hostname
   - Port: SAP Service Layer port (usually 50000)
   - Company DB: SAP company database name
   - Username: SAP Service Layer username
   - Password: SAP Service Layer password

2. **Advanced Settings**
   - SSL Enabled: Enable HTTPS connection
   - Timeout: Request timeout in seconds
   - Retry Attempts: Number of retry attempts
   - Batch Size: Number of records per batch
   - Incremental Sync Days: Days to look back for incremental sync

### Data Mapping Configuration

1. **UoM Mapping**
   - Go to SAP Integration > Configuration > UoM Mapping
   - Create mappings between SAP UoM codes and Odoo UoMs
   - Set conversion factors for different units

2. **Field Mapping**
   - Configure field mappings for each entity type
   - Set up data transformation rules
   - Define validation rules

### User Permissions

1. **User Roles**
   - SAP Manager: Full access to all features
   - SAP User: Limited access to viewing and basic operations
   - SAP Viewer: Read-only access

2. **Permissions**
   - Configure granular permissions for each user
   - Set backend-specific access controls
   - Define operation-specific permissions

## Usage

### Basic Synchronization

1. **Manual Sync**
   - Go to SAP Integration > Synchronization
   - Select the backend and entity type
   - Choose sync direction (SAP to Odoo, Odoo to SAP, or Bidirectional)
   - Click "Start Sync"

2. **Scheduled Sync**
   - Configure cron jobs for automatic synchronization
   - Set up incremental sync schedules
   - Define sync frequency and timing

### Data Management

1. **Synced Data View**
   - View all synchronized records
   - Filter by status, date, backend, or entity type
   - Resolve conflicts and errors

2. **Sync Logs**
   - Monitor sync operations
   - View detailed logs and error messages
   - Track sync performance and statistics

### Monitoring and Alerts

1. **Dashboard**
   - Real-time sync status overview
   - Performance metrics and statistics
   - Alert notifications and warnings

2. **Reports**
   - Generate sync reports
   - Export data for analysis
   - Create custom reports

## API Reference

### REST API Endpoints

#### Authentication
All API requests require authentication using API keys.

**Headers:**
```
X-API-Key: your_api_key
Content-Type: application/json
```

#### Endpoints

##### Sync Data
```http
POST /api/v1/sync
```

**Request Body:**
```json
{
  "backend_id": 1,
  "entity_type": "partner",
  "direction": "sap_to_odoo",
  "external_id": "CUSTOMER001"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Sync completed successfully",
  "result": {
    "synced_records": 1,
    "errors": 0
  }
}
```

##### Get Status
```http
GET /api/v1/status
```

**Response:**
```json
{
  "sync_status_overview": {
    "success": 150,
    "failed": 5,
    "pending": 10
  },
  "synced_data_status_overview": {
    "success": 200,
    "failed": 3,
    "conflict": 2
  },
  "new_alerts_count": 1,
  "latest_performance_metrics": {
    "avg_sync_duration": 2.5,
    "total_records_synced": 1000,
    "error_rate": 0.02
  }
}
```

##### Get Logs
```http
GET /api/v1/logs
```

**Query Parameters:**
- `limit`: Number of logs to return (default: 100)
- `offset`: Number of logs to skip (default: 0)
- `status`: Filter by status (success, failed, info, warning)
- `model_name`: Filter by model name
- `date_from`: Filter from date (ISO format)
- `date_to`: Filter to date (ISO format)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2024-01-01T10:00:00Z",
      "entity": "sap.partner",
      "operation": "sync_sap_to_odoo",
      "status": "success",
      "message": "Partner synced successfully"
    }
  ],
  "total": 1000
}
```

### Webhook Events

#### Event Types
- `sync_start` - Sync operation started
- `sync_complete` - Sync operation completed
- `sync_error` - Sync operation failed
- `data_created` - New data created
- `data_updated` - Data updated
- `data_deleted` - Data deleted
- `alert_triggered` - Alert triggered
- `system_error` - System error occurred

#### Webhook Payload
```json
{
  "event_type": "sync_complete",
  "timestamp": "2024-01-01T10:00:00Z",
  "data": {
    "sync_id": 123,
    "entity_type": "partner",
    "backend_id": 1,
    "status": "success",
    "records_synced": 5,
    "errors": 0
  }
}
```

#### Signature Validation
Webhooks include a signature header for validation:

```
X-Signature: sha256=abc123...
```

The signature is generated using HMAC-SHA256 with your webhook secret key.

## Plugin Development

### Creating a Plugin

1. **Create Plugin Class**
   ```python
   from addons.sap_integration.core.sap_base_plugin import SapBasePlugin
   
   class MyCustomPlugin(SapBasePlugin):
       PLUGIN_ID = 'my_custom_plugin'
       PLUGIN_NAME = 'My Custom Plugin'
       PLUGIN_VERSION = '1.0.0'
       PLUGIN_DESCRIPTION = 'Custom plugin for data processing'
       PLUGIN_AUTHOR = 'Your Name'
       PLUGIN_CATEGORY = 'data_processing'
       PLUGIN_DEPENDENCIES = []
       PLUGIN_CONFIG_SCHEMA = {
           'param1': {'type': str, 'required': True},
           'param2': {'type': int, 'required': False, 'default': 10}
       }
       
       def initialize(self):
           # Initialize plugin
           pass
       
       def execute(self, context=None):
           # Execute plugin logic
           return {'status': 'success', 'message': 'Plugin executed'}
       
       def cleanup(self):
           # Cleanup plugin
           pass
   ```

2. **Register Plugin**
   ```python
   plugin_manager = self.env['sap.plugin.manager']
   result = plugin_manager.register_plugin(
       plugin_class=MyCustomPlugin,
       plugin_info={
           'id': 'my_custom_plugin',
           'name': 'My Custom Plugin',
           'version': '1.0.0',
           'description': 'Custom plugin for data processing',
           'author': 'Your Name',
           'category': 'data_processing',
           'dependencies': [],
           'config_schema': {}
       }
   )
   ```

3. **Execute Plugin**
   ```python
   result = plugin_manager.execute_plugin(
       plugin_id='my_custom_plugin',
       context={'data': [1, 2, 3, 4, 5]}
   )
   ```

### Plugin Types

#### Data Processing Plugin
```python
from addons.sap_integration.core.sap_base_plugin import SapDataProcessorPlugin

class MyDataProcessor(SapDataProcessorPlugin):
    def process_data(self, data, context=None):
        # Process data
        processed_data = []
        for item in data:
            processed_item = self.transform_item(item)
            processed_data.append(processed_item)
        
        return processed_data
```

#### Sync Plugin
```python
from addons.sap_integration.core.sap_base_plugin import SapSyncPlugin

class MySyncPlugin(SapSyncPlugin):
    def sync_data(self, backend_id, entity_type, context=None):
        # Custom sync logic
        return {'status': 'success', 'synced_records': 10}
```

#### Validation Plugin
```python
from addons.sap_integration.core.sap_base_plugin import SapValidationPlugin

class MyValidationPlugin(SapValidationPlugin):
    def validate_data(self, data, context=None):
        # Validation logic
        errors = []
        if not data.get('name'):
            errors.append('Name is required')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
```

## Customization

### Custom Rules

1. **Create Custom Rule**
   ```python
   customization_engine = self.env['sap.customization.engine']
   rule = customization_engine.create_rule(
       name='Custom Validation Rule',
       rule_type='validation',
       rule_code='''
       # Custom validation logic
       if input_data.get("amount", 0) > 1000:
           result = {
               "success": True,
               "valid": True,
               "message": "Amount is valid"
           }
       else:
           result = {
               "success": True,
               "valid": False,
               "message": "Amount must be greater than 1000"
           }
       ''',
       trigger_model='sap.sync.log',
       trigger_condition='input_data.get("status") == "failed"'
   )
   ```

2. **Execute Rule**
   ```python
   result = customization_engine.execute_rule(
       rule_id=rule.id,
       input_data={'amount': 1500}
   )
   ```

### Custom Mappings

1. **UoM Mapping**
   ```python
   uom_mapping = self.env['sap.uom.mapping'].create({
       'sap_uom_code': 'PC',
       'odoo_uom_id': self.env.ref('uom.product_uom_unit').id,
       'conversion_factor': 1.0
   })
   ```

2. **Product UoM**
   ```python
   product_uom = self.env['sap.product.uom'].create({
       'product_id': product.id,
       'sap_uom_code': 'PC',
       'odoo_uom_id': self.env.ref('uom.product_uom_unit').id,
       'conversion_factor': 1.0,
       'usage_type': 'sales'
   })
   ```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check SAP Service Layer URL and port
   - Verify username and password
   - Ensure SAP Service Layer is running
   - Check network connectivity

2. **Authentication Failed**
   - Verify SAP credentials
   - Check company database name
   - Ensure user has proper permissions

3. **Sync Errors**
   - Check sync logs for detailed error messages
   - Verify data mapping configuration
   - Check for data validation errors
   - Review field mappings

4. **Performance Issues**
   - Adjust batch size settings
   - Enable incremental sync
   - Check network latency
   - Monitor system resources

### Debug Mode

Enable debug mode for detailed logging:

1. Go to SAP Integration > Configuration > Settings
2. Enable "Debug Mode"
3. Check logs for detailed information

### Log Analysis

1. **View Sync Logs**
   - Go to SAP Integration > Monitoring > Sync Logs
   - Filter by status, date, or entity type
   - Export logs for analysis

2. **Error Analysis**
   - Use the error analyzer tool
   - Review error patterns and trends
   - Check for common error causes

## Support

### Documentation
- User Guide: [User Guide](user_guide.md)
- API Reference: [API Reference](api_reference.md)
- Developer Guide: [Developer Guide](developer_guide.md)
- FAQ: [Frequently Asked Questions](faq.md)

### Community
- GitHub Issues: [Report Issues](https://github.com/your-repo/issues)
- Discussion Forum: [Community Forum](https://github.com/your-repo/discussions)
- Wiki: [Community Wiki](https://github.com/your-repo/wiki)

### Professional Support
- Email: support@yourcompany.com
- Phone: +1-555-0123
- Support Portal: [Support Portal](https://support.yourcompany.com)

## License

This module is licensed under LGPL-3.0 or later. See [LICENSE](LICENSE) for details.

## Changelog

### Version 1.0.0
- Initial release
- Basic synchronization functionality
- Data mapping and UoM management
- Error handling and logging
- Monitoring and dashboards
- Plugin architecture
- API framework
- Webhook system
- Customization engine
- Comprehensive testing suite
