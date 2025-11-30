# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerLabelTemplate(models.Model):
    _name = 'customer.label.template'
    _description = 'Customer Label Template'
    _order = 'sequence, name'

    name = fields.Char(string='Template Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    
    # Size
    label_width = fields.Float(string='Width (mm)', default=80.0, required=True)
    label_height = fields.Float(string='Height (mm)', default=60.0, required=True)
    
    # Images
    background_image = fields.Binary(string='Background Image', attachment=True)
    logo_image = fields.Binary(string='Logo', attachment=True)
    
    # Display options
    show_name = fields.Boolean(string='Show Customer Name', default=True)
    show_phone = fields.Boolean(string='Show Phone', default=True)
    show_mobile = fields.Boolean(string='Show Mobile', default=True)
    show_invoice_type = fields.Boolean(string='Show Invoice Type', default=True)
    show_logo = fields.Boolean(string='Show Logo', default=True)
    
    # Layout Settings for A4 Printing
    labels_per_row = fields.Integer(string='Labels per Row', default=2)
    labels_per_column = fields.Integer(string='Labels per Column', default=4)
    label_margin = fields.Float(string='Margin between Labels (mm)', default=2.0)
    
    # Visual Designer - Element Positions (in mm from top-left)
    name_x = fields.Float(string='Name X Position', default=5.0)
    name_y = fields.Float(string='Name Y Position', default=5.0)
    phone_x = fields.Float(string='Phone X Position', default=5.0)
    phone_y = fields.Float(string='Phone Y Position', default=20.0)
    mobile_x = fields.Float(string='Mobile X Position', default=5.0)
    mobile_y = fields.Float(string='Mobile Y Position', default=30.0)
    invoice_type_x = fields.Float(string='Invoice Type X Position', default=5.0)
    invoice_type_y = fields.Float(string='Invoice Type Y Position', default=40.0)
    logo_x = fields.Float(string='Logo X Position', default=50.0)
    logo_y = fields.Float(string='Logo Y Position', default=5.0)
    logo_width = fields.Float(string='Logo Width', default=20.0)
    logo_height = fields.Float(string='Logo Height', default=15.0)
    
    # Colors
    text_color = fields.Char(string='Text Color', default='#000000')
    bg_color = fields.Char(string='Background Color', default='#FFFFFF')
    
    # Fonts
    font_size_name = fields.Integer(string='Name Font Size', default=14)
    font_size_phone = fields.Integer(string='Phone Font Size', default=12)
    font_size_mobile = fields.Integer(string='Mobile Font Size', default=12)
    font_size_invoice_type = fields.Integer(string='Invoice Type Font Size', default=10)
    
    # Text Alignment
    name_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Name Alignment', default='right')
    
    phone_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Phone Alignment', default='right')
    
    mobile_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Mobile Alignment', default='right')
    
    invoice_type_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Invoice Type Alignment', default='right')
    
    # Font Weight
    name_bold = fields.Boolean(string='Name Bold', default=True)
    phone_bold = fields.Boolean(string='Phone Bold', default=False)
    mobile_bold = fields.Boolean(string='Mobile Bold', default=False)
    invoice_type_bold = fields.Boolean(string='Invoice Type Bold', default=False)
    
    # Font Style
    name_italic = fields.Boolean(string='Name Italic', default=False)
    phone_italic = fields.Boolean(string='Phone Italic', default=False)
    mobile_italic = fields.Boolean(string='Mobile Italic', default=False)
    invoice_type_italic = fields.Boolean(string='Invoice Type Italic', default=False)

    @api.model
    def get_default_template(self):
        """Get default template or create one"""
        template = self.search([('active', '=', True)], limit=1, order='sequence')
        if not template:
            template = self.create({'name': 'Default Customer Label Template 80x60mm'})
        return template


    def action_open_designer(self):
        """Open visual label designer"""
        self.ensure_one()
        return {
            'name': 'Customer Label Designer',
            'type': 'ir.actions.act_url',
            'url': f'/label_designer/customer/{self.id}',
            'target': 'new',
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    mobile = fields.Char(string='Mobile', help='Mobile phone number')
    
    def get_customer_invoice_type(self):
        """Get the most common invoice type from customer orders"""
        self.ensure_one()
        # Check if pos_perfume_order model exists
        if 'pos.perfume.order' in self.env:
            orders = self.env['pos.perfume.order'].search([
                ('partner_id', '=', self.id)
            ], order='create_date desc', limit=10)
            
            if orders:
                # Get the most recent invoice type
                for order in orders:
                    if order.invoice_type:
                        return order.invoice_type
        return False
    
    def get_invoice_type_display_name(self):
        """Get display name for invoice type"""
        self.ensure_one()
        invoice_type = self.get_customer_invoice_type()
        if not invoice_type:
            return ''
        
        # Map invoice type codes to display names
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
        return invoice_type_map.get(invoice_type, invoice_type)
    
    def action_print_customer_label(self):
        """Open customer label print wizard"""
        return {
            'name': 'Print Customer Label',
            'type': 'ir.actions.act_window',
            'res_model': 'print.customer.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_ids': [(6, 0, self.ids)]},
        }

