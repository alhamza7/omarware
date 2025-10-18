# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapSaleSync(models.Model):
    _name = 'sap.sale.sync'
    _description = 'SAP Sale Order Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_sale_id = fields.Many2one('sale.order', 'Odoo Sale Order')
    sap_sale_id = fields.Char('SAP Sale ID', required=True)
    sap_doc_entry = fields.Integer('SAP Doc Entry')
    
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
        return super(SapSaleSync, self).create(vals)
    
    def sync_from_sap(self):
        """Sync sale order from SAP to Odoo"""
        try:
            connection = self.backend_id.get_connection()
            
            # Get sale order data from SAP
            sales = connection.get_sales_orders(
                filter_query=f"DocEntry eq {self.sap_doc_entry}"
            )
            
            if not sales.get('value'):
                raise UserError(f"Sale order {self.sap_doc_entry} not found in SAP")
            
            sale_data = sales['value'][0]
            self.sap_data = str(sale_data)
            
            # Process sale order data
            sale_order = self._process_sale_data(sale_data)
            
            self.odoo_sale_id = sale_order.id
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced sale order {self.sap_sale_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing sale order {self.sap_sale_id}: {str(e)}")
            raise
    
    def _process_sale_data(self, sale_data):
        """Process sale order data from SAP and create/update Odoo sale order"""
        try:
            # Map SAP data to Odoo format
            sale_vals = self._map_sap_to_odoo(sale_data)
            
            # Check if sale order already exists
            sale_order = self.env['sale.order'].search([
                ('client_order_ref', '=', sale_data['DocNum'])
            ], limit=1)
            
            if sale_order:
                # Update existing sale order
                sale_order.write(sale_vals)
                _logger.info(f"Updated existing sale order: {sale_order.name}")
            else:
                # Create new sale order
                sale_order = self.env['sale.order'].create(sale_vals)
                _logger.info(f"Created new sale order: {sale_order.name}")
            
            return sale_order
            
        except Exception as e:
            _logger.error(f"Error processing sale order data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP sale order data to Odoo sale order format"""
        # Get customer
        customer = self.env['res.partner'].search([
            ('ref', '=', sap_data.get('CardCode', ''))
        ], limit=1)
        
        if not customer:
            # Create customer if not exists
            customer = self.env['res.partner'].create({
                'name': sap_data.get('CardName', ''),
                'ref': sap_data.get('CardCode', ''),
                'is_company': True,
                'customer_rank': 1,
            })
        
        # Prepare order lines
        order_lines = []
        for line in sap_data.get('DocumentLines', []):
            # Get product
            product = self.env['product.product'].search([
                ('default_code', '=', line.get('ItemCode', ''))
            ], limit=1)
            
            if product:
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': line.get('ItemDescription', ''),
                    'product_uom_qty': line.get('Quantity', 0),
                    'price_unit': line.get('UnitPrice', 0),
                    'discount': line.get('DiscountPercent', 0),
                }))
        
        return {
            'name': f"SO/{sap_data.get('DocNum', '')}",
            'client_order_ref': sap_data.get('DocNum', ''),
            'partner_id': customer.id,
            'date_order': sap_data.get('DocDate', fields.Date.today()),
            'state': 'sale',
            'order_line': order_lines,
            'note': f"SAP Sale Order: {sap_data.get('DocNum', '')}",
        }
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    def sync_to_sap(self):
        """Sync sale order from Odoo to SAP"""
        # Implementation for syncing to SAP
        pass
    
    @api.model
    def sync_all_sales(self, backend_id):
        """Sync all sale orders from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            connection = backend.get_connection()
            
            # Get all sale orders from SAP
            sales = connection.get_sales_orders(top=1000)  # Adjust as needed
            
            synced_count = 0
            for sale_data in sales.get('value', []):
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_doc_entry', '=', sale_data['DocEntry'])
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_sale_id': sale_data['DocNum'],
                        'sap_doc_entry': sale_data['DocEntry'],
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the sale order
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} sale orders from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all sale orders: {str(e)}")
            raise


