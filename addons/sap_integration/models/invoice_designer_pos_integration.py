# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    invoice_template_id = fields.Many2one(
        'invoice.template.designer',
        string='Invoice Template',
        domain=[('template_type', '=', 'pos_order')],
        help="Custom visual template for this POS order"
    )
    
    def action_print_with_designer(self):
        """Print using visual designer template"""
        self.ensure_one()
        
        # Get template
        template = self.invoice_template_id
        if not template:
            # Get default template for POS
            template = self.env['invoice.template.designer'].search([
                ('template_type', '=', 'pos_order'),
                ('is_default', '=', True),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        
        if not template:
            # Fallback to standard print
            return self.action_pos_order_invoice()
        
        # Generate PDF
        pdf = template.generate_pdf(self.id, self._name)
        
        # Save as attachment
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_invoice.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    invoice_template_id = fields.Many2one(
        'invoice.template.designer',
        string='Invoice Template',
        domain="[('template_type', 'in', ['sale_order', 'quotation'])]",
        help="Custom visual template for this sale order"
    )
    
    def action_print_with_designer(self):
        """Print using visual designer template"""
        self.ensure_one()
        
        # Get template
        template = self.invoice_template_id
        if not template:
            # Determine type
            template_type = 'quotation' if self.state in ['draft', 'sent'] else 'sale_order'
            
            # Get default template
            template = self.env['invoice.template.designer'].search([
                ('template_type', '=', template_type),
                ('is_default', '=', True),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        
        if not template:
            # Fallback to standard print
            return self.action_quotation_send()
        
        # Generate PDF
        pdf = template.generate_pdf(self.id, self._name)
        
        # Save as attachment
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

