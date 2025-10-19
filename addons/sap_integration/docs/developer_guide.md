# SAP Integration Developer Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Plugin Development](#plugin-development)
4. [API Development](#api-development)
5. [Customization Engine](#customization-engine)
6. [Testing](#testing)
7. [Deployment](#deployment)

## Architecture Overview

### Module Structure
```
sap_integration/
├── __init__.py
├── __manifest__.py
├── config/                 # Configuration management
│   ├── __init__.py
│   └── sap_config.py
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── sap_logger.py
│   ├── sap_base_service.py
│   ├── sap_mapper.py
│   ├── sap_sync_engine.py
│   ├── sap_data_mapper.py
│   ├── sap_incremental_sync.py
│   ├── sap_retry_mechanism.py
│   ├── sap_batch_processor.py
│   ├── sap_uom_converter.py
│   ├── sap_plugin_manager.py
│   ├── sap_base_plugin.py
│   ├── sap_api_framework.py
│   ├── sap_webhook_system.py
│   └── sap_customization_engine.py
├── models/                 # Odoo models
│   ├── __init__.py
│   ├── sap_backend.py
│   ├── sap_binding.py
│   ├── sap_connector.py
│   ├── sap_customer.py
│   ├── sap_product.py
│   ├── sap_quotation.py
│   ├── sap_sale.py
│   ├── sap_invoice.py
│   ├── sap_uom.py
│   ├── sap_pricelist.py
│   ├── sap_service_layer.py
│   ├── sap_dashboard.py
│   ├── sap_dashboard_enhanced.py
│   ├── sap_synced_data.py
│   ├── sap_uom_mapping.py
│   ├── sap_product_uom.py
│   ├── sap_dashboard_control.py
│   └── sap_user_management.py
├── components/             # OCA Connector components
│   ├── __init__.py
│   ├── adapter.py
│   ├── binder.py
│   ├── importer.py
│   └── exporter.py
├── services/               # Business logic services
│   ├── __init__.py
│   └── sap_customer_service.py
├── wizard/                 # Wizards and dialogs
│   ├── __init__.py
│   ├── sap_conflict_resolution_wizard.py
│   ├── sap_uom_conversion_test_wizard.py
│   ├── sap_user_permission_wizard.py
│   └── sap_bulk_permission_wizard.py
├── views/                  # Odoo views
│   ├── sap_dashboard_views.xml
│   ├── sap_backend_views.xml
│   ├── sap_connector_views.xml
│   ├── sap_mapper_views.xml
│   ├── sap_binding_views.xml
│   ├── sap_sync_log_views.xml
│   ├── sap_analysis_views.xml
│   ├── sap_synced_data_views.xml
│   ├── sap_synced_data_dashboard.xml
│   ├── sap_sync_management_views.xml
│   ├── sap_uom_management_views.xml
│   ├── sap_dashboard_control_views.xml
│   └── sap_future_proofing_views.xml
├── security/               # Security configuration
│   ├── sap_security.xml
│   └── ir.model.access.csv
├── data/                   # Data files
│   ├── sap_backend_data.xml
│   └── sap_cron_data.xml
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_sap_backend.py
│   ├── test_sap_sync_engine.py
│   ├── test_sap_data_mapper.py
│   ├── test_sap_uom_converter.py
│   ├── test_sap_plugin_manager.py
│   ├── test_sap_api_framework.py
│   ├── test_sap_webhook_system.py
│   ├── test_sap_customization_engine.py
│   ├── test_sap_dashboard_control.py
│   ├── test_sap_user_management.py
│   ├── test_integration.py
│   ├── test_performance.py
│   └── test_security.py
└── docs/                   # Documentation
    ├── README.md
    ├── user_guide.md
    ├── developer_guide.md
    └── api_reference.md
```

### Design Patterns

#### Service Layer Pattern
- **Core Services**: Business logic and data processing
- **Model Services**: Odoo model-specific operations
- **External Services**: SAP API integration

#### Plugin Architecture
- **Base Plugin**: Common functionality for all plugins
- **Plugin Manager**: Registration and lifecycle management
- **Plugin Types**: Specialized plugin categories

#### API Framework
- **RESTful API**: Standard HTTP endpoints
- **Authentication**: API key-based authentication
- **Rate Limiting**: Request throttling and limits

## Core Components

### SAP Logger

The SAP Logger provides centralized logging functionality with structured log storage.

```python
from addons.sap_integration.core.sap_logger import SapLogger

# Initialize logger
logger = SapLogger("sap_integration.my_component")

# Log messages
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")

# Log with context
logger.info("Sync started", extra={
    'backend_id': 1,
    'entity_type': 'partner',
    'record_id': 123
})
```

### SAP Base Service

Base class for all SAP services with common functionality.

```python
from addons.sap_integration.core.sap_base_service import SapBaseService

class MySapService(SapBaseService):
    _name = 'my.sap.service'
    _description = 'My SAP Service'
    
    def my_method(self):
        # Use logger
        self.logger.info("Executing my method")
        
        # Get backend
        backend = self._get_backend(backend_id)
        
        # Get connection
        connection = self._get_connection(backend)
        
        # Log success
        self._log_success(
            backend_id=backend.id,
            model_name='my.model',
            record_id=123,
            external_id='EXT001',
            operation='my_operation',
            message='Operation completed successfully'
        )
```

### SAP Sync Engine

Core synchronization engine for bidirectional data sync.

```python
from addons.sap_integration.core.sap_sync_engine import SapSyncEngine

# Initialize sync engine
sync_engine = self.env['sap.sync.engine']

# Sync single entity
result = sync_engine.sync_entity(
    backend_id=1,
    entity_type='partner',
    external_id='CUSTOMER001',
    direction='sap_to_odoo'
)

# Sync all entities
result = sync_engine.sync_all_entities(
    backend_id=1,
    entity_types=['partner', 'product'],
    direction='bidirectional'
)
```

### SAP Data Mapper

Data transformation between SAP and Odoo formats.

```python
from addons.sap_integration.core.sap_data_mapper import SapDataMapper

# Initialize data mapper
data_mapper = self.env['sap.data.mapper']

# Map SAP to Odoo
odoo_data = data_mapper.map_sap_to_odoo('partner', sap_data)

# Map Odoo to SAP
sap_data = data_mapper.map_odoo_to_sap('partner', odoo_record)
```

### SAP UoM Converter

Unit of Measure conversion and management.

```python
from addons.sap_integration.core.sap_uom_converter import SapUomConverter

# Initialize UoM converter
uom_converter = self.env['sap.uom.converter']

# Convert quantity
converted_qty = uom_converter.convert_quantity(
    quantity=10,
    from_uom_code='PC',
    to_uom_code='EA',
    product_id=123
)

# Validate UoM consistency
uom_converter.validate_uom_consistency('PC', uom_id)
```

## Plugin Development

### Creating a Plugin

#### Basic Plugin Structure

```python
from addons.sap_integration.core.sap_base_plugin import SapBasePlugin

class MyCustomPlugin(SapBasePlugin):
    # Plugin metadata
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
        """Initialize the plugin"""
        self.logger.info("Initializing My Custom Plugin")
        # Plugin initialization logic
    
    def execute(self, context=None):
        """Execute the plugin"""
        self.logger.info("Executing My Custom Plugin")
        
        # Get configuration
        param1 = self.get_config('param1')
        param2 = self.get_config('param2', 10)
        
        # Plugin execution logic
        result = self.process_data(context.get('data', []))
        
        return {
            'status': 'success',
            'message': 'Plugin executed successfully',
            'result': result
        }
    
    def cleanup(self):
        """Cleanup the plugin"""
        self.logger.info("Cleaning up My Custom Plugin")
        # Plugin cleanup logic
    
    def process_data(self, data):
        """Process data"""
        processed_data = []
        for item in data:
            processed_item = self.transform_item(item)
            processed_data.append(processed_item)
        return processed_data
    
    def transform_item(self, item):
        """Transform individual item"""
        # Transformation logic
        return item
```

#### Specialized Plugin Types

##### Data Processing Plugin

```python
from addons.sap_integration.core.sap_base_plugin import SapDataProcessorPlugin

class MyDataProcessor(SapDataProcessorPlugin):
    PLUGIN_ID = 'my_data_processor'
    PLUGIN_NAME = 'My Data Processor'
    PLUGIN_CATEGORY = 'data_processing'
    
    def process_data(self, data, context=None):
        """Process data"""
        processed_data = []
        for item in data:
            processed_item = self.transform_item(item)
            processed_data.append(processed_item)
        return processed_data
```

##### Sync Plugin

```python
from addons.sap_integration.core.sap_base_plugin import SapSyncPlugin

class MySyncPlugin(SapSyncPlugin):
    PLUGIN_ID = 'my_sync_plugin'
    PLUGIN_NAME = 'My Sync Plugin'
    PLUGIN_CATEGORY = 'sync'
    
    def sync_data(self, backend_id, entity_type, context=None):
        """Sync data"""
        # Custom sync logic
        return {
            'status': 'success',
            'synced_records': 10,
            'errors': 0
        }
```

##### Validation Plugin

```python
from addons.sap_integration.core.sap_base_plugin import SapValidationPlugin

class MyValidationPlugin(SapValidationPlugin):
    PLUGIN_ID = 'my_validation_plugin'
    PLUGIN_NAME = 'My Validation Plugin'
    PLUGIN_CATEGORY = 'validation'
    
    def validate_data(self, data, context=None):
        """Validate data"""
        errors = []
        warnings = []
        
        # Validation logic
        if not data.get('name'):
            errors.append('Name is required')
        
        if data.get('amount', 0) < 0:
            warnings.append('Amount is negative')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
```

### Plugin Registration

#### Manual Registration

```python
# Register plugin
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
        'config_schema': {
            'param1': {'type': str, 'required': True},
            'param2': {'type': int, 'required': False, 'default': 10}
        }
    }
)
```

#### Automatic Registration

```python
# Load plugins from directory
result = plugin_manager.load_plugins_from_directory('/path/to/plugins')
```

### Plugin Execution

```python
# Execute plugin
result = plugin_manager.execute_plugin(
    plugin_id='my_custom_plugin',
    context={'data': [1, 2, 3, 4, 5]}
)

# Get plugin instance
plugin = plugin_manager.get_plugin('my_custom_plugin')

# Set configuration
plugin.set_config({
    'param1': 'value1',
    'param2': 20
})

# Execute with configuration
result = plugin.execute(context={'data': [1, 2, 3, 4, 5]})
```

## API Development

### Creating API Endpoints

#### Basic Endpoint

```python
from addons.sap_integration.core.sap_api_framework import SapApiFramework

# Create API endpoint
api_framework = self.env['sap.api.framework']
endpoint = api_framework.create_endpoint(
    name='Sync Data',
    path='/api/v1/sync',
    method='POST',
    handler_function='sync_data',
    requires_authentication=True,
    rate_limit_requests=100,
    rate_limit_window=60
)
```

#### Custom Handler

```python
def custom_sync_handler(request_data):
    """Custom sync handler"""
    try:
        # Get request data
        body = request_data.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        # Process request
        backend_id = body.get('backend_id')
        entity_type = body.get('entity_type')
        
        # Execute sync
        sync_engine = self.env['sap.sync.engine']
        result = sync_engine.sync_entity(
            backend_id=backend_id,
            entity_type=entity_type,
            direction='sap_to_odoo'
        )
        
        return {
            'status': 200,
            'body': {
                'success': True,
                'result': result
            },
            'headers': {'Content-Type': 'application/json'}
        }
        
    except Exception as e:
        return {
            'status': 500,
            'body': {'error': str(e)},
            'headers': {'Content-Type': 'application/json'}
        }
```

### API Key Management

```python
# Create API key
api_key = api_framework.create_api_key(
    name='External System',
    user_id=user_id,
    endpoint_ids=[endpoint.id],
    expires_date=fields.Datetime.now() + timedelta(days=30)
)

# Validate API key
valid = api_framework.validate_api_key(
    api_key.key_value,
    '/api/v1/sync'
)
```

### Rate Limiting

```python
# Check rate limit
allowed = api_framework.check_rate_limit(
    api_key='your_api_key',
    endpoint_id=endpoint.id
)
```

## Customization Engine

### Creating Custom Rules

#### Basic Rule

```python
from addons.sap_integration.core.sap_customization_engine import SapCustomizationEngine

# Create customization rule
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

#### Rule Execution

```python
# Execute rule
result = customization_engine.execute_rule(
    rule_id=rule.id,
    input_data={'amount': 1500}
)

# Execute rules for model
result = customization_engine.execute_rules_for_model(
    model_name='sap.sync.log',
    record_id=123,
    trigger_field='status'
)
```

### Rule Types

#### Data Mapping Rules

```python
rule = customization_engine.create_rule(
    name='Custom Data Mapping',
    rule_type='data_mapping',
    rule_code='''
# Custom data mapping logic
mapped_data = {
    'name': input_data.get('CardName', ''),
    'email': input_data.get('EmailAddress', ''),
    'phone': input_data.get('Phone1', ''),
    'is_company': True,
    'customer_rank': 1
}
result = {
    'success': True,
    'mapped_data': mapped_data
}
'''
)
```

#### Business Logic Rules

```python
rule = customization_engine.create_rule(
    name='Business Logic Rule',
    rule_type='business_logic',
    rule_code='''
# Business logic
if input_data.get('amount', 0) > 10000:
    # Apply special discount
    discount = 0.1
    final_amount = input_data['amount'] * (1 - discount)
else:
    final_amount = input_data['amount']

result = {
    'success': True,
    'final_amount': final_amount,
    'discount_applied': discount if 'discount' in locals() else 0
}
'''
)
```

## Testing

### Unit Tests

#### Basic Test Structure

```python
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestMyComponent(TransactionCase):
    """Test My Component functionality"""
    
    def setUp(self):
        super().setUp()
        self.my_component = self.env['my.component']
        self.test_data = {
            'field1': 'value1',
            'field2': 'value2'
        }
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.my_component.my_method(self.test_data)
        self.assertEqual(result['status'], 'success')
    
    @patch('requests.post')
    def test_external_api_call(self, mock_post):
        """Test external API call"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'success'}
        mock_post.return_value = mock_response
        
        # Test method
        result = self.my_component.call_external_api()
        self.assertTrue(result['success'])
```

#### Integration Tests

```python
class TestSapIntegration(TransactionCase):
    """Test SAP Integration end-to-end functionality"""
    
    def test_full_sync_workflow(self):
        """Test complete sync workflow"""
        # Setup test data
        backend = self.env['sap.backend'].create({
            'name': 'Test Backend',
            'host': 'test.sap.com',
            'port': 50000,
            'company_db': 'TEST_DB',
            'username': 'test_user',
            'password': 'test_password'
        })
        
        # Mock SAP connection
        with patch.object(backend, 'get_connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = {
                'CardCode': 'TEST001',
                'CardName': 'Test Partner'
            }
            mock_connection.return_value = mock_conn
            
            # Execute sync
            sync_engine = self.env['sap.sync.engine']
            result = sync_engine.sync_entity(
                backend_id=backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            # Verify result
            self.assertEqual(result['status'], 'success')
```

### Performance Tests

```python
import time
from odoo.tests.common import TransactionCase

class TestPerformance(TransactionCase):
    """Test performance characteristics"""
    
    def test_sync_performance(self):
        """Test sync performance"""
        start_time = time.time()
        
        # Execute sync operation
        result = self.sync_engine.sync_all_entities(
            backend_id=1,
            entity_types=['partner', 'product'],
            direction='sap_to_odoo'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance
        self.assertLess(duration, 30)  # Should complete within 30 seconds
        self.assertGreater(result['successful'], 0)
```

### Security Tests

```python
class TestSecurity(TransactionCase):
    """Test security features"""
    
    def test_api_key_validation(self):
        """Test API key validation"""
        api_framework = self.env['sap.api.framework']
        
        # Test valid API key
        valid = api_framework.validate_api_key(
            'valid_api_key',
            '/api/v1/sync'
        )
        self.assertTrue(valid)
        
        # Test invalid API key
        invalid = api_framework.validate_api_key(
            'invalid_api_key',
            '/api/v1/sync'
        )
        self.assertFalse(invalid)
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        webhook_system = self.env['sap.webhook.system']
        
        # Test signature generation
        signature = webhook_system._generate_signature(
            'secret_key',
            {'test': 'data'}
        )
        
        self.assertTrue(signature.startswith('sha256='))
        self.assertEqual(len(signature), 71)
```

## Deployment

### Configuration Management

#### Environment Configuration

```python
# Development configuration
DEVELOPMENT_CONFIG = {
    'debug': True,
    'log_level': 'DEBUG',
    'sap_timeout': 30,
    'batch_size': 50
}

# Production configuration
PRODUCTION_CONFIG = {
    'debug': False,
    'log_level': 'INFO',
    'sap_timeout': 60,
    'batch_size': 200
}
```

#### Database Migration

```python
def migrate_database(env):
    """Migrate database schema"""
    # Add new fields
    env['sap.backend']._add_column('new_field', 'Char')
    
    # Update existing data
    backends = env['sap.backend'].search([])
    for backend in backends:
        backend.new_field = 'default_value'
```

### Monitoring Setup

#### Health Checks

```python
def health_check():
    """Perform health check"""
    checks = {
        'database': check_database_connection(),
        'sap_backend': check_sap_backend_connection(),
        'api_endpoints': check_api_endpoints(),
        'webhooks': check_webhook_endpoints()
    }
    
    return {
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks
    }
```

#### Performance Monitoring

```python
def monitor_performance():
    """Monitor performance metrics"""
    metrics = {
        'sync_duration': get_avg_sync_duration(),
        'error_rate': get_error_rate(),
        'throughput': get_throughput(),
        'memory_usage': get_memory_usage()
    }
    
    return metrics
```

### Backup and Recovery

#### Configuration Backup

```python
def backup_configuration():
    """Backup configuration"""
    config_data = {
        'backends': env['sap.backend'].search([]).read(),
        'mappings': env['sap.uom.mapping'].search([]).read(),
        'rules': env['sap.customization.rule'].search([]).read()
    }
    
    return config_data
```

#### Data Recovery

```python
def restore_configuration(config_data):
    """Restore configuration"""
    # Restore backends
    for backend_data in config_data['backends']:
        env['sap.backend'].create(backend_data)
    
    # Restore mappings
    for mapping_data in config_data['mappings']:
        env['sap.uom.mapping'].create(mapping_data)
    
    # Restore rules
    for rule_data in config_data['rules']:
        env['sap.customization.rule'].create(rule_data)
```

This developer guide provides comprehensive information for developers working with the SAP Integration module, including architecture details, component usage, plugin development, API development, testing, and deployment strategies.
