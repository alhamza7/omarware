# SAP Integration Module - Architecture Documentation

## Overview

This document describes the refactored architecture of the SAP Integration module, which provides seamless synchronization between Odoo and SAP Business One using the Service Layer API.

## Architecture Principles

### 1. Separation of Concerns
The module is organized into distinct layers, each with specific responsibilities:

- **Configuration Layer**: Centralized configuration and constants
- **Core Layer**: Base services, logging, and data mapping
- **Service Layer**: Business logic for synchronization operations
- **Model Layer**: Odoo models and data persistence
- **Component Layer**: OCA Connector framework integration
- **View Layer**: User interface and forms

### 2. Error Handling and Logging
- Centralized error handling with custom exceptions
- Comprehensive logging system with structured log entries
- Error tracking and retry mechanisms
- User-friendly error messages

### 3. Data Mapping
- Centralized data transformation between SAP and Odoo formats
- Field mapping configuration
- Validation rules and data preparation

## Module Structure

```
addons/sap_integration/
├── config/                 # Configuration and constants
│   ├── __init__.py
│   └── sap_config.py      # Centralized configuration
├── core/                  # Core functionality
│   ├── __init__.py
│   ├── sap_logger.py      # Logging and error handling
│   ├── sap_base_service.py # Base service class
│   └── sap_mapper.py      # Data mapping utilities
├── services/              # Business logic services
│   ├── __init__.py
│   └── sap_customer_service.py # Customer sync service
├── models/                # Odoo models
│   ├── __init__.py
│   ├── sap_backend.py     # Backend configuration
│   ├── sap_binding.py     # Binding models
│   ├── sap_customer.py    # Customer sync model
│   └── ...                # Other model files
├── components/            # OCA Connector components
│   ├── __init__.py
│   ├── adapter.py         # SAP adapters
│   ├── mapper.py          # Component mappers
│   └── ...                # Other component files
├── views/                 # User interface
│   ├── sap_backend_views.xml
│   ├── sap_sync_log_views.xml
│   └── ...                # Other view files
└── security/              # Access control
    ├── ir.model.access.csv
    └── sap_security.xml
```

## Core Components

### 1. Configuration (`config/sap_config.py`)

Centralized configuration containing:
- SAP Service Layer endpoints
- Field mappings between SAP and Odoo
- Sync configuration parameters
- Error messages and validation rules
- Default values

**Example:**
```python
SAP_PARTNER_FIELDS = {
    'card_code': 'CardCode',
    'card_name': 'CardName',
    'email': 'EmailAddress',
    # ... more fields
}

SYNC_CONFIG = {
    'default_batch_size': 100,
    'default_timeout': 30,
    'default_retry_attempts': 3,
    # ... more config
}
```

### 2. Logging System (`core/sap_logger.py`)

Comprehensive logging system with:
- Structured log entries stored in database
- Different log levels (success, error, warning, info)
- Error tracking with traceback information
- Performance metrics (duration, records processed)
- Log filtering and search capabilities

**Key Classes:**
- `SapLogger`: Centralized logger
- `SapSyncLog`: Database model for log entries
- `SapException`: Custom exception classes

### 3. Base Service (`core/sap_base_service.py`)

Abstract base class providing common functionality:
- Data validation and preparation
- Error handling and logging
- Connection management
- Sync result formatting
- Retry mechanisms

**Key Methods:**
- `_validate_data()`: Validate data before processing
- `_log_operation()`: Log operations with details
- `_handle_exception()`: Centralized exception handling
- `_get_backend_connection()`: Get SAP connection

### 4. Data Mapper (`core/sap_mapper.py`)

Centralized data transformation:
- SAP to Odoo field mapping
- Odoo to SAP field mapping
- Data validation and preparation
- Type conversion and formatting

**Key Methods:**
- `map_sap_partner_to_odoo()`: Map SAP partner to Odoo format
- `map_odoo_partner_to_sap()`: Map Odoo partner to SAP format
- `map_sap_product_to_odoo()`: Map SAP product to Odoo format
- `map_odoo_product_to_sap()`: Map Odoo product to SAP format

## Service Layer

### Customer Service (`services/sap_customer_service.py`)

Business logic for customer synchronization:

**Key Methods:**
- `sync_customer_from_sap()`: Sync single customer from SAP
- `sync_customer_to_sap()`: Sync single customer to SAP
- `sync_all_customers_from_sap()`: Batch sync all customers
- `get_customer_sync_status()`: Get sync status for customer

**Example Usage:**
```python
# Sync single customer
customer_service = self.env['sap.customer.service']
result = customer_service.sync_customer_from_sap(backend_id, sap_data)

# Batch sync all customers
result = customer_service.sync_all_customers_from_sap(backend_id)
```

## Model Layer

### Backend Model (`models/sap_backend.py`)

SAP backend configuration with:
- Connection settings
- Sync preferences
- Error handling
- Connection testing

### Binding Models (`models/sap_binding.py`)

OCA Connector binding models:
- `SapResPartner`: Partner binding
- `SapProductProduct`: Product binding
- `SapSaleOrder`: Sale order binding
- `SapAccountMove`: Invoice binding

### Sync Models (`models/sap_customer.py`)

Synchronization tracking models:
- Sync status and direction
- Error tracking and retry counts
- Data storage for debugging

## Component Layer

### Adapters (`components/adapter.py`)

OCA Connector adapters for SAP integration:
- `SapPartnerAdapter`: Partner operations
- `SapProductAdapter`: Product operations
- `SapSaleOrderAdapter`: Order operations
- `SapInvoiceAdapter`: Invoice operations

## Error Handling

### Exception Hierarchy

```
SapException (base)
├── SapConnectionError
├── SapSyncError
└── SapValidationError
```

### Error Logging

All errors are logged with:
- Error type and message
- Full traceback
- Context information
- Retry count
- Timestamp

### Retry Mechanism

- Configurable retry attempts
- Exponential backoff
- Error tracking
- Automatic retry for transient errors

## Data Flow

### Import Flow (SAP → Odoo)

1. **Trigger**: Manual sync or scheduled job
2. **Connection**: Get SAP Service Layer connection
3. **Data Retrieval**: Fetch data from SAP
4. **Mapping**: Transform SAP data to Odoo format
5. **Validation**: Validate data before processing
6. **Processing**: Create or update Odoo records
7. **Logging**: Log operation results
8. **Error Handling**: Handle and log any errors

### Export Flow (Odoo → SAP)

1. **Trigger**: Record change or manual sync
2. **Data Retrieval**: Get Odoo record data
3. **Mapping**: Transform Odoo data to SAP format
4. **Validation**: Validate data before sending
5. **Connection**: Get SAP Service Layer connection
6. **Processing**: Create or update SAP records
7. **Logging**: Log operation results
8. **Error Handling**: Handle and log any errors

## Configuration

### Backend Configuration

Each SAP backend requires:
- Service Layer URL
- Username and password
- Company database
- SSL verification settings
- Sync preferences
- Batch size and timeout settings

### Field Mapping

Field mappings are configured in `sap_config.py`:
- SAP field names to Odoo field names
- Data type conversions
- Required field validation
- Field length limits

### Sync Settings

Configurable sync options:
- Enable/disable sync for each entity type
- Auto-sync on record changes
- Incremental sync settings
- Batch processing parameters

## Security

### Access Control

- Role-based permissions
- SAP Manager: Full access
- SAP User: Read-only access
- Sync Log access: Manager only

### Data Security

- Encrypted password storage
- SSL certificate verification
- Session management
- Audit logging

## Performance

### Optimization Features

- Batch processing
- Connection pooling
- Incremental sync
- Error retry mechanisms
- Performance logging

### Monitoring

- Sync duration tracking
- Record processing counts
- Error rate monitoring
- Performance metrics

## Future Enhancements

### Planned Features

1. **Queue Job Integration**: Background job processing
2. **Real-time Sync**: Event-driven synchronization
3. **Advanced Mapping**: Configurable field mappings
4. **Sync Dashboard**: Visual sync monitoring
5. **Data Validation**: Enhanced validation rules
6. **API Extensions**: Additional SAP endpoints

### Extensibility

The architecture supports:
- Custom service implementations
- Additional entity types
- Custom field mappings
- Plugin architecture
- Third-party integrations

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check SAP Service Layer URL and credentials
2. **Mapping Errors**: Verify field mappings in configuration
3. **Validation Errors**: Check data format and required fields
4. **Sync Failures**: Review sync logs for detailed error information

### Debugging

- Enable debug logging
- Review sync log entries
- Check error tracebacks
- Validate data formats
- Test connections manually

## Conclusion

The refactored SAP Integration module provides a robust, maintainable, and extensible solution for synchronizing data between Odoo and SAP Business One. The clear separation of concerns, comprehensive error handling, and detailed logging make it easy to monitor, debug, and extend the integration as needed.
