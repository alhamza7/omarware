# -*- coding: utf-8 -*-

from odoo import models, fields, api


class QuickPrintWizard(models.TransientModel):
    _name = 'quick.print.wizard'
    _description = 'Quick Print Wizard'

    @api.model
    def default_get(self, fields_list):
        """Get default values including selected products"""
        res = super().default_get(fields_list)
        
        # Get products from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['product_ids'] = [(6, 0, active_ids)]
            res['product_count'] = len(active_ids)
        else:
            res['product_count'] = 0
        
        return res
    
    product_ids = fields.Many2many('product.product', string='Selected Products')
    product_count = fields.Integer(string='Number of Products', readonly=True)
    template_id = fields.Many2one('product.label.template', string='Label Template', 
                                   default=lambda self: self.env['product.label.template'].get_default_template(),
                                   required=True)
    print_mode = fields.Selection([
        ('single', 'Single Labels (One per page)'),
        ('a4_sheet', 'A4 Sheet (Multiple per page)'),
        ('html_to_pdf', 'HTML Screenshot to PDF')
    ], string='Print Mode', default='a4_sheet', required=True)
    copies = fields.Integer(string='Copies per Product', default=1, required=True)
    
    # Quick filters
    filter_category_id = fields.Many2one('product.category', string='Filter by Category')
    filter_has_barcode = fields.Boolean(string='Only with Barcode', default=False)
    filter_has_foreign_name = fields.Boolean(string='Only with Foreign Name', default=False)

    @api.onchange('filter_category_id', 'filter_has_barcode', 'filter_has_foreign_name')
    def _onchange_filters(self):
        """Apply filters to product selection"""
        if not any([self.filter_category_id, self.filter_has_barcode, self.filter_has_foreign_name]):
            return
        
        domain = []
        
        if self.filter_category_id:
            domain.append(('categ_id', '=', self.filter_category_id.id))
        
        if self.filter_has_barcode:
            domain.append(('barcode', '!=', False))
        
        if self.filter_has_foreign_name:
            domain.append(('foreign_name', '!=', False))
        
        if domain:
            products = self.env['product.product'].search(domain)
            self.product_ids = [(6, 0, products.ids)]
            self.product_count = len(products)
    
    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        """Update product count when products change"""
        self.product_count = len(self.product_ids)

    def action_preview(self):
        """Preview labels before printing"""
        self.ensure_one()
        
        if not self.product_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Please select at least one product',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
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
        
        if not self.product_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Please select at least one product',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # HTML to PDF mode - use HTML rendering
        if self.print_mode == 'html_to_pdf':
            if self.print_mode == 'a4_sheet' or True:  # Always use A4 for html_to_pdf
                report_ref = 'product_label_designer.action_report_product_label_a4_html'
            else:
                report_ref = 'product_label_designer.action_report_product_label_html'
        elif self.print_mode == 'a4_sheet':
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
    
    def action_add_all_products(self):
        """Add all products"""
        all_products = self.env['product.product'].search([])
        self.product_ids = [(6, 0, all_products.ids)]
        self.product_count = len(all_products)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Added {self.product_count} products',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_clear_products(self):
        """Clear all selected products"""
        self.product_ids = [(5, 0, 0)]
        self.product_count = 0



