# SAP Integration API Reference

## Table of Contents
1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Webhooks](#webhooks)
7. [Examples](#examples)

## Authentication

### API Key Authentication

All API requests require authentication using API keys. Include the API key in the request headers:

```http
X-API-Key: your_api_key_here
Content-Type: application/json
```

### Creating API Keys

1. Go to SAP Integration > API Framework > API Keys
2. Click "Create" to add a new API key
3. Fill in the details:
   - **Name**: Descriptive name for the API key
   - **Description**: Optional description
   - **User**: Associated Odoo user
   - **Allowed Endpoints**: Specific endpoints this key can access
   - **Expires Date**: Optional expiration date
4. Save the API key

### API Key Management

```python
# Create API key
api_framework = self.env['sap.api.framework']
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

## Endpoints

### Base URL

```
https://your-odoo-instance.com/sap_integration/api/v1
```

### Common Headers

```http
X-API-Key: your_api_key_here
Content-Type: application/json
Accept: application/json
```

### Sync Data

#### POST /sync

Synchronize data between SAP and Odoo.

**Request Body:**
```json
{
  "backend_id": 1,
  "entity_type": "partner",
  "direction": "sap_to_odoo",
  "external_id": "CUSTOMER001",
  "record_id": 123
}
```

**Parameters:**
- `backend_id` (integer, required): SAP backend ID
- `entity_type` (string, required): Entity type (partner, product, etc.)
- `direction` (string, required): Sync direction (sap_to_odoo, odoo_to_sap, bidirectional)
- `external_id` (string, optional): SAP external ID
- `record_id` (integer, optional): Odoo record ID

**Response:**
```json
{
  "status": "success",
  "message": "Sync completed successfully",
  "result": {
    "synced_records": 1,
    "errors": 0,
    "duration_ms": 1500
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "backend_id",
    "message": "Backend ID is required"
  }
}
```

#### POST /sync/bulk

Bulk synchronization of multiple entities.

**Request Body:**
```json
{
  "backend_id": 1,
  "entity_types": ["partner", "product"],
  "direction": "sap_to_odoo",
  "sync_type": "full",
  "batch_size": 100
}
```

**Parameters:**
- `backend_id` (integer, required): SAP backend ID
- `entity_types` (array, required): List of entity types to sync
- `direction` (string, required): Sync direction
- `sync_type` (string, optional): Sync type (full, incremental)
- `batch_size` (integer, optional): Number of records per batch

**Response:**
```json
{
  "status": "success",
  "message": "Bulk sync completed",
  "result": {
    "total_entities": 2,
    "successful_entities": 2,
    "failed_entities": 0,
    "total_records": 500,
    "successful_records": 500,
    "failed_records": 0,
    "duration_ms": 30000
  }
}
```

### Status and Monitoring

#### GET /status

Get current system status and statistics.

**Response:**
```json
{
  "sync_status_overview": {
    "success": 150,
    "failed": 5,
    "pending": 10,
    "in_progress": 2
  },
  "synced_data_status_overview": {
    "success": 200,
    "failed": 3,
    "conflict": 2,
    "pending": 5
  },
  "new_alerts_count": 1,
  "latest_performance_metrics": {
    "avg_sync_duration": 2.5,
    "total_records_synced": 1000,
    "total_errors": 20,
    "error_rate": 0.02
  },
  "backends": [
    {
      "id": 1,
      "name": "Production SAP",
      "active": true,
      "connection_status": "connected"
    }
  ]
}
```

#### GET /health

Perform health check on the system.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "checks": {
    "database": true,
    "sap_backend": true,
    "api_endpoints": true,
    "webhooks": true
  },
  "version": "1.0.0"
}
```

### Logs and Monitoring

#### GET /logs

Retrieve synchronization logs.

**Query Parameters:**
- `limit` (integer, optional): Number of logs to return (default: 100, max: 1000)
- `offset` (integer, optional): Number of logs to skip (default: 0)
- `status` (string, optional): Filter by status (success, failed, info, warning)
- `model_name` (string, optional): Filter by model name
- `date_from` (string, optional): Filter from date (ISO format)
- `date_to` (string, optional): Filter to date (ISO format)
- `backend_id` (integer, optional): Filter by backend ID

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
      "message": "Partner synced successfully",
      "backend_id": 1,
      "external_id": "CUSTOMER001",
      "record_id": 123,
      "duration_ms": 1500
    }
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

#### GET /logs/{log_id}

Get detailed information about a specific log entry.

**Response:**
```json
{
  "id": 1,
  "timestamp": "2024-01-01T10:00:00Z",
  "entity": "sap.partner",
  "operation": "sync_sap_to_odoo",
  "status": "success",
  "message": "Partner synced successfully",
  "backend_id": 1,
  "external_id": "CUSTOMER001",
  "record_id": 123,
  "duration_ms": 1500,
  "request_data": {
    "backend_id": 1,
    "entity_type": "partner",
    "external_id": "CUSTOMER001"
  },
  "response_data": {
    "status": "success",
    "synced_records": 1
  },
  "error_details": null
}
```

### Data Management

#### GET /synced-data

Retrieve synchronized data records.

**Query Parameters:**
- `limit` (integer, optional): Number of records to return (default: 100)
- `offset` (integer, optional): Number of records to skip (default: 0)
- `status` (string, optional): Filter by sync status
- `entity_type` (string, optional): Filter by entity type
- `backend_id` (integer, optional): Filter by backend ID
- `date_from` (string, optional): Filter from date
- `date_to` (string, optional): Filter to date

**Response:**
```json
{
  "synced_data": [
    {
      "id": 1,
      "name": "sap.partner - CUSTOMER001",
      "backend_id": 1,
      "odoo_model_id": 1,
      "odoo_record_id": 123,
      "odoo_record_name": "Test Customer",
      "sap_external_id": "CUSTOMER001",
      "sap_object_type": "BusinessPartners",
      "sync_direction": "sap_to_odoo",
      "sync_status": "success",
      "last_sync_date": "2024-01-01T10:00:00Z",
      "next_sync_date": "2024-01-02T10:00:00Z",
      "error_message": null,
      "has_conflicts": false
    }
  ],
  "total": 500,
  "limit": 100,
  "offset": 0
}
```

#### GET /synced-data/{record_id}

Get detailed information about a specific synced data record.

**Response:**
```json
{
  "id": 1,
  "name": "sap.partner - CUSTOMER001",
  "backend_id": 1,
  "odoo_model_id": 1,
  "odoo_record_id": 123,
  "odoo_record_name": "Test Customer",
  "sap_external_id": "CUSTOMER001",
  "sap_object_type": "BusinessPartners",
  "sync_direction": "sap_to_odoo",
  "sync_status": "success",
  "last_sync_date": "2024-01-01T10:00:00Z",
  "next_sync_date": "2024-01-02T10:00:00Z",
  "error_message": null,
  "has_conflicts": false,
  "odoo_data_snapshot": "{\"name\": \"Test Customer\", \"email\": \"test@example.com\"}",
  "sap_data_snapshot": "{\"CardCode\": \"CUSTOMER001\", \"CardName\": \"Test Customer\"}",
  "conflicts": []
}
```

### Configuration Management

#### GET /backends

Retrieve SAP backend configurations.

**Response:**
```json
{
  "backends": [
    {
      "id": 1,
      "name": "Production SAP",
      "host": "sap.company.com",
      "port": 50000,
      "company_db": "PROD_DB",
      "active": true,
      "connection_status": "connected",
      "last_connection": "2024-01-01T10:00:00Z",
      "error_message": null
    }
  ]
}
```

#### GET /backends/{backend_id}

Get detailed information about a specific backend.

**Response:**
```json
{
  "id": 1,
  "name": "Production SAP",
  "host": "sap.company.com",
  "port": 50000,
  "company_db": "PROD_DB",
  "username": "sap_user",
  "active": true,
  "ssl_enabled": true,
  "timeout": 30,
  "retry_attempts": 3,
  "batch_size": 100,
  "incremental_sync_days": 7,
  "connection_status": "connected",
  "last_connection": "2024-01-01T10:00:00Z",
  "error_message": null,
  "statistics": {
    "total_syncs": 1000,
    "successful_syncs": 950,
    "failed_syncs": 50,
    "last_sync": "2024-01-01T10:00:00Z"
  }
}
```

#### POST /backends/{backend_id}/test-connection

Test connection to a SAP backend.

**Response:**
```json
{
  "status": "success",
  "message": "Connection successful",
  "response_time_ms": 500
}
```

### UoM Management

#### GET /uom-mappings

Retrieve UoM mappings.

**Response:**
```json
{
  "uom_mappings": [
    {
      "id": 1,
      "sap_uom_code": "PC",
      "odoo_uom_id": 1,
      "odoo_uom_name": "Units",
      "conversion_factor": 1.0,
      "uom_category": "Unit",
      "active": true
    }
  ]
}
```

#### POST /uom/convert

Convert quantity between UoMs.

**Request Body:**
```json
{
  "quantity": 10,
  "from_uom_code": "PC",
  "to_uom_code": "EA",
  "product_id": 123
}
```

**Response:**
```json
{
  "status": "success",
  "converted_quantity": 10.0,
  "from_uom_code": "PC",
  "to_uom_code": "EA",
  "conversion_factor": 1.0
}
```

## Data Models

### Sync Log

```json
{
  "id": 1,
  "name": "sap.partner - CUSTOMER001 - sync_sap_to_odoo (success)",
  "backend_id": 1,
  "model_name": "sap.partner",
  "record_id": 123,
  "external_id": "CUSTOMER001",
  "operation": "sync_sap_to_odoo",
  "status": "success",
  "log_datetime": "2024-01-01T10:00:00Z",
  "message": "Partner synced successfully",
  "error_type": null,
  "stack_trace": null,
  "sync_direction": "sap_to_odoo"
}
```

### Synced Data

```json
{
  "id": 1,
  "name": "sap.partner - CUSTOMER001",
  "backend_id": 1,
  "odoo_model_id": 1,
  "odoo_record_id": 123,
  "odoo_record_name": "Test Customer",
  "sap_external_id": "CUSTOMER001",
  "sap_object_type": "BusinessPartners",
  "sync_direction": "sap_to_odoo",
  "sync_status": "success",
  "last_sync_date": "2024-01-01T10:00:00Z",
  "next_sync_date": "2024-01-02T10:00:00Z",
  "error_message": null,
  "has_conflicts": false
}
```

### SAP Backend

```json
{
  "id": 1,
  "name": "Production SAP",
  "host": "sap.company.com",
  "port": 50000,
  "company_db": "PROD_DB",
  "username": "sap_user",
  "active": true,
  "ssl_enabled": true,
  "timeout": 30,
  "retry_attempts": 3,
  "batch_size": 100,
  "incremental_sync_days": 7,
  "connection_status": "connected",
  "last_connection": "2024-01-01T10:00:00Z",
  "error_message": null
}
```

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "field_name",
    "message": "Field-specific error message"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing API key |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SAP_CONNECTION_ERROR` | 502 | SAP connection failed |
| `SAP_TIMEOUT_ERROR` | 504 | SAP request timeout |

### Error Examples

#### Validation Error

```json
{
  "status": "error",
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "backend_id",
    "message": "Backend ID is required"
  }
}
```

#### Authentication Error

```json
{
  "status": "error",
  "message": "Invalid API key",
  "error_code": "AUTHENTICATION_ERROR",
  "details": {
    "field": "X-API-Key",
    "message": "API key is invalid or expired"
  }
}
```

#### Rate Limit Error

```json
{
  "status": "error",
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 100,
    "window": 3600,
    "retry_after": 300
  }
}
```

## Rate Limiting

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limit Configuration

- **Default Limit**: 100 requests per hour
- **Window**: 1 hour (3600 seconds)
- **Burst Limit**: 10 requests per minute
- **Reset Time**: Unix timestamp when limit resets

### Rate Limit Exceeded Response

```json
{
  "status": "error",
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 100,
    "remaining": 0,
    "reset_time": "2024-01-01T11:00:00Z",
    "retry_after": 300
  }
}
```

## Webhooks

### Webhook Events

| Event Type | Description | Payload |
|------------|-------------|---------|
| `sync_start` | Sync operation started | `{sync_id, entity_type, backend_id}` |
| `sync_complete` | Sync operation completed | `{sync_id, entity_type, status, records_synced}` |
| `sync_error` | Sync operation failed | `{sync_id, entity_type, error_message}` |
| `data_created` | New data created | `{entity_type, record_id, external_id}` |
| `data_updated` | Data updated | `{entity_type, record_id, external_id}` |
| `data_deleted` | Data deleted | `{entity_type, record_id, external_id}` |
| `alert_triggered` | Alert triggered | `{alert_id, alert_type, message}` |
| `system_error` | System error occurred | `{error_type, error_message, stack_trace}` |

### Webhook Payload Format

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
    "errors": 0,
    "duration_ms": 1500
  }
}
```

### Webhook Signature Validation

Webhooks include a signature header for validation:

```http
X-Signature: sha256=abc123def456...
```

The signature is generated using HMAC-SHA256 with your webhook secret key:

```python
import hmac
import hashlib

def generate_signature(secret_key, payload):
    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

### Webhook Configuration

```python
# Create webhook endpoint
webhook_system = self.env['sap.webhook.system']
webhook = webhook_system.create_webhook(
    name='Sync Notifications',
    url='https://your-system.com/webhooks/sync',
    event_types=['sync_start', 'sync_complete', 'sync_error'],
    secret_key='your_secret_key',
    requires_authentication=True
)
```

## Examples

### Python Client

```python
import requests
import json

class SapIntegrationClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def sync_data(self, backend_id, entity_type, direction, external_id=None, record_id=None):
        """Sync data between SAP and Odoo"""
        url = f"{self.base_url}/sync"
        data = {
            'backend_id': backend_id,
            'entity_type': entity_type,
            'direction': direction
        }
        
        if external_id:
            data['external_id'] = external_id
        if record_id:
            data['record_id'] = record_id
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_status(self):
        """Get system status"""
        url = f"{self.base_url}/status"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_logs(self, limit=100, status=None, date_from=None, date_to=None):
        """Get sync logs"""
        url = f"{self.base_url}/logs"
        params = {'limit': limit}
        
        if status:
            params['status'] = status
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

# Usage
client = SapIntegrationClient(
    base_url='https://your-odoo-instance.com/sap_integration/api/v1',
    api_key='your_api_key_here'
)

# Sync partner data
result = client.sync_data(
    backend_id=1,
    entity_type='partner',
    direction='sap_to_odoo',
    external_id='CUSTOMER001'
)

print(f"Sync result: {result['status']}")

# Get system status
status = client.get_status()
print(f"System status: {status['sync_status_overview']}")

# Get recent logs
logs = client.get_logs(limit=10, status='success')
print(f"Recent successful syncs: {len(logs['logs'])}")
```

### JavaScript Client

```javascript
class SapIntegrationClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
    
    async syncData(backendId, entityType, direction, externalId = null, recordId = null) {
        const url = `${this.baseUrl}/sync`;
        const data = {
            backend_id: backendId,
            entity_type: entityType,
            direction: direction
        };
        
        if (externalId) data.external_id = externalId;
        if (recordId) data.record_id = recordId;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
    
    async getStatus() {
        const url = `${this.baseUrl}/status`;
        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });
        
        return await response.json();
    }
    
    async getLogs(limit = 100, status = null, dateFrom = null, dateTo = null) {
        const url = `${this.baseUrl}/logs`;
        const params = new URLSearchParams({ limit });
        
        if (status) params.append('status', status);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        
        const response = await fetch(`${url}?${params}`, {
            method: 'GET',
            headers: this.headers
        });
        
        return await response.json();
    }
}

// Usage
const client = new SapIntegrationClient(
    'https://your-odoo-instance.com/sap_integration/api/v1',
    'your_api_key_here'
);

// Sync partner data
client.syncData(1, 'partner', 'sap_to_odoo', 'CUSTOMER001')
    .then(result => console.log('Sync result:', result.status))
    .catch(error => console.error('Error:', error));

// Get system status
client.getStatus()
    .then(status => console.log('System status:', status.sync_status_overview))
    .catch(error => console.error('Error:', error));
```

### cURL Examples

#### Sync Data

```bash
curl -X POST "https://your-odoo-instance.com/sap_integration/api/v1/sync" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "backend_id": 1,
    "entity_type": "partner",
    "direction": "sap_to_odoo",
    "external_id": "CUSTOMER001"
  }'
```

#### Get Status

```bash
curl -X GET "https://your-odoo-instance.com/sap_integration/api/v1/status" \
  -H "X-API-Key: your_api_key_here" \
  -H "Accept: application/json"
```

#### Get Logs

```bash
curl -X GET "https://your-odoo-instance.com/sap_integration/api/v1/logs?limit=10&status=success" \
  -H "X-API-Key: your_api_key_here" \
  -H "Accept: application/json"
```

This API reference provides comprehensive documentation for integrating with the SAP Integration module's REST API, including authentication, endpoints, data models, error handling, rate limiting, webhooks, and practical examples.
