# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class PrintCustomerLabelWizard(models.TransientModel):
    _name = 'print.customer.label.wizard'
    _description = 'Print Customer Label Wizard'
    

    partner_ids = fields.Many2many('res.partner', string='Customers', required=True)
    template_id = fields.Many2one('customer.label.template', string='Label Template', 
                                   default=lambda self: self.env['customer.label.template'].get_default_template())
    copies = fields.Integer(string='Copies per Customer', default=1, required=True)
    print_mode = fields.Selection([
        ('single', 'Single Labels'),
        ('a4_sheet', 'A4 Sheet (Multiple Labels)')
    ], string='Print Mode', default='single', required=True)
    
    # Invoice Type - نفس الأنواع في pos_perfume
    invoice_type = fields.Selection([
        ('1', 'زبون محل'),
        ('2', 'شركات توصيل'),
        ('3', 'نقليات'),
        ('4', 'ديلفري'),
        ('5', 'NBS'),
        ('6', 'شورجة'),
        ('7', 'NA'),
        ('8', 'مكاتب الشورجة'),
    ], string='نوع الفاتورة / Invoice Type', 
       help="نوع الفاتورة الذي سيظهر في الملصق")
    
    # Notes
    note = fields.Text(string='ملاحظات / Notes', help='ملاحظات إضافية للطباعة على الملصق')
    
    # Customer data overrides (One2many for multiple customers)
    customer_data_ids = fields.One2many('print.customer.label.wizard.line', 'wizard_id', 
                                        string='Customer Data', 
                                        help='تعديل بيانات العملاء قبل الطباعة')
    
    @api.onchange('partner_ids')
    def _onchange_partner_ids(self):
        """Create lines for selected customers"""
        if self.partner_ids:
            # Remove old lines
            self.customer_data_ids.unlink()
            # Create new lines
            lines = []
            for partner in self.partner_ids:
                # Get default invoice type from customer orders
                default_invoice_type = partner.get_customer_invoice_type() if hasattr(partner, 'get_customer_invoice_type') else False
                lines.append((0, 0, {
                    'partner_id': partner.id,
                    'partner_name': partner.name or '',
                    'phone_override': partner.phone or '',
                    'mobile_override': partner.mobile or '',
                    'invoice_type': default_invoice_type or self.invoice_type or False,
                }))
            self.customer_data_ids = lines

    def action_preview(self):
        """Preview labels in HTML before printing"""
        self.ensure_one()
        
        if self.print_mode == 'a4_sheet':
            report_name = 'product_label_designer.report_customer_label_a4'
        else:
            report_name = 'product_label_designer.report_customer_label'
        
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
        
        # Prepare customer data
        customer_data = {}
        for line in self.customer_data_ids:
            invoice_type = line.invoice_type or self.invoice_type or ''
            customer_data[line.partner_id.id] = {
                'phone': line.phone_override or line.partner_id.phone or '',
                'mobile': line.mobile_override or line.partner_id.mobile or '',
                'invoice_type': invoice_type,
                'invoice_type_display': invoice_type_map.get(invoice_type, '') if invoice_type else '',
            }
        
        import json
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/html/{report_name}/{",".join(map(str, self.partner_ids.ids))}?template_id={self.template_id.id}&copies={self.copies}&customer_data={json.dumps(customer_data)}&note={self.note or ""}',
            'target': 'new',
        }
    
    def action_print(self):
        """Print labels directly to default printer with actual label dimensions"""
        self.ensure_one()
        
        # Always use direct print with actual label dimensions
        report_name = 'product_label_designer.report_customer_label_direct'
        
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
        
        # Prepare customer data
        customer_data = {}
        for line in self.customer_data_ids:
            invoice_type = line.invoice_type or self.invoice_type or ''
            customer_data[str(line.partner_id.id)] = {
                'phone': line.phone_override or line.partner_id.phone or '',
                'mobile': line.mobile_override or line.partner_id.mobile or '',
                'invoice_type': invoice_type,
                'invoice_type_display': invoice_type_map.get(invoice_type, '') if invoice_type else '',
            }
        
        import json
        import urllib.parse
        # Prepare data dict for options parameter (Odoo standard way)
        options_data = {
            'template_id': self.template_id.id,
            'copies': self.copies,
            'customer_data': customer_data,
            'note': self.note or '',
        }
        
        # Use Odoo's standard options parameter approach
        options_json = json.dumps(options_data, ensure_ascii=False)
        options_encoded = urllib.parse.quote(options_json, safe='')
        
        url = f'/report/html/{report_name}/{",".join(map(str, self.partner_ids.ids))}?options={options_encoded}'
        
        # Use HTML report for direct printing
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

