# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapUomSync(models.Model):
    _name = 'sap.uom.sync'
    _description = 'SAP Unit of Measure Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_uom_id = fields.Many2one('uom.uom', 'Odoo UoM')
    sap_uom_id = fields.Char('SAP UoM ID', required=True)
    sap_uom_name = fields.Char('SAP UoM Name')
    
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
        
        return super(SapUomSync, self).create(vals_list)
    
    def sync_from_sap(self):
        """Sync UoM from SAP to Odoo"""
        try:
            # For now, we'll create UoMs based on common SAP UoMs
            # In a real implementation, you would get UoM data from SAP
            uom_data = self._get_sap_uom_data(self.sap_uom_id)
            self.sap_data = str(uom_data)
            
            # Process UoM data
            uom = self._process_uom_data(uom_data)
            
            self.odoo_uom_id = uom.id
            self.sap_uom_name = uom_data.get('name', '')
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced UoM {self.sap_uom_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing UoM {self.sap_uom_id}: {str(e)}")
            raise
    
    def _get_sap_uom_data(self, sap_uom_id):
        """Get UoM data from SAP (simplified for now)"""
        # Common SAP UoM mappings
        uom_mappings = {
            'PCS': {'name': 'Pieces', 'category': 'unit', 'factor': 1.0},
            'KG': {'name': 'Kilogram', 'category': 'weight', 'factor': 1.0},
            'G': {'name': 'Gram', 'category': 'weight', 'factor': 0.001},
            'T': {'name': 'Ton', 'category': 'weight', 'factor': 1000.0},
            'M': {'name': 'Meter', 'category': 'length', 'factor': 1.0},
            'CM': {'name': 'Centimeter', 'category': 'length', 'factor': 0.01},
            'MM': {'name': 'Millimeter', 'category': 'length', 'factor': 0.001},
            'L': {'name': 'Liter', 'category': 'volume', 'factor': 1.0},
            'ML': {'name': 'Milliliter', 'category': 'volume', 'factor': 0.001},
            'BOX': {'name': 'Box', 'category': 'unit', 'factor': 1.0},
            'PKG': {'name': 'Package', 'category': 'unit', 'factor': 1.0},
        }
        
        return uom_mappings.get(sap_uom_id, {
            'name': sap_uom_id,
            'category': 'unit',
            'factor': 1.0
        })
    
    def _process_uom_data(self, uom_data):
        """Process UoM data from SAP and create/update Odoo UoM"""
        try:
            # Map SAP data to Odoo format
            uom_vals = self._map_sap_to_odoo(uom_data)
            
            # Check if UoM already exists
            uom = self.env['uom.uom'].search([
                ('name', '=', uom_data['name'])
            ], limit=1)
            
            if uom:
                # Update existing UoM
                uom.write(uom_vals)
                _logger.info(f"Updated existing UoM: {uom.name}")
            else:
                # Create new UoM
                uom = self.env['uom.uom'].create(uom_vals)
                _logger.info(f"Created new UoM: {uom.name}")
            
            return uom
            
        except Exception as e:
            _logger.error(f"Error processing UoM data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP UoM data to Odoo UoM format"""
        # Get reference UoM
        relative_uom_id = self._get_reference_uom(sap_data['category'])
        
        return {
            'name': sap_data['name'],
            'relative_uom_id': relative_uom_id,
            'relative_factor': sap_data['factor'],
        }
    
    def _get_reference_uom(self, category_type):
        """Get reference UoM by category type"""
        # Map categories to their reference UoM external IDs
        reference_uom_mapping = {
            'unit': 'uom.product_uom_unit',
            'weight': 'uom.product_uom_gram',
            'length': 'uom.product_uom_millimeter',
            'volume': 'uom.product_uom_milliliter',
            'time': 'uom.product_uom_hour',
        }
        
        uom_xmlid = reference_uom_mapping.get(category_type, 'uom.product_uom_unit')
        try:
            return self.env.ref(uom_xmlid).id
        except ValueError:
            # If reference UoM not found, return None (will create a base UoM)
            _logger.warning(f"Reference UoM {uom_xmlid} not found, creating independent UoM")
            return False
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    def sync_to_sap(self):
        """Sync UoM from Odoo to SAP"""
        # Implementation for syncing to SAP
        pass
    
    @api.model
    def sync_all_uoms(self, backend_id):
        """Sync all UoMs from SAP"""
        try:
            # Common SAP UoMs to sync
            sap_uoms = ['PCS', 'KG', 'G', 'T', 'M', 'CM', 'MM', 'L', 'ML', 'BOX', 'PKG']
            
            synced_count = 0
            for sap_uom_id in sap_uoms:
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_uom_id', '=', sap_uom_id)
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_uom_id': sap_uom_id,
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the UoM
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} UoMs from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all UoMs: {str(e)}")
            raise


