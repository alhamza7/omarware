# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapConnector(models.Model):
    _name = 'sap.connector'
    _description = 'SAP Connector'
    _order = 'name'
    
    name = fields.Char('Name', required=True, help="Name of the SAP connector")
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True, 
                                help="SAP backend configuration")
    active = fields.Boolean('Active', default=True, help="Whether this connector is active")
    
    # Sync options
    sync_customers = fields.Boolean('Sync Customers', default=True)
    sync_products = fields.Boolean('Sync Products', default=True)
    sync_quotations = fields.Boolean('Sync Quotations', default=True)
    sync_sales = fields.Boolean('Sync Sales Orders', default=True)
    sync_invoices = fields.Boolean('Sync Invoices', default=True)
    
    # Sync settings
    auto_sync = fields.Boolean('Auto Sync', default=False, 
                              help="Enable automatic synchronization")
    sync_frequency = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], 'Sync Frequency', default='daily')
    
    # Statistics
    last_sync = fields.Datetime('Last Sync', readonly=True)
    sync_status = fields.Selection([
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], 'Sync Status', default='idle', readonly=True)
    
    # Counters
    customers_synced = fields.Integer('Customers Synced', readonly=True, default=0)
    products_synced = fields.Integer('Products Synced', readonly=True, default=0)
    quotations_synced = fields.Integer('Quotations Synced', readonly=True, default=0)
    sales_synced = fields.Integer('Sales Orders Synced', readonly=True, default=0)
    invoices_synced = fields.Integer('Invoices Synced', readonly=True, default=0)
    
    error_message = fields.Text('Error Message', readonly=True)
    
    @api.model
    def create(self, vals_list):
        """Override create to set default name"""
        # Odoo 19: vals_list is always a list
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if not vals.get('name'):
                backend = self.env['sap.backend'].browse(vals.get('backend_id'))
                vals['name'] = f"Connector {backend.name}" if backend else "SAP Connector"
        
        return super(SapConnector, self).create(vals_list)
    
    def sync_all(self):
        """Sync all enabled data types"""
        if not self.active:
            raise UserError(f"Connector {self.name} is not active")
        
        if not self.backend_id.active:
            raise UserError(f"Backend {self.backend_id.name} is not active")
        
        try:
            self.sync_status = 'running'
            self.error_message = False
            
            # Reset counters
            self.customers_synced = 0
            self.products_synced = 0
            self.quotations_synced = 0
            self.sales_synced = 0
            self.invoices_synced = 0
            
            # Sync customers
            if self.sync_customers:
                self.sync_customers_from_sap()
            
            # Sync products
            if self.sync_products:
                self.sync_products_from_sap()
            
            # Sync quotations
            if self.sync_quotations:
                self.sync_quotations_from_sap()
            
            # Sync sales orders
            if self.sync_sales:
                self.sync_sales_from_sap()
            
            # Sync invoices
            if self.sync_invoices:
                self.sync_invoices_from_sap()
            
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Complete',
                    'message': f'All data synced successfully from {self.backend_id.name}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            _logger.error(f"Error in sync_all: {str(e)}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Error',
                    'message': f'Sync failed: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def sync_customers_from_sap(self):
        """Sync customers from SAP"""
        try:
            connection = self.backend_id.get_connection()
            customers = connection.get_customers(top=self.backend_id.batch_size)
            
            customer_count = 0
            for customer_data in customers.get('value', []):
                # Process customer data
                self._process_customer(customer_data)
                customer_count += 1
            
            self.customers_synced = customer_count
            _logger.info(f"Synced {customer_count} customers")
            
        except Exception as e:
            _logger.error(f"Error syncing customers: {str(e)}")
            raise
    
    def sync_products_from_sap(self):
        """Sync products from SAP"""
        try:
            connection = self.backend_id.get_connection()
            products = connection.get_products(top=self.backend_id.batch_size)
            
            product_count = 0
            for product_data in products.get('value', []):
                # Process product data
                self._process_product(product_data)
                product_count += 1
            
            self.products_synced = product_count
            _logger.info(f"Synced {product_count} products")
            
        except Exception as e:
            _logger.error(f"Error syncing products: {str(e)}")
            raise
    
    def sync_quotations_from_sap(self):
        """Sync quotations from SAP"""
        try:
            connection = self.backend_id.get_connection()
            quotations = connection.get_quotations(top=self.backend_id.batch_size)
            
            quotation_count = 0
            for quotation_data in quotations.get('value', []):
                # Process quotation data
                self._process_quotation(quotation_data)
                quotation_count += 1
            
            self.quotations_synced = quotation_count
            _logger.info(f"Synced {quotation_count} quotations")
            
        except Exception as e:
            _logger.error(f"Error syncing quotations: {str(e)}")
            raise
    
    def sync_sales_from_sap(self):
        """Sync sales orders from SAP"""
        try:
            connection = self.backend_id.get_connection()
            sales = connection.get_sales_orders(top=self.backend_id.batch_size)
            
            sale_count = 0
            for sale_data in sales.get('value', []):
                # Process sales order data
                self._process_sale(sale_data)
                sale_count += 1
            
            self.sales_synced = sale_count
            _logger.info(f"Synced {sale_count} sales orders")
            
        except Exception as e:
            _logger.error(f"Error syncing sales orders: {str(e)}")
            raise
    
    def sync_invoices_from_sap(self):
        """Sync invoices from SAP"""
        try:
            connection = self.backend_id.get_connection()
            invoices = connection.get_invoices(top=self.backend_id.batch_size)
            
            invoice_count = 0
            for invoice_data in invoices.get('value', []):
                # Process invoice data
                self._process_invoice(invoice_data)
                invoice_count += 1
            
            self.invoices_synced = invoice_count
            _logger.info(f"Synced {invoice_count} invoices")
            
        except Exception as e:
            _logger.error(f"Error syncing invoices: {str(e)}")
            raise
    
    def _process_customer(self, customer_data):
        """Process customer data from SAP"""
        # This will be implemented in the customer sync model
        pass
    
    def _process_product(self, product_data):
        """Process product data from SAP"""
        # This will be implemented in the product sync model
        pass
    
    def _process_quotation(self, quotation_data):
        """Process quotation data from SAP"""
        # This will be implemented in the quotation sync model
        pass
    
    def _process_sale(self, sale_data):
        """Process sales order data from SAP"""
        # This will be implemented in the sale sync model
        pass
    
    def _process_invoice(self, invoice_data):
        """Process invoice data from SAP"""
        # This will be implemented in the invoice sync model
        pass
    
    def get_sync_statistics(self):
        """Get synchronization statistics"""
        return {
            'customers_synced': self.customers_synced,
            'products_synced': self.products_synced,
            'quotations_synced': self.quotations_synced,
            'sales_synced': self.sales_synced,
            'invoices_synced': self.invoices_synced,
            'last_sync': self.last_sync,
            'sync_status': self.sync_status,
        }


