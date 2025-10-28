# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Product Warehouse Info

Additional SAP warehouse information for products.
Main inventory data goes to stock.quant and stock.warehouse.orderpoint.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SapProductWarehouseInfo(models.Model):
    """SAP-specific warehouse information for products"""
    _name = 'sap.product.warehouse.info'
    _description = 'SAP Product Warehouse Information'
    _order = 'product_id, warehouse_id'
    
    # ========== Relations ==========
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
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
    
    # ========== SAP Warehouse Codes ==========
    sap_warehouse_code = fields.Char(
        string='SAP Warehouse Code',
        required=True,
        index=True,
        help="Warehouse code in SAP"
    )
    sap_warehouse_name = fields.Char(
        string='SAP Warehouse Name',
        help="Warehouse name from SAP"
    )
    
    # ========== SAP Specific Fields ==========
    default_bin = fields.Char(
        string='Default Bin Location',
        help="Default bin location in SAP (e.g., A-01-05)"
    )
    
    # ========== Last Synced Quantities (from SAP) ==========
    # These are historical values from last sync
    # Actual quantities are in stock.quant
    last_in_stock = fields.Float(
        string='Last In Stock (SAP)',
        digits='Product Unit of Measure',
        readonly=True,
        help="Quantity in stock from last SAP sync"
    )
    last_committed = fields.Float(
        string='Last Committed (SAP)',
        digits='Product Unit of Measure',
        readonly=True,
        help="Committed quantity from last SAP sync"
    )
    last_ordered = fields.Float(
        string='Last Ordered (SAP)',
        digits='Product Unit of Measure',
        readonly=True,
        help="Ordered quantity from last SAP sync"
    )
    last_available = fields.Float(
        string='Last Available (SAP)',
        compute='_compute_last_available',
        store=True,
        digits='Product Unit of Measure',
        help="Available = InStock - Committed"
    )
    
    # ========== Reorder Points (from SAP) ==========
    # These sync with stock.warehouse.orderpoint
    minimum_stock = fields.Float(
        string='Minimum Stock Level',
        digits='Product Unit of Measure',
        help="Minimum stock level from SAP"
    )
    maximum_stock = fields.Float(
        string='Maximum Stock Level',
        digits='Product Unit of Measure',
        help="Maximum stock level from SAP"
    )
    min_order = fields.Float(
        string='Minimum Order Quantity',
        digits='Product Unit of Measure',
        help="Minimum order quantity from SAP"
    )
    
    # ========== Odoo Stock Integration ==========
    orderpoint_id = fields.Many2one(
        'stock.warehouse.orderpoint',
        string='Reorder Rule',
        readonly=True,
        help="Linked reorder rule in Odoo"
    )
    
    # ========== Current Odoo Quantities ==========
    # These are computed from Odoo stock.quant
    current_qty_available = fields.Float(
        string='Current Available (Odoo)',
        compute='_compute_current_quantities',
        digits='Product Unit of Measure',
        help="Current quantity available in Odoo"
    )
    current_qty_reserved = fields.Float(
        string='Current Reserved (Odoo)',
        compute='_compute_current_quantities',
        digits='Product Unit of Measure',
        help="Current reserved quantity in Odoo"
    )
    
    # ========== Sync Information ==========
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True
    )
    sync_status = fields.Selection([
        ('synced', 'Synced'),
        ('pending', 'Pending'),
        ('error', 'Error')
    ], string='Sync Status', default='pending', readonly=True, index=True)
    
    sync_error_message = fields.Text(
        string='Sync Error',
        readonly=True
    )
    
    # ========== Computed Fields ==========
    product_name = fields.Char(
        string='Product Name',
        related='product_id.name',
        readonly=True
    )
    product_code = fields.Char(
        string='Product Code',
        related='product_id.default_code',
        store=True
    )
    warehouse_name = fields.Char(
        string='Warehouse Name',
        related='warehouse_id.name',
        readonly=True
    )
    
    # ========== Constraints ==========
    _sql_constraints = [
        ('unique_product_warehouse', 'UNIQUE(product_id, warehouse_id, backend_id)',
         'Warehouse info already exists for this product and warehouse!'),
    ]
    
    # ========== Computed Methods ==========
    @api.depends('last_in_stock', 'last_committed')
    def _compute_last_available(self):
        """Calculate available quantity from SAP data"""
        for record in self:
            record.last_available = record.last_in_stock - record.last_committed
    
    @api.depends('product_id', 'warehouse_id')
    def _compute_current_quantities(self):
        """Get current quantities from Odoo stock.quant"""
        for record in self:
            if record.product_id and record.warehouse_id:
                # Get stock location for warehouse
                location = record.warehouse_id.lot_stock_id
                
                # Query stock.quant
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('location_id', '=', location.id)
                ])
                
                record.current_qty_available = sum(quants.mapped('quantity'))
                record.current_qty_reserved = sum(quants.mapped('reserved_quantity'))
            else:
                record.current_qty_available = 0.0
                record.current_qty_reserved = 0.0
    
    # ========== CRUD Methods ==========
    @api.model
    def sync_warehouse_info_from_sap(self, product, backend, sap_warehouse_data_list):
        """
        Sync warehouse information for a product from SAP
        
        Args:
            product: product.product record
            backend: sap.backend record
            sap_warehouse_data_list: List of SAP ItemWarehouseInfo data
            
        Returns:
            Dictionary with sync results
        """
        try:
            results = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'errors': 0,
                'error_messages': []
            }
            
            for warehouse_data in sap_warehouse_data_list:
                try:
                    results['total'] += 1
                    
                    # Extract warehouse information
                    sap_warehouse_code = warehouse_data.get('WarehouseCode', '')
                    
                    if not sap_warehouse_code:
                        continue
                    
                    # Get or create warehouse
                    warehouse = self._get_or_create_warehouse(backend, warehouse_data)
                    
                    # Search for existing record
                    warehouse_info = self.search([
                        ('product_id', '=', product.id),
                        ('warehouse_id', '=', warehouse.id),
                        ('backend_id', '=', backend.id)
                    ], limit=1)
                    
                    # Prepare values
                    vals = self._prepare_warehouse_info_values(
                        product, warehouse, backend, warehouse_data
                    )
                    
                    if warehouse_info:
                        # Update existing
                        warehouse_info.write(vals)
                        results['updated'] += 1
                        _logger.info(f"Updated warehouse info for {product.name} in {warehouse.name}")
                    else:
                        # Create new
                        warehouse_info = self.create(vals)
                        results['created'] += 1
                        _logger.info(f"Created warehouse info for {product.name} in {warehouse.name}")
                    
                    # Update Odoo stock.quant
                    self._update_stock_quant(warehouse_info, product, warehouse, warehouse_data)
                    
                    # Create or update reorder rule
                    self._create_or_update_orderpoint(warehouse_info, product, warehouse, warehouse_data)
                    
                except Exception as e:
                    results['errors'] += 1
                    error_msg = f"Error syncing warehouse {warehouse_data.get('WarehouseCode')}: {str(e)}"
                    results['error_messages'].append(error_msg)
                    _logger.error(error_msg)
            
            _logger.info(f"Warehouse info sync completed for {product.name}: {results}")
            return results
            
        except Exception as e:
            _logger.error(f"Error syncing warehouse info: {str(e)}")
            raise
    
    def _prepare_warehouse_info_values(self, product, warehouse, backend, warehouse_data):
        """Prepare values for warehouse info record"""
        return {
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'backend_id': backend.id,
            'sap_warehouse_code': warehouse_data.get('WarehouseCode', ''),
            'sap_warehouse_name': warehouse_data.get('WarehouseName', ''),
            'default_bin': warehouse_data.get('DefaultBin', ''),
            'last_in_stock': float(warehouse_data.get('InStock', 0.0)),
            'last_committed': float(warehouse_data.get('Committed', 0.0)),
            'last_ordered': float(warehouse_data.get('Ordered', 0.0)),
            'minimum_stock': float(warehouse_data.get('MinimumStock', 0.0)),
            'maximum_stock': float(warehouse_data.get('MaximumStock', 0.0)),
            'min_order': float(warehouse_data.get('MinOrder', 0.0)),
            'last_sync_date': fields.Datetime.now(),
            'sync_status': 'synced',
            'sync_error_message': False,
        }
    
    def _get_or_create_warehouse(self, backend, warehouse_data):
        """Get or create warehouse in Odoo"""
        sap_warehouse_code = warehouse_data.get('WarehouseCode', '')
        warehouse_name = warehouse_data.get('WarehouseName', sap_warehouse_code)
        
        # Search for existing warehouse
        warehouse = self.env['stock.warehouse'].search([
            ('code', '=', sap_warehouse_code)
        ], limit=1)
        
        if not warehouse:
            # Create new warehouse
            warehouse = self.env['stock.warehouse'].create({
                'name': warehouse_name,
                'code': sap_warehouse_code,
                'company_id': self.env.company.id,
            })
            _logger.info(f"Created new warehouse: {warehouse_name}")
        
        return warehouse
    
    def _update_stock_quant(self, warehouse_info, product, warehouse, warehouse_data):
        """Update stock.quant with quantities from SAP"""
        try:
            in_stock = float(warehouse_data.get('InStock', 0.0))
            
            if in_stock == 0:
                return  # Don't create quant for zero stock
            
            # Get location
            location = warehouse.lot_stock_id
            
            # Search for existing quant
            quant = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id', '=', location.id)
            ], limit=1)
            
            if quant:
                # Update existing
                quant.sudo().write({
                    'quantity': in_stock,
                })
                _logger.info(f"Updated stock quant for {product.name}: {in_stock}")
            else:
                # Create new
                self.env['stock.quant'].sudo().create({
                    'product_id': product.id,
                    'location_id': location.id,
                    'quantity': in_stock,
                })
                _logger.info(f"Created stock quant for {product.name}: {in_stock}")
            
        except Exception as e:
            _logger.error(f"Error updating stock quant: {str(e)}")
            # Don't raise - continue with other operations
    
    def _create_or_update_orderpoint(self, warehouse_info, product, warehouse, warehouse_data):
        """Create or update stock.warehouse.orderpoint (reorder rule)"""
        try:
            min_stock = warehouse_info.minimum_stock
            max_stock = warehouse_info.maximum_stock
            min_order = warehouse_info.min_order
            
            if min_stock == 0 and max_stock == 0:
                return  # No reorder rule needed
            
            # Get location
            location = warehouse.lot_stock_id
            
            # Search for existing orderpoint
            orderpoint = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', product.id),
                ('warehouse_id', '=', warehouse.id)
            ], limit=1)
            
            vals = {
                'product_id': product.id,
                'warehouse_id': warehouse.id,
                'location_id': location.id,
                'product_min_qty': min_stock,
                'product_max_qty': max_stock if max_stock > 0 else min_stock * 2,
                'qty_multiple': min_order if min_order > 0 else 1,
            }
            
            if orderpoint:
                # Update existing
                orderpoint.write(vals)
                _logger.info(f"Updated orderpoint for {product.name}")
            else:
                # Create new
                orderpoint = self.env['stock.warehouse.orderpoint'].create(vals)
                _logger.info(f"Created orderpoint for {product.name}")
            
            # Link to warehouse info
            warehouse_info.write({
                'orderpoint_id': orderpoint.id
            })
            
        except Exception as e:
            _logger.error(f"Error creating/updating orderpoint: {str(e)}")
            # Don't raise - continue with other operations
    
    @api.model
    def import_all_warehouse_info_from_sap(self, backend, batch_size=100):
        """
        Import warehouse information for all products from SAP
        
        Args:
            backend: sap.backend record
            batch_size: Number of products to process per batch
            
        Returns:
            Dictionary with import results
        """
        try:
            _logger.info(f"Importing all warehouse info from SAP backend {backend.name}")
            
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            results = {
                'total_products': 0,
                'successful_products': 0,
                'failed_products': 0,
                'total_warehouses': 0,
                'created_records': 0,
                'updated_records': 0,
                'errors': []
            }
            
            # Get all items with their warehouse info
            skip = 0
            has_more = True
            
            while has_more:
                # Fetch batch WITHOUT expand (SAP doesn't support it)
                params = {
                    '$top': batch_size,
                    '$skip': skip,
                    '$orderby': 'ItemCode'
                }
                
                items_data = connection.get('Items', params)
                batch = items_data.get('value', [])
                
                if not batch:
                    has_more = False
                    break
                
                _logger.info(f"Processing batch: {skip + 1} to {skip + len(batch)}")
                
                # Process each item
                for item_data in batch:
                    try:
                        results['total_products'] += 1
                        
                        item_code = item_data.get('ItemCode')
                        
                        # Fetch warehouse info from Items endpoint with select
                        try:
                            # ItemWarehouseInfoCollection is not a separate endpoint
                            # We need to get the full item to access warehouse info
                            wh_params = {
                                '$filter': f"ItemCode eq '{item_code}'",
                                '$select': 'ItemCode,ItemWarehouseInfoCollection'
                            }
                            item_with_wh = connection.get('Items', wh_params)
                            items_value = item_with_wh.get('value', [])
                            if items_value:
                                warehouse_info_list = items_value[0].get('ItemWarehouseInfoCollection', [])
                            else:
                                warehouse_info_list = []
                        except Exception as wh_error:
                            _logger.warning(f"Could not fetch warehouse info for {item_code}: {str(wh_error)}")
                            warehouse_info_list = []
                        
                        if not warehouse_info_list:
                            _logger.debug(f"No warehouse info for item {item_code}")
                            continue
                        
                        # Find product in Odoo
                        product = self.env['product.product'].search([
                            ('default_code', '=', item_code)
                        ], limit=1)
                        
                        if not product:
                            _logger.warning(f"Product {item_code} not found in Odoo, skipping warehouse info")
                            results['failed_products'] += 1
                            continue
                        
                        # Sync warehouse info for this product
                        warehouse_result = self.sync_warehouse_info_from_sap(
                            product, backend, warehouse_info_list
                        )
                        
                        results['total_warehouses'] += warehouse_result['total']
                        results['created_records'] += warehouse_result['created']
                        results['updated_records'] += warehouse_result['updated']
                        
                        if warehouse_result['errors'] > 0:
                            results['errors'].extend(warehouse_result['error_messages'])
                            results['failed_products'] += 1
                        else:
                            results['successful_products'] += 1
                        
                    except Exception as e:
                        results['failed_products'] += 1
                        error_msg = f"Error processing item {item_code}: {str(e)}"
                        results['errors'].append(error_msg)
                        _logger.error(error_msg)
                
                skip += len(batch)
            
            _logger.info(f"Warehouse info import completed: {results}")
            return results
            
        except Exception as e:
            _logger.error(f"Error importing all warehouse info: {str(e)}")
            raise
    
    # ========== Action Methods ==========
    def action_view_stock_quant(self):
        """Open stock quants for this product/warehouse"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Quantities',
            'res_model': 'stock.quant',
            'view_mode': 'list,form',
            'domain': [
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.warehouse_id.lot_stock_id.id)
            ],
            'context': {
                'default_product_id': self.product_id.id,
                'default_location_id': self.warehouse_id.lot_stock_id.id,
            }
        }
    
    def action_view_orderpoint(self):
        """Open the reorder rule"""
        self.ensure_one()
        if not self.orderpoint_id:
            raise UserError("No reorder rule linked yet!")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reorder Rule',
            'res_model': 'stock.warehouse.orderpoint',
            'res_id': self.orderpoint_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_sync_from_sap(self):
        """Re-sync warehouse info from SAP"""
        self.ensure_one()
        try:
            connection = self.backend_id.get_connection()
            
            # Get item warehouse info
            params = {
                '$filter': f"ItemCode eq '{self.product_id.default_code}'",
                '$expand': 'ItemWarehouseInfoCollection'
            }
            items_data = connection.get('Items', params)
            
            if not items_data.get('value'):
                raise UserError(f"Item {self.product_id.default_code} not found in SAP")
            
            warehouse_info_list = items_data['value'][0].get('ItemWarehouseInfoCollection', [])
            
            # Find matching warehouse
            matching_warehouse = None
            for wh_data in warehouse_info_list:
                if wh_data.get('WarehouseCode') == self.sap_warehouse_code:
                    matching_warehouse = wh_data
                    break
            
            if not matching_warehouse:
                raise UserError(f"Warehouse info not found in SAP for {self.sap_warehouse_code}")
            
            # Re-sync
            result = self.sync_warehouse_info_from_sap(
                self.product_id, self.backend_id, [matching_warehouse]
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': f'Warehouse info synced from SAP: {result}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error syncing warehouse info: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error!',
                    'message': f'Failed to sync: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }



