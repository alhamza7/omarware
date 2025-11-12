# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta
import logging

from ..config.sap_config import SYNC_CONFIG, ERROR_MESSAGES
from ..core.sap_logger import SapLogger, SapConnectionError

_logger = logging.getLogger(__name__)


class SapBackend(models.Model):
    """SAP Backend Configuration using OCA Connector Framework"""
    _name = 'sap.backend'
    _description = 'SAP Backend Configuration'
    _inherit = 'connector.backend'
    _backend_type = 'sap'
    _order = 'name'
    
    
    name = fields.Char('Name', required=True, help="Name of the SAP backend configuration")
    base_url = fields.Char('Service Layer URL', required=True, 
                          help="SAP Service Layer URL (e.g., https://sap-server.com:50000/b1s/v1)")
    username = fields.Char('Username', required=True, help="SAP username")
    password = fields.Char('Password', required=True, help="SAP password")
    company_db = fields.Char('Company Database', required=True, 
                            help="SAP company database name")
    active = fields.Boolean('Active', default=True, help="Whether this backend is active")
    verify_ssl = fields.Boolean('Verify SSL Certificate', default=False, 
                                help="Enable SSL certificate verification (disable for self-signed certificates)")
    last_connection = fields.Datetime('Last Connection', readonly=True)
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
    ], 'Connection Status', default='disconnected', readonly=True)
    error_message = fields.Text('Error Message', readonly=True)
    
    # Sync settings
    sync_customers = fields.Boolean('Sync Customers', default=True)
    sync_products = fields.Boolean('Sync Products', default=True)
    sync_quotations = fields.Boolean('Sync Quotations', default=True)
    sync_sales = fields.Boolean('Sync Sales Orders', default=True)
    sync_invoices = fields.Boolean('Sync Invoices', default=True)
    
    # Auto-sync settings (Event Listeners)
    auto_export_partners = fields.Boolean(
        'Auto Export Partners',
        default=False,
        help="Automatically export new/updated partners to SAP"
    )
    auto_export_products = fields.Boolean(
        'Auto Export Products',
        default=False,
        help="Automatically export new/updated products to SAP"
    )
    auto_export_orders = fields.Boolean(
        'Auto Export Orders',
        default=False,
        help="Automatically export confirmed sale orders to SAP"
    )
    auto_import_on_read = fields.Boolean(
        'Auto Import on Read',
        default=False,
        help="Automatically import from SAP when record not found in Odoo"
    )
    
    # Advanced settings
    batch_size = fields.Integer(
        'Batch Size', 
        default=SYNC_CONFIG['default_batch_size'],
        help="Number of records to process in each batch"
    )
    timeout = fields.Integer(
        'Timeout (seconds)', 
        default=SYNC_CONFIG['default_timeout'],
        help="Request timeout in seconds"
    )
    retry_attempts = fields.Integer(
        'Retry Attempts', 
        default=SYNC_CONFIG['default_retry_attempts'],
        help="Number of retry attempts on failure"
    )
    
    # Incremental Sync settings
    enable_incremental_sync = fields.Boolean(
        'Enable Incremental Sync',
        default=True,
        help="Only sync records modified since last sync"
    )
    last_partner_sync = fields.Datetime('Last Partner Sync')
    last_product_sync = fields.Datetime('Last Product Sync')
    last_order_sync = fields.Datetime('Last Order Sync')
    last_invoice_sync = fields.Datetime('Last Invoice Sync')
    incremental_sync_days = fields.Integer(
        'Incremental Sync Days',
        default=SYNC_CONFIG['incremental_sync_days'],
        help="Number of days to look back for incremental sync (fallback if no last sync)"
    )
    
    @api.model
    def create(self, vals_list):
        """Override create to test connection"""
        records = super(SapBackend, self).create(vals_list)
        for record in records:
            if record.active:
                record.test_connection()
        return records
    
    def write(self, vals):
        """Override write to test connection if URL or credentials changed"""
        result = super(SapBackend, self).write(vals)
        if any(field in vals for field in ['base_url', 'username', 'password', 'company_db', 'active']):
            if self.active:
                self.test_connection()
        return result
    
    def test_connection(self):
        """Test connection to SAP Service Layer"""
        try:
            from .sap_service_layer import SapServiceLayerConnection
            
            _logger.info(f"Testing connection to SAP backend: {self.name}")
            
            connection = SapServiceLayerConnection(
                self.base_url,
                self.username,
                self.password,
                self.company_db,
                verify_ssl=self.verify_ssl,
                timeout=self.timeout
            )
            
            if connection.test_connection():
                self.connection_status = 'connected'
                self.last_connection = fields.Datetime.now()
                self.error_message = False
                connection.close_session()
                
                # Log successful connection
                self.env['sap.sync.log'].log_success(
                    backend_id=self.id,
                    operation='Connection Test',
                    message=f'Successfully connected to {self.name}'
                )
                
                _logger.info(f"Connection to {self.name} successful")
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': f'Connection to {self.name} successful!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise SapConnectionError("Connection test failed")
                
        except Exception as e:
            self.connection_status = 'error'
            self.error_message = str(e)
            
            # Log connection error
            self.env['sap.sync.log'].log_error(
                backend_id=self.id,
                operation='Connection Test',
                message=f'Failed to connect to {self.name}: {str(e)}',
                error_type=type(e).__name__
            )
            
            _logger.error(f"SAP Backend connection error: {str(e)}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Error',
                    'message': f'Failed to connect to {self.name}: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def get_connection(self):
        """Get SAP Service Layer connection"""
        try:
            from .sap_service_layer import SapServiceLayerConnection
            
            if not self.active:
                raise UserError(f"Backend {self.name} is not active")
            
            if self.connection_status != 'connected':
                self.test_connection()
            
            return SapServiceLayerConnection(
                self.base_url,
                self.username,
                self.password,
                self.company_db
            )
        except Exception as e:
            _logger.error(f"Error getting SAP connection: {str(e)}")
            raise UserError(f"Failed to connect to SAP: {str(e)}")
    
    def sync_all_data(self):
        """Sync all data from SAP"""
        if not self.active:
            raise UserError(f"Backend {self.name} is not active")
        
        try:
            connection = self.get_connection()
            
            # Sync customers
            if self.sync_customers:
                self._sync_customers(connection)
            
            # Sync products
            if self.sync_products:
                self._sync_products(connection)
            
            # Sync quotations
            if self.sync_quotations:
                self._sync_quotations(connection)
            
            # Sync sales orders
            if self.sync_sales:
                self._sync_sales(connection)
            
            # Sync invoices
            if self.sync_invoices:
                self._sync_invoices(connection)
            
            connection.close_session()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Complete',
                    'message': f'All data synced successfully from {self.name}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error syncing all data: {str(e)}")
            raise UserError(f"Sync failed: {str(e)}")
    
    def _sync_customers(self, connection):
        """Sync customers from SAP"""
        try:
            customers = connection.get_customers(top=self.batch_size)
            _logger.info(f"Syncing {len(customers.get('value', []))} customers")
            # Implementation will be added in customer sync model
        except Exception as e:
            _logger.error(f"Error syncing customers: {str(e)}")
            raise
    
    def _sync_products(self, connection):
        """Sync products from SAP"""
        try:
            products = connection.get_products(top=self.batch_size)
            _logger.info(f"Syncing {len(products.get('value', []))} products")
            # Implementation will be added in product sync model
        except Exception as e:
            _logger.error(f"Error syncing products: {str(e)}")
            raise
    
    def _sync_quotations(self, connection):
        """Sync quotations from SAP"""
        try:
            quotations = connection.get_quotations(top=self.batch_size)
            _logger.info(f"Syncing {len(quotations.get('value', []))} quotations")
            # Implementation will be added in quotation sync model
        except Exception as e:
            _logger.error(f"Error syncing quotations: {str(e)}")
            raise
    
    def _sync_sales(self, connection):
        """Sync sales orders from SAP"""
        try:
            sales = connection.get_sales_orders(top=self.batch_size)
            _logger.info(f"Syncing {len(sales.get('value', []))} sales orders")
            # Implementation will be added in sale sync model
        except Exception as e:
            _logger.error(f"Error syncing sales orders: {str(e)}")
            raise
    
    def _sync_invoices(self, connection):
        """Sync invoices from SAP"""
        try:
            invoices = connection.get_invoices(top=self.batch_size)
            _logger.info(f"Syncing {len(invoices.get('value', []))} invoices")
            # Implementation will be added in invoice sync model
        except Exception as e:
            _logger.error(f"Error syncing invoices: {str(e)}")
            raise
    
    def sync_incremental_partners(self):
        """Incrementally sync partners modified since last sync"""
        self.ensure_one()
        
        if not self.enable_incremental_sync:
            raise UserError("Incremental sync is not enabled for this backend")
        
        # Calculate sync date
        if self.last_partner_sync:
            sync_date = self.last_partner_sync
        else:
            sync_date = fields.Datetime.now() - timedelta(days=self.incremental_sync_days)
        
        # Format date for OData filter
        date_str = sync_date.strftime('%Y-%m-%dT%H:%M:%S')
        filter_query = f"UpdateDate ge datetime'{date_str}'"
        
        _logger.info(f"Incremental sync for partners since {date_str}")
        
        # Perform sync
        result = self.env['sap.res.partner'].import_batch(self, filters=filter_query)
        
        # Update last sync date
        self.last_partner_sync = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Incremental Sync Complete',
                'message': f"Synced {result.get('imported', 0)} partners since {sync_date}",
                'type': 'success',
            }
        }
    
    def sync_incremental_products(self):
        """Incrementally sync products modified since last sync"""
        self.ensure_one()
        
        if not self.enable_incremental_sync:
            raise UserError("Incremental sync is not enabled for this backend")
        
        # Calculate sync date
        if self.last_product_sync:
            sync_date = self.last_product_sync
        else:
            sync_date = fields.Datetime.now() - timedelta(days=self.incremental_sync_days)
        
        # Format date for OData filter
        date_str = sync_date.strftime('%Y-%m-%dT%H:%M:%S')
        filter_query = f"UpdateDate ge datetime'{date_str}'"
        
        _logger.info(f"Incremental sync for products since {date_str}")
        
        # Perform sync
        result = self.env['sap.product.product'].import_batch(self, filters=filter_query)
        
        # Update last sync date
        self.last_product_sync = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Incremental Sync Complete',
                'message': f"Synced {result.get('imported', 0)} products since {sync_date}",
                'type': 'success',
            }
        }
    
    def sync_incremental_all(self):
        """Incrementally sync all entities"""
        self.ensure_one()
        
        results = {
            'partners': 0,
            'products': 0,
            'orders': 0,
        }
        
        try:
            # Sync partners
            if self.sync_customers:
                partner_result = self.sync_incremental_partners()
                results['partners'] = partner_result.get('params', {}).get('message', '').split()[1] if partner_result else 0
            
            # Sync products
            if self.sync_products:
                product_result = self.sync_incremental_products()
                results['products'] = product_result.get('params', {}).get('message', '').split()[1] if product_result else 0
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Incremental Sync Complete',
                    'message': f"Synced: {results['partners']} partners, {results['products']} products",
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in incremental sync: {str(e)}")
            raise UserError(f"Incremental sync failed: {str(e)}")
    
    def action_import_uom_groups(self):
        """Import all UoM Groups and UoMs from SAP"""
        self.ensure_one()
        
        if not self.active:
            raise UserError("Backend is not active")
        
        if self.connection_status != 'connected':
            raise UserError("Backend is not connected. Please test connection first.")
        
        try:
            # Import all UoMs and UoM Groups
            uom_sync = self.env['sap.uom.sync']
            result = uom_sync.import_all_uoms_from_sap(self)
            
            _logger.info(f"Imported {result} UoMs from {self.name}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'UoM Groups Imported Successfully! ✅',
                    'message': f'Successfully imported {result} Unit of Measures and UoM Groups from SAP',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error importing UoM groups: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Failed ❌',
                    'message': f'Failed to import UoM Groups: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    @api.model
    def get_invoice_types_from_sap(self):
        """Get invoice types from SAP User-Defined Fields
        
        Returns:
            list: List of tuples [(value, label), ...]
        """
        try:
            # Get active SAP backend
            backend = self.search([('active', '=', True)], limit=1)
            
            if not backend:
                _logger.warning("No active SAP backend found")
                return []
            
            # Get connection and fetch invoice types
            connection = backend.get_connection()
            invoice_types = connection.get_invoice_types()
            
            if invoice_types:
                _logger.info(f"Found {len(invoice_types)} invoice types from SAP: {invoice_types}")
                return invoice_types
            else:
                _logger.warning("No invoice types found in SAP, returning default values")
                # إرجاع قيم افتراضية إذا لم يتم العثور على أي شيء في SAP
                return [
                    ('retail', 'بيع تجزئة - Retail'),
                    ('wholesale', 'بيع جملة - Wholesale'),
                    ('delivery', 'توصيل - Delivery'),
                    ('corporate', 'شركات - Corporate'),
                    ('individual', 'أفراد - Individual'),
                ]
                
        except Exception as e:
            _logger.error(f"Error fetching invoice types from SAP: {str(e)}", exc_info=True)
            # إرجاع قيم افتراضية في حالة الخطأ
            return [
                ('retail', 'بيع تجزئة - Retail'),
                ('wholesale', 'بيع جملة - Wholesale'),
                ('delivery', 'توصيل - Delivery'),
                ('corporate', 'شركات - Corporate'),
                ('individual', 'أفراد - Individual'),
            ]


