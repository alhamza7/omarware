# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SapResPartner(models.Model):
    """Binding Model for SAP Business Partners (Customers/Suppliers)"""
    _name = 'sap.res.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'SAP Business Partner Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Odoo Partner',
        required=True,
        ondelete='cascade',
        index=True,
    )
    backend_id = fields.Many2one(
        comodel_name='sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True,
    )
    external_id = fields.Char(
        string='SAP CardCode',
        required=True,
        index=True,
    )
    
    # SAP specific fields
    sap_card_name = fields.Char('SAP Card Name')
    sap_card_type = fields.Selection([
        ('cCustomer', 'Customer'),
        ('cSupplier', 'Supplier'),
        ('cLid', 'Lead'),
    ], string='SAP Card Type', default='cCustomer')
    
    # Sync tracking
    sync_date = fields.Datetime('Last Sync Date', readonly=True)
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    # Constraints
    _sql_constraints = [
        ('sap_partner_uniq', 'UNIQUE(backend_id, external_id)',
         'A partner with the same SAP CardCode already exists for this backend.'),
    ]
    
    @api.model
    def import_batch(self, backend, filters=None):
        """Import SAP Business Partners in batch"""
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Starting batch import of partners from SAP backend {backend.name}")
            
            with backend.work_on(self._name) as work:
                importer = work.component(usage='batch.importer')
                result = importer.run(filters=filters)
                
            _logger.info(f"Batch import completed: {result.get('imported', 0)} imported, {result.get('errors', 0)} errors")
            return result
            
        except Exception as e:
            _logger.error(f"Error in batch import for {self._name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'imported': 0,
                'errors': 1
            }
    
    def import_record(self, backend, external_id):
        """Import a single SAP Business Partner"""
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Importing partner {external_id} from SAP backend {backend.name}")
            
            with backend.work_on(self._name) as work:
                importer = work.component(usage='record.importer')
                binding = importer.run(external_id)
                
            _logger.info(f"Partner {external_id} imported successfully")
            return binding
            
        except Exception as e:
            _logger.error(f"Error importing partner {external_id}: {str(e)}", exc_info=True)
            raise
    
    def export_record(self, fields=None):
        """Export this partner to SAP"""
        self.ensure_one()
        
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Exporting partner {self.odoo_id.name} (ID: {self.id}) to SAP backend {self.backend_id.name}")
            
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='record.exporter')
                result = exporter.run(self, fields=fields)
                
            _logger.info(f"Partner exported successfully to SAP with CardCode: {self.external_id}")
            return result
            
        except Exception as e:
            _logger.error(f"Error exporting partner {self.id}: {str(e)}", exc_info=True)
            # Store error for later retry
            self.write({
                'sync_error': str(e),
                'sync_retry_count': self.sync_retry_count + 1
            })
            raise


class SapProductProduct(models.Model):
    """Binding Model for SAP Items (Products)"""
    _name = 'sap.product.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'product.product': 'odoo_id'}
    _description = 'SAP Product Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Odoo Product',
        required=True,
        ondelete='cascade',
        index=True,
    )
    backend_id = fields.Many2one(
        comodel_name='sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True,
    )
    external_id = fields.Char(
        string='SAP ItemCode',
        required=True,
        index=True,
    )
    
    # SAP specific fields
    sap_item_name = fields.Char('SAP Item Name')
    sap_item_type = fields.Selection([
        ('itItems', 'Item'),
        ('itService', 'Service'),
    ], string='SAP Item Type', default='itItems')
    sap_items_group_code = fields.Integer('SAP Items Group Code')
    
    # Sync tracking
    sync_date = fields.Datetime('Last Sync Date', readonly=True)
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_product_uniq', 'UNIQUE(backend_id, external_id)',
         'A product with the same SAP ItemCode already exists for this backend.'),
    ]
    
    @api.model
    def import_batch(self, backend, filters=None):
        """Import SAP Items in batch"""
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Starting batch import of products from SAP backend {backend.name}")
            
            with backend.work_on(self._name) as work:
                importer = work.component(usage='batch.importer')
                result = importer.run(filters=filters)
                
            _logger.info(f"Batch import completed: {result.get('imported', 0)} imported, {result.get('errors', 0)} errors")
            return result
            
        except Exception as e:
            _logger.error(f"Error in batch import for {self._name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'imported': 0,
                'errors': 1
            }
    
    def import_record(self, backend, external_id):
        """Import a single SAP Item"""
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Importing product {external_id} from SAP backend {backend.name}")
            
            with backend.work_on(self._name) as work:
                importer = work.component(usage='record.importer')
                binding = importer.run(external_id)
                
            _logger.info(f"Product {external_id} imported successfully")
            return binding
            
        except Exception as e:
            _logger.error(f"Error importing product {external_id}: {str(e)}", exc_info=True)
            raise
    
    def export_record(self, fields=None):
        """Export this product to SAP"""
        self.ensure_one()
        
        try:
            from odoo.addons.component.core import WorkContext
            
            _logger.info(f"Exporting product {self.odoo_id.name} (ID: {self.id}) to SAP backend {self.backend_id.name}")
            
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='record.exporter')
                result = exporter.run(self, fields=fields)
                
            _logger.info(f"Product exported successfully to SAP with ItemCode: {self.external_id}")
            return result
            
        except Exception as e:
            _logger.error(f"Error exporting product {self.id}: {str(e)}", exc_info=True)
            # Store error for later retry
            self.write({
                'sync_error': str(e),
                'sync_retry_count': self.sync_retry_count + 1
            })
            raise


class SapSaleOrder(models.Model):
    """Binding Model for SAP Orders/Quotations"""
    _name = 'sap.sale.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'SAP Sale Order Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Odoo Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    backend_id = fields.Many2one(
        comodel_name='sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True,
    )
    external_id = fields.Char(
        string='SAP DocEntry',
        required=True,
        index=True,
    )
    
    # SAP specific fields
    sap_doc_num = fields.Char('SAP DocNum')
    sap_doc_type = fields.Selection([
        ('quotation', 'Quotation'),
        ('order', 'Order'),
    ], string='SAP Document Type', default='order')
    
    # Sync tracking
    sync_date = fields.Datetime('Last Sync Date', readonly=True)
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_order_uniq', 'UNIQUE(backend_id, external_id)',
         'A sale order with the same SAP DocEntry already exists for this backend.'),
    ]


class SapAccountMove(models.Model):
    """Binding Model for SAP Invoices"""
    _name = 'sap.account.move'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'account.move': 'odoo_id'}
    _description = 'SAP Invoice Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='account.move',
        string='Odoo Invoice',
        required=True,
        ondelete='cascade',
        index=True,
    )
    backend_id = fields.Many2one(
        comodel_name='sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True,
    )
    external_id = fields.Char(
        string='SAP DocEntry',
        required=True,
        index=True,
    )
    
    # SAP specific fields
    sap_doc_num = fields.Char('SAP DocNum')
    
    # Sync tracking
    sync_date = fields.Datetime('Last Sync Date', readonly=True)
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_invoice_uniq', 'UNIQUE(backend_id, external_id)',
         'An invoice with the same SAP DocEntry already exists for this backend.'),
    ]

