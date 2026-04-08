# -*- coding: utf-8 -*-

import logging
import base64
from io import BytesIO
from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    _logger.warning('python-barcode not installed. Barcode generation will not work.')


class NBSBarcodeService(models.AbstractModel):
    _name = 'nbs.barcode.service'
    _description = 'Barcode Generation Service'
    
    @api.model
    def generate_barcode_image(self, barcode_value, barcode_type='code128'):
        """
        Generate barcode image
        
        Args:
            barcode_value: String value to encode
            barcode_type: Type of barcode (code128, ean13, etc.)
        
        Returns:
            Base64 encoded image string, or None if failed
        """
        if not BARCODE_AVAILABLE:
            _logger.error('Barcode library not available')
            return None
        
        try:
            # Get barcode class
            barcode_class = barcode.get_barcode_class(barcode_type)
            
            # Generate barcode
            barcode_instance = barcode_class(barcode_value, writer=ImageWriter())
            
            # Render to bytes
            buffer = BytesIO()
            barcode_instance.write(buffer, options={
                'module_width': 0.3,
                'module_height': 15.0,
                'text_distance': 5.0,
                'font_size': 10,
                'quiet_zone': 5.0,
            })
            
            # Encode to base64
            buffer.seek(0)
            barcode_b64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            return barcode_b64
        
        except Exception as e:
            _logger.error(f'Barcode generation failed: {e}')
            return None
    
    @api.model
    def test_barcode_generation(self):
        """Test barcode generation"""
        if not BARCODE_AVAILABLE:
            return {'available': False, 'error': 'python-barcode not installed'}
        
        try:
            test_value = 'TEST123456'
            result = self.generate_barcode_image(test_value)
            
            return {
                'available': True,
                'test_successful': result is not None
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}


