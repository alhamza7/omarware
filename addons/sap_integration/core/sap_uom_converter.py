# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP UoM Converter

Advanced unit of measure conversion engine with precision handling and validation.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
import math
import json

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapUomConverter(SapBaseService):
    """Advanced UoM conversion engine"""
    _name = 'sap.uom.converter'
    _description = 'SAP UoM Converter'
    
    @api.model
    def convert_quantity(self, quantity, from_uom, to_uom, precision_digits=None, 
                        rounding_method='round', context=None):
        """
        Convert quantity between different units of measure
        
        :param quantity: Quantity to convert
        :param from_uom: Source UoM (SAP code or Odoo UoM record)
        :param to_uom: Target UoM (SAP code or Odoo UoM record)
        :param precision_digits: Number of decimal places for result
        :param rounding_method: Rounding method to use
        :param context: Additional context for conversion
        :return: Converted quantity
        """
        try:
            if not quantity or quantity == 0:
                return 0.0
            
            # Validate inputs
            self._validate_conversion_inputs(quantity, from_uom, to_uom)
            
            # Get conversion factor
            conversion_factor = self._get_conversion_factor(from_uom, to_uom, context)
            
            if conversion_factor is None:
                raise SapValidationError(f"No conversion factor found from {from_uom} to {to_uom}")
            
            # Perform conversion
            converted_quantity = quantity * conversion_factor
            
            # Apply precision and rounding
            if precision_digits is not None:
                converted_quantity = self._apply_precision_and_rounding(
                    converted_quantity, precision_digits, rounding_method
                )
            
            _logger.info(f"Converted {quantity} {from_uom} to {converted_quantity} {to_uom}")
            
            return converted_quantity
            
        except Exception as e:
            _logger.error(f"Error converting quantity: {str(e)}")
            raise SapValidationError(f"Failed to convert quantity: {str(e)}")
    
    def _validate_conversion_inputs(self, quantity, from_uom, to_uom):
        """Validate conversion inputs"""
        try:
            # Validate quantity
            if not isinstance(quantity, (int, float, Decimal)):
                raise SapValidationError("Quantity must be a number")
            
            if quantity < 0:
                raise SapValidationError("Quantity cannot be negative")
            
            # Validate UoMs
            if not from_uom or not to_uom:
                raise SapValidationError("Both source and target UoMs are required")
            
            if from_uom == to_uom:
                raise SapValidationError("Source and target UoMs cannot be the same")
            
        except Exception as e:
            _logger.error(f"Error validating conversion inputs: {str(e)}")
            raise
    
    def _get_conversion_factor(self, from_uom, to_uom, context=None):
        """Get conversion factor between two UoMs"""
        try:
            # Try direct mapping first
            factor = self._get_direct_conversion_factor(from_uom, to_uom)
            if factor is not None:
                return factor
            
            # Try reverse mapping
            factor = self._get_reverse_conversion_factor(from_uom, to_uom)
            if factor is not None:
                return factor
            
            # Try conversion through base unit
            factor = self._get_conversion_through_base_unit(from_uom, to_uom)
            if factor is not None:
                return factor
            
            # Try conversion through intermediate units
            factor = self._get_conversion_through_intermediate(from_uom, to_uom)
            if factor is not None:
                return factor
            
            return None
            
        except Exception as e:
            _logger.error(f"Error getting conversion factor: {str(e)}")
            return None
    
    def _get_direct_conversion_factor(self, from_uom, to_uom):
        """Get direct conversion factor"""
        try:
            # Handle different UoM types
            from_code = self._get_uom_code(from_uom)
            to_code = self._get_uom_code(to_uom)
            
            # Search for direct mapping
            mapping = self.env['sap.uom.mapping'].search([
                ('sap_uom_code', '=', from_code),
                ('odoo_uom_id.name', '=', to_code),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                return mapping.conversion_factor
            
            return None
            
        except Exception as e:
            _logger.error(f"Error getting direct conversion factor: {str(e)}")
            return None
    
    def _get_reverse_conversion_factor(self, from_uom, to_uom):
        """Get reverse conversion factor"""
        try:
            from_code = self._get_uom_code(from_uom)
            to_code = self._get_uom_code(to_uom)
            
            # Search for reverse mapping
            mapping = self.env['sap.uom.mapping'].search([
                ('sap_uom_code', '=', to_code),
                ('odoo_uom_id.name', '=', from_code),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                return mapping.inverse_factor
            
            return None
            
        except Exception as e:
            _logger.error(f"Error getting reverse conversion factor: {str(e)}")
            return None
    
    def _get_conversion_through_base_unit(self, from_uom, to_uom):
        """Get conversion factor through base unit"""
        try:
            from_code = self._get_uom_code(from_uom)
            to_code = self._get_uom_code(to_uom)
            
            # Get mappings to base units
            from_mapping = self.env['sap.uom.mapping'].search([
                ('sap_uom_code', '=', from_code),
                ('active', '=', True)
            ], limit=1)
            
            to_mapping = self.env['sap.uom.mapping'].search([
                ('sap_uom_code', '=', to_code),
                ('active', '=', True)
            ], limit=1)
            
            if from_mapping and to_mapping:
                # Check if they have the same base unit category
                if from_mapping.odoo_uom_id.category_id == to_mapping.odoo_uom_id.category_id:
                    # Calculate conversion through base unit
                    return from_mapping.conversion_factor / to_mapping.conversion_factor
            
            return None
            
        except Exception as e:
            _logger.error(f"Error getting conversion through base unit: {str(e)}")
            return None
    
    def _get_conversion_through_intermediate(self, from_uom, to_uom):
        """Get conversion factor through intermediate units"""
        try:
            # This would implement a more complex conversion path
            # through intermediate units (e.g., A -> B -> C)
            # For now, return None to keep it simple
            return None
            
        except Exception as e:
            _logger.error(f"Error getting conversion through intermediate: {str(e)}")
            return None
    
    def _get_uom_code(self, uom):
        """Get UoM code from various input types"""
        try:
            if isinstance(uom, str):
                return uom
            elif hasattr(uom, 'name'):
                return uom.name
            elif hasattr(uom, 'sap_uom_code'):
                return uom.sap_uom_code
            else:
                return str(uom)
                
        except Exception as e:
            _logger.error(f"Error getting UoM code: {str(e)}")
            return str(uom)
    
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
                rounded_quantity = rounded_quantity.quantize(precision, rounding=ROUND_DOWN)
            elif rounding_method == 'ceil':
                rounded_quantity = rounded_quantity.quantize(precision, rounding=ROUND_UP)
            elif rounding_method == 'trunc':
                rounded_quantity = rounded_quantity.quantize(precision, rounding=ROUND_DOWN)
            
            return float(rounded_quantity)
            
        except Exception as e:
            _logger.error(f"Error applying precision and rounding: {str(e)}")
            return quantity
    
    @api.model
    def convert_product_quantities(self, product_id, quantities, target_uom, context=None):
        """
        Convert multiple quantities for a product to target UoM
        
        :param product_id: Product ID
        :param quantities: Dictionary of quantities by UoM
        :param target_uom: Target UoM
        :param context: Additional context
        :return: Dictionary of converted quantities
        """
        try:
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                raise SapValidationError(f"Product with ID {product_id} not found")
            
            converted_quantities = {}
            total_quantity = 0.0
            
            for uom, quantity in quantities.items():
                if quantity and quantity > 0:
                    try:
                        converted_qty = self.convert_quantity(
                            quantity, uom, target_uom, context=context
                        )
                        converted_quantities[uom] = converted_qty
                        total_quantity += converted_qty
                        
                    except Exception as e:
                        _logger.warning(f"Failed to convert {quantity} {uom} to {target_uom}: {str(e)}")
                        converted_quantities[uom] = 0.0
            
            converted_quantities['total'] = total_quantity
            
            return converted_quantities
            
        except Exception as e:
            _logger.error(f"Error converting product quantities: {str(e)}")
            raise SapValidationError(f"Failed to convert product quantities: {str(e)}")
    
    @api.model
    def validate_uom_compatibility(self, uom1, uom2):
        """
        Validate if two UoMs are compatible for conversion
        
        :param uom1: First UoM
        :param uom2: Second UoM
        :return: Boolean indicating compatibility
        """
        try:
            # Get UoM codes
            code1 = self._get_uom_code(uom1)
            code2 = self._get_uom_code(uom2)
            
            if code1 == code2:
                return True
            
            # Check if conversion factor exists
            factor = self._get_conversion_factor(uom1, uom2)
            return factor is not None
            
        except Exception as e:
            _logger.error(f"Error validating UoM compatibility: {str(e)}")
            return False
    
    @api.model
    def get_conversion_chain(self, from_uom, to_uom):
        """
        Get the conversion chain from one UoM to another
        
        :param from_uom: Source UoM
        :param to_uom: Target UoM
        :return: List of conversion steps
        """
        try:
            chain = []
            
            # Try direct conversion
            factor = self._get_direct_conversion_factor(from_uom, to_uom)
            if factor is not None:
                chain.append({
                    'from': from_uom,
                    'to': to_uom,
                    'factor': factor,
                    'type': 'direct'
                })
                return chain
            
            # Try reverse conversion
            factor = self._get_reverse_conversion_factor(from_uom, to_uom)
            if factor is not None:
                chain.append({
                    'from': from_uom,
                    'to': to_uom,
                    'factor': factor,
                    'type': 'reverse'
                })
                return chain
            
            # Try conversion through base unit
            factor = self._get_conversion_through_base_unit(from_uom, to_uom)
            if factor is not None:
                chain.append({
                    'from': from_uom,
                    'to': to_uom,
                    'factor': factor,
                    'type': 'base_unit'
                })
                return chain
            
            return []
            
        except Exception as e:
            _logger.error(f"Error getting conversion chain: {str(e)}")
            return []
    
    @api.model
    def create_conversion_rule(self, from_uom, to_uom, factor, precision_digits=2, 
                              rounding_method='round', active=True):
        """
        Create a new conversion rule
        
        :param from_uom: Source UoM
        :param to_uom: Target UoM
        :param factor: Conversion factor
        :param precision_digits: Number of decimal places
        :param rounding_method: Rounding method
        :param active: Whether the rule is active
        :return: Created mapping record
        """
        try:
            from_code = self._get_uom_code(from_uom)
            to_code = self._get_uom_code(to_uom)
            
            # Find or create Odoo UoM
            odoo_uom = self._find_or_create_odoo_uom(to_code)
            
            # Create mapping
            mapping_vals = {
                'sap_uom_code': from_code,
                'odoo_uom_id': odoo_uom.id,
                'conversion_factor': factor,
                'precision_digits': precision_digits,
                'rounding_method': rounding_method,
                'active': active,
                'usage_type': 'all'
            }
            
            mapping = self.env['sap.uom.mapping'].create(mapping_vals)
            
            _logger.info(f"Created conversion rule: {from_code} → {to_code} (factor: {factor})")
            
            return mapping
            
        except Exception as e:
            _logger.error(f"Error creating conversion rule: {str(e)}")
            raise SapValidationError(f"Failed to create conversion rule: {str(e)}")
    
    def _find_or_create_odoo_uom(self, uom_code):
        """Find or create Odoo UoM"""
        try:
            # Try to find existing UoM
            odoo_uom = self.env['uom.uom'].search([
                ('name', '=', uom_code)
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
                'name': uom_code,
                'category_id': category.id,
                'factor': 1.0,
                'uom_type': 'reference',
                'active': True
            })
            
            return odoo_uom
            
        except Exception as e:
            _logger.error(f"Error finding or creating Odoo UoM: {str(e)}")
            raise SapValidationError(f"Failed to find or create Odoo UoM: {str(e)}")
    
    @api.model
    def get_conversion_statistics(self, days_back=30):
        """Get conversion statistics"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days_back))
            ]
            
            mappings = self.env['sap.uom.mapping'].search(domain)
            
            stats = {
                'total_mappings': len(mappings),
                'active_mappings': len(mappings.filtered('active')),
                'valid_mappings': len(mappings.filtered(lambda m: m.validation_status == 'valid')),
                'warning_mappings': len(mappings.filtered(lambda m: m.validation_status == 'warning')),
                'error_mappings': len(mappings.filtered(lambda m: m.validation_status == 'error')),
                'by_category': {},
                'by_usage_type': {}
            }
            
            # Group by category
            for mapping in mappings:
                category = mapping.uom_category
                if category not in stats['by_category']:
                    stats['by_category'][category] = 0
                stats['by_category'][category] += 1
            
            # Group by usage type
            for mapping in mappings:
                usage_type = mapping.usage_type
                if usage_type not in stats['by_usage_type']:
                    stats['by_usage_type'][usage_type] = 0
                stats['by_usage_type'][usage_type] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting conversion statistics: {str(e)}")
            return {}
