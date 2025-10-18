# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Importers

These importers synchronize data from SAP to Odoo
"""

from odoo import _
from odoo.addons.component.core import Component
# TODO: Uncomment when queue_job is installed
# from odoo.addons.queue_job.job import job
import logging

_logger = logging.getLogger(__name__)


class SapImporter(Component):
    """Base SAP Importer"""
    _name = 'sap.importer'
    _inherit = 'base.importer'
    _usage = 'record.importer'
    
    def _get_external_data(self, external_id):
        """Return external data for a given external ID"""
        adapter = self.component(usage='backend.adapter')
        return adapter.read(external_id)
    
    def _before_import(self):
        """Hook before import"""
        pass
    
    def _import_dependencies(self):
        """Import dependencies before importing the record"""
        pass
    
    def _map_data(self, external_data):
        """Map external data to Odoo format"""
        mapper = self.component(usage='import.mapper')
        return mapper.map_record(external_data).values()
    
    def _validate_data(self, data):
        """Validate the data before creating/updating"""
        return data
    
    def _create(self, data):
        """Create the Odoo record"""
        return self.model.create(data)
    
    def _update(self, binding, data):
        """Update the Odoo record"""
        binding.write(data)
        return binding
    
    def _after_import(self, binding):
        """Hook after import"""
        pass
    
    def run(self, external_id, force=False):
        """Run the import of a record from SAP"""
        self._before_import()
        
        # Check if record already exists
        binder = self.binder_for()
        binding = binder.to_internal(external_id)
        
        if binding and not force:
            _logger.info(f"Record {external_id} already imported, skipping")
            return binding
        
        # Import dependencies first
        self._import_dependencies()
        
        # Get external data
        external_data = self._get_external_data(external_id)
        if not external_data:
            raise ValueError(f"Record {external_id} not found in SAP")
        
        # Map data
        data = self._map_data(external_data)
        data = self._validate_data(data)
        
        # Create or update
        if binding:
            binding = self._update(binding, data)
        else:
            data['backend_id'] = self.backend_record.id
            data['external_id'] = str(external_id)
            binding = self._create(data)
        
        # Bind the record
        binder.bind(external_id, binding)
        
        self._after_import(binding)
        
        return binding


class SapBatchImporter(Component):
    """Base SAP Batch Importer"""
    _name = 'sap.batch.importer'
    _inherit = 'base.importer'
    _usage = 'batch.importer'
    
    def run(self, filters=None):
        """Import a batch of records from SAP"""
        adapter = self.component(usage='backend.adapter')
        
        # Get all records from SAP
        records = adapter.search(filters=filters, top=self.backend_record.batch_size)
        
        _logger.info(f"Batch importing {len(records)} records from SAP")
        
        imported_count = 0
        error_count = 0
        
        for record in records:
            try:
                external_id = self._get_external_id(record)
                if external_id:
                    # TODO: Uncomment when queue_job is installed
                    # self._import_record.delay(
                    #     self.backend_record,
                    #     external_id
                    # )
                    # For now, import directly
                    self._import_record(external_id)
                    imported_count += 1
            except Exception as e:
                error_count += 1
                _logger.error(f"Error importing record: {str(e)}")
        
        _logger.info(f"Batch import completed: {imported_count} imported, {error_count} errors")
        
        return {
            'imported': imported_count,
            'errors': error_count,
        }
    
    def _get_external_id(self, record):
        """Extract external ID from record"""
        raise NotImplementedError
    
    def _import_record(self, external_id):
        """Import a single record"""
        importer = self.component(usage='record.importer')
        return importer.run(external_id)
    
    # TODO: Uncomment when queue_job is installed
    # @job(default_channel='root.sap')
    # def _import_record_job(self, backend_record, external_id):
    #     """Import a single record as a job"""
    #     with backend_record.work_on(self.model._name) as work:
    #         importer = work.component(usage='record.importer')
    #         return importer.run(external_id)


# ===== Partner Importers =====

class SapPartnerImporter(Component):
    """Importer for SAP Business Partners"""
    _name = 'sap.partner.importer'
    _inherit = 'sap.importer'
    _apply_on = 'sap.res.partner'
    
    def _import_dependencies(self):
        """Import partner dependencies (country, state, etc.)"""
        # Countries and states should already exist in Odoo
        pass


class SapPartnerBatchImporter(Component):
    """Batch Importer for SAP Business Partners"""
    _name = 'sap.partner.batch.importer'
    _inherit = 'sap.batch.importer'
    _apply_on = 'sap.res.partner'
    
    def _get_external_id(self, record):
        return record.get('CardCode')


# ===== Product Importers =====

class SapProductImporter(Component):
    """Importer for SAP Items"""
    _name = 'sap.product.importer'
    _inherit = 'sap.importer'
    _apply_on = 'sap.product.product'
    
    def _import_dependencies(self):
        """Import product dependencies (UoM, category, etc.)"""
        # UoM and categories should be handled separately
        pass


class SapProductBatchImporter(Component):
    """Batch Importer for SAP Items"""
    _name = 'sap.product.batch.importer'
    _inherit = 'sap.batch.importer'
    _apply_on = 'sap.product.product'
    
    def _get_external_id(self, record):
        return record.get('ItemCode')


# ===== Sale Order Importers =====

class SapSaleOrderImporter(Component):
    """Importer for SAP Orders"""
    _name = 'sap.sale.order.importer'
    _inherit = 'sap.importer'
    _apply_on = 'sap.sale.order'
    
    def _import_dependencies(self):
        """Import order dependencies (partner, products)"""
        # Partners and products should be imported first
        pass
    
    def _after_import(self, binding):
        """After importing the order, import order lines"""
        # Order lines are already included in the order data
        pass


class SapSaleOrderBatchImporter(Component):
    """Batch Importer for SAP Orders"""
    _name = 'sap.sale.order.batch.importer'
    _inherit = 'sap.batch.importer'
    _apply_on = 'sap.sale.order'
    
    def _get_external_id(self, record):
        return record.get('DocEntry')


# ===== Invoice Importers =====

class SapInvoiceImporter(Component):
    """Importer for SAP Invoices"""
    _name = 'sap.invoice.importer'
    _inherit = 'sap.importer'
    _apply_on = 'sap.account.move'
    
    def _import_dependencies(self):
        """Import invoice dependencies"""
        pass


class SapInvoiceBatchImporter(Component):
    """Batch Importer for SAP Invoices"""
    _name = 'sap.invoice.batch.importer'
    _inherit = 'sap.batch.importer'
    _apply_on = 'sap.account.move'
    
    def _get_external_id(self, record):
        return record.get('DocEntry')

