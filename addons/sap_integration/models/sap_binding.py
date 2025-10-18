# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SapResPartner(models.Model):
    """Binding Model for SAP Business Partners (Customers/Suppliers)"""
    _name = 'sap.res.partner'
    _inherit = 'external.binding'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'SAP Business Partner Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
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
        index=True,
    )
    
    # SAP specific fields
    sap_card_name = fields.Char('SAP Card Name')
    sap_card_type = fields.Selection([
        ('cCustomer', 'Customer'),
        ('cSupplier', 'Supplier'),
        ('cLid', 'Lead'),
    ], string='SAP Card Type', default='cCustomer')
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_partner_uniq', 'unique(backend_id, external_id)',
         'A partner with the same SAP CardCode already exists for this backend.'),
    ]
    
    @api.model
    def import_batch(self, backend, filters=None):
        """Import SAP Business Partners in batch"""
        # TODO: Implement with @job decorator when queue_job is available
        # @job(default_channel='root.sap')
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)
    
    def import_record(self, backend, external_id):
        """Import a single SAP Business Partner"""
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id)
    
    def export_record(self, fields=None):
        """Export this partner to SAP"""
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)


class SapProductProduct(models.Model):
    """Binding Model for SAP Items (Products)"""
    _name = 'sap.product.product'
    _inherit = 'external.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'SAP Product Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
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
        index=True,
    )
    
    # SAP specific fields
    sap_item_name = fields.Char('SAP Item Name')
    sap_item_type = fields.Selection([
        ('itItems', 'Item'),
        ('itService', 'Service'),
    ], string='SAP Item Type', default='itItems')
    sap_items_group_code = fields.Integer('SAP Items Group Code')
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_product_uniq', 'unique(backend_id, external_id)',
         'A product with the same SAP ItemCode already exists for this backend.'),
    ]
    
    @api.model
    def import_batch(self, backend, filters=None):
        """Import SAP Items in batch"""
        # TODO: Implement with @job decorator when queue_job is available
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)
    
    def import_record(self, backend, external_id):
        """Import a single SAP Item"""
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id)
    
    def export_record(self, fields=None):
        """Export this product to SAP"""
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)


class SapSaleOrder(models.Model):
    """Binding Model for SAP Orders/Quotations"""
    _name = 'sap.sale.order'
    _inherit = 'external.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'SAP Sale Order Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
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
        index=True,
    )
    
    # SAP specific fields
    sap_doc_num = fields.Char('SAP DocNum')
    sap_doc_type = fields.Selection([
        ('quotation', 'Quotation'),
        ('order', 'Order'),
    ], string='SAP Document Type', default='order')
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_order_uniq', 'unique(backend_id, external_id)',
         'A sale order with the same SAP DocEntry already exists for this backend.'),
    ]


class SapAccountMove(models.Model):
    """Binding Model for SAP Invoices"""
    _name = 'sap.account.move'
    _inherit = 'external.binding'
    _inherits = {'account.move': 'odoo_id'}
    _description = 'SAP Invoice Binding'
    
    # Required fields for binding
    odoo_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice',
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
        index=True,
    )
    
    # SAP specific fields
    sap_doc_num = fields.Char('SAP DocNum')
    
    # Error handling
    sync_error = fields.Text('Synchronization Error', readonly=True)
    sync_retry_count = fields.Integer('Retry Count', default=0)
    
    _sql_constraints = [
        ('sap_invoice_uniq', 'unique(backend_id, external_id)',
         'An invoice with the same SAP DocEntry already exists for this backend.'),
    ]

