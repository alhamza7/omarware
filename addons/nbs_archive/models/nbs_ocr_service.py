# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64
import logging

_logger = logging.getLogger(__name__)


class NBSOCRService(models.Model):
    _name = 'nbs.ocr.service'
    _description = 'OCR Processing Service'
    
    name = fields.Char(string='OCR Job', required=True)
    document_id = fields.Many2one('nbs.document', string='Document')
    attachment_id = fields.Many2one('nbs.document.attachment', string='Attachment')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    
    extracted_text = fields.Text(string='Extracted Text')
    confidence_score = fields.Float(string='Confidence Score')
    language = fields.Char(string='Detected Language')
    
    error_message = fields.Text(string='Error Message')
    
    def process_ocr(self):
        """Process OCR on attachment"""
        self.ensure_one()
        try:
            self.write({'status': 'processing'})
            
            # OCR processing logic here
            # Using pytesseract (already in requirements)
            try:
                import pytesseract
                from PIL import Image
                import io
                
                # Get file data
                file_data = base64.b64decode(self.attachment_id.file_data)
                image = Image.open(io.BytesIO(file_data))
                
                # Extract text
                text = pytesseract.image_to_string(image, lang='ara+eng')
                
                self.write({
                    'status': 'completed',
                    'extracted_text': text,
                    'confidence_score': 0.85
                })
                
                # Update document with extracted text
                if self.document_id:
                    self.document_id.write({
                        'ocr_text': text
                    })
                
            except ImportError:
                self.write({
                    'status': 'failed',
                    'error_message': 'OCR library not installed. Run: pip install pytesseract'
                })
        except Exception as e:
            _logger.error(f'OCR processing error: {str(e)}', exc_info=True)
            self.write({
                'status': 'failed',
                'error_message': str(e)
            })


class NBSEmailNotification(models.Model):
    _name = 'nbs.email.notification'
    _description = 'Email Notifications'
    
    name = fields.Char(string='Subject', required=True)
    document_id = fields.Many2one('nbs.document', string='Document')
    recipient_ids = fields.Many2many('res.users', string='Recipients')
    
    email_template_id = fields.Many2one('mail.template', string='Email Template')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], default='pending')
    
    send_date = fields.Datetime(string='Send Date')
    error_message = fields.Text(string='Error')
    
    def send_notification(self):
        """Send email notification"""
        self.ensure_one()
        try:
            for recipient in self.recipient_ids:
                # Send email using Odoo mail system
                self.env['mail.mail'].create({
                    'subject': self.name,
                    'body_html': f'<p>Document: {self.document_id.name}</p>',
                    'email_to': recipient.email
                }).send()
            
            self.write({'status': 'sent', 'send_date': fields.Datetime.now()})
        except Exception as e:
            self.write({'status': 'failed', 'error_message': str(e)})


class NBSDocumentAnalytics(models.Model):
    _name = 'nbs.document.analytics'
    _description = 'Document Analytics & Reports'
    
    name = fields.Char(string='Report Name', required=True)
    report_type = fields.Selection([
        ('department', 'By Department'),
        ('type', 'By Document Type'),
        ('user', 'By User'),
        ('timeline', 'Timeline'),
        ('storage', 'Storage Usage')
    ], required=True)
    
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    
    department_id = fields.Many2one('nbs.department', string='Department')
    
    # Results
    total_documents = fields.Integer(string='Total Documents', compute='_compute_stats')
    active_documents = fields.Integer(string='Active', compute='_compute_stats')
    archived_documents = fields.Integer(string='Archived', compute='_compute_stats')
    trash_documents = fields.Integer(string='In Trash', compute='_compute_stats')
    
    total_size_mb = fields.Float(string='Total Size (MB)', compute='_compute_storage')
    
    def _compute_stats(self):
        for analytics in self:
            domain = []
            if analytics.department_id:
                domain.append(('department_id', '=', analytics.department_id.id))
            if analytics.date_from:
                domain.append(('create_date', '>=', analytics.date_from))
            if analytics.date_to:
                domain.append(('create_date', '<=', analytics.date_to))
            
            analytics.total_documents = self.env['nbs.document'].search_count(domain)
            analytics.active_documents = self.env['nbs.document'].search_count(domain + [('state', '=', 'active')])
            analytics.archived_documents = self.env['nbs.document'].search_count(domain + [('state', '=', 'archived')])
            analytics.trash_documents = self.env['nbs.document'].search_count(domain + [('is_deleted', '=', True)])
    
    def _compute_storage(self):
        for analytics in self:
            # Calculate total storage
            attachments = self.env['nbs.document.attachment'].search([
                ('document_id.department_id', '=', analytics.department_id.id if analytics.department_id else False)
            ])
            total_bytes = sum(attachments.mapped('file_size'))
            analytics.total_size_mb = total_bytes / (1024 * 1024)
