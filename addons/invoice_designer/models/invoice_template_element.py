# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class InvoiceTemplateElement(models.Model):
    """عناصر القالب - Text, Field, Image, Table, etc."""
    _name = 'invoice.template.element'
    _description = 'Invoice Template Element'
    _order = 'z_index, sequence'

    # ==================== Basic ====================
    template_id = fields.Many2one('invoice.template.designer', 'Template', required=True, ondelete='cascade')
    name = fields.Char('Element Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    # Visibility toggle for canvas/UI
    visible = fields.Boolean('Visible', default=True, help='Show/Hide this element on the designer and print')

    # ==================== Element Type ====================
    element_type = fields.Selection([
        ('text', 'Static Text'),
        ('field', 'Dynamic Field'),
        ('image', 'Image'),
        ('table', 'Table'),
        ('shape', 'Shape'),
        ('line', 'Line'),
        ('barcode', 'Barcode'),
        ('qr', 'QR Code'),
        ('gradient_box', 'Gradient Box'),
        ('icon', 'Icon'),
    ], string='Type', required=True, default='text')

    # ==================== Position & Size (mm) ====================
    x = fields.Float('X Position (mm)', default=0.0, required=True)
    y = fields.Float('Y Position (mm)', default=0.0, required=True)
    width = fields.Float('Width (mm)', default=50.0, required=True)
    height = fields.Float('Height (mm)', default=10.0, required=True)
    rotation = fields.Float('Rotation (degrees)', default=0.0)
    z_index = fields.Integer('Z-Index (Layer)', default=1)

    # ==================== Content ====================
    # For text/field
    content = fields.Text('Static Content', translate=True)
    field_name = fields.Char('Field Name')  # e.g., 'partner_id.name', 'amount_total'
    field_format = fields.Char('Field Format')  # e.g., '%.2f', '%Y-%m-%d'
    
    # For image
    image_data = fields.Binary('Image Data')
    image_filename = fields.Char('Image Filename')
    image_url = fields.Char('Image URL')
    object_fit = fields.Selection([
        ('fill', 'Fill'),
        ('contain', 'Contain'),
        ('cover', 'Cover'),
        ('none', 'None'),
        ('scale-down', 'Scale Down'),
    ], string='Object Fit', default='contain', help='How the image should fit within its box')
    
    # For shape
    shape_type = fields.Selection([
        ('rectangle', 'Rectangle'),
        ('circle', 'Circle'),
        ('ellipse', 'Ellipse'),
        ('triangle', 'Triangle'),
        ('polygon', 'Polygon'),
    ], string='Shape Type')
    
    # For line
    line_x2 = fields.Float('End X (mm)')
    line_y2 = fields.Float('End Y (mm)')

    # ==================== FONT CONTROL (9 Weights) ====================
    font_family_id = fields.Many2one('invoice.template.font', 'Font Family')
    font_family_name = fields.Selection([
        # Arabic Google Fonts
        ('Almarai', 'Almarai (عربي - حديث)'),
        ('Cairo', 'Cairo (عربي - كايرو)'),
        ('Tajawal', 'Tajawal (عربي - تجوال)'),
        ('Amiri', 'Amiri (عربي - كلاسيكي)'),
        ('Scheherazade New', 'Scheherazade (عربي - شهرزاد)'),
        ('Noto Sans Arabic', 'Noto Sans Arabic (عربي)'),
        ('IBM Plex Sans Arabic', 'IBM Plex Sans Arabic'),
        ('Markazi Text', 'Markazi Text (عربي)'),
        ('El Messiri', 'El Messiri (عربي)'),
        ('Lateef', 'Lateef (عربي)'),
        # Standard Fonts
        ('Arial', 'Arial'),
        ('Helvetica', 'Helvetica'),
        ('Times New Roman', 'Times New Roman'),
        ('Courier New', 'Courier New'),
        ('Georgia', 'Georgia'),
        ('Verdana', 'Verdana'),
        ('Tahoma', 'Tahoma'),
        ('Trebuchet MS', 'Trebuchet MS'),
        ('custom', 'Custom Font'),
    ], string='Font Family', default='Almarai')
    
    custom_font_name = fields.Char('Custom Font Name', help='Enter custom font name if selected "Custom Font"')
    
    font_size = fields.Integer('Font Size (pt)', default=12)
    font_weight = fields.Selection([
        ('100', '100 - Thin'),
        ('200', '200 - Extra Light'),
        ('300', '300 - Light'),
        ('400', '400 - Normal'),
        ('500', '500 - Medium'),
        ('600', '600 - Semi Bold'),
        ('700', '700 - Bold'),
        ('800', '800 - Extra Bold'),
        ('900', '900 - Black'),
    ], string='Font Weight', default='400')
    
    font_style = fields.Selection([
        ('normal', 'Normal'),
        ('italic', 'Italic'),
        ('oblique', 'Oblique'),
    ], string='Font Style', default='normal')

    # ==================== TEXT STYLING ====================
    text_decoration = fields.Selection([
        ('none', 'None'),
        ('underline', 'Underline'),
        ('overline', 'Overline'),
        ('line-through', 'Strike Through'),
    ], string='Text Decoration', default='none')
    
    text_transform = fields.Selection([
        ('none', 'None'),
        ('uppercase', 'UPPERCASE'),
        ('lowercase', 'lowercase'),
        ('capitalize', 'Capitalize Each Word'),
    ], string='Text Transform', default='none')
    
    letter_spacing = fields.Float('Letter Spacing (px)', default=0.0)
    line_height = fields.Float('Line Height', default=1.2)
    text_shadow = fields.Char('Text Shadow CSS')  # e.g., '2px 2px 4px rgba(0,0,0,0.3)'
    
    # Text Alignment
    text_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justify'),
    ], string='Text Align', default='left')
    
    vertical_align = fields.Selection([
        ('top', 'Top'),
        ('middle', 'Middle'),
        ('bottom', 'Bottom'),
    ], string='Vertical Align', default='top')

    # ==================== COLORS & GRADIENTS ====================
    color = fields.Char('Text/Foreground Color', default='#000000')
    background_color = fields.Char('Background Color', default='transparent')
    
    # Gradient Support
    background_gradient = fields.Boolean('Use Gradient Background')
    gradient_type = fields.Selection([
        ('linear', 'Linear'),
        ('radial', 'Radial'),
    ], string='Gradient Type', default='linear')
    gradient_direction = fields.Integer('Gradient Direction (deg)', default=90)
    gradient_color_start = fields.Char('Gradient Start Color', default='#4A90E2')
    gradient_color_end = fields.Char('Gradient End Color', default='#357ABD')
    gradient_color_stops = fields.Text('Gradient Color Stops (JSON)')  # Advanced: multiple stops
    
    opacity = fields.Float('Opacity', default=1.0, help='0.0 = transparent, 1.0 = opaque')

    # ==================== BORDERS ====================
    # General border fields (for convenience/backward compatibility)
    border_width = fields.Integer('Border Width (px)', default=0, help='General border width for all sides')
    border_style = fields.Selection([
        ('none', 'None'),
        ('solid', 'Solid'),
        ('dashed', 'Dashed'),
        ('dotted', 'Dotted'),
        ('double', 'Double'),
    ], string='Border Style', default='solid', help='General border style')
    border_color = fields.Char('Border Color', default='#000000', help='General border color')
    
    # ==================== BORDERS (4 Sides Separate) ====================
    # Top Border
    border_top_width = fields.Integer('Top Border Width (px)', default=0)
    border_top_style = fields.Selection([
        ('none', 'None'),
        ('solid', 'Solid'),
        ('dashed', 'Dashed'),
        ('dotted', 'Dotted'),
        ('double', 'Double'),
        ('groove', 'Groove'),
        ('ridge', 'Ridge'),
        ('inset', 'Inset'),
        ('outset', 'Outset'),
    ], string='Top Border Style', default='solid')
    border_top_color = fields.Char('Top Border Color', default='#000000')
    
    # Right Border
    border_right_width = fields.Integer('Right Border Width (px)', default=0)
    border_right_style = fields.Selection([
        ('none', 'None'), ('solid', 'Solid'), ('dashed', 'Dashed'), 
        ('dotted', 'Dotted'), ('double', 'Double'), ('groove', 'Groove'),
        ('ridge', 'Ridge'), ('inset', 'Inset'), ('outset', 'Outset'),
    ], string='Right Border Style', default='solid')
    border_right_color = fields.Char('Right Border Color', default='#000000')
    
    # Bottom Border
    border_bottom_width = fields.Integer('Bottom Border Width (px)', default=0)
    border_bottom_style = fields.Selection([
        ('none', 'None'), ('solid', 'Solid'), ('dashed', 'Dashed'), 
        ('dotted', 'Dotted'), ('double', 'Double'), ('groove', 'Groove'),
        ('ridge', 'Ridge'), ('inset', 'Inset'), ('outset', 'Outset'),
    ], string='Bottom Border Style', default='solid')
    border_bottom_color = fields.Char('Bottom Border Color', default='#000000')
    
    # Left Border
    border_left_width = fields.Integer('Left Border Width (px)', default=0)
    border_left_style = fields.Selection([
        ('none', 'None'), ('solid', 'Solid'), ('dashed', 'Dashed'), 
        ('dotted', 'Dotted'), ('double', 'Double'), ('groove', 'Groove'),
        ('ridge', 'Ridge'), ('inset', 'Inset'), ('outset', 'Outset'),
    ], string='Left Border Style', default='solid')
    border_left_color = fields.Char('Left Border Color', default='#000000')

    # ==================== BORDER RADIUS ====================
    border_radius = fields.Integer('Border Radius (px)', default=0, help='General border radius for all corners')
    
    # ==================== BORDER RADIUS (4 Corners) ====================
    border_top_left_radius = fields.Integer('Top-Left Radius (px)', default=0)
    border_top_right_radius = fields.Integer('Top-Right Radius (px)', default=0)
    border_bottom_right_radius = fields.Integer('Bottom-Right Radius (px)', default=0)
    border_bottom_left_radius = fields.Integer('Bottom-Left Radius (px)', default=0)

    # ==================== BOX SHADOW ====================
    box_shadow = fields.Char('Box Shadow CSS', help='CSS box-shadow property (e.g., 2px 2px 5px rgba(0,0,0,0.3))')
    box_shadow_enabled = fields.Boolean('Enable Box Shadow')
    box_shadow_x = fields.Integer('Shadow X Offset (px)', default=0)
    box_shadow_y = fields.Integer('Shadow Y Offset (px)', default=2)
    box_shadow_blur = fields.Integer('Shadow Blur (px)', default=4)
    box_shadow_spread = fields.Integer('Shadow Spread (px)', default=0)
    box_shadow_color = fields.Char('Shadow Color', default='rgba(0,0,0,0.2)')
    box_shadow_inset = fields.Boolean('Inset Shadow')

    # ==================== CSS FILTERS ====================
    filter_blur = fields.Integer('Blur Filter (px)', default=0)
    filter_brightness = fields.Float('Brightness', default=1.0, help='1.0 = normal')
    filter_contrast = fields.Float('Contrast', default=1.0, help='1.0 = normal')
    filter_grayscale = fields.Float('Grayscale', default=0.0, help='0.0 = color, 1.0 = grayscale')
    filter_hue_rotate = fields.Integer('Hue Rotate (deg)', default=0)
    filter_saturate = fields.Float('Saturate', default=1.0, help='1.0 = normal')
    filter_sepia = fields.Float('Sepia', default=0.0, help='0.0 = no sepia, 1.0 = full sepia')
    filter_invert = fields.Float('Invert', default=0.0, help='0.0 = normal, 1.0 = inverted')

    # ==================== PADDING & MARGIN ====================
    padding_top = fields.Integer('Padding Top (px)', default=0)
    padding_right = fields.Integer('Padding Right (px)', default=0)
    padding_bottom = fields.Integer('Padding Bottom (px)', default=0)
    padding_left = fields.Integer('Padding Left (px)', default=0)
    
    margin_top = fields.Integer('Margin Top (px)', default=0)
    margin_right = fields.Integer('Margin Right (px)', default=0)
    margin_bottom = fields.Integer('Margin Bottom (px)', default=0)
    margin_left = fields.Integer('Margin Left (px)', default=0)

    # ==================== DISPLAY & POSITION ====================
    display = fields.Selection([
        ('block', 'Block'),
        ('inline', 'Inline'),
        ('inline-block', 'Inline Block'),
        ('flex', 'Flex'),
        ('grid', 'Grid'),
        ('none', 'Hidden'),
    ], string='Display', default='block')
    
    position = fields.Selection([
        ('absolute', 'Absolute'),
        ('relative', 'Relative'),
        ('fixed', 'Fixed'),
        ('static', 'Static'),
    ], string='Position', default='absolute')

    # ==================== FLEX LAYOUT (if display=flex) ====================
    flex_direction = fields.Selection([
        ('row', 'Row (→)'),
        ('row-reverse', 'Row Reverse (←)'),
        ('column', 'Column (↓)'),
        ('column-reverse', 'Column Reverse (↑)'),
    ], string='Flex Direction', default='row')
    
    justify_content = fields.Selection([
        ('flex-start', 'Start'),
        ('center', 'Center'),
        ('flex-end', 'End'),
        ('space-between', 'Space Between'),
        ('space-around', 'Space Around'),
        ('space-evenly', 'Space Evenly'),
    ], string='Justify Content', default='flex-start')
    
    align_items = fields.Selection([
        ('flex-start', 'Start'),
        ('center', 'Center'),
        ('flex-end', 'End'),
        ('stretch', 'Stretch'),
        ('baseline', 'Baseline'),
    ], string='Align Items', default='stretch')

    # ==================== HOVER & ANIMATIONS ====================
    hover_enabled = fields.Boolean('Enable Hover Effect')
    hover_color = fields.Char('Hover Color')
    hover_bg_color = fields.Char('Hover Background Color')
    hover_transform = fields.Char('Hover Transform CSS')  # e.g., 'scale(1.1)'
    
    animation_enabled = fields.Boolean('Enable Animation')
    animation_name = fields.Selection([
        ('fade-in', 'Fade In'),
        ('slide-in-left', 'Slide In Left'),
        ('slide-in-right', 'Slide In Right'),
        ('slide-in-top', 'Slide In Top'),
        ('slide-in-bottom', 'Slide In Bottom'),
        ('scale-in', 'Scale In'),
        ('rotate-in', 'Rotate In'),
        ('bounce', 'Bounce'),
    ], string='Animation Name')
    animation_duration = fields.Float('Animation Duration (s)', default=0.5)
    animation_delay = fields.Float('Animation Delay (s)', default=0.0)

    # ==================== TABLE SETTINGS ====================
    table_data_source = fields.Char('Table Data Source')  # e.g., 'order_line'
    table_column_ids = fields.One2many(
        'invoice.template.table.column',
        'element_id',
        string='Table Columns'
    )
    
    # Table Style
    table_layout = fields.Selection([
        ('fixed', 'Fixed'),
        ('auto', 'Auto'),
    ], string='Table Layout', default='fixed')
    
    table_border_collapse = fields.Selection([
        ('collapse', 'Collapse'),
        ('separate', 'Separate'),
    ], string='Border Collapse', default='collapse')
    
    table_border_spacing = fields.Integer('Border Spacing (px)', default=0)
    table_bg_color = fields.Char('Table Background', default='#FFFFFF')
    table_border_width = fields.Integer('Table Border Width (px)', default=1)
    table_border_color = fields.Char('Table Border Color', default='#DDDDDD')
    table_border_style = fields.Selection([
        ('solid', 'Solid'), ('dashed', 'Dashed'), ('dotted', 'Dotted'),
    ], string='Table Border Style', default='solid')
    
    # Header
    show_header = fields.Boolean('Show Header', default=True)
    header_height = fields.Integer('Header Height (mm)', default=10)
    header_repeat = fields.Boolean('Repeat Header on Each Page', default=True)
    header_bg_color = fields.Char('Header Background', default='#4A90E2')
    header_text_color = fields.Char('Header Text Color', default='#FFFFFF')
    header_font_weight = fields.Selection([
        ('400', 'Normal'), ('500', 'Medium'), ('600', 'Semi Bold'),
        ('700', 'Bold'), ('800', 'Extra Bold'), ('900', 'Black'),
    ], string='Header Font Weight', default='700')
    
    # Rows
    row_height = fields.Integer('Row Height (mm)', default=8)
    row_min_height = fields.Integer('Min Row Height (mm)', default=8)
    alternate_row_colors = fields.Boolean('Alternate Row Colors', default=True)
    row_color_odd = fields.Char('Odd Row Color', default='#FFFFFF')
    row_color_even = fields.Char('Even Row Color', default='#F9F9F9')
    row_hover_color = fields.Char('Row Hover Color', default='#E3F2FD')
    
    # Footer (Totals)
    show_footer = fields.Boolean('Show Footer (Totals)')
    footer_bg_color = fields.Char('Footer Background', default='#F5F5F5')
    footer_font_weight = fields.Selection([
        ('400', 'Normal'), ('500', 'Medium'), ('600', 'Semi Bold'),
        ('700', 'Bold'), ('800', 'Extra Bold'), ('900', 'Black'),
    ], string='Footer Font Weight', default='700')
    
    # Pagination
    rows_per_page = fields.Integer('Rows Per Page', default=0, help='0 = unlimited')
    page_break_inside = fields.Selection([
        ('auto', 'Auto'),
        ('avoid', 'Avoid'),
    ], string='Page Break Inside', default='avoid')

    # ==================== BARCODE/QR SETTINGS ====================
    code_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN-13'),
        ('ean8', 'EAN-8'),
        ('upca', 'UPC-A'),
        ('qr', 'QR Code'),
        ('datamatrix', 'Data Matrix'),
        ('pdf417', 'PDF417'),
    ], string='Code Type')
    
    code_data_source = fields.Char('Data Source Field')  # e.g., 'name', 'sap_doc_number'
    code_show_text = fields.Boolean('Show Text Below Code', default=True)
    code_text_position = fields.Selection([
        ('bottom', 'Bottom'),
        ('top', 'Top'),
    ], string='Text Position', default='bottom')
    code_module_size = fields.Integer('Module/Bar Size (px)', default=2)
    code_quiet_zone = fields.Integer('Quiet Zone (px)', default=10)
    code_error_correction = fields.Selection([
        ('L', 'Low (7%)'),
        ('M', 'Medium (15%)'),
        ('Q', 'Quartile (25%)'),
        ('H', 'High (30%)'),
    ], string='QR Error Correction', default='M')

    # ==================== TABLE SETTINGS ====================
    # Table Structure
    table_columns = fields.Selection([
        ('product_qty_price_total', 'Product + Qty + Price + Total'),
        ('product_qty_price', 'Product + Qty + Price'),
        ('product_total', 'Product + Total'),
        ('custom', 'Custom Columns'),
    ], string='Table Columns', default='product_qty_price_total')
    
    # Column Order (sequence)
    column_order_product = fields.Integer('Product Order', default=1)
    column_order_description = fields.Integer('Description Order', default=2)
    column_order_qty = fields.Integer('Qty Order', default=3)
    column_order_uom = fields.Integer('UOM Order', default=4)
    column_order_price = fields.Integer('Price Order', default=5)
    column_order_discount = fields.Integer('Discount Order', default=6)
    column_order_tax = fields.Integer('Tax Order', default=7)
    column_order_subtotal = fields.Integer('Subtotal Order', default=8)
    
    # Column Visibility
    show_column_product = fields.Boolean('Show Product Column', default=True)
    show_column_description = fields.Boolean('Show Description', default=False)
    show_column_qty = fields.Boolean('Show Quantity', default=True)
    show_column_uom = fields.Boolean('Show Unit of Measure', default=True)
    show_column_price = fields.Boolean('Show Unit Price', default=True)
    show_column_discount = fields.Boolean('Show Discount', default=False)
    show_column_tax = fields.Boolean('Show Tax', default=False)
    show_column_subtotal = fields.Boolean('Show Subtotal', default=True)
    
    # Column Widths (percentage)
    column_width_product = fields.Integer('Product Width %', default=40)
    column_width_description = fields.Integer('Description Width %', default=20)
    column_width_qty = fields.Integer('Qty Width %', default=10)
    column_width_uom = fields.Integer('UOM Width %', default=10)
    column_width_price = fields.Integer('Price Width %', default=15)
    column_width_discount = fields.Integer('Discount Width %', default=10)
    column_width_tax = fields.Integer('Tax Width %', default=10)
    column_width_subtotal = fields.Integer('Subtotal Width %', default=15)
    
    # Column Alignment (text-align)
    column_align_product = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Product Align', default='right')
    column_align_description = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Description Align', default='right')
    column_align_qty = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Qty Align', default='center')
    column_align_uom = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='UOM Align', default='center')
    column_align_price = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Price Align', default='right')
    column_align_discount = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Discount Align', default='center')
    column_align_tax = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Tax Align', default='right')
    column_align_subtotal = fields.Selection([
        ('left', 'Left'), ('center', 'Center'), ('right', 'Right')
    ], string='Subtotal Align', default='right')
    
    # Column Headers (Arabic)
    header_product = fields.Char('Product Header', default='المنتج')
    header_description = fields.Char('Description Header', default='الوصف')
    header_qty = fields.Char('Qty Header', default='الكمية')
    header_uom = fields.Char('UOM Header', default='الوحدة')
    header_price = fields.Char('Price Header', default='السعر')
    header_discount = fields.Char('Discount Header', default='الخصم')
    header_tax = fields.Char('Tax Header', default='الضريبة')
    header_subtotal = fields.Char('Subtotal Header', default='المجموع')
    
    # Table Direction
    table_direction = fields.Selection([
        ('rtl', 'Right to Left (RTL) - Arabic'),
        ('ltr', 'Left to Right (LTR) - English'),
    ], string='Table Direction', default='rtl')
    
    # Table Font
    table_font_family = fields.Selection([
        ('inherit', 'Inherit from Element'),
        ('Almarai', 'Almarai (عربي)'),
        ('Cairo', 'Cairo (عربي)'),
        ('Tajawal', 'Tajawal (عربي)'),
        ('Amiri', 'Amiri (عربي)'),
        ('Arial', 'Arial'),
        ('Helvetica', 'Helvetica'),
        ('Times New Roman', 'Times New Roman'),
        ('custom', 'Custom'),
    ], string='Table Font Family', default='inherit')
    
    table_custom_font = fields.Char('Custom Table Font')
    
    # Table Styling
    table_header_bg = fields.Char('Table Header Background', default='#4a5568')
    table_header_color = fields.Char('Table Header Color', default='#ffffff')
    table_header_font_size = fields.Integer('Header Font Size', default=12)
    table_header_font_weight = fields.Selection([
        ('400', 'Normal'),
        ('600', 'Semi Bold'),
        ('700', 'Bold'),
    ], string='Header Font Weight', default='700')
    
    table_row_bg = fields.Char('Table Row Background', default='#ffffff')
    table_row_alternate_bg = fields.Char('Alternate Row Background', default='#f8f9fa')
    table_row_color = fields.Char('Table Row Color', default='#333333')
    table_row_font_size = fields.Integer('Row Font Size', default=11)
    table_border_color = fields.Char('Table Border Color', default='#dee2e6')
    table_border_width = fields.Integer('Table Border Width', default=1)
    table_cell_padding = fields.Integer('Cell Padding (px)', default=8)
    
    # Table Footer
    show_table_footer = fields.Boolean('Show Table Footer', default=False)
    table_footer_text = fields.Char('Footer Text', default='')
    
    # Table pagination
    table_max_rows_per_page = fields.Integer('Max Rows Per Page', default=20, help='Maximum number of rows per page before creating a new page. Set 0 for no pagination.')

    # ==================== CONDITIONAL VISIBILITY ====================
    visible_condition = fields.Char('Visible If (Python Expression)')  # e.g., "amount_total > 1000"
    
    # ==================== Custom CSS ====================
    custom_css = fields.Text('Custom CSS')

    # ==================== Methods ====================
    def _render_html(self):
        """Render element as HTML"""
        self.ensure_one()
        
        style = self._generate_css_style()
        
        if self.element_type == 'text':
            return f'<div class="element element-text" style="{style}">{self.content or ""}</div>'
        
        elif self.element_type == 'field':
            return f'<div class="element element-field" style="{style}" data-field="{self.field_name}">{{{{ {self.field_name} }}}}</div>'
        
        elif self.element_type == 'image':
            img_src = f"data:image/png;base64,{self.image_data.decode('utf-8')}" if self.image_data else self.image_url
            return f'<img class="element element-image" src="{img_src}" style="{style}"/>'
        
        elif self.element_type == 'table':
            return self._render_table_html()
        
        elif self.element_type == 'shape':
            return self._render_shape_html(style)
        
        elif self.element_type == 'line':
            return self._render_line_html()
        
        elif self.element_type in ('barcode', 'qr'):
            return self._render_barcode_html(style)
        
        return ''

    def _generate_css_style(self):
        """Generate complete CSS style string"""
        self.ensure_one()
        
        styles = []
        
        # Box Model
        styles.append("box-sizing: border-box;")
        
        # Position & Size
        styles.append(f"position: {self.position};")
        styles.append(f"left: {self.x}mm;")
        styles.append(f"top: {self.y}mm;")
        styles.append(f"width: {self.width}mm;")
        styles.append(f"height: {self.height}mm;")
        
        if self.rotation:
            styles.append(f"transform: rotate({self.rotation}deg);")
        
        styles.append(f"z-index: {self.z_index};")
        
        # Overflow
        styles.append("overflow: visible;")
        
        # Font
        font_name = self.custom_font_name if self.font_family_name == 'custom' and self.custom_font_name else self.font_family_name
        if font_name:
            styles.append(f"font-family: '{font_name}', 'Almarai', 'Arial', sans-serif;")
        if self.font_size:
            styles.append(f"font-size: {self.font_size}pt;")
        if self.font_weight:
            styles.append(f"font-weight: {self.font_weight};")
        if self.font_style != 'normal':
            styles.append(f"font-style: {self.font_style};")
        
        # Text
        if self.text_decoration != 'none':
            styles.append(f"text-decoration: {self.text_decoration};")
        if self.text_transform != 'none':
            styles.append(f"text-transform: {self.text_transform};")
        if self.letter_spacing:
            styles.append(f"letter-spacing: {self.letter_spacing}px;")
        if self.line_height:
            styles.append(f"line-height: {self.line_height};")
        if self.text_shadow:
            styles.append(f"text-shadow: {self.text_shadow};")
        if self.text_align:
            styles.append(f"text-align: {self.text_align};")
        
        # Colors
        if self.color:
            styles.append(f"color: {self.color};")
        
        if self.background_gradient:
            gradient = self._generate_gradient_css()
            styles.append(f"background: {gradient};")
        elif self.background_color and self.background_color != 'transparent':
            styles.append(f"background-color: {self.background_color};")
        
        if self.opacity < 1.0:
            styles.append(f"opacity: {self.opacity};")
        
        # Borders
        if self.border_top_width:
            styles.append(f"border-top: {self.border_top_width}px {self.border_top_style} {self.border_top_color};")
        if self.border_right_width:
            styles.append(f"border-right: {self.border_right_width}px {self.border_right_style} {self.border_right_color};")
        if self.border_bottom_width:
            styles.append(f"border-bottom: {self.border_bottom_width}px {self.border_bottom_style} {self.border_bottom_color};")
        if self.border_left_width:
            styles.append(f"border-left: {self.border_left_width}px {self.border_left_style} {self.border_left_color};")
        
        # Border Radius
        if any([self.border_top_left_radius, self.border_top_right_radius, 
                self.border_bottom_right_radius, self.border_bottom_left_radius]):
            styles.append(f"border-radius: {self.border_top_left_radius}px {self.border_top_right_radius}px {self.border_bottom_right_radius}px {self.border_bottom_left_radius}px;")
        
        # Box Shadow
        if self.box_shadow_enabled:
            inset = 'inset ' if self.box_shadow_inset else ''
            styles.append(f"box-shadow: {inset}{self.box_shadow_x}px {self.box_shadow_y}px {self.box_shadow_blur}px {self.box_shadow_spread}px {self.box_shadow_color};")
        
        # Filters
        filters = []
        if self.filter_blur:
            filters.append(f"blur({self.filter_blur}px)")
        if self.filter_brightness != 1.0:
            filters.append(f"brightness({self.filter_brightness})")
        if self.filter_contrast != 1.0:
            filters.append(f"contrast({self.filter_contrast})")
        if self.filter_grayscale:
            filters.append(f"grayscale({self.filter_grayscale})")
        if self.filter_hue_rotate:
            filters.append(f"hue-rotate({self.filter_hue_rotate}deg)")
        if self.filter_saturate != 1.0:
            filters.append(f"saturate({self.filter_saturate})")
        if self.filter_sepia:
            filters.append(f"sepia({self.filter_sepia})")
        if self.filter_invert:
            filters.append(f"invert({self.filter_invert})")
        
        if filters:
            styles.append(f"filter: {' '.join(filters)};")
        
        # Padding
        if any([self.padding_top, self.padding_right, self.padding_bottom, self.padding_left]):
            styles.append(f"padding: {self.padding_top}px {self.padding_right}px {self.padding_bottom}px {self.padding_left}px;")
        
        # Margin
        if any([self.margin_top, self.margin_right, self.margin_bottom, self.margin_left]):
            styles.append(f"margin: {self.margin_top}px {self.margin_right}px {self.margin_bottom}px {self.margin_left}px;")
        
        # Display
        if self.display:
            styles.append(f"display: {self.display};")
        
        # Flex
        if self.display == 'flex':
            if self.flex_direction:
                styles.append(f"flex-direction: {self.flex_direction};")
            if self.justify_content:
                styles.append(f"justify-content: {self.justify_content};")
            if self.align_items:
                styles.append(f"align-items: {self.align_items};")
        
        # Custom CSS
        if self.custom_css:
            styles.append(self.custom_css)
        
        return ' '.join(styles)

    def _generate_gradient_css(self):
        """Generate CSS gradient"""
        self.ensure_one()
        
        if self.gradient_type == 'linear':
            return f"linear-gradient({self.gradient_direction}deg, {self.gradient_color_start}, {self.gradient_color_end})"
        else:  # radial
            return f"radial-gradient(circle, {self.gradient_color_start}, {self.gradient_color_end})"

    def _render_table_html(self):
        """Render table HTML"""
        # Simplified for now
        return f'<table class="element element-table" style="{self._generate_css_style()}"><tr><td>Table Placeholder</td></tr></table>'

    def _render_shape_html(self, style):
        """Render shape HTML"""
        return f'<div class="element element-shape shape-{self.shape_type}" style="{style}"></div>'

    def _render_line_html(self):
        """Render line HTML"""
        return f'<svg class="element element-line"><line x1="{self.x}" y1="{self.y}" x2="{self.line_x2}" y2="{self.line_y2}" stroke="{self.color}" stroke-width="1"/></svg>'

    def _render_barcode_html(self, style):
        """Render barcode/QR HTML"""
        return f'<div class="element element-barcode" style="{style}"><span class="barcode-placeholder">{self.code_type.upper()}</span></div>'

    def _render_for_pdf(self, data_dict):
        """Render element for PDF with actual data"""
        self.ensure_one()
        
        style = self._generate_css_style()
        
        if self.element_type == 'text':
            return f'<div class="element element-text" style="{style}">{self.content or ""}</div>'
        
        elif self.element_type == 'field':
            # Replace field placeholder with actual data
            field_value = self._get_field_value(self.field_name, data_dict)
            return f'<div class="element element-field" style="{style}">{field_value}</div>'
        
        elif self.element_type == 'image':
            img_src = f"data:image/png;base64,{self.image_data.decode('utf-8')}" if self.image_data else self.image_url
            return f'<img class="element element-image" src="{img_src}" style="{style}"/>'
        
        elif self.element_type == 'table':
            return self._render_table_for_pdf(data_dict)
        
        elif self.element_type == 'shape':
            return self._render_shape_html(style)
        
        elif self.element_type == 'line':
            return self._render_line_html()
        
        elif self.element_type in ('barcode', 'qr'):
            return self._render_barcode_html(style)
        
        return ''
    
    def _get_field_value(self, field_name, data_dict):
        """Get field value from data dictionary with formatting"""
        if not field_name or not data_dict:
            return ''
        
        value = data_dict.get(field_name, '')
        
        # Format based on field type
        if not value:
            return ''
        
        # Handle different data types
        if hasattr(value, 'name'):  # Many2one field
            return value.name or ''
        elif isinstance(value, (int, float)):
            if field_name in ['amount_untaxed', 'amount_tax', 'amount_total', 'amount_discount', 'amount_total_iqd']:
                # Format currency
                currency = data_dict.get('currency_id')
                if currency:
                    return f"{currency.symbol or ''} {value:,.2f}"
                return f"{value:,.2f}"
            return str(value)
        elif hasattr(value, 'strftime'):  # Date/Datetime
            return value.strftime('%Y-%m-%d')
        else:
            return str(value)
    
    def _render_table_for_pdf(self, data_dict):
        """Render order lines table with actual data and full customization"""
        order_lines = data_dict.get('order_line', [])
        
        if not order_lines:
            return f'<div class="element element-table" style="{self._generate_css_style()}">لا توجد منتجات</div>'
        
        # Build column list based on visibility settings with custom order
        all_columns = [
            ('product', self.header_product, self.column_width_product, self.column_order_product, self.show_column_product, self.column_align_product),
            ('description', self.header_description, self.column_width_description, self.column_order_description, self.show_column_description, self.column_align_description),
            ('qty', self.header_qty, self.column_width_qty, self.column_order_qty, self.show_column_qty, self.column_align_qty),
            ('uom', self.header_uom, self.column_width_uom, self.column_order_uom, self.show_column_uom, self.column_align_uom),
            ('price', self.header_price, self.column_width_price, self.column_order_price, self.show_column_price, self.column_align_price),
            ('discount', self.header_discount, self.column_width_discount, self.column_order_discount, self.show_column_discount, self.column_align_discount),
            ('tax', self.header_tax, self.column_width_tax, self.column_order_tax, self.show_column_tax, self.column_align_tax),
            ('subtotal', self.header_subtotal, self.column_width_subtotal, self.column_order_subtotal, self.show_column_subtotal, self.column_align_subtotal),
        ]
        
        # Filter visible columns and sort by order
        columns = [(col[0], col[1], col[2], col[5]) for col in all_columns if col[4]]  # col[4] is show_column
        columns = sorted(columns, key=lambda x: all_columns[[c[0] for c in all_columns].index(x[0])][3])  # Sort by order field
        
        # Determine table font
        table_font = ''
        if self.table_font_family == 'inherit':
            if self.font_family_name and self.font_family_name != 'custom':
                table_font = self.font_family_name
            elif self.font_family_name == 'custom' and self.custom_font_name:
                table_font = self.custom_font_name
        elif self.table_font_family == 'custom' and self.table_custom_font:
            table_font = self.table_custom_font
        elif self.table_font_family != 'inherit':
            table_font = self.table_font_family
        
        font_style = f"font-family: '{table_font}', 'Almarai', 'Arial', sans-serif;" if table_font else ''
        
        # Table direction
        direction = self.table_direction or 'rtl'
        text_align_default = 'right' if direction == 'rtl' else 'left'
        
        # Table header style
        header_style = f"background-color: {self.table_header_bg}; color: {self.table_header_color}; font-size: {self.table_header_font_size}pt; font-weight: {self.table_header_font_weight}; padding: {self.table_cell_padding}px; {font_style}"
        
        # Build table HTML
        table_html = f'''
        <table class="element element-table" style="{self._generate_css_style()}; width: 100%; border-collapse: collapse; direction: {direction}; text-align: {text_align_default}; border: {self.table_border_width}px solid {self.table_border_color}; {font_style}">
            <thead>
                <tr style="{header_style}">
        '''
        
        # Add headers
        for col_key, col_header, col_width, col_align in columns:
            table_html += f'<th style="width: {col_width}%; padding: {self.table_cell_padding}px; text-align: {col_align}; border: {self.table_border_width}px solid {self.table_border_color};">{col_header}</th>'
        
        table_html += '''
                </tr>
            </thead>
            <tbody>
        '''
        
        # Add rows
        for idx, line in enumerate(order_lines):
            # Alternate row colors
            row_bg = self.table_row_alternate_bg if idx % 2 == 1 else self.table_row_bg
            row_style = f"background-color: {row_bg}; color: {self.table_row_color}; font-size: {self.table_row_font_size}pt; {font_style}"
            
            table_html += f'<tr style="{row_style}">'
            
            # Get line data
            product_name = line.product_id.name if hasattr(line, 'product_id') and line.product_id else ''
            description = line.name if hasattr(line, 'name') else ''
            quantity = line.quantity if hasattr(line, 'quantity') else (line.product_uom_qty if hasattr(line, 'product_uom_qty') else 0)
            uom = line.product_uom.name if hasattr(line, 'product_uom') and line.product_uom else (line.product_id.uom_id.name if hasattr(line, 'product_id') and line.product_id and line.product_id.uom_id else 'قطعة')
            price = line.price_unit if hasattr(line, 'price_unit') else 0
            discount = line.discount if hasattr(line, 'discount') else 0
            tax = line.price_tax if hasattr(line, 'price_tax') else 0
            subtotal = line.price_subtotal if hasattr(line, 'price_subtotal') else (quantity * price)
            
            # Add cells based on visible columns (in order)
            for col_key, col_header, col_width, col_align in columns:
                cell_style = f"padding: {self.table_cell_padding}px; text-align: {col_align}; border: {self.table_border_width}px solid {self.table_border_color};"
                
                if col_key == 'product':
                    table_html += f'<td style="{cell_style}">{product_name}</td>'
                elif col_key == 'description':
                    table_html += f'<td style="{cell_style}">{description}</td>'
                elif col_key == 'qty':
                    table_html += f'<td style="{cell_style}">{quantity}</td>'
                elif col_key == 'uom':
                    table_html += f'<td style="{cell_style}">{uom}</td>'
                elif col_key == 'price':
                    table_html += f'<td style="{cell_style}">{price:,.2f}</td>'
                elif col_key == 'discount':
                    table_html += f'<td style="{cell_style}">{discount}%</td>'
                elif col_key == 'tax':
                    table_html += f'<td style="{cell_style}">{tax:,.2f}</td>'
                elif col_key == 'subtotal':
                    table_html += f'<td style="{cell_style}">{subtotal:,.2f}</td>'
            
            table_html += '</tr>'
        
        table_html += '''
            </tbody>
        '''
        
        # Add footer if enabled
        if self.show_table_footer and self.table_footer_text:
            table_html += f'''
            <tfoot>
                <tr style="{header_style}">
                    <td colspan="{len(columns)}" style="padding: {self.table_cell_padding}px; text-align: center;">{self.table_footer_text}</td>
                </tr>
            </tfoot>
            '''
        
        table_html += '''
        </table>
        '''
        
        return table_html

    @api.constrains('x', 'y', 'width', 'height')
    def _check_dimensions(self):
        """Validate dimensions"""
        for element in self:
            if element.width <= 0 or element.height <= 0:
                raise ValidationError(_('Width and height must be positive!'))

