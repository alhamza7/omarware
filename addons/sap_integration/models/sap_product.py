# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapProductSync(models.Model):
    _name = 'sap.product.sync'
    _description = 'SAP Product Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_product_id = fields.Many2one('product.product', 'Odoo Product')
    sap_product_id = fields.Char('SAP Product ID', required=True)
    sap_product_name = fields.Char('SAP Product Name')
    
    # Sync information
    last_sync = fields.Datetime('Last Sync', readonly=True)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], 'Sync Status', default='pending', readonly=True)
    sync_direction = fields.Selection([
        ('sap_to_odoo', 'SAP to Odoo'),
        ('odoo_to_sap', 'Odoo to SAP'),
        ('bidirectional', 'Bidirectional'),
    ], 'Sync Direction', default='sap_to_odoo')
    
    # Error handling
    error_message = fields.Text('Error Message', readonly=True)
    retry_count = fields.Integer('Retry Count', default=0)
    max_retries = fields.Integer('Max Retries', default=3)
    
    # Data mapping
    sap_data = fields.Text('SAP Data (JSON)', help="Raw data from SAP")
    odoo_data = fields.Text('Odoo Data (JSON)', help="Raw data from Odoo")
    
    @api.model
    def create(self, vals):
        """Override create to set default values"""
        if not vals.get('backend_id') and vals.get('connector_id'):
            vals['backend_id'] = self.env['sap.connector'].browse(vals['connector_id']).backend_id.id
        return super(SapProductSync, self).create(vals)
    
    def sync_from_sap(self):
        """Sync product from SAP to Odoo"""
        try:
            connection = self.backend_id.get_connection()
            
            # Get product data from SAP
            products = connection.get('Items', {
                '$filter': f"ItemCode eq '{self.sap_product_id}'"
            })
            
            if not products.get('value'):
                raise UserError(f"Product {self.sap_product_id} not found in SAP")
            
            product_data = products['value'][0]
            self.sap_data = str(product_data)
            
            # Process product data
            product = self._process_product_data(product_data)
            
            self.odoo_product_id = product.id
            self.sap_product_name = product_data.get('ItemName', '')
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced product {self.sap_product_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing product {self.sap_product_id}: {str(e)}")
            raise
    
    def sync_to_sap(self):
        """Sync product from Odoo to SAP"""
        try:
            if not self.odoo_product_id:
                raise UserError("No Odoo product linked to this sync record")
            
            connection = self.backend_id.get_connection()
            
            # Prepare product data for SAP
            product_data = self._prepare_product_data_for_sap()
            self.sap_data = str(product_data)
            
            # Create or update product in SAP
            if self.sap_product_id:
                # Update existing product
                result = connection.update_product(self.sap_product_id, product_data)
            else:
                # Create new product
                result = connection.create_product(product_data)
                if result:
                    self.sap_product_id = result.get('ItemCode')
            
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced product to SAP: {self.sap_product_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing product to SAP: {str(e)}")
            raise
    
    # Fields that must NOT be updated on existing products because Odoo blocks
    # changing them once the product has been used in transactions (stock moves,
    # sale/purchase order lines, POS lines, etc.).
    _SAP_READONLY_ON_UPDATE = frozenset({'uom_id', 'uom_po_id'})

    def _process_product_data(self, product_data):
        """Process product data from SAP and create/update Odoo product.

        On creation: all mapped fields including uom_id are applied.
        On update: uom_id is intentionally skipped to avoid Odoo's
        'Invalid Operation' error when the product already has transactions
        with a different unit of measure.
        """
        try:
            product_vals = self._map_sap_to_odoo(product_data)

            product = self.env['product.product'].search([
                ('default_code', '=', product_data['ItemCode'])
            ], limit=1)

            if product:
                # Strip UoM fields - changing them on an existing product that
                # already has stock moves / order lines raises a hard Odoo error.
                safe_vals = {k: v for k, v in product_vals.items()
                             if k not in self._SAP_READONLY_ON_UPDATE}
                product.write(safe_vals)
                _logger.info(f"Updated existing product: {product.name} (uom_id preserved)")
            else:
                product = self.env['product.product'].create(product_vals)
                _logger.info(f"Created new product: {product.name} (uom_id={product_vals.get('uom_id')})")

            return product

        except Exception as e:
            _logger.error(f"Error processing product data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP product data to Odoo product format"""
        return {
            'name': sap_data.get('ItemName', ''),
            'default_code': sap_data.get('ItemCode', ''),
            'list_price': sap_data.get('SalesUnitPrice', 0.0),
            'standard_price': sap_data.get('PurchaseUnitPrice', 0.0),
            'sale_ok': True,
            'purchase_ok': True,
            'available_in_pos': True,  # Make product available in Point of Sale
            'type': 'consu',  # Consumable = Storable products (displayed as "Goods" in UI)
            'tracking': 'none',  # Enable inventory tracking
            'is_storable': True,  # Enable "Track Inventory" checkbox in UI
            'categ_id': self._get_product_category(sap_data.get('ItemsGroupCode', '')),
            'uom_id': self._get_uom_id(sap_data.get('SalesUnit', '')),
            # Note: uom_po_id removed in Odoo 19.0
            'description': sap_data.get('UserText', ''),
            'description_sale': sap_data.get('UserText', ''),
            'description_purchase': sap_data.get('UserText', ''),
            'active': sap_data.get('Valid', 'Y') == 'Y',
        }
    
    def _prepare_product_data_for_sap(self):
        """Prepare Odoo product data for SAP format"""
        product = self.odoo_product_id
        return {
            'ItemName': product.name,
            'ItemCode': product.default_code or '',
            'SalesUnitPrice': product.list_price,
            'PurchaseUnitPrice': product.standard_price,
            'SalesUnit': self._get_sap_uom(product.uom_id),
            'PurchaseUnit': self._get_sap_uom(product.uom_id),  # Use same as sales in Odoo 19.0
            'ItemsGroupCode': self._get_sap_category(product.categ_id),
            'UserText': product.description or '',
            'Valid': 'Y' if product.active else 'N',
            'ItemType': 'itItems',
        }
    
    def _get_product_category(self, sap_category_code):
        """Get product category by SAP category code"""
        if not sap_category_code:
            return self.env.ref('product.product_category_all').id
        
        # Try to find existing category with SAP code
        category = self.env['product.category'].search([
            ('name', 'ilike', f"SAP_{sap_category_code}")
        ], limit=1)
        
        if category:
            return category.id
        
        # Create new category if not found
        category = self.env['product.category'].create({
            'name': f"SAP Category {sap_category_code}",
            'parent_id': self.env.ref('product.product_category_all').id,
        })
        return category.id
    
    def _get_uom_id(self, sap_uom):
        """Get UoM ID by SAP UoM code"""
        if not sap_uom:
            return self.env.ref('uom.product_uom_unit').id
        
        # Try to find existing UoM with SAP code
        uom = self.env['uom.uom'].search([
            ('name', 'ilike', sap_uom)
        ], limit=1)
        
        if uom:
            return uom.id
        
        # Create new UoM if not found
        uom = self.env['uom.uom'].create({
            'name': sap_uom,
            'relative_uom_id': self.env.ref('uom.product_uom_unit').id,
            'relative_factor': 1.0,
        })
        return uom.id
    
    def _get_sap_uom(self, odoo_uom):
        """Get SAP UoM code from Odoo UoM"""
        if not odoo_uom:
            return 'PCS'
        return odoo_uom.name or 'PCS'
    
    def _get_sap_category(self, odoo_category):
        """Get SAP category code from Odoo category"""
        if not odoo_category:
            return '1'
        # This would need to be mapped based on your SAP setup
        return '1'  # Default category
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    @api.model
    def import_record(self, backend, external_id, update_only=False):
        """Import a single product record from SAP - DIRECT METHOD
        
        Args:
            backend: SAP backend record
            external_id: SAP item code
            update_only: If True, only update existing products, don't create new ones
        
        Returns:
            product.product record or None
        """
        try:
            _logger.info(f"Importing product {external_id} from SAP backend {backend.name}")
            
            # Get product data from SAP
            connection = backend.get_connection()
            products = connection.get('Items', {
                '$filter': f"ItemCode eq '{external_id}'"
            })
            
            if not products.get('value'):
                _logger.warning(f"Product {external_id} not found in SAP")
                return None
            
            product_data = products['value'][0]
            
            # Use direct import helper
            direct_importer = self.env['sap.product.direct.import']
            product = direct_importer.import_product_direct(backend, external_id, product_data, update_only=update_only)
            
            if product:
                _logger.info(f"Successfully imported product {external_id}: {product.name}")
            return product
            
        except Exception as e:
            _logger.error(f"Error importing product {external_id}: {str(e)}", exc_info=True)
            raise
    
    @api.model
    def sync_all_products(self, backend_id):
        """Sync all products from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            connection = backend.get_connection()
            
            # Get all products from SAP
            products = connection.get('Items', {'$top': 1000})  # Adjust as needed
            
            synced_count = 0
            for product_data in products.get('value', []):
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_product_id', '=', product_data['ItemCode'])
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_product_id': product_data['ItemCode'],
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the product
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} products from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all products: {str(e)}")
            raise


