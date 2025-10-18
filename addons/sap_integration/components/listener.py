# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Event Listeners

These listeners automatically trigger synchronization when records are created/updated
"""

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
import logging

_logger = logging.getLogger(__name__)


class SapBindingListener(Component):
    """Listen to binding record events"""
    _name = 'sap.binding.listener'
    _inherit = 'base.event.listener'
    
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        """Export record when created"""
        # TODO: Uncomment when queue_job is installed
        # record.with_delay().export_record()
        # For now, export directly
        _logger.info(f"New binding created: {record._name} [{record.id}]")
    
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """Export record when updated"""
        # TODO: Uncomment when queue_job is installed
        # record.with_delay().export_record(fields=fields)
        _logger.info(f"Binding updated: {record._name} [{record.id}]")
    
    def no_connector_export(self, record):
        """Check if export should be skipped"""
        return record.env.context.get('connector_no_export', False)


class SapPartnerListener(Component):
    """Listen to partner events for automatic export"""
    _name = 'sap.res.partner.listener'
    _inherit = 'sap.binding.listener'
    _apply_on = ['sap.res.partner']


class SapProductListener(Component):
    """Listen to product events for automatic export"""
    _name = 'sap.product.product.listener'
    _inherit = 'sap.binding.listener'
    _apply_on = ['sap.product.product']


class SapSaleOrderListener(Component):
    """Listen to sale order events for automatic export"""
    _name = 'sap.sale.order.listener'
    _inherit = 'sap.binding.listener'
    _apply_on = ['sap.sale.order']
    
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """Export order only if it's confirmed"""
        if record.state in ['sale', 'done']:
            _logger.info(f"Sale order confirmed, ready for export: {record.name}")
            # TODO: Uncomment when queue_job is installed
            # record.with_delay().export_record(fields=fields)


class SapInvoiceListener(Component):
    """Listen to invoice events for automatic export"""
    _name = 'sap.account.move.listener'
    _inherit = 'sap.binding.listener'
    _apply_on = ['sap.account.move']
    
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """Export invoice only if it's posted"""
        if record.state == 'posted':
            _logger.info(f"Invoice posted, ready for export: {record.name}")
            # TODO: Uncomment when queue_job is installed
            # record.with_delay().export_record(fields=fields)


# ===== Odoo Model Listeners (Auto-create bindings) =====

class ResPartnerListener(Component):
    """Listen to res.partner events to create bindings"""
    _name = 'res.partner.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner']
    
    def on_record_create(self, record, fields=None):
        """Create SAP binding when partner is created"""
        # Check if auto-export is enabled in any active backend
        backends = self.env['sap.backend'].search([
            ('active', '=', True),
            ('auto_export_partners', '=', True)
        ])
        
        for backend in backends:
            try:
                # Check if binding already exists
                existing = self.env['sap.res.partner'].search([
                    ('odoo_id', '=', record.id),
                    ('backend_id', '=', backend.id),
                ])
                
                if not existing:
                    binding = self.env['sap.res.partner'].create({
                        'odoo_id': record.id,
                        'backend_id': backend.id,
                    })
                    _logger.info(f"Auto-created SAP binding for partner: {record.name} on backend {backend.name}")
                    
                    # Export immediately if not using queue_job
                    binding.export_record()
            except Exception as e:
                _logger.error(f"Error auto-creating partner binding: {str(e)}")
    
    def on_record_write(self, record, fields=None):
        """Update SAP when partner is updated"""
        # Find existing bindings with auto-export enabled
        bindings = self.env['sap.res.partner'].search([
            ('odoo_id', '=', record.id),
            ('backend_id.active', '=', True),
            ('backend_id.auto_export_partners', '=', True)
        ])
        
        for binding in bindings:
            try:
                if binding.external_id:  # Only update if already exported
                    _logger.info(f"Auto-updating partner {record.name} to SAP backend {binding.backend_id.name}")
                    binding.export_record()
            except Exception as e:
                _logger.error(f"Error auto-updating partner binding: {str(e)}")


class ProductProductListener(Component):
    """Listen to product.product events to create bindings"""
    _name = 'product.product.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.product']
    
    def on_record_create(self, record, fields=None):
        """Create SAP binding when product is created"""
        # Check if auto-export is enabled in any active backend
        backends = self.env['sap.backend'].search([
            ('active', '=', True),
            ('auto_export_products', '=', True)
        ])
        
        for backend in backends:
            try:
                # Check if binding already exists
                existing = self.env['sap.product.product'].search([
                    ('odoo_id', '=', record.id),
                    ('backend_id', '=', backend.id),
                ])
                
                if not existing:
                    binding = self.env['sap.product.product'].create({
                        'odoo_id': record.id,
                        'backend_id': backend.id,
                    })
                    _logger.info(f"Auto-created SAP binding for product: {record.name} on backend {backend.name}")
                    
                    # Export immediately if not using queue_job
                    binding.export_record()
            except Exception as e:
                _logger.error(f"Error auto-creating product binding: {str(e)}")
    
    def on_record_write(self, record, fields=None):
        """Update SAP when product is updated"""
        # Find existing bindings with auto-export enabled
        bindings = self.env['sap.product.product'].search([
            ('odoo_id', '=', record.id),
            ('backend_id.active', '=', True),
            ('backend_id.auto_export_products', '=', True)
        ])
        
        for binding in bindings:
            try:
                if binding.external_id:  # Only update if already exported
                    _logger.info(f"Auto-updating product {record.name} to SAP backend {binding.backend_id.name}")
                    binding.export_record()
            except Exception as e:
                _logger.error(f"Error auto-updating product binding: {str(e)}")


class SaleOrderListener(Component):
    """Listen to sale.order events to create bindings"""
    _name = 'sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']
    
    def on_record_write(self, record, fields=None):
        """Create SAP binding when order is confirmed"""
        # Auto-create binding when order is confirmed and auto-export is enabled
        if record.state in ['sale', 'done']:
            backends = self.env['sap.backend'].search([
                ('active', '=', True),
                ('auto_export_orders', '=', True)
            ])
            
            for backend in backends:
                try:
                    # Check if binding already exists
                    existing = self.env['sap.sale.order'].search([
                        ('odoo_id', '=', record.id),
                        ('backend_id', '=', backend.id),
                    ])
                    
                    if not existing:
                        binding = self.env['sap.sale.order'].create({
                            'odoo_id': record.id,
                            'backend_id': backend.id,
                        })
                        _logger.info(f"Auto-created SAP binding for sale order: {record.name} on backend {backend.name}")
                        
                        # Export immediately if not using queue_job
                        binding.export_record()
                    elif existing.external_id:
                        # Update existing export
                        _logger.info(f"Auto-updating sale order {record.name} to SAP backend {backend.name}")
                        existing.export_record()
                except Exception as e:
                    _logger.error(f"Error auto-exporting sale order: {str(e)}")

