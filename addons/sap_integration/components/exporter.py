# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Exporters

These exporters synchronize data from Odoo to SAP
"""

from odoo import _
from odoo.addons.component.core import Component
# TODO: Uncomment when queue_job is installed
# from odoo.addons.queue_job.job import job
import logging

_logger = logging.getLogger(__name__)


class SapExporter(Component):
    """Base SAP Exporter"""
    _name = 'sap.exporter'
    _inherit = 'base.exporter'
    _usage = 'record.exporter'
    _collection = 'sap.backend'
    
    def _has_to_skip(self, binding):
        """Return True if the export should be skipped"""
        return False
    
    def _export_dependencies(self, binding):
        """Export dependencies before exporting the record"""
        pass
    
    def _map_data(self, binding):
        """Map Odoo data to external format"""
        mapper = self.component(usage='export.mapper')
        return mapper.map_record(binding).values()
    
    def _validate_data(self, data):
        """Validate the data before sending to SAP"""
        return data
    
    def _create_data(self, data):
        """Create the record in SAP"""
        adapter = self.component(usage='backend.adapter')
        external_data = adapter.create(data)
        return external_data
    
    def _update_data(self, external_id, data):
        """Update the record in SAP"""
        adapter = self.component(usage='backend.adapter')
        adapter.write(external_id, data)
    
    def _after_export(self, binding, external_id):
        """Hook after export"""
        pass
    
    def run(self, binding):
        """Run the export of a record to SAP"""
        if self._has_to_skip(binding):
            return
        
        # Export dependencies first
        self._export_dependencies(binding)
        
        # Map data
        data = self._map_data(binding)
        data = self._validate_data(data)
        
        # Create or update in SAP
        if binding.external_id:
            # Update existing record
            self._update_data(binding.external_id, data)
            external_id = binding.external_id
        else:
            # Create new record
            external_data = self._create_data(data)
            external_id = self._extract_external_id(external_data)
            
            # Bind the record
            binder = self.binder_for()
            binder.bind(external_id, binding)
        
        self._after_export(binding, external_id)
        
        return external_id
    
    def _extract_external_id(self, external_data):
        """Extract external ID from the response"""
        raise NotImplementedError


# ===== Partner Exporters =====

class SapPartnerExporter(Component):
    """Exporter for SAP Business Partners"""
    _name = 'sap.partner.exporter'
    _inherit = 'sap.exporter'
    _collection = 'sap.backend'
    _apply_on = 'sap.res.partner'
    
    def _extract_external_id(self, external_data):
        return external_data.get('CardCode')


# ===== Product Exporters =====

class SapProductExporter(Component):
    """Exporter for SAP Items"""
    _name = 'sap.product.exporter'
    _inherit = 'sap.exporter'
    _collection = 'sap.backend'
    _apply_on = 'sap.product.product'
    
    def _extract_external_id(self, external_data):
        return external_data.get('ItemCode')


# ===== Sale Order Exporters =====

class SapSaleOrderExporter(Component):
    """Exporter for SAP Orders"""
    _name = 'sap.sale.order.exporter'
    _inherit = 'sap.exporter'
    _collection = 'sap.backend'
    _apply_on = 'sap.sale.order'
    
    def _has_to_skip(self, binding):
        """Skip if order is not confirmed"""
        return binding.state not in ['sale', 'done']
    
    def _export_dependencies(self, binding):
        """Export partner and products before exporting order"""
        # Ensure partner is exported
        if hasattr(binding.partner_id, 'sap_bind_ids'):
            partner_bindings = binding.partner_id.sap_bind_ids.filtered(
                lambda b: b.backend_id == self.backend_record
            )
            if not partner_bindings or not partner_bindings[0].external_id:
                _logger.warning(f"Partner {binding.partner_id.name} not exported to SAP")
        
        # Ensure products are exported
        for line in binding.order_line:
            if hasattr(line.product_id, 'sap_bind_ids'):
                product_bindings = line.product_id.sap_bind_ids.filtered(
                    lambda b: b.backend_id == self.backend_record
                )
                if not product_bindings or not product_bindings[0].external_id:
                    _logger.warning(f"Product {line.product_id.name} not exported to SAP")
    
    def _extract_external_id(self, external_data):
        return external_data.get('DocEntry')
    
    def _after_export(self, binding, external_id):
        """Save DocNum after export"""
        # The external_data is not available here, so we need to read it
        try:
            adapter = self.component(usage='backend.adapter')
            sap_data = adapter.read(external_id)
            if sap_data and 'DocNum' in sap_data:
                binding.write({'sap_doc_num': sap_data['DocNum']})
        except Exception as e:
            _logger.warning(f"Could not retrieve DocNum: {str(e)}")


# ===== Invoice Exporters =====

class SapInvoiceExporter(Component):
    """Exporter for SAP Invoices"""
    _name = 'sap.invoice.exporter'
    _inherit = 'sap.exporter'
    _collection = 'sap.backend'
    _apply_on = 'sap.account.move'
    
    def _has_to_skip(self, binding):
        """Skip if invoice is not posted"""
        return binding.state != 'posted'
    
    def _extract_external_id(self, external_data):
        return external_data.get('DocEntry')

