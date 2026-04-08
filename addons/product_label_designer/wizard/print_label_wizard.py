# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PrintLabelWizard(models.TransientModel):
    _name = 'print.label.wizard'
    _description = 'Print Label Wizard'

    product_ids = fields.Many2many('product.product', string='Products', required=True)
    template_id = fields.Many2one('product.label.template', string='Label Template', 
                                   default=lambda self: self.env['product.label.template'].get_default_template())
    copies = fields.Integer(string='Copies per Product', default=1, required=True)
    print_mode = fields.Selection([
        ('single', 'Single Labels'),
        ('a4_sheet', 'A4 Sheet (Multiple Labels)')
    ], string='Print Mode', default='a4_sheet', required=True)

    def action_preview(self):
        """Preview labels in HTML before printing"""
        self.ensure_one()
        
        if self.print_mode == 'a4_sheet':
            report_name = 'product_label_designer.report_product_label_a4'
        else:
            report_name = 'product_label_designer.report_product_label'
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/html/{report_name}/{",".join(map(str, self.product_ids.ids))}?template_id={self.template_id.id}&copies={self.copies}',
            'target': 'new',
        }
    
    def action_print(self):
        """Print labels"""
        self.ensure_one()
        
        if self.print_mode == 'a4_sheet':
            report_ref = 'product_label_designer.action_report_product_label_a4'
        else:
            report_ref = 'product_label_designer.action_report_product_label'
            
        return self.env.ref(report_ref).report_action(
            self.product_ids, 
            data={
                'template_id': self.template_id.id,
                'copies': self.copies,
                'print_mode': self.print_mode,
            }
        )

