# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InvoiceTemplateFont(models.Model):
    """مكتبة الخطوط المتاحة"""
    _name = 'invoice.template.font'
    _description = 'Available Fonts for Invoice Designer'
    _order = 'name'

    name = fields.Char('Font Name', required=True)
    font_family = fields.Char('CSS Font Family', required=True)
    font_file = fields.Binary('Font File (.ttf/.otf/.woff)')
    font_filename = fields.Char('Font Filename')
    is_system_font = fields.Boolean('System Font', default=False)
    is_web_font = fields.Boolean('Web Font (Google Fonts, etc.)', default=False)
    web_font_url = fields.Char('Web Font URL')
    
    # Preview
    preview_text = fields.Char('Preview Text', default='AaBbCc 123 مثال عربي')
    category = fields.Selection([
        ('serif', 'Serif'),
        ('sans-serif', 'Sans-Serif'),
        ('monospace', 'Monospace'),
        ('cursive', 'Cursive'),
        ('fantasy', 'Fantasy'),
        ('arabic', 'Arabic'),
    ], string='Category')
    
    # Weights Available
    supports_thin = fields.Boolean('Supports Thin (100)')
    supports_extra_light = fields.Boolean('Supports Extra Light (200)')
    supports_light = fields.Boolean('Supports Light (300)')
    supports_normal = fields.Boolean('Supports Normal (400)', default=True)
    supports_medium = fields.Boolean('Supports Medium (500)')
    supports_semi_bold = fields.Boolean('Supports Semi Bold (600)')
    supports_bold = fields.Boolean('Supports Bold (700)', default=True)
    supports_extra_bold = fields.Boolean('Supports Extra Bold (800)')
    supports_black = fields.Boolean('Supports Black (900)')
    
    # Styles Available
    supports_italic = fields.Boolean('Supports Italic', default=True)
    supports_oblique = fields.Boolean('Supports Oblique')
    
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Font name must be unique!'),
    ]

