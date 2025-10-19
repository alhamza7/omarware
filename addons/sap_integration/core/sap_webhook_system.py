# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Webhook System

Webhook system for real-time event notifications and external integrations.
"""

from odoo import models, fields, api
import logging, http
from odoo.exceptions import UserError, ValidationError
import json
import hashlib
import hmac
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapWebhookEndpoint(models.Model):
    """SAP Webhook Endpoint Configuration"""
    _name = 'sap.webhook.endpoint'
    _description = 'SAP Webhook Endpoint'
    _order = 'sequence, name'
    
    # Basic Information
    name = fields.Char(
        string='Webhook Name',
        required=True,
        index=True
    )
    url = fields.Char(
        string='Webhook URL',
        required=True,
        help="Target URL for webhook notifications"
    )
    description = fields.Text(
        string='Description',
        help="Webhook description and purpose"
    )
    
    # Event Configuration
    event_types = fields.Selection([
        ('sync_start', 'Sync Start'),
        ('sync_complete', 'Sync Complete'),
        ('sync_error', 'Sync Error'),
        ('data_created', 'Data Created'),
        ('data_updated', 'Data Updated'),
        ('data_deleted', 'Data Deleted'),
        ('alert_triggered', 'Alert Triggered'),
        ('system_error', 'System Error'),
        ('custom', 'Custom Event')
    ], string='Event Types', required=True, multiple=True)
    
    custom_event_types = fields.Text(
        string='Custom Event Types',
        help="Comma-separated list of custom event types"
    )
    
    # Security
    secret_key = fields.Char(
        string='Secret Key',
        help="Secret key for webhook signature validation"
    )
    requires_authentication = fields.Boolean(
        string='Requires Authentication',
        default=True
    )
    auth_token = fields.Char(
        string='Auth Token',
        help="Authentication token for webhook requests"
    )
    
    # Configuration
    http_method = fields.Selection([
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH')
    ], string='HTTP Method', default='POST', required=True)
    
    headers = fields.Text(
        string='Custom Headers',
        help="Custom headers in JSON format"
    )
    
    timeout = fields.Integer(
        string='Timeout (seconds)',
        default=30,
        help="Request timeout in seconds"
    )
    
    retry_attempts = fields.Integer(
        string='Retry Attempts',
        default=3,
        help="Number of retry attempts for failed requests"
    )
    
    retry_delay = fields.Integer(
        string='Retry Delay (seconds)',
        default=5,
        help="Delay between retry attempts in seconds"
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
    last_success = fields.Datetime(
        string='Last Success',
        readonly=True
    )
    last_failure = fields.Datetime(
        string='Last Failure',
        readonly=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_url', 'unique(url)', 
         'Webhook URL must be unique.'),
    ]
    
    def action_test_webhook(self):
        """Test webhook endpoint"""
        try:
            webhook_system = self.env['sap.webhook.system']
            result = webhook_system.send_webhook(
                webhook_id=self.id,
                event_type='test',
                data={'test': True, 'message': 'Test webhook request'}
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Webhook Test',
                    'message': f'Webhook test completed: {result.get("status", "unknown")}',
                    'type': 'success' if result.get('success') else 'warning'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error testing webhook: {str(e)}")
            raise UserError(f"Failed to test webhook: {str(e)}")
    
    def action_view_logs(self):
        """View webhook logs"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Logs for {self.name}',
            'res_model': 'sap.webhook.log',
            'view_mode': 'tree,form',
            'domain': [('webhook_id', '=', self.id)],
            'context': {'default_webhook_id': self.id}
        }


class SapWebhookLog(models.Model):
    """SAP Webhook Log"""
    _name = 'sap.webhook.log'
    _description = 'SAP Webhook Log'
    _order = 'request_time desc'
    
    # Webhook Information
    webhook_id = fields.Many2one(
        'sap.webhook.endpoint',
        string='Webhook',
        required=True,
        ondelete='cascade'
    )
    
    # Event Information
    event_type = fields.Char(
        string='Event Type',
        required=True
    )
    event_data = fields.Text(
        string='Event Data',
        help="Event data in JSON format"
    )
    
    # Request Information
    request_url = fields.Char(
        string='Request URL',
        required=True
    )
    request_method = fields.Char(
        string='Request Method',
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
    
    # Response Information
    response_status = fields.Integer(
        string='Response Status',
        help="HTTP response status code"
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
        default=False
    )
    error_message = fields.Text(
        string='Error Message',
        help="Error message if request failed"
    )
    
    # Retry Information
    retry_count = fields.Integer(
        string='Retry Count',
        default=0
    )
    max_retries = fields.Integer(
        string='Max Retries',
        default=3
    )
    
    @api.model
    def log_webhook_request(self, webhook_id, event_type, event_data, 
                           request_data, response_data, success=True, 
                           error_message='', duration_ms=0, retry_count=0):
        """Log webhook request"""
        try:
            log_vals = {
                'webhook_id': webhook_id,
                'event_type': event_type,
                'event_data': json.dumps(event_data) if event_data else '',
                'request_url': request_data.get('url', ''),
                'request_method': request_data.get('method', 'POST'),
                'request_headers': json.dumps(request_data.get('headers', {})),
                'request_body': request_data.get('body', ''),
                'response_status': response_data.get('status', 0),
                'response_headers': json.dumps(response_data.get('headers', {})),
                'response_body': response_data.get('body', ''),
                'response_time': fields.Datetime.now(),
                'duration_ms': duration_ms,
                'success': success,
                'error_message': error_message,
                'retry_count': retry_count
            }
            
            log = self.create(log_vals)
            
            # Update webhook statistics
            webhook = self.env['sap.webhook.endpoint'].browse(webhook_id)
            webhook.total_requests += 1
            if success:
                webhook.successful_requests += 1
                webhook.last_success = log.request_time
            else:
                webhook.failed_requests += 1
                webhook.last_failure = log.request_time
            webhook.last_request = log.request_time
            
            return log
            
        except Exception as e:
            _logger.error(f"Error logging webhook request: {str(e)}")
            return None


class SapWebhookSystem(SapBaseService):
    """SAP Webhook System"""
    _name = 'sap.webhook.system'
    _description = 'SAP Webhook System'
    
    @api.model
    def send_webhook(self, webhook_id, event_type, data, context=None):
        """Send webhook notification"""
        try:
            webhook = self.env['sap.webhook.endpoint'].browse(webhook_id)
            if not webhook.exists() or not webhook.active:
                raise SapValidationError(f"Webhook {webhook_id} not found or inactive")
            
            # Check if event type is supported
            if not self._is_event_type_supported(webhook, event_type):
                _logger.info(f"Event type {event_type} not supported for webhook {webhook.name}")
                return {'success': False, 'message': 'Event type not supported'}
            
            # Prepare request data
            request_data = self._prepare_request_data(webhook, event_type, data)
            
            # Send webhook
            start_time = time.time()
            response = self._send_webhook_request(webhook, request_data)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request
            self.env['sap.webhook.log'].log_webhook_request(
                webhook_id=webhook_id,
                event_type=event_type,
                event_data=data,
                request_data=request_data,
                response_data=response,
                success=response.get('success', False),
                error_message=response.get('error_message', ''),
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            _logger.error(f"Error sending webhook: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def _is_event_type_supported(self, webhook, event_type):
        """Check if event type is supported by webhook"""
        try:
            if event_type in webhook.event_types:
                return True
            
            if 'custom' in webhook.event_types and webhook.custom_event_types:
                custom_types = [t.strip() for t in webhook.custom_event_types.split(',')]
                return event_type in custom_types
            
            return False
            
        except Exception as e:
            _logger.error(f"Error checking event type support: {str(e)}")
            return False
    
    def _prepare_request_data(self, webhook, event_type, data):
        """Prepare request data for webhook"""
        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SAP-Integration-Webhook/1.0',
                'X-Event-Type': event_type,
                'X-Timestamp': str(int(time.time()))
            }
            
            # Add custom headers
            if webhook.headers:
                try:
                    custom_headers = json.loads(webhook.headers)
                    headers.update(custom_headers)
                except json.JSONDecodeError:
                    _logger.warning(f"Invalid custom headers for webhook {webhook.name}")
            
            # Add authentication
            if webhook.requires_authentication and webhook.auth_token:
                headers['Authorization'] = f'Bearer {webhook.auth_token}'
            
            # Add signature if secret key is provided
            if webhook.secret_key:
                signature = self._generate_signature(webhook.secret_key, data)
                headers['X-Signature'] = signature
            
            # Prepare body
            body = {
                'event_type': event_type,
                'timestamp': fields.Datetime.now().isoformat(),
                'data': data
            }
            
            return {
                'url': webhook.url,
                'method': webhook.http_method,
                'headers': headers,
                'body': json.dumps(body)
            }
            
        except Exception as e:
            _logger.error(f"Error preparing request data: {str(e)}")
            raise SapValidationError(f"Failed to prepare request data: {str(e)}")
    
    def _generate_signature(self, secret_key, data):
        """Generate webhook signature"""
        try:
            message = json.dumps(data, sort_keys=True)
            signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return f"sha256={signature}"
            
        except Exception as e:
            _logger.error(f"Error generating signature: {str(e)}")
            return ""
    
    def _send_webhook_request(self, webhook, request_data):
        """Send webhook request"""
        try:
            response = requests.request(
                method=request_data['method'],
                url=request_data['url'],
                headers=request_data['headers'],
                data=request_data['body'],
                timeout=webhook.timeout
            )
            
            return {
                'success': response.status_code < 400,
                'status': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'error_message': '' if response.status_code < 400 else f'HTTP {response.status_code}'
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status': 408,
                'headers': {},
                'body': '',
                'error_message': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'status': 0,
                'headers': {},
                'body': '',
                'error_message': 'Connection error'
            }
        except Exception as e:
            return {
                'success': False,
                'status': 0,
                'headers': {},
                'body': '',
                'error_message': str(e)
            }
    
    @api.model
    def send_event_webhooks(self, event_type, data, context=None):
        """Send webhooks for specific event type"""
        try:
            # Find all active webhooks for this event type
            webhooks = self.env['sap.webhook.endpoint'].search([
                ('active', '=', True)
            ])
            
            results = []
            for webhook in webhooks:
                if self._is_event_type_supported(webhook, event_type):
                    result = self.send_webhook(webhook.id, event_type, data, context)
                    results.append({
                        'webhook_id': webhook.id,
                        'webhook_name': webhook.name,
                        'result': result
                    })
            
            _logger.info(f"Sent {len(results)} webhooks for event {event_type}")
            
            return {
                'success': True,
                'event_type': event_type,
                'webhooks_sent': len(results),
                'results': results
            }
            
        except Exception as e:
            _logger.error(f"Error sending event webhooks: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    @api.model
    def retry_failed_webhooks(self, webhook_id=None, hours_back=24):
        """Retry failed webhook requests"""
        try:
            domain = [
                ('success', '=', False),
                ('request_time', '>=', fields.Datetime.now() - timedelta(hours=hours_back))
            ]
            
            if webhook_id:
                domain.append(('webhook_id', '=', webhook_id))
            
            failed_logs = self.env['sap.webhook.log'].search(domain)
            
            retry_count = 0
            for log in failed_logs:
                if log.retry_count < log.max_retries:
                    try:
                        # Retry webhook
                        webhook = log.webhook_id
                        event_data = json.loads(log.event_data) if log.event_data else {}
                        
                        result = self.send_webhook(
                            webhook.id,
                            log.event_type,
                            event_data
                        )
                        
                        if result.get('success'):
                            retry_count += 1
                            log.write({'success': True, 'retry_count': log.retry_count + 1})
                        
                    except Exception as e:
                        _logger.error(f"Error retrying webhook {log.id}: {str(e)}")
                        continue
            
            _logger.info(f"Retried {retry_count} failed webhooks")
            
            return {
                'success': True,
                'retry_count': retry_count,
                'message': f'Retried {retry_count} failed webhooks'
            }
            
        except Exception as e:
            _logger.error(f"Error retrying failed webhooks: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    @api.model
    def get_webhook_statistics(self, webhook_id=None, days=30):
        """Get webhook statistics"""
        try:
            domain = [
                ('request_time', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            
            if webhook_id:
                domain.append(('webhook_id', '=', webhook_id))
            
            logs = self.env['sap.webhook.log'].search(domain)
            
            stats = {
                'total_requests': len(logs),
                'successful_requests': len(logs.filtered('success')),
                'failed_requests': len(logs.filtered(lambda l: not l.success)),
                'success_rate': 0,
                'average_duration': 0,
                'by_event_type': {},
                'by_webhook': {}
            }
            
            if logs:
                stats['success_rate'] = (len(logs.filtered('success')) / len(logs)) * 100
                stats['average_duration'] = sum(logs.mapped('duration_ms')) / len(logs)
            
            # Group by event type
            for log in logs:
                event_type = log.event_type
                if event_type not in stats['by_event_type']:
                    stats['by_event_type'][event_type] = 0
                stats['by_event_type'][event_type] += 1
            
            # Group by webhook
            for log in logs:
                webhook_name = log.webhook_id.name
                if webhook_name not in stats['by_webhook']:
                    stats['by_webhook'][webhook_name] = 0
                stats['by_webhook'][webhook_name] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting webhook statistics: {str(e)}")
            return {}
    
    @api.model
    def create_webhook(self, name, url, event_types, **kwargs):
        """Create webhook endpoint"""
        try:
            webhook_vals = {
                'name': name,
                'url': url,
                'event_types': event_types,
                'description': kwargs.get('description', ''),
                'secret_key': kwargs.get('secret_key'),
                'requires_authentication': kwargs.get('requires_authentication', True),
                'auth_token': kwargs.get('auth_token'),
                'http_method': kwargs.get('http_method', 'POST'),
                'headers': kwargs.get('headers'),
                'timeout': kwargs.get('timeout', 30),
                'retry_attempts': kwargs.get('retry_attempts', 3),
                'retry_delay': kwargs.get('retry_delay', 5),
                'active': True
            }
            
            webhook = self.env['sap.webhook.endpoint'].create(webhook_vals)
            
            _logger.info(f"Created webhook: {name} ({url})")
            
            return webhook
            
        except Exception as e:
            _logger.error(f"Error creating webhook: {str(e)}")
            raise SapValidationError(f"Failed to create webhook: {str(e)}")
    
    @api.model
    def validate_webhook_url(self, url):
        """Validate webhook URL"""
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme or not parsed.netloc:
                return False
            
            if parsed.scheme not in ['http', 'https']:
                return False
            
            return True
            
        except Exception as e:
            _logger.error(f"Error validating webhook URL: {str(e)}")
            return False
