# -*- coding: utf-8 -*-

from odoo import models, api
import json


class ReportCustomerLabel(models.AbstractModel):
    _name = 'report.product_label_designer.report_customer_label'
    _description = 'Customer Label Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data and dict(data) or {}
        partners = self.env['res.partner'].browse(docids)
        
        # Parse customer_data from JSON string if it's a string
        customer_data = data.get('customer_data', {})
        if isinstance(customer_data, str):
            try:
                customer_data = json.loads(customer_data)
            except (json.JSONDecodeError, ValueError):
                customer_data = {}
        
        # Invoice type mapping
        invoice_type_map = {
            '1': 'زبون محل',
            '2': 'شركات توصيل',
            '3': 'نقليات',
            '4': 'ديلفري',
            '5': 'NBS',
            '6': 'شورجة',
            '7': 'NA',
            '8': 'مكاتب الشورجة',
        }
        
        # Process customer data
        processed_customer_data = {}
        for partner_id, partner_data in customer_data.items():
            invoice_type = partner_data.get('invoice_type', '')
            # If invoice_type_display is already provided, use it, otherwise map it
            invoice_type_display = partner_data.get('invoice_type_display', '')
            if not invoice_type_display and invoice_type:
                # Ensure invoice_type is a string for mapping
                invoice_type_str = str(invoice_type) if invoice_type else ''
                invoice_type_display = invoice_type_map.get(invoice_type_str, '')
            processed_customer_data[str(partner_id)] = {
                'phone': partner_data.get('phone', ''),
                'mobile': partner_data.get('mobile', ''),
                'invoice_type': invoice_type,
                'invoice_type_display': invoice_type_display,
            }
        
        # Get template
        template_id = data.get('template_id')
        if template_id:
            template = self.env['customer.label.template'].browse(int(template_id))
        else:
            template = self.env['customer.label.template'].get_default_template()
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partners,
            'data': data,
            'template': template,
            'copies': int(data.get('copies', 1)),
            'customer_data': processed_customer_data,
            'note': data.get('note', ''),
            'invoice_type_map': invoice_type_map,
        }


class ReportCustomerLabelA4(models.AbstractModel):
    _name = 'report.product_label_designer.report_customer_label_a4'
    _description = 'Customer Label Report A4'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data and dict(data) or {}
        partners = self.env['res.partner'].browse(docids)
        
        # Parse customer_data from JSON string if it's a string
        customer_data = data.get('customer_data', {})
        if isinstance(customer_data, str):
            try:
                customer_data = json.loads(customer_data)
            except (json.JSONDecodeError, ValueError):
                customer_data = {}
        
        # Invoice type mapping
        invoice_type_map = {
            '1': 'زبون محل',
            '2': 'شركات توصيل',
            '3': 'نقليات',
            '4': 'ديلفري',
            '5': 'NBS',
            '6': 'شورجة',
            '7': 'NA',
            '8': 'مكاتب الشورجة',
        }
        
        # Process customer data
        processed_customer_data = {}
        for partner_id, partner_data in customer_data.items():
            invoice_type = partner_data.get('invoice_type', '')
            # If invoice_type_display is already provided, use it, otherwise map it
            invoice_type_display = partner_data.get('invoice_type_display', '')
            if not invoice_type_display and invoice_type:
                # Ensure invoice_type is a string for mapping
                invoice_type_str = str(invoice_type) if invoice_type else ''
                invoice_type_display = invoice_type_map.get(invoice_type_str, '')
            processed_customer_data[str(partner_id)] = {
                'phone': partner_data.get('phone', ''),
                'mobile': partner_data.get('mobile', ''),
                'invoice_type': invoice_type,
                'invoice_type_display': invoice_type_display,
            }
        
        # Get template
        template_id = data.get('template_id')
        if template_id:
            template = self.env['customer.label.template'].browse(int(template_id))
        else:
            template = self.env['customer.label.template'].get_default_template()
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partners,
            'data': data,
            'template': template,
            'copies': int(data.get('copies', 1)),
            'customer_data': processed_customer_data,
            'note': data.get('note', ''),
            'invoice_type_map': invoice_type_map,
        }


class ReportCustomerLabelDirect(models.AbstractModel):
    _name = 'report.product_label_designer.report_customer_label_direct'
    _description = 'Customer Label Report Direct Print'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for direct printing with actual label dimensions"""
        import logging
        _logger = logging.getLogger(__name__)
        
        # Get data from context or parameter
        # In Odoo, URL parameters come as **kwargs to report_routes, which passes them as data
        # Also, Odoo's report_routes automatically parses 'options' parameter from URL
        data = data and dict(data) or {}
        _logger.info("ReportCustomerLabelDirect: Initial data parameter keys: %s", list(data.keys()) if data else [])
        
        # Odoo's report_routes automatically parses 'options' from URL and merges it into data
        # So customer_data should already be in data if it was passed via options
        # But we also check direct URL parameters as fallback
        if not data.get('customer_data'):
            try:
                from odoo.http import request
                if request and hasattr(request, 'httprequest'):
                    # Try to get from request args (URL parameters) as fallback
                    if hasattr(request.httprequest, 'args') and request.httprequest.args:
                        import urllib.parse
                        # Get all parameters from URL
                        params = {}
                        for key, value in request.httprequest.args.items():
                            params[key] = value
                        
                        _logger.info("ReportCustomerLabelDirect: URL params: %s", list(params.keys()))
                        
                        if 'customer_data' in params:
                            # URL decode the customer_data
                            customer_data_param = urllib.parse.unquote(params.get('customer_data', '{}'))
                            data['customer_data'] = customer_data_param
                            _logger.info("ReportCustomerLabelDirect: Customer data from URL (first 200 chars): %s", customer_data_param[:200] if len(customer_data_param) > 200 else customer_data_param)
                        if 'template_id' in params:
                            data['template_id'] = params.get('template_id')
                        if 'copies' in params:
                            data['copies'] = params.get('copies', '1')
                        if 'note' in params:
                            data['note'] = urllib.parse.unquote(params.get('note', ''))
            except (ImportError, AttributeError, TypeError) as e:
                _logger.warning("ReportCustomerLabelDirect: Error getting data from request: %s", str(e))
        
        _logger.info("ReportCustomerLabelDirect: Final data dict keys: %s", list(data.keys()) if data else [])
        _logger.info("ReportCustomerLabelDirect: Has customer_data: %s", bool(data.get('customer_data')))
        
        partners = self.env['res.partner'].browse(docids)
        
        # Parse customer_data from JSON string if it's a string
        # Note: If data comes from 'options' parameter, Odoo already parses it, so customer_data should be a dict
        customer_data = data.get('customer_data', {})
        _logger.info("ReportCustomerLabelDirect: customer_data type: %s, value: %s", type(customer_data), customer_data)
        
        if isinstance(customer_data, str):
            try:
                customer_data = json.loads(customer_data)
                _logger.info("ReportCustomerLabelDirect: Parsed customer_data from string: %s", customer_data)
            except (json.JSONDecodeError, ValueError) as e:
                _logger.error("ReportCustomerLabelDirect: Error parsing customer_data JSON: %s, raw data: %s", str(e), customer_data[:200] if len(customer_data) > 200 else customer_data)
                customer_data = {}
        elif isinstance(customer_data, dict):
            _logger.info("ReportCustomerLabelDirect: customer_data is already a dict: %s", customer_data)
        else:
            _logger.warning("ReportCustomerLabelDirect: customer_data is unexpected type: %s, value: %s", type(customer_data), customer_data)
            customer_data = {}
        
        # Invoice type mapping
        invoice_type_map = {
            '1': 'زبون محل',
            '2': 'شركات توصيل',
            '3': 'نقليات',
            '4': 'ديلفري',
            '5': 'NBS',
            '6': 'شورجة',
            '7': 'NA',
            '8': 'مكاتب الشورجة',
        }
        
        # Invoice type mapping
        invoice_type_map = {
            '1': 'زبون محل',
            '2': 'شركات توصيل',
            '3': 'نقليات',
            '4': 'ديلفري',
            '5': 'NBS',
            '6': 'شورجة',
            '7': 'NA',
            '8': 'مكاتب الشورجة',
        }
        
        # Process customer data
        processed_customer_data = {}
        _logger.info("ReportCustomerLabelDirect: Processing customer_data with %d partners", len(customer_data))
        for partner_id, partner_data in customer_data.items():
            invoice_type = partner_data.get('invoice_type', '')
            # If invoice_type_display is already provided, use it, otherwise map it
            invoice_type_display = partner_data.get('invoice_type_display', '')
            if not invoice_type_display and invoice_type:
                # Ensure invoice_type is a string for mapping
                invoice_type_str = str(invoice_type) if invoice_type else ''
                invoice_type_display = invoice_type_map.get(invoice_type_str, '')
                _logger.info("ReportCustomerLabelDirect: Partner %s - invoice_type=%s, invoice_type_display=%s", partner_id, invoice_type_str, invoice_type_display)
            elif invoice_type_display:
                _logger.info("ReportCustomerLabelDirect: Partner %s - Using provided invoice_type_display=%s", partner_id, invoice_type_display)
            else:
                _logger.warning("ReportCustomerLabelDirect: Partner %s - No invoice_type found", partner_id)
            
            processed_customer_data[str(partner_id)] = {
                'phone': partner_data.get('phone', ''),
                'mobile': partner_data.get('mobile', ''),
                'invoice_type': invoice_type,
                'invoice_type_display': invoice_type_display,
            }
        
        _logger.info("ReportCustomerLabelDirect: Final processed_customer_data: %s", processed_customer_data)
        
        # Get template
        template_id = data.get('template_id')
        if template_id:
            template = self.env['customer.label.template'].browse(int(template_id))
        else:
            template = self.env['customer.label.template'].get_default_template()
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partners,
            'data': data,
            'template': template,
            'copies': int(data.get('copies', 1)),
            'customer_data': processed_customer_data,
            'note': data.get('note', ''),
            'invoice_type_map': invoice_type_map,
        }


