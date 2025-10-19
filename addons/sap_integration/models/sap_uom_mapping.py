# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP UoM Mapping

Comprehensive unit of measure mapping and conversion system between SAP and Odoo.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from decimal import Decimal, ROUND_HALF_UP
import math

from ..core.sap_logger import SapLogger, SapValidationError


class SapUomMapping(models.Model):
    """SAP UoM Mapping and Conversion"""
    _name = 'sap.uom.mapping'
    _description = 'SAP UoM Mapping'
    _order = 'sap_uom_code, odoo_uom_id'
    
    
    # Basic Information
    name = fields.Char(
        string='Mapping Name',
        required=True,
        compute='_compute_name',
        store=True
    )
    sap_uom_code = fields.Char(
        string='SAP UoM Code',
        required=True,
        index=True,
        help="Unit of measure code in SAP (e.g., EA, KG, M, L)"
    )
    sap_uom_name = fields.Char(
        string='SAP UoM Name',
        help="Unit of measure name in SAP"
    )
    odoo_uom_id = fields.Many2one(
        'uom.uom',
        string='Odoo UoM',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Conversion Information
    conversion_factor = fields.Float(
        string='Conversion Factor',
        required=True,
        default=1.0,
        digits=(16, 6),
        help="Factor to convert from SAP UoM to Odoo UoM (SAP = Odoo * factor)"
    )
    inverse_factor = fields.Float(
        string='Inverse Factor',
        compute='_compute_inverse_factor',
        store=True,
        digits=(16, 6),
        help="Factor to convert from Odoo UoM to SAP UoM"
    )
    
    # Precision and Rounding
    precision_digits = fields.Integer(
        string='Precision Digits',
        default=2,
        help="Number of decimal places for calculations"
    )
    rounding_method = fields.Selection([
        ('round', 'Round'),
        ('floor', 'Floor'),
        ('ceil', 'Ceiling'),
        ('trunc', 'Truncate')
    ], string='Rounding Method', default='round')
    
    # Category and Type
    uom_category = fields.Selection([
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('length', 'Length'),
        ('area', 'Area'),
        ('time', 'Time'),
        ('count', 'Count'),
        ('other', 'Other')
    ], string='UoM Category', required=True)
    
    # Status and Validation
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this mapping is active"
    )
    is_base_unit = fields.Boolean(
        string='Is Base Unit',
        default=False,
        help="Whether this is the base unit for the category"
    )
    validation_status = fields.Selection([
        ('valid', 'Valid'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string='Validation Status', default='valid', readonly=True)
    validation_message = fields.Text(
        string='Validation Message',
        readonly=True
    )
    
    # Usage Information
    usage_type = fields.Selection([
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('inventory', 'Inventory'),
        ('all', 'All')
    ], string='Usage Type', default='all', required=True)
    
    # Constraints
    _sql_constraints = [
        ('unique_sap_odoo_mapping', 
         'unique(sap_uom_code, odoo_uom_id)',
         'A mapping with the same SAP UoM code and Odoo UoM already exists.'),
        ('positive_conversion_factor',
         'CHECK (conversion_factor > 0)',
         'Conversion factor must be positive.'),
    ]
    
    @api.depends('sap_uom_code', 'odoo_uom_id')
    def _compute_name(self):
        """Compute mapping name"""
        for record in self:
            if record.sap_uom_code and record.odoo_uom_id:
                record.name = f"{record.sap_uom_code} → {record.odoo_uom_id.name}"
            else:
                record.name = ''
    
    @api.depends('conversion_factor')
    def _compute_inverse_factor(self):
        """Compute inverse conversion factor"""
        for record in self:
            if record.conversion_factor and record.conversion_factor != 0:
                record.inverse_factor = 1.0 / record.conversion_factor
            else:
                record.inverse_factor = 0.0
    
    @api.model
    def create(self, vals):
        """Override create to validate mapping"""
        record = super().create(vals)
        record._validate_mapping()
        return record
    
    def write(self, vals):
        """Override write to validate mapping"""
        result = super().write(vals)
        self._validate_mapping()
        return result
    
    def _validate_mapping(self):
        """Validate UoM mapping"""
        for record in self:
            try:
                # Check if conversion factor is positive
                if record.conversion_factor <= 0:
                    record.validation_status = 'error'
                    record.validation_message = 'Conversion factor must be positive'
                    continue
                
                # Check if UoM categories match
                if record.odoo_uom_id and record.odoo_uom_id.category_id:
                    odoo_category = self._get_uom_category_type(record.odoo_uom_id.category_id)
                    if odoo_category != record.uom_category:
                        record.validation_status = 'warning'
                        record.validation_message = f'UoM category mismatch: SAP={record.uom_category}, Odoo={odoo_category}'
                        continue
                
                # Check for circular references
                if self._has_circular_reference(record):
                    record.validation_status = 'error'
                    record.validation_message = 'Circular reference detected in UoM mapping'
                    continue
                
                # All validations passed
                record.validation_status = 'valid'
                record.validation_message = 'Mapping is valid'
                
            except Exception as e:
                record.validation_status = 'error'
                record.validation_message = f'Validation error: {str(e)}'
                _logger.error(f"Error validating UoM mapping {record.name}: {str(e)}")
    
    def _get_uom_category_type(self, category):
        """Get UoM category type from Odoo category"""
        category_mapping = {
            'Weight': 'weight',
            'Volume': 'volume',
            'Length': 'length',
            'Area': 'area',
            'Time': 'time',
            'Count': 'count',
        }
        return category_mapping.get(category.name, 'other')
    
    def _has_circular_reference(self, record):
        """Check for circular references in UoM mapping"""
        try:
            # This is a simplified check - in a real scenario, you'd need more complex logic
            # to detect circular references in the conversion chain
            return False
        except Exception as e:
            _logger.error(f"Error checking circular reference: {str(e)}")
            return False
    
    @api.model
    def convert_quantity(self, quantity, from_uom_code, to_uom_code, precision_digits=None):
        """
        Convert quantity from one UoM to another
        
        :param quantity: Quantity to convert
        :param from_uom_code: Source UoM code (SAP or Odoo)
        :param to_uom_code: Target UoM code (SAP or Odoo)
        :param precision_digits: Number of decimal places for result
        :return: Converted quantity
        """
        try:
            if not quantity or quantity == 0:
                return 0.0
            
            # Find mapping
            mapping = self._find_conversion_mapping(from_uom_code, to_uom_code)
            if not mapping:
                raise SapValidationError(f"No conversion mapping found from {from_uom_code} to {to_uom_code}")
            
            # Perform conversion
            converted_quantity = quantity * mapping.conversion_factor
            
            # Apply precision and rounding
            if precision_digits is None:
                precision_digits = mapping.precision_digits
            
            converted_quantity = self._apply_precision_and_rounding(
                converted_quantity, precision_digits, mapping.rounding_method
            )
            
            _logger.info(f"Converted {quantity} {from_uom_code} to {converted_quantity} {to_uom_code}")
            
            return converted_quantity
            
        except Exception as e:
            _logger.error(f"Error converting quantity: {str(e)}")
            raise SapValidationError(f"Failed to convert quantity: {str(e)}")
    
    def _find_conversion_mapping(self, from_uom_code, to_uom_code):
        """Find conversion mapping between two UoM codes"""
        try:
            # Direct mapping
            mapping = self.search([
                ('sap_uom_code', '=', from_uom_code),
                ('odoo_uom_id.name', '=', to_uom_code),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                return mapping
            
            # Reverse mapping
            mapping = self.search([
                ('sap_uom_code', '=', to_uom_code),
                ('odoo_uom_id.name', '=', from_uom_code),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                # Use inverse factor for reverse conversion
                mapping.conversion_factor = mapping.inverse_factor
                return mapping
            
            # Try to find through base unit
            return self._find_conversion_through_base_unit(from_uom_code, to_uom_code)
            
        except Exception as e:
            _logger.error(f"Error finding conversion mapping: {str(e)}")
            return None
    
    def _find_conversion_through_base_unit(self, from_uom_code, to_uom_code):
        """Find conversion through base unit"""
        try:
            # Find mappings to base units
            from_mapping = self.search([
                ('sap_uom_code', '=', from_uom_code),
                ('active', '=', True)
            ], limit=1)
            
            to_mapping = self.search([
                ('sap_uom_code', '=', to_uom_code),
                ('active', '=', True)
            ], limit=1)
            
            if from_mapping and to_mapping:
                # Check if they have the same base unit
                if from_mapping.odoo_uom_id.category_id == to_mapping.odoo_uom_id.category_id:
                    # Create a virtual mapping through base unit
                    virtual_mapping = self.env['sap.uom.mapping'].new({
                        'sap_uom_code': from_uom_code,
                        'odoo_uom_id': to_mapping.odoo_uom_id,
                        'conversion_factor': from_mapping.conversion_factor / to_mapping.conversion_factor,
                        'precision_digits': max(from_mapping.precision_digits, to_mapping.precision_digits),
                        'rounding_method': from_mapping.rounding_method
                    })
                    return virtual_mapping
            
            return None
            
        except Exception as e:
            _logger.error(f"Error finding conversion through base unit: {str(e)}")
            return None
    
    def _apply_precision_and_rounding(self, quantity, precision_digits, rounding_method):
        """Apply precision and rounding to quantity"""
        try:
            # Convert to Decimal for precise calculation
            decimal_quantity = Decimal(str(quantity))
            
            # Apply precision
            precision = Decimal('0.1') ** precision_digits
            rounded_quantity = decimal_quantity.quantize(precision, rounding=ROUND_HALF_UP)
            
            # Apply rounding method
            if rounding_method == 'floor':
                rounded_quantity = rounded_quantity.quantize(precision, rounding=math.floor)
            elif rounding_method == 'ceil':
                rounded_quantity = rounded_quantity.quantize(precision, rounding=math.ceil)
            elif rounding_method == 'trunc':
                rounded_quantity = rounded_quantity.quantize(precision, rounding=math.trunc)
            
            return float(rounded_quantity)
            
        except Exception as e:
            _logger.error(f"Error applying precision and rounding: {str(e)}")
            return quantity
    
    @api.model
    def get_conversion_factor(self, from_uom_code, to_uom_code):
        """Get conversion factor between two UoM codes"""
        try:
            mapping = self._find_conversion_mapping(from_uom_code, to_uom_code)
            if mapping:
                return mapping.conversion_factor
            else:
                return 1.0
                
        except Exception as e:
            _logger.error(f"Error getting conversion factor: {str(e)}")
            return 1.0
    
    @api.model
    def create_mapping_from_sap(self, sap_uom_data):
        """Create UoM mapping from SAP data"""
        try:
            sap_code = sap_uom_data.get('UoMCode', '')
            sap_name = sap_uom_data.get('UoMName', '')
            
            if not sap_code:
                raise SapValidationError("SAP UoM code is required")
            
            # Find or create Odoo UoM
            odoo_uom = self._find_or_create_odoo_uom(sap_uom_data)
            
            # Create mapping
            mapping_vals = {
                'sap_uom_code': sap_code,
                'sap_uom_name': sap_name,
                'odoo_uom_id': odoo_uom.id,
                'conversion_factor': 1.0,  # Default to 1:1 mapping
                'uom_category': self._determine_uom_category(sap_uom_data),
                'usage_type': 'all',
                'active': True
            }
            
            mapping = self.create(mapping_vals)
            
            _logger.info(f"Created UoM mapping: {sap_code} → {odoo_uom.name}")
            
            return mapping
            
        except Exception as e:
            _logger.error(f"Error creating mapping from SAP: {str(e)}")
            raise SapValidationError(f"Failed to create UoM mapping: {str(e)}")
    
    def _find_or_create_odoo_uom(self, sap_uom_data):
        """Find or create Odoo UoM from SAP data"""
        try:
            sap_code = sap_uom_data.get('UoMCode', '')
            sap_name = sap_uom_data.get('UoMName', '')
            
            # Try to find existing UoM
            odoo_uom = self.env['uom.uom'].search([
                ('name', '=', sap_code)
            ], limit=1)
            
            if odoo_uom:
                return odoo_uom
            
            # Create new UoM
            category = self._get_or_create_uom_category(sap_uom_data)
            
            odoo_uom = self.env['uom.uom'].create({
                'name': sap_code,
                'category_id': category.id,
                'factor': 1.0,
                'uom_type': 'reference',
                'active': True
            })
            
            _logger.info(f"Created Odoo UoM: {sap_code}")
            
            return odoo_uom
            
        except Exception as e:
            _logger.error(f"Error finding or creating Odoo UoM: {str(e)}")
            raise SapValidationError(f"Failed to find or create Odoo UoM: {str(e)}")
    
    def _get_or_create_uom_category(self, sap_uom_data):
        """Get or create UoM category from SAP data"""
        try:
            # Determine category type
            category_type = self._determine_uom_category(sap_uom_data)
            
            # Find existing category
            category = self.env['uom.category'].search([
                ('name', '=', category_type.title())
            ], limit=1)
            
            if category:
                return category
            
            # Create new category
            category = self.env['uom.category'].create({
                'name': category_type.title(),
                'active': True
            })
            
            _logger.info(f"Created UoM category: {category_type.title()}")
            
            return category
            
        except Exception as e:
            _logger.error(f"Error getting or creating UoM category: {str(e)}")
            raise SapValidationError(f"Failed to get or create UoM category: {str(e)}")
    
    def _determine_uom_category(self, sap_uom_data):
        """Determine UoM category from SAP data"""
        try:
            sap_code = sap_uom_data.get('UoMCode', '').upper()
            sap_name = sap_uom_data.get('UoMName', '').upper()
            
            # Weight units
            weight_units = ['KG', 'G', 'LB', 'OZ', 'TON', 'MT']
            if any(unit in sap_code for unit in weight_units) or 'WEIGHT' in sap_name:
                return 'weight'
            
            # Volume units
            volume_units = ['L', 'ML', 'GAL', 'LTR', 'M3', 'CM3']
            if any(unit in sap_code for unit in volume_units) or 'VOLUME' in sap_name:
                return 'volume'
            
            # Length units
            length_units = ['M', 'CM', 'MM', 'IN', 'FT', 'YD']
            if any(unit in sap_code for unit in length_units) or 'LENGTH' in sap_name:
                return 'length'
            
            # Area units
            area_units = ['M2', 'CM2', 'FT2', 'SQ', 'AREA']
            if any(unit in sap_code for unit in area_units) or 'AREA' in sap_name:
                return 'area'
            
            # Time units
            time_units = ['H', 'MIN', 'SEC', 'DAY', 'WEEK', 'MONTH', 'YEAR']
            if any(unit in sap_code for unit in time_units) or 'TIME' in sap_name:
                return 'time'
            
            # Count units
            count_units = ['EA', 'PCS', 'UNIT', 'PIECE', 'ITEM']
            if any(unit in sap_code for unit in count_units) or 'COUNT' in sap_name:
                return 'count'
            
            # Default to other
            return 'other'
            
        except Exception as e:
            _logger.error(f"Error determining UoM category: {str(e)}")
            return 'other'
    
    @api.model
    def sync_uom_from_sap(self, backend_id, sap_uom_data_list):
        """Sync UoM mappings from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            if not backend.exists():
                raise SapValidationError(f"SAP Backend with ID {backend_id} not found")
            
            sync_results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for sap_uom_data in sap_uom_data_list:
                try:
                    sync_results['total_processed'] += 1
                    
                    # Check if mapping already exists
                    existing_mapping = self.search([
                        ('sap_uom_code', '=', sap_uom_data.get('UoMCode', ''))
                    ], limit=1)
                    
                    if existing_mapping:
                        # Update existing mapping
                        existing_mapping.write({
                            'sap_uom_name': sap_uom_data.get('UoMName', ''),
                            'active': True
                        })
                        sync_results['successful'] += 1
                    else:
                        # Create new mapping
                        self.create_mapping_from_sap(sap_uom_data)
                        sync_results['successful'] += 1
                        
                except Exception as e:
                    _logger.error(f"Error syncing UoM {sap_uom_data}: {str(e)}")
                    sync_results['failed'] += 1
            
            _logger.info(f"UoM sync completed: {sync_results}")
            
            return sync_results
            
        except Exception as e:
            _logger.error(f"Error syncing UoM from SAP: {str(e)}")
            raise SapValidationError(f"Failed to sync UoM from SAP: {str(e)}")
    
    def action_validate_mapping(self):
        """Validate UoM mapping"""
        self._validate_mapping()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Validation Complete',
                'message': f'UoM mapping validation completed. Status: {self.validation_status}',
                'type': 'success' if self.validation_status == 'valid' else 'warning'
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
            'context': {'default_mapping_id': self.id}
        }
