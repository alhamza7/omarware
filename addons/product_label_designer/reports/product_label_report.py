# -*- coding: utf-8 -*-

from odoo import models, api
import logging
import base64
import io

_logger = logging.getLogger(__name__)


class ReportProductLabelSimple(models.AbstractModel):
    """Report handler for simple product label printing (used by SAP integration)"""
    _name = 'report.product_label_designer.report_label_simple'
    _description = 'Product Label Simple Report'

    @api.model
    def _generate_qr_code_base64(self, data, size=300):
        """
        Generate QR code using pure Python qrcode library (no reportlab dependency).
        Returns base64 encoded PNG image.
        """
        try:
            import qrcode
            from PIL import Image
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize to requested size
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('ascii')
            
            return f"data:image/png;base64,{img_base64}"
        except ImportError:
            _logger.error("qrcode library not installed. Install with: pip install qrcode[pil]")
            return None
        except Exception as e:
            _logger.error(f"Error generating QR code: {str(e)}")
            return None

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare report values for product label printing.
        Handles template_id from URL query parameters.
        """
        data = data and dict(data) or {}
        _logger.info(f"ReportProductLabelSimple: docids={docids}, data keys={list(data.keys()) if data else []}")
        
        # Get template from data or URL parameters
        template_id = data.get('template_id')
        
        # If not in data, try to get from request URL parameters
        if not template_id:
            try:
                from odoo.http import request
                if request and hasattr(request, 'httprequest'):
                    template_id = request.httprequest.args.get('template_id')
                    if template_id:
                        _logger.info(f"Got template_id from URL: {template_id}")
            except (ImportError, AttributeError, TypeError) as e:
                _logger.warning(f"Error getting template_id from request: {str(e)}")
        
        # Get template object
        if template_id:
            try:
                template = self.env['product.label.template'].browse(int(template_id))
                if not template.exists():
                    _logger.warning(f"Template {template_id} not found, using default")
                    template = self.env['product.label.template'].get_default_template()
            except (ValueError, TypeError) as e:
                _logger.warning(f"Invalid template_id {template_id}: {str(e)}, using default")
                template = self.env['product.label.template'].get_default_template()
        else:
            template = self.env['product.label.template'].get_default_template()
        
        # Get products
        products = self.env['product.product'].browse(docids)
        
        # Get number of copies
        copies = int(data.get('copies', 1))
        
        _logger.info(f"Report values: products={products.ids}, template={template.id}, copies={copies}")
        
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'docs': products,
            'data': data,
            'template': template,
            'copies': copies,
            'generate_qr': self._generate_qr_code_base64,  # Add helper function
        }


class ReportProductLabelSimpleHTML(models.AbstractModel):
    """Report handler for simple product label printing HTML (with auto-print)"""
    _name = 'report.product_label_designer.report_label_simple_html'
    _description = 'Product Label Simple Report HTML'

    @api.model
    def _generate_qr_code_base64(self, data, size=300):
        """
        Generate QR code using pure Python qrcode library (no reportlab dependency).
        Returns base64 encoded PNG image.
        """
        try:
            import qrcode
            from PIL import Image
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize to requested size
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('ascii')
            
            return f"data:image/png;base64,{img_base64}"
        except ImportError:
            _logger.error("qrcode library not installed. Install with: pip install qrcode[pil]")
            return None
        except Exception as e:
            _logger.error(f"Error generating QR code: {str(e)}")
            return None

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare report values for product label printing (HTML version with auto-print).
        Handles template_id from URL query parameters.
        """
        data = data and dict(data) or {}
        _logger.info(f"ReportProductLabelSimpleHTML: docids={docids}, data keys={list(data.keys()) if data else []}")
        
        # Get template from data or URL parameters
        template_id = data.get('template_id')
        scanned_barcode = data.get('scanned_barcode')  # Get the actual scanned barcode
        
        # If not in data, try to get from request URL parameters
        if not template_id or not scanned_barcode:
            try:
                from odoo.http import request
                if request and hasattr(request, 'httprequest'):
                    if not template_id:
                        template_id = request.httprequest.args.get('template_id')
                        if template_id:
                            _logger.info(f"Got template_id from URL: {template_id}")
                    if not scanned_barcode:
                        scanned_barcode = request.httprequest.args.get('scanned_barcode')
                        if scanned_barcode:
                            _logger.info(f"Got scanned_barcode from URL: {scanned_barcode}")
                            data['scanned_barcode'] = scanned_barcode
            except (ImportError, AttributeError, TypeError) as e:
                _logger.warning(f"Error getting parameters from request: {str(e)}")
        
        # Get template object
        if template_id:
            try:
                template = self.env['product.label.template'].browse(int(template_id))
                if not template.exists():
                    _logger.warning(f"Template {template_id} not found, using default")
                    template = self.env['product.label.template'].get_default_template()
            except (ValueError, TypeError) as e:
                _logger.warning(f"Invalid template_id {template_id}: {str(e)}, using default")
                template = self.env['product.label.template'].get_default_template()
        else:
            template = self.env['product.label.template'].get_default_template()
        
        # Get products
        products = self.env['product.product'].browse(docids)
        
        # Get number of copies
        copies = int(data.get('copies', 1))
        
        _logger.info(f"Report values (HTML): products={products.ids}, template={template.id}, copies={copies}, scanned_barcode={scanned_barcode}")
        
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'docs': products,
            'data': data,
            'template': template,
            'copies': copies,
            'generate_qr': self._generate_qr_code_base64,  # Add helper function
        }

