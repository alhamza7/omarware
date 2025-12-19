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
    sync_suppliers = fields.Boolean('Sync Suppliers', default=True)
    sync_products = fields.Boolean('Sync Products', default=True)
    sync_pricelists = fields.Boolean('Sync Pricelists', default=False,
                                     help="Sync pricelists after products (like in complete migration)")
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
    suppliers_synced = fields.Integer('Suppliers Synced', readonly=True, default=0)
    products_synced = fields.Integer('Products Synced', readonly=True, default=0)
    pricelists_synced = fields.Integer('Pricelists Synced', readonly=True, default=0)
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
            self.suppliers_synced = 0
            self.products_synced = 0
            self.pricelists_synced = 0
            self.quotations_synced = 0
            self.sales_synced = 0
            self.invoices_synced = 0
            
            # Sync customers
            if self.sync_customers:
                self.sync_customers_from_sap()
            
            # Sync suppliers
            if self.sync_suppliers:
                self.sync_suppliers_from_sap()
            
            # Sync products
            if self.sync_products:
                self.sync_products_from_sap()
            
            # Sync pricelists (after products, like in complete migration)
            if self.sync_pricelists:
                self.sync_pricelists_from_sap()
            
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
        """Sync customers from SAP with pagination"""
        try:
            connection = self.backend_id.get_connection()
            customer_model = self.env['sap.customer.sync']
            
            # Initialize pagination
            skip = 0
            customer_count = 0
            has_more = True
            batch_size = self.backend_id.batch_size or 100
            
            _logger.info(f"Starting customer sync from SAP (batch_size: {batch_size})")
            
            while has_more:
                # Build query parameters with pagination
                # جلب Business Partners التي تبدأ بـ IBG أو OBG بغض النظر عن CardType
                filter_query = "(startswith(CardCode, 'IBG') or startswith(CardCode, 'OBG'))"
                
                params = {
                    '$top': batch_size,
                    '$skip': skip,
                    '$filter': filter_query,
                    '$orderby': 'CardCode'
                }
                
                _logger.info(f"Using filter: {filter_query}")
                
                # Fetch batch
                _logger.info(f"Fetching customers batch: skip={skip}, top={batch_size}")
                customers_data = connection.get('BusinessPartners', params)
                batch = customers_data.get('value', [])
                
                if not batch:
                    _logger.info("No more customers to fetch")
                    has_more = False
                    break
                
                # Process each customer in batch
                for customer_data in batch:
                    try:
                        card_code = customer_data.get('CardCode')
                        card_name = customer_data.get('CardName', 'Unknown')
                        _logger.info(f"Processing customer: {card_code} - {card_name}")
                        
                        # Use customer model import method
                        result = customer_model.import_record(self.backend_id, card_code)
                        if result:
                            customer_count += 1
                        
                    except Exception as e:
                        _logger.error(f"Error processing customer {customer_data.get('CardCode', 'Unknown')}: {str(e)}")
                        # Rollback the failed transaction
                        self.env.cr.rollback()
                        continue
                
                # Update skip for next batch
                skip += len(batch)
                
                # Check if there are more records
                # التوقف فقط إذا كان الـ batch فارغ أو عدد السجلات = 0
                if len(batch) == 0:
                    has_more = False
                    _logger.info(f"No more records to fetch")
                
                # Commit batch to avoid memory issues
                self.env.cr.commit()
            
            self.customers_synced = customer_count
            _logger.info(f"Customer sync completed: {customer_count} customers synced")
            
        except Exception as e:
            _logger.error(f"Error syncing customers: {str(e)}")
            raise
    
    def sync_suppliers_from_sap(self):
        """Sync suppliers from SAP with pagination"""
        try:
            connection = self.backend_id.get_connection()
            supplier_model = self.env['sap.customer.sync']  # نستخدم نفس الـ model لأنهم business partners
            
            # Initialize pagination
            skip = 0
            supplier_count = 0
            has_more = True
            batch_size = self.backend_id.batch_size or 100
            
            _logger.info(f"Starting supplier sync from SAP (batch_size: {batch_size})")
            
            while has_more:
                # Build query parameters with pagination
                params = {
                    '$top': batch_size,
                    '$skip': skip,
                    '$filter': "CardType eq 'S'",  # Supplier type
                    '$orderby': 'CardCode'
                }
                
                # Fetch batch
                _logger.info(f"Fetching suppliers batch: skip={skip}, top={batch_size}")
                suppliers_data = connection.get('BusinessPartners', params)
                batch = suppliers_data.get('value', [])
                
                if not batch:
                    _logger.info("No more suppliers to fetch")
                    has_more = False
                    break
                
                # Process each supplier in batch
                for supplier_data in batch:
                    try:
                        card_code = supplier_data.get('CardCode')
                        card_name = supplier_data.get('CardName', 'Unknown')
                        _logger.info(f"Processing supplier: {card_code} - {card_name}")
                        
                        # Use customer model import method (works for suppliers too)
                        result = supplier_model.import_record(self.backend_id, card_code)
                        if result:
                            supplier_count += 1
                        
                    except Exception as e:
                        _logger.error(f"Error processing supplier {supplier_data.get('CardCode', 'Unknown')}: {str(e)}")
                        # Rollback the failed transaction
                        self.env.cr.rollback()
                        continue
                
                # Update skip for next batch
                skip += len(batch)
                
                # Check if there are more records
                # التوقف فقط إذا كان الـ batch فارغ أو عدد السجلات = 0
                if len(batch) == 0:
                    has_more = False
                    _logger.info(f"No more records to fetch")
                
                # Commit batch to avoid memory issues
                self.env.cr.commit()
            
            self.suppliers_synced = supplier_count
            _logger.info(f"Supplier sync completed: {supplier_count} suppliers synced")
            
        except Exception as e:
            _logger.error(f"Error syncing suppliers: {str(e)}")
            raise
    
    def sync_products_from_sap(self):
        """Sync products from SAP with pagination"""
        try:
            connection = self.backend_id.get_connection()
            product_model = self.env['sap.product.sync']
            
            # Initialize pagination
            skip = 0
            product_count = 0
            has_more = True
            batch_size = self.backend_id.batch_size or 100
            processed_item_codes = set()  # Track processed items to prevent duplicates
            
            _logger.info(f"Starting product sync from SAP (batch_size: {batch_size})")
            
            while has_more:
                # Build query parameters with pagination
                params = {
                    '$top': batch_size,
                    '$skip': skip,
                    '$orderby': 'ItemCode'
                }
                
                # Fetch batch
                _logger.info(f"Fetching products batch: skip={skip}, top={batch_size}")
                products_data = connection.get('Items', params)
                batch = products_data.get('value', [])
                
                if not batch:
                    _logger.info("No more products to fetch")
                    has_more = False
                    break
                
                # Process each product in batch
                for product_data in batch:
                    try:
                        item_code = product_data.get('ItemCode')
                        item_name = product_data.get('ItemName', 'Unknown')
                        
                        # Skip products without ItemCode to prevent duplicates
                        if not item_code or not str(item_code).strip():
                            _logger.warning(f"Skipping product without ItemCode: {item_name}")
                            continue
                        
                        # Normalize item_code (remove whitespace)
                        item_code = str(item_code).strip()
                        
                        # Check if this item was already processed in this sync session
                        if item_code in processed_item_codes:
                            _logger.warning(f"Duplicate ItemCode detected in batch: {item_code} - {item_name}. Skipping to prevent duplicate.")
                            continue
                        
                        processed_item_codes.add(item_code)
                        _logger.info(f"Processing product: {item_code} - {item_name}")
                        
                        # Use product model import method
                        result = product_model.import_record(self.backend_id, item_code)
                        if result:
                            product_count += 1
                        
                    except Exception as e:
                        _logger.error(f"Error processing product {product_data.get('ItemCode', 'Unknown')}: {str(e)}")
                        # Rollback the failed transaction
                        self.env.cr.rollback()
                        continue
                
                # Update skip for next batch
                skip += len(batch)
                
                # Check if there are more records
                # التوقف فقط إذا كان الـ batch فارغ أو عدد السجلات = 0
                if len(batch) == 0:
                    has_more = False
                    _logger.info(f"No more records to fetch")
                
                # Commit batch to avoid memory issues
                self.env.cr.commit()
            
            self.products_synced = product_count
            _logger.info(f"Product sync completed: {product_count} products synced")
            
        except Exception as e:
            _logger.error(f"Error syncing products: {str(e)}")
            raise
    
    def sync_pricelists_from_sap(self):
        """Sync pricelists from SAP (like in complete migration Stage 3)"""
        try:
            _logger.info("Starting pricelist sync from SAP")
            
            # Use the same method as complete migration
            pricelist_sync = self.env['sap.product.pricelist.sync']
            result = pricelist_sync.import_all_pricelists_from_sap(
                self.backend_id, 
                self.backend_id.batch_size or 100
            )
            
            # Update counter
            self.pricelists_synced = result.get('created_prices', 0) + result.get('updated_prices', 0)
            
            _logger.info(f"Pricelist sync completed: {result.get('created_prices', 0)} created, {result.get('updated_prices', 0)} updated")
            
        except Exception as e:
            _logger.error(f"Error syncing pricelists: {str(e)}")
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
    
    # NOTE: The following methods are no longer needed as we call
    # model-specific import methods directly in sync_customers_from_sap
    # and sync_products_from_sap above.
    #
    # If you need custom processing logic, override the import_record
    # methods in sap.customer.sync and sap.product.sync models instead.
    
    def get_sync_statistics(self):
        """Get synchronization statistics"""
        return {
            'customers_synced': self.customers_synced,
            'suppliers_synced': self.suppliers_synced,
            'products_synced': self.products_synced,
            'pricelists_synced': self.pricelists_synced,
            'quotations_synced': self.quotations_synced,
            'sales_synced': self.sales_synced,
            'invoices_synced': self.invoices_synced,
            'last_sync': self.last_sync,
            'sync_status': self.sync_status,
        }


