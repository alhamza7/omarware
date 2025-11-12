# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class UltramsgConfig(models.Model):
    """ULTRAMSG API Configuration"""
    _name = 'ultramsg.config'
    _description = 'ULTRAMSG API Configuration'
    
    name = fields.Char(string='Configuration Name', required=True, default='ULTRAMSG')
    active = fields.Boolean(string='Active', default=True)
    
    # API Credentials
    instance_id = fields.Char(
        string='Instance ID', 
        required=True, 
        help='Your ULTRAMSG Instance ID (e.g., instance12345)'
    )
    api_token = fields.Char(
        string='API Token', 
        required=True, 
        help='Your ULTRAMSG API Token'
    )
    api_url = fields.Char(
        string='API URL', 
        default='https://api.ultramsg.com',
        required=True,
        help='ULTRAMSG API Base URL'
    )
    
    # Settings
    phone_prefix = fields.Char(
        string='Phone Prefix',
        default='964',
        help='Country code prefix (964 for Iraq). Will replace leading 0 from phone numbers.'
    )
    
    # Statistics
    total_messages_sent = fields.Integer(
        string='Total Messages Sent', 
        compute='_compute_statistics', 
        store=False
    )
    total_messages_failed = fields.Integer(
        string='Total Messages Failed', 
        compute='_compute_statistics', 
        store=False
    )
    last_message_date = fields.Datetime(
        string='Last Message Date',
        compute='_compute_statistics',
        store=False
    )
    
    @api.depends('active')
    def _compute_statistics(self):
        """Compute message statistics"""
        for record in self:
            messages = self.env['ultramsg.message'].search([])
            sent_messages = messages.filtered(lambda m: m.state == 'sent')
            record.total_messages_sent = len(sent_messages)
            record.total_messages_failed = len(messages.filtered(lambda m: m.state == 'failed'))
            
            if sent_messages:
                record.last_message_date = max(sent_messages.mapped('sent_date'))
            else:
                record.last_message_date = False
    
    def format_phone_number(self, phone):
        """
        Format phone number for WhatsApp (same as PowerShell method)
        Input: 07800114976 or +9647800114976
        Output: +9647800114976 (with + prefix as used in successful PowerShell test)
        """
        if not phone:
            return None
        
        # Remove spaces but keep + if present
        phone = phone.strip().replace(' ', '')
        
        # If already starts with +, keep it
        if phone.startswith('+'):
            return phone
        
        # Remove all non-digit characters (except +)
        phone_clean = ''.join(filter(lambda c: c.isdigit() or c == '+', phone))
        
        # If starts with 0, replace with country code and add +
        if phone_clean.startswith('0'):
            phone_clean = '+' + self.phone_prefix + phone_clean[1:]
        # If doesn't start with country code, add + and country code
        elif not phone_clean.startswith(self.phone_prefix):
            phone_clean = '+' + self.phone_prefix + phone_clean
        else:
            # Already has country code, just add +
            phone_clean = '+' + phone_clean
        
        return phone_clean
    
    def send_message(self, phone, message_type='text', message_body='', document_url='', document_name=''):
        """
        Send message via ULTRAMSG API
        """
        self.ensure_one()
        
        import requests
        
        try:
            # Clean instance_id and token (remove spaces and special characters)
            instance_id = (self.instance_id or '').strip()
            api_token = (self.api_token or '').strip()
            api_url = (self.api_url or '').strip()
            
            # Format phone number
            formatted_phone = self.format_phone_number(phone)
            if not formatted_phone:
                return {'success': False, 'error': 'Invalid phone number'}
            
            _logger.info(f"[ULTRAMSG] Sending {message_type} message to {formatted_phone}")
            _logger.info(f"[ULTRAMSG] Instance ID: '{instance_id}' (length: {len(instance_id)})")
            _logger.info(f"[ULTRAMSG] API Token: '{api_token[:10]}...' (length: {len(api_token)})")
            _logger.info(f"[ULTRAMSG] API URL: '{api_url}'")
            
            # Prepare API endpoint and data
            # Note: ULTRAMSG API requires 'instance' prefix before instance_id
            if message_type == 'document':
                url = f"{api_url}/instance{instance_id}/messages/document"
                data = {
                    'token': api_token,
                    'to': formatted_phone,
                    'document': document_url,
                    'caption': message_body or '',
                    'filename': document_name or 'document.pdf',
                }
            elif message_type == 'image':
                url = f"{api_url}/instance{instance_id}/messages/image"
                data = {
                    'token': api_token,
                    'to': formatted_phone,
                    'image': document_url,
                    'caption': message_body or '',
                }
            else:  # text
                url = f"{api_url}/instance{instance_id}/messages/chat"
                data = {
                    'token': api_token,
                    'to': formatted_phone,
                    'body': message_body,
                }
            
            _logger.info(f"[ULTRAMSG] API URL: {url}")
            _logger.info(f"[ULTRAMSG] Data: {data}")
            
            # Send request - use same method as PowerShell (application/x-www-form-urlencoded)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.post(url, data=data, headers=headers, timeout=30)
            response_data = response.json()
            
            _logger.info(f"[ULTRAMSG] API Response: {response_data}")
            
            # Check if successful
            if response.status_code == 200 and response_data.get('sent') == 'true':
                return {
                    'success': True,
                    'ultramsg_id': response_data.get('id'),
                    'response': response_data,
                }
            else:
                error_msg = response_data.get('error') or response_data.get('message') or 'Unknown error'
                return {
                    'success': False,
                    'error': error_msg,
                    'response': response_data,
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout - ULTRAMSG API did not respond'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            _logger.error(f"[ULTRAMSG] Error in send_message: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def action_test_connection(self):
        """Test ULTRAMSG connection"""
        self.ensure_one()
        
        # Send test message to yourself (admin number)
        test_phone = '07800000000'  # Replace with actual test number
        
        result = self.send_message(
            phone=test_phone,
            message_type='text',
            message_body='Test message from Odoo ULTRAMSG Integration'
        )
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'ULTRAMSG connection successful!',
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Connection failed: {result.get("error")}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    @api.model
    def action_test_send_message_direct(self, phone, message_type='text', message_body='', document_url='', document_name=''):
        """
        Test sending a message - called from JavaScript (no record ID needed)
        Returns result for display in UI
        """
        _logger.info(f"[ULTRAMSG Test] action_test_send_message_direct called with: phone={phone}, type={message_type}")
        
        try:
            # Get active config (first active one)
            config = self.env['ultramsg.config'].search([('active', '=', True)], limit=1)
            if not config:
                return {
                    'success': False,
                    'message': 'لم يتم العثور على إعدادات ULTRAMSG نشطة. يرجى تفعيل الإعدادات.',
                    'message_id': False,
                    'response': {},
                }
            
            # Ensure we have a single record
            config.ensure_one()
            
            # Call the instance method
            return config.action_test_send_message(phone, message_type, message_body, document_url, document_name)
        except Exception as e:
            _logger.error(f"[ULTRAMSG Test] Error in action_test_send_message_direct: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'خطأ: {str(e)}',
                'message_id': False,
                'response': {'error': str(e)},
            }
    
    def action_test_send_message(self, phone, message_type='text', message_body='', document_url='', document_name=''):
        """
        Test sending a message
        Returns result for display in UI
        """
        self.ensure_one()
        
        _logger.info(f"[ULTRAMSG Test] action_test_send_message called with: phone={phone}, type={message_type}")
        
        try:
            # Validate inputs
            if not phone:
                return {
                    'success': False,
                    'message': 'رقم الهاتف مطلوب',
                    'message_id': False,
                    'response': {},
                }
            
            if message_type == 'text' and not message_body:
                return {
                    'success': False,
                    'message': 'نص الرسالة مطلوب',
                    'message_id': False,
                    'response': {},
                }
            
            if message_type in ['document', 'image'] and not document_url:
                return {
                    'success': False,
                    'message': 'رابط المستند/الصورة مطلوب',
                    'message_id': False,
                    'response': {},
                }
            
            # Check if config is active
            if not self.active:
                return {
                    'success': False,
                    'message': 'إعدادات ULTRAMSG غير مفعلة',
                    'message_id': False,
                    'response': {},
                }
            
            # Check if credentials are set
            if not self.instance_id or not self.api_token:
                return {
                    'success': False,
                    'message': 'إعدادات ULTRAMSG غير مكتملة (Instance ID أو API Token مفقود)',
                    'message_id': False,
                    'response': {},
                }
            
            _logger.info(f"[ULTRAMSG Test] Calling send_message...")
            result = self.send_message(
                phone=phone,
                message_type=message_type,
                message_body=message_body,
                document_url=document_url,
                document_name=document_name,
            )
            
            _logger.info(f"[ULTRAMSG Test] send_message result type: {type(result)}, value: {result}")
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                _logger.error(f"[ULTRAMSG Test] Expected dict but got {type(result)}: {result}")
                return {
                    'success': False,
                    'message': f'خطأ في النظام: النتيجة ليست بالشكل الصحيح',
                    'message_id': False,
                    'response': {'error': f'Invalid result type: {type(result)}'},
                }
            
            # Create a log entry
            if result.get('success'):
                message = self.env['ultramsg.message'].create({
                    'phone': phone,
                    'message_type': message_type,
                    'message_body': message_body,
                    'document_url': document_url,
                    'document_name': document_name,
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'ultramsg_id': result.get('ultramsg_id'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.info(f"[ULTRAMSG Test] Message created with ID: {message.id}")
            else:
                message = self.env['ultramsg.message'].create({
                    'phone': phone,
                    'message_type': message_type,
                    'message_body': message_body,
                    'document_url': document_url,
                    'document_name': document_name,
                    'state': 'failed',
                    'error_message': result.get('error'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.warning(f"[ULTRAMSG Test] Message failed, created log with ID: {message.id}, error: {result.get('error')}")
            
            return {
                'success': result.get('success', False),
                'message': result.get('error') if not result.get('success') else 'تم إرسال الرسالة بنجاح',
                'message_id': message.id,
                'response': result.get('response', {}),
            }
        except Exception as e:
            _logger.error(f"[ULTRAMSG Test] Error in test send message: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'خطأ: {str(e)}',
                'message_id': False,
                'response': {'error': str(e)},
            }

