# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

from ..core.sap_logger import SapLogger, SapSyncError, SapValidationError

_logger = logging.getLogger(__name__)


class SapCustomerSync(models.Model):
    _name = 'sap.customer.sync'
    _description = 'SAP Customer Synchronizer'
    _order = 'last_sync desc'
    
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_partner_id = fields.Many2one('res.partner', 'Odoo Partner')
    sap_customer_id = fields.Char('SAP Customer ID', required=True)
    sap_customer_name = fields.Char('SAP Customer Name')
    
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
        return super(SapCustomerSync, self).create(vals)
    
    def sync_from_sap(self):
        """Sync customer from SAP to Odoo using service layer"""
        try:
            # Get customer data from SAP
            connection = self.backend_id.get_connection()
            customers = connection.get('BusinessPartners', {
                '$filter': f"CardCode eq '{self.sap_customer_id}'"
            })
            
            if not customers.get('value'):
                raise SapValidationError(f"Customer {self.sap_customer_id} not found in SAP")
            
            customer_data = customers['value'][0]
            self.sap_data = str(customer_data)
            
            # DEBUG: Log data type
            _logger.info(f"Customer data type: {type(customer_data)}, Keys: {list(customer_data.keys()) if isinstance(customer_data, dict) else 'NOT A DICT'}")
            
            # Use service layer to sync customer
            customer_service = self.env['sap.customer.service']
            sync_result = customer_service.sync_customer_from_sap(
                self.backend_id.id, 
                customer_data
            )
            
            if sync_result['status'] == 'success':
                # Update sync record
                partner = self.env['res.partner'].browse(sync_result['partner_id'])
                self.odoo_partner_id = partner.id
                self.sap_customer_name = customer_data.get('CardName', '')
                self.sync_status = 'success'
                self.last_sync = fields.Datetime.now()
                self.error_message = False
                self.retry_count = 0
                
                _logger.info(f"Successfully synced customer {self.sap_customer_id}")
            else:
                raise SapSyncError(sync_result.get('message', 'Unknown sync error'))
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing customer {self.sap_customer_id}: {str(e)}", exc_info=True)
            raise
    
    def sync_to_sap(self):
        """Sync customer from Odoo to SAP using service layer"""
        try:
            if not self.odoo_partner_id:
                raise SapValidationError("No Odoo partner linked to this sync record")
            
            # Use service layer to sync customer
            customer_service = self.env['sap.customer.service']
            sync_result = customer_service.sync_customer_to_sap(
                self.backend_id.id, 
                self.odoo_partner_id.id
            )
            
            if sync_result['status'] == 'success':
                # Update sync record
                if not self.sap_customer_id:
                    self.sap_customer_id = sync_result.get('sap_card_code')
                
                self.sync_status = 'success'
                self.last_sync = fields.Datetime.now()
                self.error_message = False
                self.retry_count = 0
                
                _logger.info(f"Successfully synced customer to SAP: {self.sap_customer_id}")
            else:
                raise SapSyncError(sync_result.get('message', 'Unknown sync error'))
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing customer to SAP: {str(e)}")
            raise
    
    # Legacy methods removed - now handled by service layer
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    @api.model
    def import_record(self, backend, external_id):
        """Import a single customer record from SAP - DIRECT METHOD"""
        try:
            _logger.info(f"Importing customer {external_id} from SAP backend {backend.name}")
            
            # Get customer data from SAP
            connection = backend.get_connection()
            customers = connection.get('BusinessPartners', {
                '$filter': f"CardCode eq '{external_id}'"
            })
            
            if not customers.get('value'):
                _logger.warning(f"Customer {external_id} not found in SAP")
                return None
            
            customer_data = customers['value'][0]
            
            # Use direct import helper
            direct_importer = self.env['sap.customer.direct.import']
            partner = direct_importer.import_customer_direct(backend, external_id, customer_data)
            
            _logger.info(f"Successfully imported customer {external_id}: {partner.name}")
            return partner
            
        except Exception as e:
            _logger.error(f"Error importing customer {external_id}: {str(e)}", exc_info=True)
            raise
    
    @api.model
    def sync_all_customers(self, backend_id):
        """Sync all customers from SAP using service layer"""
        try:
            # Use service layer to sync all customers
            customer_service = self.env['sap.customer.service']
            result = customer_service.sync_all_customers_from_sap(backend_id)
            
            _logger.info(f"Synced {result['successful']} customers from SAP, {result['failed']} failed")
            return result
            
        except Exception as e:
            _logger.error(f"Error syncing all customers: {str(e)}")
            raise


