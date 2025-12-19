# -*- coding: utf-8 -*-
"""
SAP Product Direct Import - Simplified Version
This bypasses the complex service layer and imports directly
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapProductDirectImport(models.TransientModel):
    """Direct SAP Product Import Helper"""
    _name = 'sap.product.direct.import'
    _description = 'SAP Product Direct Import'
    
    @api.model
    def import_product_direct(self, backend, item_code, product_data):
        """
        Import a single product directly without service layer complexity
        
        Args:
            backend: SAP backend record
            item_code: SAP item code
            product_data: Dictionary with product data from SAP
        
        Returns:
            product.product record
        """
        try:
            # Validate input
            if not isinstance(product_data, dict):
                raise UserError(f"Product data must be a dictionary, got {type(product_data)}")
            
            # Validate item_code to prevent duplicates
            if not item_code or not str(item_code).strip():
                raise UserError(f"Product ItemCode is empty or invalid. Cannot import product without ItemCode.")
            
            # Extract basic info
            item_name = product_data.get('ItemName', item_code)
            
            # Check if product already exists (using exact match to prevent duplicates)
            product = self.env['product.product'].search([
                ('default_code', '=', str(item_code).strip())
            ], limit=1)
            
            # Prepare product data
            product_vals = {
                'name': item_name,
                'default_code': str(item_code).strip(),  # Ensure no whitespace
                'sale_ok': True,
                'purchase_ok': True,
                'available_in_pos': True,  # Make product available in Point of Sale
                'type': 'consu',  # Consumable = Storable products (displayed as "Goods" in UI)
                'tracking': 'none',  # Enable inventory tracking
                'is_storable': True,  # Enable "Track Inventory" checkbox in UI
            }
            
            # Add optional fields safely
            if product_data.get('ItemDescription'):
                product_vals['description'] = product_data['ItemDescription']
                product_vals['description_sale'] = product_data['ItemDescription']
            
            # Prices
            if 'SalesUnitPrice' in product_data:
                try:
                    product_vals['list_price'] = float(product_data['SalesUnitPrice'])
                except (ValueError, TypeError):
                    product_vals['list_price'] = 0.0
            
            if 'PurchaseUnitPrice' in product_data:
                try:
                    product_vals['standard_price'] = float(product_data['PurchaseUnitPrice'])
                except (ValueError, TypeError):
                    product_vals['standard_price'] = 0.0
            
            # Weight and Volume
            if 'Weight' in product_data:
                try:
                    product_vals['weight'] = float(product_data['Weight'])
                except (ValueError, TypeError):
                    pass
            
            if 'Volume' in product_data:
                try:
                    product_vals['volume'] = float(product_data['Volume'])
                except (ValueError, TypeError):
                    pass
            
            # UoM
            if product_data.get('SalesUnit'):
                uom = self._get_or_create_uom(product_data['SalesUnit'])
                product_vals['uom_id'] = uom.id
            
            # Note: uom_po_id removed in Odoo 19.0
            # Purchase UoM can be set through product.supplierinfo if needed
            
            # Category
            if product_data.get('ItemsGroupCode'):
                category = self._get_or_create_category(product_data['ItemsGroupCode'])
                product_vals['categ_id'] = category.id
            
            # Active status
            if 'Valid' in product_data:
                product_vals['active'] = product_data['Valid'] == 'Y'
            
            # Barcode
            if product_data.get('BarCode'):
                product_vals['barcode'] = product_data['BarCode']
            
            # Create or update product
            if product:
                product.write(product_vals)
                _logger.info(f"Updated existing product: {product.name} ({item_code})")
            else:
                product = self.env['product.product'].create(product_vals)
                _logger.info(f"Created new product: {product.name} ({item_code})")
            
            # Create or update sync record
            sync_record = self.env['sap.product.sync'].search([
                ('backend_id', '=', backend.id),
                ('sap_product_id', '=', item_code)
            ], limit=1)
            
            sync_vals = {
                'backend_id': backend.id,
                'sap_product_id': item_code,
                'sap_product_name': item_name,
                'odoo_product_id': product.id,
                'sync_status': 'success',
                'last_sync': fields.Datetime.now(),
                'error_message': False,
            }
            
            if sync_record:
                sync_record.write(sync_vals)
            else:
                self.env['sap.product.sync'].create(sync_vals)
            
            return product
            
        except Exception as e:
            _logger.error(f"Error in direct product import for {item_code}: {str(e)}", exc_info=True)
            raise
    
    def _get_or_create_uom(self, uom_code):
        """Get or create UoM by code"""
        try:
            # Search for existing UoM
            uom = self.env['uom.uom'].search([
                ('name', '=ilike', uom_code)
            ], limit=1)
            
            if not uom:
                # Create new UoM
                uom = self.env['uom.uom'].create({
                    'name': uom_code,
                    'category_id': self.env.ref('uom.product_uom_categ_unit').id,
                    'uom_type': 'reference',
                    'factor': 1.0,
                })
                _logger.info(f"Created new UoM: {uom_code}")
            
            return uom
        except:
            # Return default UoM if error
            return self.env.ref('uom.product_uom_unit')
    
    def _get_or_create_category(self, category_code):
        """Get or create product category by SAP code"""
        try:
            # Search for existing category
            category = self.env['product.category'].search([
                ('name', '=ilike', f"SAP_{category_code}")
            ], limit=1)
            
            if not category:
                category = self.env['product.category'].create({
                    'name': f"SAP Category {category_code}",
                    'parent_id': self.env.ref('product.product_category_all').id,
                })
                _logger.info(f"Created new category: SAP Category {category_code}")
            
            return category
        except:
            # Return default category if error
            return self.env.ref('product.product_category_all')



