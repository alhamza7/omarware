# -*- coding: utf-8 -*-
"""SAP Warehouse Management"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapWarehouse(models.Model):
    """Binding Model for SAP Warehouses"""
    _name = 'sap.warehouse'
    _description = 'SAP Warehouse Binding'
    _inherits = {'stock.warehouse': 'odoo_id'}
    
    odoo_id = fields.Many2one(
        'stock.warehouse',
        string='Odoo Warehouse',
        required=True,
        ondelete='cascade',
        index=True
    )
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True
    )
    external_id = fields.Char(
        string='SAP Warehouse Code',
        required=True,
        index=True
    )
    
    sap_warehouse_name = fields.Char('SAP Warehouse Name')
    sap_business_place_id = fields.Integer('Business Place ID')
    sync_date = fields.Datetime('Last Sync Date', readonly=True)
    active = fields.Boolean(default=True)
    
    # Constraints
    _sql_constraints = [
        ('sap_warehouse_uniq', 'UNIQUE(backend_id, external_id)',
         'A warehouse with the same SAP code already exists for this backend.'),
    ]
    
    def button_import_from_sap(self):
        """Button to import warehouse from SAP"""
        self.ensure_one()
        if not self.backend_id:
            raise UserError("Please select a SAP Backend first")
        
        try:
            result = self.import_from_sap(self.backend_id, self.external_id)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Warehouse {self.sap_warehouse_name} imported successfully',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(f"Error importing warehouse: {str(e)}")
    
    @api.model
    def import_from_sap(self, backend, warehouse_code):
        """Import a single warehouse from SAP"""
        try:
            _logger.info(f"Importing warehouse {warehouse_code} from SAP")
            
            # Get warehouse data from SAP
            warehouse_data = self._get_sap_warehouse_data(backend, warehouse_code)
            
            # Create or update warehouse binding
            binding = self._create_or_update_warehouse(backend, warehouse_data)
            
            _logger.info(f"Successfully imported warehouse {warehouse_code}")
            return binding
            
        except Exception as e:
            _logger.error(f"Error importing warehouse {warehouse_code}: {str(e)}")
            raise
    
    @api.model
    def import_all_from_sap(self, backend):
        """Import all warehouses from SAP"""
        try:
            _logger.info(f"Importing all warehouses from SAP backend {backend.name}")
            
            # Get all warehouses from SAP
            warehouses_data = self._get_all_sap_warehouses(backend)
            
            imported_count = 0
            for warehouse_data in warehouses_data:
                try:
                    self._create_or_update_warehouse(backend, warehouse_data)
                    imported_count += 1
                except Exception as e:
                    _logger.error(f"Error importing warehouse {warehouse_data.get('Code')}: {str(e)}")
                    continue
            
            _logger.info(f"Successfully imported {imported_count} warehouses")
            return imported_count
            
        except Exception as e:
            _logger.error(f"Error importing all warehouses: {str(e)}")
            raise
    
    def _get_sap_warehouse_data(self, backend, warehouse_code):
        """Get warehouse data from SAP API"""
        try:
            # Get connection to SAP
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            # Call SAP Service Layer API
            endpoint = f"Warehouses('{warehouse_code}')"
            response = connection.get(endpoint, {})
            
            return response
            
        except Exception as e:
            _logger.error(f"Error getting warehouse data from SAP: {str(e)}")
            raise
    
    def _get_all_sap_warehouses(self, backend):
        """Get all warehouses from SAP API"""
        try:
            # Get connection to SAP
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            # Call SAP Service Layer API
            endpoint = "Warehouses"
            response = connection.get(endpoint, {})
            
            return response.get('value', [])
            
        except Exception as e:
            _logger.error(f"Error getting warehouses from SAP: {str(e)}")
            raise
    
    def _create_or_update_warehouse(self, backend, sap_data):
        """Create or update warehouse binding"""
        try:
            warehouse_code = sap_data.get('WarehouseCode')
            warehouse_name = sap_data.get('WarehouseName', warehouse_code)
            
            # Check if binding already exists
            binding = self.search([
                ('backend_id', '=', backend.id),
                ('external_id', '=', warehouse_code)
            ], limit=1)
            
            # Check if Odoo warehouse exists
            odoo_warehouse = self.env['stock.warehouse'].search([
                ('code', '=', warehouse_code)
            ], limit=1)
            
            if not odoo_warehouse:
                # Create new Odoo warehouse
                odoo_warehouse = self.env['stock.warehouse'].create({
                    'name': warehouse_name,
                    'code': warehouse_code,
                })
            
            vals = {
                'backend_id': backend.id,
                'odoo_id': odoo_warehouse.id,
                'external_id': warehouse_code,
                'sap_warehouse_name': warehouse_name,
                'sap_business_place_id': sap_data.get('BusinessPlaceID', 0),
                'sync_date': fields.Datetime.now(),
                'active': True,
            }
            
            if binding:
                binding.write(vals)
            else:
                binding = self.create(vals)
            
            return binding
            
        except Exception as e:
            _logger.error(f"Error creating/updating warehouse: {str(e)}")
            raise
    
    @api.model
    def import_batch(self, backend, filters=None):
        """Import SAP Warehouses in batch"""
        try:
            _logger.info(f"Starting batch import of warehouses from SAP backend {backend.name}")
            
            from odoo.addons.component.core import WorkContext
            work = WorkContext(
                model_name='sap.warehouse',
                collection=backend,
                components_registry=self.env['component.core']._cache
            )
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)
            
        except Exception as e:
            _logger.error(f"Error in batch import for sap.warehouse: {str(e)}")
            raise


class SapStockLocation(models.Model):
    """SAP Stock Location Binding"""
    _name = 'sap.stock.location'
    _description = 'SAP Stock Location Binding'
    
    backend_id = fields.Many2one('sap.backend', required=True, ondelete='cascade')
    warehouse_id = fields.Many2one('sap.warehouse', required=True, ondelete='cascade')
    external_id = fields.Char('SAP Location Code', required=True, index=True)
    odoo_id = fields.Many2one('stock.location', required=True, ondelete='cascade')
    
    sap_location_name = fields.Char('SAP Location Name')
    sap_bin_location = fields.Char('Bin Location')
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('sap_location_uniq', 'UNIQUE(warehouse_id, external_id)',
         'A location with the same code already exists for this warehouse.'),
    ]

