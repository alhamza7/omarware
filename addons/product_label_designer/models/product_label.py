# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductLabelTemplate(models.Model):
    _name = 'product.label.template'
    _description = 'Product Label Template'
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
    show_name = fields.Boolean(string='Show Product Name', default=True)
    show_foreign_name = fields.Boolean(string='Show Foreign Name', default=False)
    show_code = fields.Boolean(string='Show Product Code', default=True)
    show_price = fields.Boolean(string='Show Price', default=True)
    show_barcode = fields.Boolean(string='Show Barcode', default=True)
    show_qr = fields.Boolean(string='Show QR Code', default=False)
    show_logo = fields.Boolean(string='Show Logo', default=True)
    
    # Layout Settings for A4 Printing
    labels_per_row = fields.Integer(string='Labels per Row', default=2)
    labels_per_column = fields.Integer(string='Labels per Column', default=4)
    label_margin = fields.Float(string='Margin between Labels (mm)', default=2.0)
    
    # Visual Designer - Element Positions (in mm from top-left)
    name_x = fields.Float(string='Name X Position', default=5.0)
    name_y = fields.Float(string='Name Y Position', default=5.0)
    foreign_name_x = fields.Float(string='Foreign Name X Position', default=5.0)
    foreign_name_y = fields.Float(string='Foreign Name Y Position', default=12.0)
    code_x = fields.Float(string='Code X Position', default=40.0)
    code_y = fields.Float(string='Code Y Position', default=25.0)
    price_x = fields.Float(string='Price X Position', default=40.0)
    price_y = fields.Float(string='Price Y Position', default=35.0)
    barcode_x = fields.Float(string='Barcode X Position', default=5.0)
    barcode_y = fields.Float(string='Barcode Y Position', default=45.0)
    qr_x = fields.Float(string='QR Code X Position', default=60.0)
    qr_y = fields.Float(string='QR Code Y Position', default=45.0)
    qr_size = fields.Float(string='QR Code Size (mm)', default=15.0)
    logo_x = fields.Float(string='Logo X Position', default=5.0)
    logo_y = fields.Float(string='Logo Y Position', default=5.0)
    logo_width = fields.Float(string='Logo Width', default=20.0)
    logo_height = fields.Float(string='Logo Height', default=15.0)
    
    # Colors
    text_color = fields.Char(string='Text Color', default='#000000')
    price_color = fields.Char(string='Price Color', default='#00A09D')
    bg_color = fields.Char(string='Background Color', default='#FFFFFF')
    
    # Fonts
    font_size_name = fields.Integer(string='Name Font Size', default=14)
    font_size_foreign_name = fields.Integer(string='Foreign Name Font Size', default=12)
    font_size_code = fields.Integer(string='Code Font Size', default=24)
    font_size_price = fields.Integer(string='Price Font Size', default=18)
    font_size_barcode = fields.Integer(string='Barcode Font Size', default=10)
    
    # Text Alignment
    name_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Name Alignment', default='right')
    
    foreign_name_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Foreign Name Alignment', default='left')
    
    code_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Code Alignment', default='center')
    
    price_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Price Alignment', default='center')
    
    # Font Weight
    name_bold = fields.Boolean(string='Name Bold', default=True)
    foreign_name_bold = fields.Boolean(string='Foreign Name Bold', default=False)
    code_bold = fields.Boolean(string='Code Bold', default=True)
    price_bold = fields.Boolean(string='Price Bold', default=True)
    
    # Font Style
    name_italic = fields.Boolean(string='Name Italic', default=False)
    foreign_name_italic = fields.Boolean(string='Foreign Name Italic', default=False)
    code_italic = fields.Boolean(string='Code Italic', default=False)
    price_italic = fields.Boolean(string='Price Italic', default=False)
    
    # Price settings
    show_currency_symbol = fields.Boolean(string='Show Currency Symbol', default=False)

    @api.model
    def get_default_template(self):
        """Get default template or create one"""
        template = self.search([('active', '=', True)], limit=1, order='sequence')
        if not template:
            template = self.create({'name': 'Default Template 80x60mm'})
        return template


    def action_open_designer(self):
        """Open visual label designer"""
        self.ensure_one()
        return {
            'name': 'Label Designer',
            'type': 'ir.actions.act_url',
            'url': f'/label_designer/{self.id}',
            'target': 'new',
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    foreign_name = fields.Char(string='Foreign Name', help='Product name in foreign language (e.g., English)')

    def action_print_label(self):
        """Open label print wizard"""
        return {
            'name': 'Print Product Label',
            'type': 'ir.actions.act_window',
            'res_model': 'print.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_ids': [(6, 0, self.ids)]},
        }
    
    def get_product_url(self):
        """Get full URL to product page"""
        self.ensure_one()
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if not base_url:
                base_url = 'http://localhost:8069'
            # Use barcode if available, otherwise use product code or ID
            identifier = self.barcode or self.default_code or str(self.id)
            return f"{base_url}/product/{identifier}"
        except:
            # Fallback to simple URL
            return f"http://localhost:8069/product/{self.id}"

