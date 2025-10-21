# -*- coding: utf-8 -*-
"""SAP Warehouse Management"""

from odoo import models, fields, api
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
    
    _sql_constraints = [
        ('sap_warehouse_uniq', 'unique(backend_id, external_id)',
         'A warehouse with the same SAP code already exists for this backend.'),
    ]
    
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
        ('sap_location_uniq', 'unique(warehouse_id, external_id)',
         'A location with the same code already exists for this warehouse.'),
    ]

