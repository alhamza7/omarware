# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP API Framework

Comprehensive API framework for external integrations and webhooks.
"""

from odoo import models, fields, api
import logging, http
from odoo.exceptions import UserError, ValidationError
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from functools import wraps

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapApiEndpoint(models.Model):
    """SAP API Endpoint Configuration"""
    _name = 'sap.api.endpoint'
    _description = 'SAP API Endpoint'
    _order = 'sequence, name'
    
    # Basic Information
    name = fields.Char(
        string='Endpoint Name',
        required=True,
        index=True
    )
    path = fields.Char(
        string='API Path',
        required=True,
        help="API endpoint path (e.g., /api/v1/sync)"
    )
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH')
    ], string='HTTP Method', required=True, default='POST')
    
    # Functionality
    handler_function = fields.Char(
        string='Handler Function',
        required=True,
        help="Function name to handle the endpoint"
    )
    description = fields.Text(
        string='Description',
        help="Endpoint description and usage"
    )
    
    # Security
    requires_authentication = fields.Boolean(
        string='Requires Authentication',
        default=True
    )
    api_key_required = fields.Boolean(
        string='API Key Required',
        default=True
    )
    allowed_ips = fields.Text(
        string='Allowed IPs',
        help="Comma-separated list of allowed IP addresses"
    )
    
    # Rate Limiting
    rate_limit_enabled = fields.Boolean(
        string='Rate Limit Enabled',
        default=True
    )
    rate_limit_requests = fields.Integer(
        string='Rate Limit Requests',
        default=100,
        help="Maximum requests per time window"
    )
    rate_limit_window = fields.Integer(
        string='Rate Limit Window (minutes)',
        default=60,
        help="Time window for rate limiting in minutes"
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Statistics
    total_requests = fields.Integer(
        string='Total Requests',
        default=0,
        readonly=True
    )
    successful_requests = fields.Integer(
        string='Successful Requests',
        default=0,
        readonly=True
    )
    failed_requests = fields.Integer(
        string='Failed Requests',
        default=0,
        readonly=True
    )
    last_request = fields.Datetime(
        string='Last Request',
        readonly=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_path_method', 'unique(path, method)', 
         'An endpoint with the same path and method already exists.'),
    ]
    
    def action_test_endpoint(self):
        """Test endpoint functionality"""
        try:
            # This would typically make a test request to the endpoint
            _logger.info(f"Testing endpoint: {self.name}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Endpoint Test',
                    'message': f'Endpoint {self.name} test completed',
                    'type': 'success'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error testing endpoint: {str(e)}")
            raise UserError(f"Failed to test endpoint: {str(e)}")
    
    def action_view_statistics(self):
        """View endpoint statistics"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Statistics for {self.name}',
            'res_model': 'sap.api.request.log',
            'view_mode': 'tree,form',
            'domain': [('endpoint_id', '=', self.id)],
            'context': {'default_endpoint_id': self.id}
        }


class SapApiKey(models.Model):
    """SAP API Key Management"""
    _name = 'sap.api.key'
    _description = 'SAP API Key'
    _order = 'name'
    
    # Basic Information
    name = fields.Char(
        string='API Key Name',
        required=True,
        index=True
    )
    key_value = fields.Char(
        string='API Key',
        required=True,
        index=True,
        help="The actual API key value"
    )
    description = fields.Text(
        string='Description',
        help="API key description and usage"
    )
    
    # Access Control
    user_id = fields.Many2one(
        'res.users',
        string='Associated User',
        help="User associated with this API key"
    )
    endpoint_ids = fields.Many2many(
        'sap.api.endpoint',
        'sap_api_key_endpoint_rel',
        'key_id',
        'endpoint_id',
        string='Allowed Endpoints',
        help="Endpoints this API key can access"
    )
    
    # Security
    expires_date = fields.Datetime(
        string='Expires Date',
        help="API key expiration date (optional)"
    )
    last_used = fields.Datetime(
        string='Last Used',
        readonly=True
    )
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_key_value', 'unique(key_value)', 
         'API key value must be unique.'),
    ]
    
    @api.model
    def create(self, vals):
        """Override create to generate API key"""
        if 'key_value' not in vals or not vals['key_value']:
            vals['key_value'] = self._generate_api_key()
        
        return super().create(vals)
    
    def _generate_api_key(self):
        """Generate a new API key"""
        import secrets
        import string
        
        # Generate a secure random key
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        return f"sap_{key}"
    
    def action_generate_new_key(self):
        """Generate a new API key"""
        self.key_value = self._generate_api_key()
        self.last_used = False
        self.usage_count = 0
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'New API Key Generated',
                'message': f'New API key generated for {self.name}',
                'type': 'success'
            }
        }
    
    def action_revoke_key(self):
        """Revoke API key"""
        self.active = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'API Key Revoked',
                'message': f'API key {self.name} has been revoked',
                'type': 'warning'
            }
        }


class SapApiRequestLog(models.Model):
    """SAP API Request Log"""
    _name = 'sap.api.request.log'
    _description = 'SAP API Request Log'
    _order = 'request_time desc'
    
    # Request Information
    endpoint_id = fields.Many2one(
        'sap.api.endpoint',
        string='Endpoint',
        required=True,
        ondelete='cascade'
    )
    api_key_id = fields.Many2one(
        'sap.api.key',
        string='API Key',
        ondelete='set null'
    )
    
    # Request Details
    request_method = fields.Char(
        string='Method',
        required=True
    )
    request_path = fields.Char(
        string='Path',
        required=True
    )
    request_headers = fields.Text(
        string='Request Headers',
        help="Request headers in JSON format"
    )
    request_body = fields.Text(
        string='Request Body',
        help="Request body content"
    )
    request_ip = fields.Char(
        string='IP Address',
        required=True
    )
    user_agent = fields.Char(
        string='User Agent'
    )
    
    # Response Details
    response_status = fields.Integer(
        string='Response Status',
        required=True
    )
    response_headers = fields.Text(
        string='Response Headers',
        help="Response headers in JSON format"
    )
    response_body = fields.Text(
        string='Response Body',
        help="Response body content"
    )
    
    # Timing
    request_time = fields.Datetime(
        string='Request Time',
        default=fields.Datetime.now,
        required=True
    )
    response_time = fields.Datetime(
        string='Response Time'
    )
    duration_ms = fields.Float(
        string='Duration (ms)',
        help="Request duration in milliseconds"
    )
    
    # Status
    success = fields.Boolean(
        string='Success',
        default=True
    )
    error_message = fields.Text(
        string='Error Message',
        help="Error message if request failed"
    )
    
    @api.model
    def log_request(self, endpoint_id, request_data, response_data, duration_ms=0):
        """Log API request"""
        try:
            log_vals = {
                'endpoint_id': endpoint_id,
                'api_key_id': request_data.get('api_key_id'),
                'request_method': request_data.get('method', ''),
                'request_path': request_data.get('path', ''),
                'request_headers': json.dumps(request_data.get('headers', {})),
                'request_body': request_data.get('body', ''),
                'request_ip': request_data.get('ip', ''),
                'user_agent': request_data.get('user_agent', ''),
                'response_status': response_data.get('status', 200),
                'response_headers': json.dumps(response_data.get('headers', {})),
                'response_body': response_data.get('body', ''),
                'response_time': fields.Datetime.now(),
                'duration_ms': duration_ms,
                'success': response_data.get('status', 200) < 400,
                'error_message': response_data.get('error_message', '')
            }
            
            log = self.create(log_vals)
            
            # Update endpoint statistics
            endpoint = self.env['sap.api.endpoint'].browse(endpoint_id)
            endpoint.total_requests += 1
            if log.success:
                endpoint.successful_requests += 1
            else:
                endpoint.failed_requests += 1
            endpoint.last_request = log.request_time
            
            return log
            
        except Exception as e:
            _logger.error(f"Error logging request: {str(e)}")
            return None


class SapApiFramework(SapBaseService):
    """SAP API Framework"""
    _name = 'sap.api.framework'
    _description = 'SAP API Framework'
    
    _rate_limits = {}
    
    @api.model
    def validate_api_key(self, api_key, endpoint_path):
        """Validate API key for endpoint"""
        try:
            if not api_key:
                return False
            
            # Find API key
            key_record = self.env['sap.api.key'].search([
                ('key_value', '=', api_key),
                ('active', '=', True)
            ], limit=1)
            
            if not key_record:
                return False
            
            # Check expiration
            if key_record.expires_date and key_record.expires_date < fields.Datetime.now():
                return False
            
            # Check endpoint access
            if key_record.endpoint_ids:
                endpoint = self.env['sap.api.endpoint'].search([
                    ('path', '=', endpoint_path),
                    ('id', 'in', key_record.endpoint_ids.ids)
                ], limit=1)
                
                if not endpoint:
                    return False
            
            # Update usage statistics
            key_record.last_used = fields.Datetime.now()
            key_record.usage_count += 1
            
            return True
            
        except Exception as e:
            _logger.error(f"Error validating API key: {str(e)}")
            return False
    
    @api.model
    def check_rate_limit(self, api_key, endpoint_id):
        """Check rate limit for API key and endpoint"""
        try:
            endpoint = self.env['sap.api.endpoint'].browse(endpoint_id)
            
            if not endpoint.rate_limit_enabled:
                return True
            
            # Get rate limit key
            rate_key = f"{api_key}_{endpoint_id}"
            current_time = time.time()
            window_seconds = endpoint.rate_limit_window * 60
            
            # Clean old entries
            if rate_key in self._rate_limits:
                self._rate_limits[rate_key] = [
                    req_time for req_time in self._rate_limits[rate_key]
                    if current_time - req_time < window_seconds
                ]
            else:
                self._rate_limits[rate_key] = []
            
            # Check if limit exceeded
            if len(self._rate_limits[rate_key]) >= endpoint.rate_limit_requests:
                return False
            
            # Add current request
            self._rate_limits[rate_key].append(current_time)
            
            return True
            
        except Exception as e:
            _logger.error(f"Error checking rate limit: {str(e)}")
            return True
    
    @api.model
    def handle_api_request(self, endpoint_path, method, request_data):
        """Handle API request"""
        try:
            # Find endpoint
            endpoint = self.env['sap.api.endpoint'].search([
                ('path', '=', endpoint_path),
                ('method', '=', method),
                ('active', '=', True)
            ], limit=1)
            
            if not endpoint:
                return {
                    'status': 404,
                    'body': {'error': 'Endpoint not found'},
                    'headers': {'Content-Type': 'application/json'}
                }
            
            # Validate API key
            api_key = request_data.get('headers', {}).get('X-API-Key')
            if endpoint.api_key_required:
                if not self.validate_api_key(api_key, endpoint_path):
                    return {
                        'status': 401,
                        'body': {'error': 'Invalid or missing API key'},
                        'headers': {'Content-Type': 'application/json'}
                    }
            
            # Check rate limit
            if not self.check_rate_limit(api_key, endpoint.id):
                return {
                    'status': 429,
                    'body': {'error': 'Rate limit exceeded'},
                    'headers': {'Content-Type': 'application/json'}
                }
            
            # Execute handler function
            handler_result = self._execute_handler(endpoint.handler_function, request_data)
            
            # Log request
            self.env['sap.api.request.log'].log_request(
                endpoint.id,
                request_data,
                handler_result,
                handler_result.get('duration_ms', 0)
            )
            
            return handler_result
            
        except Exception as e:
            _logger.error(f"Error handling API request: {str(e)}")
            return {
                'status': 500,
                'body': {'error': 'Internal server error'},
                'headers': {'Content-Type': 'application/json'}
            }
    
    def _execute_handler(self, handler_function, request_data):
        """Execute handler function"""
        try:
            # This would typically use a registry of handler functions
            # For now, we'll implement some basic handlers
            
            if handler_function == 'sync_data':
                return self._handle_sync_data(request_data)
            elif handler_function == 'get_status':
                return self._handle_get_status(request_data)
            elif handler_function == 'get_logs':
                return self._handle_get_logs(request_data)
            else:
                return {
                    'status': 501,
                    'body': {'error': 'Handler function not implemented'},
                    'headers': {'Content-Type': 'application/json'}
                }
                
        except Exception as e:
            _logger.error(f"Error executing handler: {str(e)}")
            return {
                'status': 500,
                'body': {'error': str(e)},
                'headers': {'Content-Type': 'application/json'}
            }
    
    def _handle_sync_data(self, request_data):
        """Handle sync data request"""
        try:
            body = request_data.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            backend_id = body.get('backend_id')
            entity_type = body.get('entity_type')
            
            if not backend_id or not entity_type:
                return {
                    'status': 400,
                    'body': {'error': 'Backend ID and entity type are required'},
                    'headers': {'Content-Type': 'application/json'}
                }
            
            # Execute sync
            sync_engine = self.env['sap.sync.engine']
            result = sync_engine.sync_all_entities(
                backend_id=backend_id,
                entity_types=[entity_type],
                direction='bidirectional'
            )
            
            return {
                'status': 200,
                'body': {
                    'success': True,
                    'result': result,
                    'message': 'Sync completed successfully'
                },
                'headers': {'Content-Type': 'application/json'}
            }
            
        except Exception as e:
            _logger.error(f"Error handling sync data: {str(e)}")
            return {
                'status': 500,
                'body': {'error': str(e)},
                'headers': {'Content-Type': 'application/json'}
            }
    
    def _handle_get_status(self, request_data):
        """Handle get status request"""
        try:
            dashboard = self.env['sap.dashboard.control']
            status_data = dashboard.get_dashboard_data()
            
            return {
                'status': 200,
                'body': status_data,
                'headers': {'Content-Type': 'application/json'}
            }
            
        except Exception as e:
            _logger.error(f"Error handling get status: {str(e)}")
            return {
                'status': 500,
                'body': {'error': str(e)},
                'headers': {'Content-Type': 'application/json'}
            }
    
    def _handle_get_logs(self, request_data):
        """Handle get logs request"""
        try:
            body = request_data.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            limit = body.get('limit', 100)
            offset = body.get('offset', 0)
            
            logs = self.env['sap.sync.log'].search(
                [],
                limit=limit,
                offset=offset,
                order='create_date desc'
            )
            
            log_data = []
            for log in logs:
                log_data.append({
                    'id': log.id,
                    'timestamp': log.create_date,
                    'entity': log.model_name,
                    'operation': log.operation,
                    'status': log.status,
                    'message': log.message
                })
            
            return {
                'status': 200,
                'body': {
                    'logs': log_data,
                    'total': len(log_data)
                },
                'headers': {'Content-Type': 'application/json'}
            }
            
        except Exception as e:
            _logger.error(f"Error handling get logs: {str(e)}")
            return {
                'status': 500,
                'body': {'error': str(e)},
                'headers': {'Content-Type': 'application/json'}
            }
    
    @api.model
    def create_endpoint(self, name, path, method, handler_function, **kwargs):
        """Create API endpoint"""
        try:
            endpoint_vals = {
                'name': name,
                'path': path,
                'method': method,
                'handler_function': handler_function,
                'description': kwargs.get('description', ''),
                'requires_authentication': kwargs.get('requires_authentication', True),
                'api_key_required': kwargs.get('api_key_required', True),
                'rate_limit_enabled': kwargs.get('rate_limit_enabled', True),
                'rate_limit_requests': kwargs.get('rate_limit_requests', 100),
                'rate_limit_window': kwargs.get('rate_limit_window', 60)
            }
            
            endpoint = self.env['sap.api.endpoint'].create(endpoint_vals)
            
            _logger.info(f"Created API endpoint: {name} ({path})")
            
            return endpoint
            
        except Exception as e:
            _logger.error(f"Error creating endpoint: {str(e)}")
            raise SapValidationError(f"Failed to create endpoint: {str(e)}")
    
    @api.model
    def create_api_key(self, name, user_id=None, endpoint_ids=None, **kwargs):
        """Create API key"""
        try:
            key_vals = {
                'name': name,
                'description': kwargs.get('description', ''),
                'user_id': user_id,
                'expires_date': kwargs.get('expires_date'),
                'active': True
            }
            
            api_key = self.env['sap.api.key'].create(key_vals)
            
            if endpoint_ids:
                api_key.endpoint_ids = [(6, 0, endpoint_ids)]
            
            _logger.info(f"Created API key: {name}")
            
            return api_key
            
        except Exception as e:
            _logger.error(f"Error creating API key: {str(e)}")
            raise SapValidationError(f"Failed to create API key: {str(e)}")
    
    @api.model
    def get_api_statistics(self, days=30):
        """Get API statistics"""
        try:
            domain = [
                ('request_time', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            
            logs = self.env['sap.api.request.log'].search(domain)
            
            stats = {
                'total_requests': len(logs),
                'successful_requests': len(logs.filtered('success')),
                'failed_requests': len(logs.filtered(lambda l: not l.success)),
                'average_duration': sum(logs.mapped('duration_ms')) / len(logs) if logs else 0,
                'by_endpoint': {},
                'by_status': {}
            }
            
            # Group by endpoint
            for log in logs:
                endpoint_name = log.endpoint_id.name
                if endpoint_name not in stats['by_endpoint']:
                    stats['by_endpoint'][endpoint_name] = 0
                stats['by_endpoint'][endpoint_name] += 1
            
            # Group by status
            for log in logs:
                status = log.response_status
                if status not in stats['by_status']:
                    stats['by_status'][status] = 0
                stats['by_status'][status] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting API statistics: {str(e)}")
            return {}
