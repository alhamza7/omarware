# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapPricelistSync(models.Model):
    _name = 'sap.pricelist.sync'
    _description = 'SAP Pricelist Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_pricelist_id = fields.Many2one('product.pricelist', 'Odoo Pricelist')
    sap_pricelist_id = fields.Char('SAP Pricelist ID', required=True)
    sap_pricelist_name = fields.Char('SAP Pricelist Name')
    
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
    def create(self, vals_list):
        """Override create to set default values"""
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if not vals.get('backend_id') and vals.get('connector_id'):
                connector = self.env['sap.connector'].browse(vals['connector_id'])
                vals['backend_id'] = connector.backend_id.id
        
        return super(SapPricelistSync, self).create(vals_list)
    
    def sync_from_sap(self):
        """Sync pricelist from SAP to Odoo"""
        try:
            # For now, we'll create a basic pricelist
            # In a real implementation, you would get pricelist data from SAP
            pricelist_data = self._get_sap_pricelist_data(self.sap_pricelist_id)
            self.sap_data = str(pricelist_data)
            
            # Process pricelist data
            pricelist = self._process_pricelist_data(pricelist_data)
            
            self.odoo_pricelist_id = pricelist.id
            self.sap_pricelist_name = pricelist_data.get('name', '')
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced pricelist {self.sap_pricelist_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing pricelist {self.sap_pricelist_id}: {str(e)}")
            raise
    
    def _get_sap_pricelist_data(self, sap_pricelist_id):
        """Get pricelist data from SAP (simplified for now)"""
        # This would be replaced with actual SAP API calls
        return {
            'name': f"SAP Pricelist {sap_pricelist_id}",
            'currency': 'USD',
            'active': True,
        }
    
    def _process_pricelist_data(self, pricelist_data):
        """Process pricelist data from SAP and create/update Odoo pricelist"""
        try:
            # Map SAP data to Odoo format
            pricelist_vals = self._map_sap_to_odoo(pricelist_data)
            
            # Check if pricelist already exists
            pricelist = self.env['product.pricelist'].search([
                ('name', '=', pricelist_data['name'])
            ], limit=1)
            
            if pricelist:
                # Update existing pricelist
                pricelist.write(pricelist_vals)
                _logger.info(f"Updated existing pricelist: {pricelist.name}")
            else:
                # Create new pricelist
                pricelist = self.env['product.pricelist'].create(pricelist_vals)
                _logger.info(f"Created new pricelist: {pricelist.name}")
            
            return pricelist
            
        except Exception as e:
            _logger.error(f"Error processing pricelist data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP pricelist data to Odoo pricelist format"""
        # Get currency
        currency = self.env['res.currency'].search([
            ('name', '=', sap_data.get('currency', 'USD'))
        ], limit=1)
        
        if not currency:
            currency = self.env.ref('base.USD')
        
        return {
            'name': sap_data['name'],
            'currency_id': currency.id,
            'active': sap_data.get('active', True),
        }
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    def sync_to_sap(self):
        """Sync pricelist from Odoo to SAP"""
        # Implementation for syncing to SAP
        pass
    
    @api.model
    def sync_all_pricelists(self, backend_id):
        """Sync all pricelists from SAP"""
        try:
            # Common SAP pricelists to sync
            sap_pricelists = ['STANDARD', 'CUSTOMER', 'PROMOTION']
            
            synced_count = 0
            for sap_pricelist_id in sap_pricelists:
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_pricelist_id', '=', sap_pricelist_id)
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_pricelist_id': sap_pricelist_id,
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the pricelist
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} pricelists from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all pricelists: {str(e)}")
            raise


