# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class UltramsgMessage(models.Model):
    """Log for ULTRAMSG WhatsApp messages"""
    _name = 'ultramsg.message'
    _description = 'ULTRAMSG WhatsApp Message Log'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Message Reference', required=True, default='New', readonly=True, tracking=True)
    
    # Message details
    phone = fields.Char(string='Phone Number', required=True, help='Phone number in format: 07800114976', tracking=True)
    formatted_phone = fields.Char(string='Formatted Phone', compute='_compute_formatted_phone', store=True, readonly=True)
    
    message_type = fields.Selection([
        ('text', 'Text'),
        ('document', 'Document'),
        ('image', 'Image'),
    ], string='Message Type', required=True, default='document', tracking=True)
    
    message_body = fields.Text(string='Message Body')
    document_url = fields.Char(string='Document URL')
    document_name = fields.Char(string='Document Name')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Response from ULTRAMSG
    ultramsg_id = fields.Char(string='ULTRAMSG ID', readonly=True)
    ultramsg_response = fields.Text(string='API Response', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    
    # Timestamps
    sent_date = fields.Datetime(string='Sent Date', readonly=True)
    
    # Generic relation - can link to any model
    res_model = fields.Char(string='Related Model', help='Model name of the related document')
    res_id = fields.Integer(string='Related ID', help='ID of the related document')
    res_name = fields.Char(string='Related Document', compute='_compute_res_name', store=False)
    
    @api.depends('phone')
    def _compute_formatted_phone(self):
        """Compute formatted phone with country code"""
        for record in self:
            config = self.env['ultramsg.config'].search([('active', '=', True)], limit=1)
            if config and record.phone:
                record.formatted_phone = config.format_phone_number(record.phone)
            else:
                record.formatted_phone = record.phone
    
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        """Get name of related document"""
        for record in self:
            if record.res_model and record.res_id:
                try:
                    related_record = self.env[record.res_model].browse(record.res_id)
                    if related_record.exists():
                        record.res_name = related_record.display_name
                    else:
                        record.res_name = f"{record.res_model} #{record.res_id}"
                except:
                    record.res_name = f"{record.res_model} #{record.res_id}"
            else:
                record.res_name = ''
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence for message reference"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ultramsg.message') or 'New'
        return super(UltramsgMessage, self).create(vals_list)
    
    def action_send_message(self):
        """Send message via ULTRAMSG API"""
        for record in self:
            try:
                record.write({'state': 'sending'})
                
                # Get ULTRAMSG config
                config = self.env['ultramsg.config'].search([('active', '=', True)], limit=1)
                if not config:
                    raise Exception('ULTRAMSG configuration not found. Please configure ULTRAMSG first.')
                
                # Send message
                result = config.send_message(
                    phone=record.phone,
                    message_type=record.message_type,
                    message_body=record.message_body,
                    document_url=record.document_url,
                    document_name=record.document_name,
                )
                
                if result.get('success'):
                    record.write({
                        'state': 'sent',
                        'sent_date': fields.Datetime.now(),
                        'ultramsg_id': result.get('ultramsg_id'),
                        'ultramsg_response': str(result.get('response')),
                    })
                    _logger.info(f"Message sent successfully: {record.name}")
                else:
                    record.write({
                        'state': 'failed',
                        'error_message': result.get('error'),
                        'ultramsg_response': str(result.get('response')),
                    })
                    _logger.error(f"Failed to send message {record.name}: {result.get('error')}")
                    
            except Exception as e:
                record.write({
                    'state': 'failed',
                    'error_message': str(e),
                })
                _logger.error(f"Error sending message {record.name}: {e}", exc_info=True)
    
    def action_retry_send(self):
        """Retry sending failed messages"""
        failed_messages = self.filtered(lambda m: m.state == 'failed')
        for message in failed_messages:
            message.action_send_message()

