# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
import logging
import json


_logger = logging.getLogger(__name__)


class LabelDesignerController(http.Controller):
    
    @http.route('/label_designer/<int:template_id>', type='http', auth='user', website=True)
    def label_designer(self, template_id, **kwargs):
        """Visual label designer interface for product labels"""
        template = request.env['product.label.template'].browse(template_id)
        
        if not template.exists():
            return request.not_found()
        
        # Get a sample product for preview
        sample_product = request.env['product.product'].search([], limit=1)
        
        return request.render('product_label_designer.label_designer_template', {
            'template': template,
            'sample_product': sample_product,
        })
    
    @http.route('/label_designer/customer/<int:template_id>', type='http', auth='user', website=True)
    def customer_label_designer(self, template_id, **kwargs):
        """Visual label designer interface for customer labels"""
        template = request.env['customer.label.template'].browse(template_id)
        
        if not template.exists():
            return request.not_found()
        
        # Get a sample customer for preview
        sample_partner = request.env['res.partner'].search([], limit=1)
        
        return request.render('product_label_designer.customer_label_designer_template', {
            'template': template,
            'sample_partner': sample_partner,
        })
    
    @http.route('/label_designer/save_positions', type='json', auth='user', methods=['POST'], csrf=False)
    def save_positions(self, template_id, positions):
        """Save element positions for product labels"""
        try:
            _logger.debug('save_positions called with template_id=%s positions=%s', template_id, positions)
            template = request.env['product.label.template'].browse(template_id)
            if template.exists():
                template.write(positions)
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('save_positions failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/customer/save_positions', type='json', auth='user', methods=['POST'], csrf=False)
    def save_customer_positions(self, template_id, positions):
        """Save element positions for customer labels"""
        try:
            _logger.debug('save_customer_positions called with template_id=%s positions=%s', template_id, positions)
            template = request.env['customer.label.template'].browse(template_id)
            if template.exists():
                template.write(positions)
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('save_customer_positions failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/upload_image', type='json', auth='user', methods=['POST'], csrf=False)
    def upload_image(self, template_id, image_type, image_data):
        """Upload background or logo image for product labels"""
        try:
            _logger.debug('upload_image called with template_id=%s image_type=%s size=%s', template_id, image_type, len(image_data) if image_data else 0)
            template = request.env['product.label.template'].browse(template_id)
            if template.exists():
                if image_type == 'background':
                    template.write({'background_image': image_data})
                elif image_type == 'logo':
                    template.write({'logo_image': image_data})
                else:
                    return {'success': False, 'error': 'Invalid image type'}
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('upload_image failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/remove_image', type='json', auth='user', methods=['POST'], csrf=False)
    def remove_image(self, template_id, image_type):
        """Remove background or logo image for product labels"""
        try:
            _logger.debug('remove_image called with template_id=%s image_type=%s', template_id, image_type)
            template = request.env['product.label.template'].browse(template_id)
            if template.exists():
                if image_type == 'background':
                    template.write({'background_image': False})
                elif image_type == 'logo':
                    template.write({'logo_image': False})
                else:
                    return {'success': False, 'error': 'Invalid image type'}
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('remove_image failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/customer/upload_image', type='json', auth='user', methods=['POST'], csrf=False)
    def upload_customer_image(self, template_id, image_type, image_data):
        """Upload background or logo image for customer labels"""
        try:
            _logger.debug('upload_customer_image called with template_id=%s image_type=%s size=%s', template_id, image_type, len(image_data) if image_data else 0)
            template = request.env['customer.label.template'].browse(template_id)
            if template.exists():
                if image_type == 'background':
                    template.write({'background_image': image_data})
                elif image_type == 'logo':
                    template.write({'logo_image': image_data})
                else:
                    return {'success': False, 'error': 'Invalid image type'}
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('upload_customer_image failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/customer/remove_image', type='json', auth='user', methods=['POST'], csrf=False)
    def remove_customer_image(self, template_id, image_type):
        """Remove background or logo image for customer labels"""
        try:
            _logger.debug('remove_customer_image called with template_id=%s image_type=%s', template_id, image_type)
            template = request.env['customer.label.template'].browse(template_id)
            if template.exists():
                if image_type == 'background':
                    template.write({'background_image': False})
                elif image_type == 'logo':
                    template.write({'logo_image': False})
                else:
                    return {'success': False, 'error': 'Invalid image type'}
                return {'success': True}
            return {'success': False, 'error': 'Template not found'}
        except Exception as e:
            _logger.exception('remove_customer_image failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/label_designer/preview', type='json', auth='user', methods=['POST'], csrf=False)
    def preview_label(self, template_id, product_id):
        """Get preview HTML"""
        try:
            _logger.debug('preview_label called with template_id=%s product_id=%s', template_id, product_id)
            template = request.env['product.label.template'].browse(template_id)
            product = request.env['product.product'].browse(product_id)
            if template.exists() and product.exists():
                html = request.env['ir.qweb']._render('product_label_designer.label_preview_content', {
                    'template': template,
                    'product': product,
                })
                return {'success': True, 'html': html}
            return {'success': False, 'error': 'Record not found'}
        except Exception as e:
            _logger.exception('preview_label failed: %s', e)
            return {'success': False, 'error': str(e)}
    
    # SAP Continuous Label Printing Routes
    
    @http.route('/sap/label/printer', type='http', auth='user', website=True)
    def sap_label_printer_interface(self, **kwargs):
        """Continuous SAP label printing interface"""
        # Get default or first SAP-enabled template
        template = request.env['product.label.template'].search([
            ('sap_mode_enabled', '=', True),
            ('active', '=', True)
        ], limit=1)
        
        if not template:
            # Get first active template
            template = request.env['product.label.template'].search([
                ('active', '=', True)
            ], limit=1)
        
        return request.render('product_label_designer.sap_label_printer_interface', {
            'template': template,
        })
    
    @http.route('/sap/label/lookup', type='json', auth='user', methods=['POST'], csrf=False)
    def sap_product_lookup(self, barcode, template_id):
        """Lookup product by barcode from local data and prepare for printing"""
        try:
            _logger.info(f'Product lookup for barcode: {barcode}, template: {template_id}')
            
            template = request.env['product.label.template'].browse(template_id)
            if not template.exists():
                return {'success': False, 'error': 'Template not found'}
            
            # Get product info from local data
            result = template.get_product_info_by_barcode(barcode)
            
            if not result.get('success'):
                return result
            
            # Product found in local data
            product_id = result.get('product_id')
            
            # Generate print URL (use HTML report for auto-print)
            # Pass scanned barcode as URL parameter so it can be printed instead of product barcode
            import urllib.parse
            print_url = f'/report/html/product_label_designer.report_label_simple_html/{product_id}?template_id={template_id}&scanned_barcode={urllib.parse.quote(barcode)}'
            
            return {
                'success': True,
                'product_id': product_id,
                'product_name': result.get('product_name', ''),
                'display_name': result.get('display_name', ''),
                'uom': result.get('uom', ''),
                'barcode': barcode,
                'print_url': print_url,
            }
            
        except Exception as e:
            _logger.exception(f'SAP lookup failed: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/sap/label/print', type='json', auth='user', methods=['POST'], csrf=False)
    def sap_print_label(self, product_id, template_id):
        """Trigger immediate label printing"""
        try:
            product = request.env['product.product'].browse(product_id)
            template = request.env['product.label.template'].browse(template_id)
            
            if not product.exists() or not template.exists():
                return {'success': False, 'error': 'Product or template not found'}
            
            # Generate label PDF
            pdf = request.env.ref('product_label_designer.action_report_label_simple')._render_qweb_pdf([product.id], data={'template_id': template_id})[0]
            
            return {
                'success': True,
                'product_id': product.id,
                'product_name': product.sap_product_name or product.name,
            }
            
        except Exception as e:
            _logger.exception(f'SAP print failed: {e}')
            return {
                'success': False,
                'error': str(e)
            }

