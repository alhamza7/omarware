# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """ربط Sale Order مع Invoice Designer"""
    _inherit = 'sale.order'
    
    invoice_template_id = fields.Many2one(
        'invoice.template.designer',
        string='Invoice Template',
        domain=[('template_type', 'in', ['sale_order', 'invoice'])],
        help='Template to use for printing this order'
    )
    
    def action_print_with_designer(self):
        """طباعة باستخدام Invoice Designer"""
        self.ensure_one()
        
        # Get default template if not set
        template = self.invoice_template_id
        if not template:
            template = self.env['invoice.template.designer'].search([
                ('template_type', '=', 'sale_order'),
                ('is_default', '=', True),
            ], limit=1)
        
        if not template:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Template'),
                    'message': _('Please configure an invoice template first.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Generate PDF with template
        pdf = template.generate_invoice_pdf(self.id)
        
        # Return PDF
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=sale.order&id={self.id}&field=invoice_pdf&filename=Invoice_{self.name}.pdf',
            'target': 'new',
        }


class SaleOrderLine(models.Model):
    """توسيع Sale Order Line"""
    _inherit = 'sale.order.line'
    
    # يمكن إضافة حقول إضافية هنا إذا لزم الأمر


class PosOrder(models.Model):
    """ربط POS Order مع Invoice Designer"""
    _inherit = 'pos.order'
    
    invoice_template_id = fields.Many2one(
        'invoice.template.designer',
        string='Receipt Template',
        domain=[('template_type', 'in', ['pos_receipt', 'invoice'])],
        help='Template to use for printing this receipt'
    )
    
    def action_print_with_designer(self):
        """طباعة POS receipt باستخدام Designer"""
        self.ensure_one()
        
        # Get default template
        template = self.invoice_template_id
        if not template:
            template = self.env['invoice.template.designer'].search([
                ('template_type', '=', 'pos_receipt'),
                ('is_default', '=', True),
            ], limit=1)
        
        if not template:
            # Fallback to sale order template
            template = self.env['invoice.template.designer'].search([
                ('template_type', '=', 'sale_order'),
                ('is_default', '=', True),
            ], limit=1)
        
        if not template:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Template'),
                    'message': _('Please configure a receipt template first.'),
                    'type': 'warning',
                }
            }
        
        # Generate and print
        # For POS, we'll return the template to print
        return {
            'type': 'ir.actions.report',
            'report_name': f'invoice_designer.pos_receipt_{template.id}',
        }

