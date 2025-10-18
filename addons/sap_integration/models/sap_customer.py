# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

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
        """Sync customer from SAP to Odoo"""
        try:
            connection = self.backend_id.get_connection()
            
            # Get customer data from SAP
            customers = connection.get_customers(
                filter_query=f"CardCode eq '{self.sap_customer_id}'"
            )
            
            if not customers.get('value'):
                raise UserError(f"Customer {self.sap_customer_id} not found in SAP")
            
            customer_data = customers['value'][0]
            self.sap_data = str(customer_data)
            
            # Process customer data
            partner = self._process_customer_data(customer_data)
            
            self.odoo_partner_id = partner.id
            self.sap_customer_name = customer_data.get('CardName', '')
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced customer {self.sap_customer_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing customer {self.sap_customer_id}: {str(e)}")
            raise
    
    def sync_to_sap(self):
        """Sync customer from Odoo to SAP"""
        try:
            if not self.odoo_partner_id:
                raise UserError("No Odoo partner linked to this sync record")
            
            connection = self.backend_id.get_connection()
            
            # Prepare customer data for SAP
            customer_data = self._prepare_customer_data_for_sap()
            self.sap_data = str(customer_data)
            
            # Create or update customer in SAP
            if self.sap_customer_id:
                # Update existing customer
                result = connection.update_customer(self.sap_customer_id, customer_data)
            else:
                # Create new customer
                result = connection.create_customer(customer_data)
                if result:
                    self.sap_customer_id = result.get('CardCode')
            
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced customer to SAP: {self.sap_customer_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing customer to SAP: {str(e)}")
            raise
    
    def _process_customer_data(self, customer_data):
        """Process customer data from SAP and create/update Odoo partner"""
        try:
            # Map SAP data to Odoo format
            partner_vals = self._map_sap_to_odoo(customer_data)
            
            # Check if partner already exists
            partner = self.env['res.partner'].search([
                ('ref', '=', customer_data['CardCode'])
            ], limit=1)
            
            if partner:
                # Update existing partner
                partner.write(partner_vals)
                _logger.info(f"Updated existing partner: {partner.name}")
            else:
                # Create new partner
                partner = self.env['res.partner'].create(partner_vals)
                _logger.info(f"Created new partner: {partner.name}")
            
            return partner
            
        except Exception as e:
            _logger.error(f"Error processing customer data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP customer data to Odoo partner format"""
        return {
            'name': sap_data.get('CardName', ''),
            'ref': sap_data.get('CardCode', ''),
            'email': sap_data.get('EmailAddress', ''),
            'phone': sap_data.get('Phone1', ''),
            'mobile': sap_data.get('Cellular', ''),
            'street': sap_data.get('Address', ''),
            'street2': sap_data.get('Address2', ''),
            'city': sap_data.get('City', ''),
            'zip': sap_data.get('ZipCode', ''),
            'state_id': self._get_state_id(sap_data.get('State', '')),
            'country_id': self._get_country_id(sap_data.get('Country', '')),
            'is_company': True,
            'customer_rank': 1,
            'supplier_rank': 0,
            'website': sap_data.get('Website', ''),
            'comment': f"SAP Customer: {sap_data.get('CardCode', '')}",
        }
    
    def _prepare_customer_data_for_sap(self):
        """Prepare Odoo partner data for SAP format"""
        partner = self.odoo_partner_id
        return {
            'CardName': partner.name,
            'CardCode': partner.ref or '',
            'EmailAddress': partner.email or '',
            'Phone1': partner.phone or '',
            'Cellular': partner.mobile or '',
            'Address': partner.street or '',
            'Address2': partner.street2 or '',
            'City': partner.city or '',
            'ZipCode': partner.zip or '',
            'State': partner.state_id.name or '',
            'Country': partner.country_id.code or '',
            'Website': partner.website or '',
            'CardType': 'cCustomer',
        }
    
    def _get_state_id(self, state_name):
        """Get state ID by name"""
        if not state_name:
            return False
        state = self.env['res.country.state'].search([
            ('name', 'ilike', state_name)
        ], limit=1)
        return state.id if state else False
    
    def _get_country_id(self, country_code):
        """Get country ID by code"""
        if not country_code:
            return False
        country = self.env['res.country'].search([
            ('code', '=', country_code)
        ], limit=1)
        return country.id if country else False
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    @api.model
    def sync_all_customers(self, backend_id):
        """Sync all customers from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            connection = backend.get_connection()
            
            # Get all customers from SAP
            customers = connection.get_customers(top=1000)  # Adjust as needed
            
            synced_count = 0
            for customer_data in customers.get('value', []):
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_customer_id', '=', customer_data['CardCode'])
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_customer_id': customer_data['CardCode'],
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the customer
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} customers from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all customers: {str(e)}")
            raise


