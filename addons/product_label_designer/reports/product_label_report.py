# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class ReportProductLabelSimple(models.AbstractModel):
    """Report handler for simple product label printing (used by SAP integration)"""
    _name = 'report.product_label_designer.report_label_simple'
    _description = 'Product Label Simple Report'

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
        }


class ReportProductLabelSimpleHTML(models.AbstractModel):
    """Report handler for simple product label printing HTML (with auto-print)"""
    _name = 'report.product_label_designer.report_label_simple_html'
    _description = 'Product Label Simple Report HTML'

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
        
        _logger.info(f"Report values (HTML): products={products.ids}, template={template.id}, copies={copies}")
        
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'docs': products,
            'data': data,
            'template': template,
            'copies': copies,
        }

