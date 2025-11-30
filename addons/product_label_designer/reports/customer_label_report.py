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
            processed_customer_data[str(partner_id)] = {
                'phone': partner_data.get('phone', ''),
                'mobile': partner_data.get('mobile', ''),
                'invoice_type': partner_data.get('invoice_type', ''),
                'invoice_type_display': invoice_type_map.get(partner_data.get('invoice_type', ''), ''),
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
            processed_customer_data[str(partner_id)] = {
                'phone': partner_data.get('phone', ''),
                'mobile': partner_data.get('mobile', ''),
                'invoice_type': partner_data.get('invoice_type', ''),
                'invoice_type_display': invoice_type_map.get(partner_data.get('invoice_type', ''), ''),
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


