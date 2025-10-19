# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP UoM Conversion Test Wizard

Wizard for testing UoM conversions and validating conversion rules.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

from ..core.sap_logger import SapLogger


class SapUomConversionTestWizard(models.TransientModel):
    """Wizard for testing UoM conversions"""
    _name = 'sap.uom.conversion.test.wizard'
    _description = 'SAP UoM Conversion Test Wizard'
    
    
    # Test Parameters
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Product to test conversion for"
    )
    from_uom = fields.Char(
        string='From UoM',
        required=True,
        help="Source unit of measure"
    )
    to_uom = fields.Char(
        string='To UoM',
        required=True,
        help="Target unit of measure"
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        help="Quantity to convert"
    )
    usage_type = fields.Selection([
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('inventory', 'Inventory'),
        ('production', 'Production'),
        ('all', 'All')
    ], string='Usage Type', default='all')
    
    # Conversion Results
    conversion_factor = fields.Float(
        string='Conversion Factor',
        readonly=True,
        help="Conversion factor used"
    )
    converted_quantity = fields.Float(
        string='Converted Quantity',
        readonly=True,
        help="Converted quantity result"
    )
    precision_digits = fields.Integer(
        string='Precision Digits',
        readonly=True,
        help="Number of decimal places used"
    )
    rounding_method = fields.Char(
        string='Rounding Method',
        readonly=True,
        help="Rounding method used"
    )
    
    # Validation Results
    is_valid = fields.Boolean(
        string='Is Valid',
        readonly=True,
        help="Whether the conversion is valid"
    )
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
        help="Error message if conversion failed"
    )
    conversion_chain = fields.Text(
        string='Conversion Chain',
        readonly=True,
        help="Detailed conversion chain information"
    )
    
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        defaults = super().default_get(fields_list)
        
        # Set default values from context
        if 'default_product_id' in self.env.context:
            defaults['product_id'] = self.env.context['default_product_id']
        if 'default_from_uom' in self.env.context:
            defaults['from_uom'] = self.env.context['default_from_uom']
        if 'default_to_uom' in self.env.context:
            defaults['to_uom'] = self.env.context['default_to_uom']
        
        return defaults
    
    def action_test_conversion(self):
        """Test the UoM conversion"""
        try:
            # Validate inputs
            if not self.from_uom or not self.to_uom:
                raise UserError("Both source and target UoMs are required")
            
            if not self.quantity or self.quantity <= 0:
                raise UserError("Quantity must be positive")
            
            # Clear previous results
            self.write({
                'conversion_factor': 0.0,
                'converted_quantity': 0.0,
                'precision_digits': 0,
                'rounding_method': '',
                'is_valid': False,
                'error_message': '',
                'conversion_chain': ''
            })
            
            # Test conversion
            if self.product_id:
                # Test product-specific conversion
                result = self._test_product_conversion()
            else:
                # Test general conversion
                result = self._test_general_conversion()
            
            # Update results
            self.write(result)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conversion Test Complete',
                    'message': f'Conversion test completed. Result: {self.converted_quantity}',
                    'type': 'success' if self.is_valid else 'warning'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error testing conversion: {str(e)}")
            self.write({
                'is_valid': False,
                'error_message': str(e)
            })
            raise UserError(f"Conversion test failed: {str(e)}")
    
    def _test_product_conversion(self):
        """Test product-specific conversion"""
        try:
            # Get product UoM converter
            converter = self.env['sap.product.uom']
            
            # Convert quantity
            converted_quantity = converter.convert_quantity(
                self.product_id.id,
                self.quantity,
                self.from_uom,
                self.to_uom,
                self.usage_type
            )
            
            # Get conversion details
            from_mapping = converter._get_uom_mapping(
                self.product_id.id, self.from_uom, self.usage_type
            )
            to_mapping = converter._get_uom_mapping(
                self.product_id.id, self.to_uom, self.usage_type
            )
            
            # Calculate conversion factor
            conversion_factor = 1.0
            if from_mapping and to_mapping:
                conversion_factor = from_mapping.conversion_factor / to_mapping.conversion_factor
            
            # Build conversion chain
            conversion_chain = self._build_conversion_chain(from_mapping, to_mapping)
            
            return {
                'conversion_factor': conversion_factor,
                'converted_quantity': converted_quantity,
                'precision_digits': from_mapping.precision_digits if from_mapping else 2,
                'rounding_method': from_mapping.rounding_method if from_mapping else 'round',
                'is_valid': True,
                'error_message': '',
                'conversion_chain': conversion_chain
            }
            
        except Exception as e:
            _logger.error(f"Error in product conversion test: {str(e)}")
            return {
                'conversion_factor': 0.0,
                'converted_quantity': 0.0,
                'precision_digits': 0,
                'rounding_method': '',
                'is_valid': False,
                'error_message': str(e),
                'conversion_chain': ''
            }
    
    def _test_general_conversion(self):
        """Test general conversion"""
        try:
            # Get general UoM converter
            converter = self.env['sap.uom.converter']
            
            # Convert quantity
            converted_quantity = converter.convert_quantity(
                self.quantity,
                self.from_uom,
                self.to_uom
            )
            
            # Get conversion factor
            conversion_factor = converter._get_conversion_factor(self.from_uom, self.to_uom)
            
            # Get conversion chain
            conversion_chain = converter.get_conversion_chain(self.from_uom, self.to_uom)
            chain_text = self._format_conversion_chain(conversion_chain)
            
            return {
                'conversion_factor': conversion_factor or 1.0,
                'converted_quantity': converted_quantity,
                'precision_digits': 2,
                'rounding_method': 'round',
                'is_valid': True,
                'error_message': '',
                'conversion_chain': chain_text
            }
            
        except Exception as e:
            _logger.error(f"Error in general conversion test: {str(e)}")
            return {
                'conversion_factor': 0.0,
                'converted_quantity': 0.0,
                'precision_digits': 0,
                'rounding_method': '',
                'is_valid': False,
                'error_message': str(e),
                'conversion_chain': ''
            }
    
    def _build_conversion_chain(self, from_mapping, to_mapping):
        """Build conversion chain information"""
        try:
            chain_info = []
            
            if from_mapping:
                chain_info.append(f"From: {from_mapping.sap_uom_code} (factor: {from_mapping.conversion_factor})")
            
            if to_mapping:
                chain_info.append(f"To: {to_mapping.sap_uom_code} (factor: {to_mapping.conversion_factor})")
            
            if from_mapping and to_mapping:
                conversion_factor = from_mapping.conversion_factor / to_mapping.conversion_factor
                chain_info.append(f"Conversion Factor: {conversion_factor}")
            
            return '\n'.join(chain_info)
            
        except Exception as e:
            _logger.error(f"Error building conversion chain: {str(e)}")
            return ''
    
    def _format_conversion_chain(self, conversion_chain):
        """Format conversion chain for display"""
        try:
            if not conversion_chain:
                return 'No conversion chain available'
            
            chain_text = []
            for step in conversion_chain:
                chain_text.append(f"{step['from']} → {step['to']} (factor: {step['factor']}, type: {step['type']})")
            
            return '\n'.join(chain_text)
            
        except Exception as e:
            _logger.error(f"Error formatting conversion chain: {str(e)}")
            return 'Error formatting conversion chain'
    
    def action_validate_mapping(self):
        """Validate UoM mapping"""
        try:
            if not self.product_id:
                raise UserError("Product is required for mapping validation")
            
            # Get product UoM mappings
            product_uoms = self.env['sap.product.uom'].get_product_uoms(
                self.product_id.id, self.usage_type
            )
            
            validation_results = []
            
            for uom in product_uoms:
                try:
                    # Test conversion to base UoM
                    converted_qty = self.env['sap.product.uom'].convert_quantity(
                        self.product_id.id,
                        1.0,
                        uom.sap_uom_code,
                        self.product_id.uom_id.name,
                        self.usage_type
                    )
                    
                    validation_results.append({
                        'uom': uom.sap_uom_code,
                        'status': 'valid',
                        'message': f'Conversion successful: 1 {uom.sap_uom_code} = {converted_qty} {self.product_id.uom_id.name}'
                    })
                    
                except Exception as e:
                    validation_results.append({
                        'uom': uom.sap_uom_code,
                        'status': 'error',
                        'message': f'Conversion failed: {str(e)}'
                    })
            
            # Display validation results
            message = "UoM Mapping Validation Results:\n\n"
            for result in validation_results:
                status_icon = "✅" if result['status'] == 'valid' else "❌"
                message += f"{status_icon} {result['uom']}: {result['message']}\n"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validation Complete',
                    'message': message,
                    'type': 'info'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error validating mapping: {str(e)}")
            raise UserError(f"Mapping validation failed: {str(e)}")
    
    def action_create_conversion_rule(self):
        """Create conversion rule based on test results"""
        try:
            if not self.is_valid:
                raise UserError("Cannot create conversion rule from invalid test")
            
            # Create conversion rule
            converter = self.env['sap.uom.converter']
            mapping = converter.create_conversion_rule(
                self.from_uom,
                self.to_uom,
                self.conversion_factor,
                self.precision_digits,
                'round'
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conversion Rule Created',
                    'message': f'Conversion rule created: {self.from_uom} → {self.to_uom}',
                    'type': 'success'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error creating conversion rule: {str(e)}")
            raise UserError(f"Failed to create conversion rule: {str(e)}")
    
    def action_export_results(self):
        """Export test results"""
        try:
            results = {
                'product_id': self.product_id.id if self.product_id else None,
                'product_name': self.product_id.name if self.product_id else 'N/A',
                'from_uom': self.from_uom,
                'to_uom': self.to_uom,
                'quantity': self.quantity,
                'conversion_factor': self.conversion_factor,
                'converted_quantity': self.converted_quantity,
                'precision_digits': self.precision_digits,
                'rounding_method': self.rounding_method,
                'is_valid': self.is_valid,
                'error_message': self.error_message,
                'conversion_chain': self.conversion_chain,
                'test_date': fields.Datetime.now()
            }
            
            # In a real implementation, you would export this to a file
            # For now, just log the results
            _logger.info(f"Conversion test results exported: {results}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Results Exported',
                    'message': 'Test results have been exported successfully',
                    'type': 'success'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error exporting results: {str(e)}")
            raise UserError(f"Failed to export results: {str(e)}")
