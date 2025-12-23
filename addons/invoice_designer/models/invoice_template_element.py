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
    font_family_name = fields.Char('Font Family Name', default='Arial')
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

    # ==================== BORDER RADIUS (4 Corners) ====================
    border_top_left_radius = fields.Integer('Top-Left Radius (px)', default=0)
    border_top_right_radius = fields.Integer('Top-Right Radius (px)', default=0)
    border_bottom_right_radius = fields.Integer('Bottom-Right Radius (px)', default=0)
    border_bottom_left_radius = fields.Integer('Bottom-Left Radius (px)', default=0)

    # ==================== BOX SHADOW ====================
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
        
        # Position & Size
        styles.append(f"position: {self.position};")
        styles.append(f"left: {self.x}mm;")
        styles.append(f"top: {self.y}mm;")
        styles.append(f"width: {self.width}mm;")
        styles.append(f"height: {self.height}mm;")
        
        if self.rotation:
            styles.append(f"transform: rotate({self.rotation}deg);")
        
        styles.append(f"z-index: {self.z_index};")
        
        # Font
        if self.font_family_name:
            styles.append(f"font-family: '{self.font_family_name}';")
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
        # Similar to _render_html but with data substitution
        return self._render_html()

    @api.constrains('x', 'y', 'width', 'height')
    def _check_dimensions(self):
        """Validate dimensions"""
        for element in self:
            if element.width <= 0 or element.height <= 0:
                raise ValidationError(_('Width and height must be positive!'))

