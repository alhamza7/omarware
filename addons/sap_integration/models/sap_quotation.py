# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapQuotationSync(models.Model):
    _name = 'sap.quotation.sync'
    _description = 'SAP Quotation Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_quotation_id = fields.Many2one('sale.order', 'Odoo Quotation')
    sap_quotation_id = fields.Char('SAP Quotation ID', required=True)
    sap_doc_entry = fields.Integer('SAP Doc Entry')
    
    # Sync information
    last_sync = fields.Datetime('Last Sync', readonly=True)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], 'Sync Status', default='pending', readonly=True)
    sync_direction = fields.Selection([
        ('sap_to_odoo', 'SAP to Odoo'),
        ('odoo_to_sap', 'Odoo to SAP'),
        ('bidirectional', 'Bidirectional'),
    ], 'Sync Direction', default='sap_to_odoo')
    
    # Error handling
    error_message = fields.Text('Error Message', readonly=True)
    retry_count = fields.Integer('Retry Count', default=0)
    max_retries = fields.Integer('Max Retries', default=3)
    
    # Data mapping
    sap_data = fields.Text('SAP Data (JSON)', help="Raw data from SAP")
    odoo_data = fields.Text('Odoo Data (JSON)', help="Raw data from Odoo")
    
    @api.model
    def create(self, vals):
        """Override create to set default values"""
        if not vals.get('backend_id') and vals.get('connector_id'):
            vals['backend_id'] = self.env['sap.connector'].browse(vals['connector_id']).backend_id.id
        return super(SapQuotationSync, self).create(vals)
    
    def sync_from_sap(self):
        """Sync quotation from SAP to Odoo"""
        try:
            connection = self.backend_id.get_connection()
            
            # Get quotation data from SAP
            quotations = connection.get_quotations(
                filter_query=f"DocEntry eq {self.sap_doc_entry}"
            )
            
            if not quotations.get('value'):
                raise UserError(f"Quotation {self.sap_doc_entry} not found in SAP")
            
            quotation_data = quotations['value'][0]
            self.sap_data = str(quotation_data)
            
            # Process quotation data
            quotation = self._process_quotation_data(quotation_data)
            
            self.odoo_quotation_id = quotation.id
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced quotation {self.sap_quotation_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing quotation {self.sap_quotation_id}: {str(e)}")
            raise
    
    def sync_to_sap(self):
        """Sync quotation from Odoo to SAP"""
        try:
            if not self.odoo_quotation_id:
                raise UserError("No Odoo quotation linked to this sync record")
            
            connection = self.backend_id.get_connection()
            
            # Prepare quotation data for SAP
            quotation_data = self._prepare_quotation_data_for_sap()
            self.sap_data = str(quotation_data)
            
            # Create or update quotation in SAP
            if self.sap_doc_entry:
                # Update existing quotation
                result = connection.update_quotation(self.sap_doc_entry, quotation_data)
            else:
                # Create new quotation
                result = connection.create_quotation(quotation_data)
                if result:
                    self.sap_doc_entry = result.get('DocEntry')
                    self.sap_quotation_id = result.get('DocNum')
            
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced quotation to SAP: {self.sap_quotation_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing quotation to SAP: {str(e)}")
            raise
    
    def _process_quotation_data(self, quotation_data):
        """Process quotation data from SAP and create/update Odoo quotation"""
        try:
            # Map SAP data to Odoo format
            quotation_vals = self._map_sap_to_odoo(quotation_data)
            
            # Check if quotation already exists
            quotation = self.env['sale.order'].search([
                ('client_order_ref', '=', quotation_data['DocNum'])
            ], limit=1)
            
            if quotation:
                # Update existing quotation
                quotation.write(quotation_vals)
                _logger.info(f"Updated existing quotation: {quotation.name}")
            else:
                # Create new quotation
                quotation = self.env['sale.order'].create(quotation_vals)
                _logger.info(f"Created new quotation: {quotation.name}")
            
            return quotation
            
        except Exception as e:
            _logger.error(f"Error processing quotation data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP quotation data to Odoo quotation format"""
        # Get customer
        customer = self.env['res.partner'].search([
            ('ref', '=', sap_data.get('CardCode', ''))
        ], limit=1)
        
        if not customer:
            # Create customer if not exists
            customer = self.env['res.partner'].create({
                'name': sap_data.get('CardName', ''),
                'ref': sap_data.get('CardCode', ''),
                'is_company': True,
                'customer_rank': 1,
            })
        
        # Prepare order lines
        order_lines = []
        for line in sap_data.get('DocumentLines', []):
            # Get product
            product = self.env['product.product'].search([
                ('default_code', '=', line.get('ItemCode', ''))
            ], limit=1)
            
            if product:
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': line.get('ItemDescription', ''),
                    'product_uom_qty': line.get('Quantity', 0),
                    'price_unit': line.get('UnitPrice', 0),
                    'discount': line.get('DiscountPercent', 0),
                }))
        
        return {
            'name': f"QUO/{sap_data.get('DocNum', '')}",
            'client_order_ref': sap_data.get('DocNum', ''),
            'partner_id': customer.id,
            'date_order': sap_data.get('DocDate', fields.Date.today()),
            'validity_date': sap_data.get('DocDueDate', fields.Date.today()),
            'state': 'draft',
            'order_line': order_lines,
            'note': f"SAP Quotation: {sap_data.get('DocNum', '')}",
        }
    
    def _prepare_quotation_data_for_sap(self):
        """Prepare Odoo quotation data for SAP format"""
        quotation = self.odoo_quotation_id
        
        # Prepare document lines
        document_lines = []
        for line in quotation.order_line:
            document_lines.append({
                'ItemCode': line.product_id.default_code or '',
                'ItemDescription': line.name,
                'Quantity': line.product_uom_qty,
                'UnitPrice': line.price_unit,
                'DiscountPercent': line.discount,
            })
        
        return {
            'CardCode': quotation.partner_id.ref or '',
            'DocDate': quotation.date_order.strftime('%Y-%m-%d'),
            'DocDueDate': quotation.validity_date.strftime('%Y-%m-%d'),
            'DocumentLines': document_lines,
        }
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    @api.model
    def sync_all_quotations(self, backend_id):
        """Sync all quotations from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            connection = backend.get_connection()
            
            # Get all quotations from SAP
            quotations = connection.get_quotations(top=1000)  # Adjust as needed
            
            synced_count = 0
            for quotation_data in quotations.get('value', []):
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_doc_entry', '=', quotation_data['DocEntry'])
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_quotation_id': quotation_data['DocNum'],
                        'sap_doc_entry': quotation_data['DocEntry'],
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the quotation
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} quotations from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all quotations: {str(e)}")
            raise


