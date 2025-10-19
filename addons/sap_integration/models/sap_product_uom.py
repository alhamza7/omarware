# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Product UoM Management

Extended product model with multiple UoM support for sales, purchase, and inventory.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from decimal import Decimal, ROUND_HALF_UP

from ..core.sap_logger import SapLogger, SapValidationError


class SapProductUom(models.Model):
    """SAP Product UoM Management"""
    _name = 'sap.product.uom'
    _description = 'SAP Product UoM Management'
    _order = 'product_id, usage_type, sequence'
    
    
    # Basic Information
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True
    )
    sap_uom_code = fields.Char(
        string='SAP UoM Code',
        required=True,
        help="Unit of measure code in SAP"
    )
    odoo_uom_id = fields.Many2one(
        'uom.uom',
        string='Odoo UoM',
        required=True,
        ondelete='cascade'
    )
    
    # Usage Information
    usage_type = fields.Selection([
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('inventory', 'Inventory'),
        ('production', 'Production'),
        ('all', 'All')
    ], string='Usage Type', required=True, default='all')
    
    # Conversion Information
    conversion_factor = fields.Float(
        string='Conversion Factor',
        required=True,
        default=1.0,
        digits=(16, 6),
        help="Factor to convert from this UoM to base UoM"
    )
    precision_digits = fields.Integer(
        string='Precision Digits',
        default=2,
        help="Number of decimal places for calculations"
    )
    
    # SAP Specific Information
    sap_uom_name = fields.Char(
        string='SAP UoM Name',
        help="Unit of measure name in SAP"
    )
    sap_uom_category = fields.Char(
        string='SAP UoM Category',
        help="Unit of measure category in SAP"
    )
    
    # Status and Validation
    active = fields.Boolean(
        string='Active',
        default=True
    )
    is_primary = fields.Boolean(
        string='Is Primary',
        default=False,
        help="Whether this is the primary UoM for the usage type"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of preference for this UoM"
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_product_uom_usage',
         'unique(product_id, sap_uom_code, usage_type)',
         'A UoM mapping with the same SAP code and usage type already exists for this product.'),
        ('positive_conversion_factor',
         'CHECK (conversion_factor > 0)',
         'Conversion factor must be positive.'),
    ]
    
    @api.model
    def create(self, vals):
        """Override create to validate UoM mapping"""
        record = super().create(vals)
        record._validate_uom_mapping()
        return record
    
    def write(self, vals):
        """Override write to validate UoM mapping"""
        result = super().write(vals)
        self._validate_uom_mapping()
        return result
    
    def _validate_uom_mapping(self):
        """Validate UoM mapping for product"""
        for record in self:
            try:
                # Check if conversion factor is positive
                if record.conversion_factor <= 0:
                    raise SapValidationError("Conversion factor must be positive")
                
                # Check if UoM categories match
                if record.odoo_uom_id and record.odoo_uom_id.category_id:
                    if not self._is_uom_category_compatible(record):
                        _logger.warning(f"UoM category mismatch for product {record.product_id.name}")
                
                # Ensure only one primary UoM per usage type
                if record.is_primary:
                    self._ensure_single_primary_uom(record)
                
            except Exception as e:
                _logger.error(f"Error validating UoM mapping: {str(e)}")
                raise
    
    def _is_uom_category_compatible(self, record):
        """Check if UoM categories are compatible"""
        try:
            # Get product's base UoM category
            base_uom = record.product_id.uom_id
            if not base_uom or not base_uom.category_id:
                return True
            
            # Check if categories match
            return base_uom.category_id == record.odoo_uom_id.category_id
            
        except Exception as e:
            _logger.error(f"Error checking UoM category compatibility: {str(e)}")
            return False
    
    def _ensure_single_primary_uom(self, record):
        """Ensure only one primary UoM per usage type"""
        try:
            # Find other primary UoMs for the same product and usage type
            other_primary = self.search([
                ('product_id', '=', record.product_id.id),
                ('usage_type', '=', record.usage_type),
                ('is_primary', '=', True),
                ('id', '!=', record.id)
            ])
            
            # Remove primary flag from others
            if other_primary:
                other_primary.write({'is_primary': False})
                _logger.info(f"Removed primary flag from other UoMs for product {record.product_id.name}")
            
        except Exception as e:
            _logger.error(f"Error ensuring single primary UoM: {str(e)}")
    
    @api.model
    def get_product_uoms(self, product_id, usage_type=None):
        """
        Get all UoMs for a product
        
        :param product_id: Product ID
        :param usage_type: Usage type filter (optional)
        :return: Recordset of UoM mappings
        """
        try:
            domain = [
                ('product_id', '=', product_id),
                ('active', '=', True)
            ]
            
            if usage_type:
                domain.append(('usage_type', 'in', [usage_type, 'all']))
            
            return self.search(domain, order='is_primary desc, sequence')
            
        except Exception as e:
            _logger.error(f"Error getting product UoMs: {str(e)}")
            return self.env['sap.product.uom']
    
    @api.model
    def get_primary_uom(self, product_id, usage_type):
        """
        Get primary UoM for a product and usage type
        
        :param product_id: Product ID
        :param usage_type: Usage type
        :return: Primary UoM mapping record
        """
        try:
            domain = [
                ('product_id', '=', product_id),
                ('usage_type', 'in', [usage_type, 'all']),
                ('is_primary', '=', True),
                ('active', '=', True)
            ]
            
            primary_uom = self.search(domain, limit=1)
            
            if not primary_uom:
                # Fallback to first available UoM
                primary_uom = self.search([
                    ('product_id', '=', product_id),
                    ('usage_type', 'in', [usage_type, 'all']),
                    ('active', '=', True)
                ], limit=1)
            
            return primary_uom
            
        except Exception as e:
            _logger.error(f"Error getting primary UoM: {str(e)}")
            return self.env['sap.product.uom']
    
    @api.model
    def convert_quantity(self, product_id, quantity, from_uom, to_uom, usage_type='all'):
        """
        Convert quantity for a product between UoMs
        
        :param product_id: Product ID
        :param quantity: Quantity to convert
        :param from_uom: Source UoM
        :param to_uom: Target UoM
        :param usage_type: Usage type for conversion
        :return: Converted quantity
        """
        try:
            if not quantity or quantity == 0:
                return 0.0
            
            # Get UoM mappings
            from_mapping = self._get_uom_mapping(product_id, from_uom, usage_type)
            to_mapping = self._get_uom_mapping(product_id, to_uom, usage_type)
            
            if not from_mapping or not to_mapping:
                raise SapValidationError(f"No UoM mapping found for product {product_id}")
            
            # Calculate conversion factor
            conversion_factor = from_mapping.conversion_factor / to_mapping.conversion_factor
            
            # Perform conversion
            converted_quantity = quantity * conversion_factor
            
            # Apply precision
            precision_digits = min(from_mapping.precision_digits, to_mapping.precision_digits)
            converted_quantity = self._apply_precision(converted_quantity, precision_digits)
            
            _logger.info(f"Converted {quantity} {from_uom} to {converted_quantity} {to_uom} for product {product_id}")
            
            return converted_quantity
            
        except Exception as e:
            _logger.error(f"Error converting quantity: {str(e)}")
            raise SapValidationError(f"Failed to convert quantity: {str(e)}")
    
    def _get_uom_mapping(self, product_id, uom, usage_type):
        """Get UoM mapping for a product"""
        try:
            # Try to find mapping by SAP UoM code
            mapping = self.search([
                ('product_id', '=', product_id),
                ('sap_uom_code', '=', uom),
                ('usage_type', 'in', [usage_type, 'all']),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                return mapping
            
            # Try to find mapping by Odoo UoM name
            mapping = self.search([
                ('product_id', '=', product_id),
                ('odoo_uom_id.name', '=', uom),
                ('usage_type', 'in', [usage_type, 'all']),
                ('active', '=', True)
            ], limit=1)
            
            return mapping
            
        except Exception as e:
            _logger.error(f"Error getting UoM mapping: {str(e)}")
            return None
    
    def _apply_precision(self, quantity, precision_digits):
        """Apply precision to quantity"""
        try:
            decimal_quantity = Decimal(str(quantity))
            precision = Decimal('0.1') ** precision_digits
            rounded_quantity = decimal_quantity.quantize(precision, rounding=ROUND_HALF_UP)
            return float(rounded_quantity)
            
        except Exception as e:
            _logger.error(f"Error applying precision: {str(e)}")
            return quantity
    
    @api.model
    def sync_product_uoms_from_sap(self, product_id, sap_uom_data_list):
        """
        Sync product UoMs from SAP data
        
        :param product_id: Product ID
        :param sap_uom_data_list: List of SAP UoM data
        :return: Sync results
        """
        try:
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                raise SapValidationError(f"Product with ID {product_id} not found")
            
            sync_results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for sap_uom_data in sap_uom_data_list:
                try:
                    sync_results['total_processed'] += 1
                    
                    # Extract UoM information
                    sap_code = sap_uom_data.get('UoMCode', '')
                    sap_name = sap_uom_data.get('UoMName', '')
                    usage_type = sap_uom_data.get('UsageType', 'all')
                    conversion_factor = float(sap_uom_data.get('ConversionFactor', 1.0))
                    
                    if not sap_code:
                        sync_results['skipped'] += 1
                        continue
                    
                    # Check if mapping already exists
                    existing_mapping = self.search([
                        ('product_id', '=', product_id),
                        ('sap_uom_code', '=', sap_code),
                        ('usage_type', '=', usage_type)
                    ], limit=1)
                    
                    if existing_mapping:
                        # Update existing mapping
                        existing_mapping.write({
                            'sap_uom_name': sap_name,
                            'conversion_factor': conversion_factor,
                            'active': True
                        })
                        sync_results['successful'] += 1
                    else:
                        # Create new mapping
                        self._create_product_uom_mapping(
                            product_id, sap_code, sap_name, usage_type, conversion_factor
                        )
                        sync_results['successful'] += 1
                        
                except Exception as e:
                    _logger.error(f"Error syncing UoM {sap_uom_data}: {str(e)}")
                    sync_results['failed'] += 1
            
            _logger.info(f"Product UoM sync completed for product {product_id}: {sync_results}")
            
            return sync_results
            
        except Exception as e:
            _logger.error(f"Error syncing product UoMs from SAP: {str(e)}")
            raise SapValidationError(f"Failed to sync product UoMs from SAP: {str(e)}")
    
    def _create_product_uom_mapping(self, product_id, sap_code, sap_name, usage_type, conversion_factor):
        """Create product UoM mapping"""
        try:
            # Find or create Odoo UoM
            odoo_uom = self._find_or_create_odoo_uom(sap_code)
            
            # Create mapping
            mapping_vals = {
                'product_id': product_id,
                'sap_uom_code': sap_code,
                'sap_uom_name': sap_name,
                'odoo_uom_id': odoo_uom.id,
                'usage_type': usage_type,
                'conversion_factor': conversion_factor,
                'active': True
            }
            
            mapping = self.create(mapping_vals)
            
            _logger.info(f"Created product UoM mapping: {sap_code} for product {product_id}")
            
            return mapping
            
        except Exception as e:
            _logger.error(f"Error creating product UoM mapping: {str(e)}")
            raise SapValidationError(f"Failed to create product UoM mapping: {str(e)}")
    
    def _find_or_create_odoo_uom(self, sap_code):
        """Find or create Odoo UoM"""
        try:
            # Try to find existing UoM
            odoo_uom = self.env['uom.uom'].search([
                ('name', '=', sap_code)
            ], limit=1)
            
            if odoo_uom:
                return odoo_uom
            
            # Create new UoM
            category = self.env['uom.category'].search([('name', '=', 'Other')], limit=1)
            if not category:
                category = self.env['uom.category'].create({
                    'name': 'Other',
                    'active': True
                })
            
            odoo_uom = self.env['uom.uom'].create({
                'name': sap_code,
                'category_id': category.id,
                'factor': 1.0,
                'uom_type': 'reference',
                'active': True
            })
            
            return odoo_uom
            
        except Exception as e:
            _logger.error(f"Error finding or creating Odoo UoM: {str(e)}")
            raise SapValidationError(f"Failed to find or create Odoo UoM: {str(e)}")
    
    def action_set_primary(self):
        """Set this UoM as primary for its usage type"""
        self.ensure_one()
        self.is_primary = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Primary UoM Set',
                'message': f'{self.sap_uom_code} is now the primary UoM for {self.usage_type}',
                'type': 'success'
            }
        }
    
    def action_test_conversion(self):
        """Test UoM conversion"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Test UoM Conversion',
            'res_model': 'sap.uom.conversion.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_from_uom': self.sap_uom_code,
                'default_to_uom': self.product_id.uom_id.name
            }
        }
