# -*- coding: utf-8 -*-

from odoo import http
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

