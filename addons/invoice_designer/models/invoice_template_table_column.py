# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InvoiceTemplateTableColumn(models.Model):
    """أعمدة الجدول - Table Columns"""
    _name = 'invoice.template.table.column'
    _description = 'Invoice Template Table Column'
    _order = 'sequence'

    element_id = fields.Many2one('invoice.template.element', 'Element', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Column Name', required=True, translate=True)
    field_name = fields.Char('Field Path', required=True, help='e.g., product_id.name, product_uom_qty')
    
    # Column Width
    width = fields.Float('Width', default=10.0)
    width_type = fields.Selection([
        ('percent', 'Percentage (%)'),
        ('fixed', 'Fixed (mm)'),
        ('auto', 'Auto'),
    ], string='Width Type', default='percent')
    
    # Header Styling
    header_text = fields.Char('Header Text', translate=True)
    header_font_size = fields.Integer('Header Font Size', default=12)
    header_font_weight = fields.Selection([
        ('400', 'Normal'), ('500', 'Medium'), ('600', 'Semi Bold'),
        ('700', 'Bold'), ('800', 'Extra Bold'), ('900', 'Black'),
    ], string='Header Font Weight', default='700')
    header_bg_color = fields.Char('Header Background', default='#4A90E2')
    header_text_color = fields.Char('Header Text Color', default='#FFFFFF')
    header_align = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right'),
    ], string='Header Align', default='center')
    
    # Cell Styling
    cell_font_size = fields.Integer('Cell Font Size', default=11)
    cell_align = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right'),
    ], string='Cell Align', default='left')
    cell_vertical_align = fields.Selection([
        ('top', 'Top'), ('middle', 'Middle'), ('bottom', 'Bottom'),
    ], string='Vertical Align', default='middle')
    
    cell_padding_top = fields.Integer('Cell Padding Top', default=5)
    cell_padding_right = fields.Integer('Cell Padding Right', default=5)
    cell_padding_bottom = fields.Integer('Cell Padding Bottom', default=5)
    cell_padding_left = fields.Integer('Cell Padding Left', default=5)
    
    # Data Format
    data_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('monetary', 'Money'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('boolean', 'Yes/No'),
    ], string='Data Type', default='text')
    
    format_string = fields.Char('Format String', help='e.g., %.2f, %Y-%m-%d')
    prefix = fields.Char('Prefix')
    suffix = fields.Char('Suffix')
    decimal_places = fields.Integer('Decimal Places', default=2)
    
    # Totals
    show_total = fields.Boolean('Show Total in Footer')
    total_function = fields.Selection([
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('count', 'Count'),
        ('min', 'Minimum'),
        ('max', 'Maximum'),
    ], string='Total Function', default='sum')
    total_label = fields.Char('Total Label', translate=True)
    
    # Conditional Formatting
    conditional_formatting = fields.Boolean('Enable Conditional Formatting')
    condition_field = fields.Char('Condition Field')
    condition_operator = fields.Selection([
        ('==', 'Equals (==)'),
        ('!=', 'Not Equals (!=)'),
        ('>', 'Greater Than (>)'),
        ('<', 'Less Than (<)'),
        ('>=', 'Greater or Equal (>=)'),
        ('<=', 'Less or Equal (<=)'),
    ], string='Operator')
    condition_value = fields.Char('Condition Value')
    condition_color = fields.Char('Text Color if True')
    condition_bg_color = fields.Char('Background Color if True')

