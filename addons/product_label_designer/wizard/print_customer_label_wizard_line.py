# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PrintCustomerLabelWizardLine(models.TransientModel):
    _name = 'print.customer.label.wizard.line'
    _description = 'Print Customer Label Wizard Line'

    wizard_id = fields.Many2one('print.customer.label.wizard', string='Wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    partner_name = fields.Char(string='Customer Name', readonly=True)
    
    # Override fields
    phone_override = fields.Char(string='Phone', help='يمكن تعديل رقم الهاتف')
    mobile_override = fields.Char(string='Mobile', help='يمكن تعديل رقم الموبايل')
    
    # Invoice Type for this customer
    invoice_type = fields.Selection([
        ('1', 'زبون محل'),
        ('2', 'شركات توصيل'),
        ('3', 'نقليات'),
        ('4', 'ديلفري'),
        ('5', 'NBS'),
        ('6', 'شورجة'),
        ('7', 'NA'),
        ('8', 'مكاتب الشورجة'),
    ], string='نوع الفاتورة / Invoice Type')
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Set default values from partner"""
        if self.partner_id:
            self.partner_name = self.partner_id.name or ''
            self.phone_override = self.partner_id.phone or ''
            self.mobile_override = self.partner_id.mobile or ''
            # Get default invoice type from customer orders
            if hasattr(self.partner_id, 'get_customer_invoice_type'):
                default_invoice_type = self.partner_id.get_customer_invoice_type()
                if default_invoice_type:
                    self.invoice_type = default_invoice_type

