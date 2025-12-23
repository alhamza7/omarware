# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class InvoiceTemplateDesigner(models.Model):
    """مصمم قوالب الفواتير - Visual Invoice Template Designer"""
    _name = 'invoice.template.designer'
    _description = 'Invoice Template Designer'
    _order = 'sequence, name'
    
    # ========== Basic Info ==========
    name = fields.Char('Template Name', required=True, translate=True)
    code = fields.Char('Template Code', required=True, copy=False, index=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    
    # ========== Template Type ==========
    template_type = fields.Selection([
        ('sale_order', 'Sale Order'),
        ('quotation', 'Quotation'),
        ('invoice', 'Invoice'),
        ('pos_order', 'POS Order'),
        ('delivery', 'Delivery Note'),
    ], string='Template Type', required=True, default='sale_order')
    
    # ========== Canvas Settings ==========
    canvas_width = fields.Integer('Canvas Width (mm)', default=210)  # A4
    canvas_height = fields.Integer('Canvas Height (mm)', default=297)  # A4
    canvas_unit = fields.Selection([
        ('mm', 'Millimeters'),
        ('px', 'Pixels'),
    ], string='Unit', default='mm')
    
    orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='Orientation', default='portrait')
    
    # ========== Design Data ==========
    design_json = fields.Text('Design Data (JSON)',
                              help="Canvas design data in JSON format")
    elements = fields.One2many('invoice.template.element', 'template_id',
                              string='Elements')
    
    # ========== Background ==========
    background_color = fields.Char('Background Color', default='#FFFFFF')
    background_image = fields.Binary('Background Image')
    background_filename = fields.Char('Background Filename')
    background_opacity = fields.Float('Background Opacity', default=1.0,
                                     help="0.0 = transparent, 1.0 = opaque")
    
    # ========== Margins ==========
    margin_top = fields.Integer('Margin Top (mm)', default=10)
    margin_bottom = fields.Integer('Margin Bottom (mm)', default=10)
    margin_left = fields.Integer('Margin Left (mm)', default=10)
    margin_right = fields.Integer('Margin Right (mm)', default=10)
    
    # ========== Settings ==========
    is_default = fields.Boolean('Default Template',
                                help="Use this template by default for this type")
    show_grid = fields.Boolean('Show Grid', default=True)
    grid_size = fields.Integer('Grid Size (mm)', default=5)
    snap_to_grid = fields.Boolean('Snap to Grid', default=True)
    
    # ========== Statistics ==========
    usage_count = fields.Integer('Usage Count', readonly=True, default=0)
    last_used = fields.Datetime('Last Used', readonly=True)
    
    # ========== Company ==========
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Template code must be unique per company!'),
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure code is unique"""
        for vals in vals_list:
            if vals.get('code'):
                existing = self.search([
                    ('code', '=', vals['code']),
                    ('company_id', '=', vals.get('company_id', self.env.company.id))
                ])
                if existing:
                    raise UserError(_(f"Template with code '{vals['code']}' already exists!"))
        return super(InvoiceTemplateDesigner, self).create(vals_list)
    
    def action_open_designer(self):
        """Open visual designer"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'invoice_designer',
            'name': _('Invoice Designer: %s') % self.name,
            'params': {
                'template_id': self.id,
            },
            'target': 'fullscreen',
        }
    
    def action_preview(self):
        """Preview template with sample data"""
        self.ensure_one()
        
        # Get sample record based on template type
        if self.template_type == 'sale_order':
            record = self.env['sale.order'].search([], limit=1)
        elif self.template_type == 'pos_order':
            record = self.env['pos.order'].search([], limit=1)
        else:
            raise UserError(_('No sample data available for this template type'))
        
        if not record:
            raise UserError(_('No records found for preview'))
        
        # Generate PDF
        pdf = self.generate_pdf(record.id, record._name)
        
        # Save as attachment
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'Preview_{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def generate_pdf(self, record_id, model_name):
        """Generate PDF for a record using this template"""
        self.ensure_one()
        
        # Update usage stats
        self.sudo().write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now()
        })
        
        # Get record
        record = self.env[model_name].browse(record_id)
        
        # Generate HTML from template
        html = self._render_template(record)
        
        # Convert to PDF
        pdf = self.env['ir.actions.report']._run_wkhtmltopdf(
            [html.encode('utf-8')],
            landscape=(self.orientation == 'landscape'),
            specific_paperformat_args={
                'data-report-margin-top': self.margin_top,
                'data-report-margin-bottom': self.margin_bottom,
                'data-report-margin-left': self.margin_left,
                'data-report-margin-right': self.margin_right,
                'data-report-page-width': self.canvas_width if self.orientation == 'portrait' else self.canvas_height,
                'data-report-page-height': self.canvas_height if self.orientation == 'portrait' else self.canvas_width,
            }
        )
        
        return pdf
    
    def _render_template(self, record):
        """Render template with data"""
        self.ensure_one()
        
        html_parts = ['<!DOCTYPE html><html><head>']
        html_parts.append('<meta charset="utf-8"/>')
        html_parts.append('<style>')
        html_parts.append(f'''
            body {{
                margin: 0;
                padding: 0;
                background-color: {self.background_color};
            }}
            .page {{
                width: {self.canvas_width}mm;
                height: {self.canvas_height}mm;
                position: relative;
                page-break-after: always;
            }}
            .element {{
                position: absolute;
                box-sizing: border-box;
            }}
        ''')
        html_parts.append('</style>')
        html_parts.append('</head><body>')
        html_parts.append('<div class="page">')
        
        # Background image
        if self.background_image:
            html_parts.append(f'''
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                        opacity: {self.background_opacity}; z-index: -1;">
                <img src="data:image/png;base64,{self.background_image.decode()}" 
                     style="width: 100%; height: 100%; object-fit: cover;"/>
            </div>
            ''')
        
        # Render elements
        for element in self.elements.sorted(key=lambda e: e.sequence):
            html_parts.append(element._render_html(record))
        
        html_parts.append('</div>')
        html_parts.append('</body></html>')
        
        return ''.join(html_parts)
    
    def action_duplicate(self):
        """Duplicate template"""
        self.ensure_one()
        
        new_template = self.copy({
            'name': f'{self.name} (Copy)',
            'code': f'{self.code}_COPY',
            'is_default': False,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }


class InvoiceTemplateElement(models.Model):
    """عنصر في قالب الفاتورة - Template Element"""
    _name = 'invoice.template.element'
    _description = 'Invoice Template Element'
    _order = 'sequence, id'
    
    template_id = fields.Many2one('invoice.template.designer', 'Template',
                                  required=True, ondelete='cascade')
    sequence = fields.Integer('Layer Order', default=10,
                             help="Lower numbers are rendered first (behind)")
    
    # ========== Element Type ==========
    element_type = fields.Selection([
        ('text', 'Static Text'),
        ('field', 'Data Field'),
        ('image', 'Image'),
        ('shape', 'Shape'),
        ('line', 'Line'),
        ('table', 'Table'),
        ('barcode', 'Barcode'),
        ('qrcode', 'QR Code'),
    ], string='Element Type', required=True, default='text')
    
    # ========== Position & Size (in mm) ==========
    x = fields.Float('X Position', default=0, help="Left position in mm")
    y = fields.Float('Y Position', default=0, help="Top position in mm")
    width = fields.Float('Width', default=50, help="Width in mm")
    height = fields.Float('Height', default=10, help="Height in mm")
    rotation = fields.Float('Rotation', default=0, help="Rotation in degrees")
    
    # ========== Data Binding ==========
    field_name = fields.Char('Field Name',
                             help="e.g., 'partner_id.name', 'amount_total', 'sap_doc_num'")
    field_model = fields.Char('Model', help="e.g., 'sale.order'")
    format_string = fields.Char('Format String',
                                help="Python format string, e.g., '{:.2f}'")
    default_value = fields.Char('Default Value',
                                help="Value to show if field is empty")
    
    # ========== Style - Font ==========
    font_family = fields.Char('Font Family', default='Arial')
    font_size = fields.Integer('Font Size (pt)', default=12)
    font_weight = fields.Selection([
        ('normal', 'Normal'),
        ('bold', 'Bold'),
    ], string='Font Weight', default='normal')
    font_style = fields.Selection([
        ('normal', 'Normal'),
        ('italic', 'Italic'),
    ], string='Font Style', default='normal')
    text_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justify'),
    ], string='Text Align', default='left')
    
    # ========== Style - Colors ==========
    color = fields.Char('Text Color', default='#000000')
    background_color = fields.Char('Background Color', default='transparent')
    
    # ========== Style - Border ==========
    border_width = fields.Integer('Border Width (px)', default=0)
    border_color = fields.Char('Border Color', default='#000000')
    border_style = fields.Selection([
        ('solid', 'Solid'),
        ('dashed', 'Dashed'),
        ('dotted', 'Dotted'),
    ], string='Border Style', default='solid')
    border_radius = fields.Integer('Border Radius (px)', default=0)
    
    # ========== Content ==========
    static_text = fields.Text('Static Text')
    image_data = fields.Binary('Image Data')
    image_filename = fields.Char('Image Filename')
    
    # ========== Table Settings ==========
    table_data_source = fields.Char('Table Data Source',
                                    help="e.g., 'order_line' for sale order lines")
    table_columns_json = fields.Text('Table Columns (JSON)')
    show_table_header = fields.Boolean('Show Header', default=True)
    table_row_height = fields.Integer('Row Height (mm)', default=10)
    
    # ========== Conditions ==========
    visible_if = fields.Char('Visible If',
                            help="Python expression, e.g., 'invoice_type == \"2\"'")
    
    def _render_html(self, record):
        """Render element as HTML"""
        self.ensure_one()
        
        # Check visibility condition
        if self.visible_if:
            try:
                if not self._eval_condition(self.visible_if, record):
                    return ''
            except Exception as e:
                _logger.warning(f"Error evaluating condition: {e}")
        
        # Build style
        style = self._build_style()
        
        # Render based on type
        if self.element_type == 'text':
            content = self.static_text or ''
        elif self.element_type == 'field':
            content = self._get_field_value(record)
        elif self.element_type == 'image':
            return self._render_image(style)
        elif self.element_type == 'table':
            return self._render_table(record, style)
        elif self.element_type == 'shape':
            return self._render_shape(style)
        elif self.element_type == 'line':
            return self._render_line(style)
        elif self.element_type in ['barcode', 'qrcode']:
            return self._render_code(record, style)
        else:
            content = ''
        
        return f'<div class="element" style="{style}">{content}</div>'
    
    def _build_style(self):
        """Build CSS style string"""
        styles = []
        styles.append(f'left: {self.x}mm')
        styles.append(f'top: {self.y}mm')
        styles.append(f'width: {self.width}mm')
        styles.append(f'height: {self.height}mm')
        
        if self.rotation:
            styles.append(f'transform: rotate({self.rotation}deg)')
        
        styles.append(f'font-family: {self.font_family}')
        styles.append(f'font-size: {self.font_size}pt')
        styles.append(f'font-weight: {self.font_weight}')
        styles.append(f'font-style: {self.font_style}')
        styles.append(f'text-align: {self.text_align}')
        styles.append(f'color: {self.color}')
        styles.append(f'background-color: {self.background_color}')
        
        if self.border_width > 0:
            styles.append(f'border: {self.border_width}px {self.border_style} {self.border_color}')
        
        if self.border_radius > 0:
            styles.append(f'border-radius: {self.border_radius}px')
        
        return '; '.join(styles)
    
    def _get_field_value(self, record):
        """Get field value from record"""
        if not self.field_name:
            return self.default_value or ''
        
        try:
            # Navigate through relations (e.g., partner_id.name)
            value = record
            for part in self.field_name.split('.'):
                value = getattr(value, part, None)
                if value is None:
                    break
            
            if value is None:
                return self.default_value or ''
            
            # Apply format string
            if self.format_string:
                try:
                    return self.format_string.format(value)
                except:
                    pass
            
            return str(value)
        except Exception as e:
            _logger.warning(f"Error getting field value '{self.field_name}': {e}")
            return self.default_value or ''
    
    def _render_image(self, style):
        """Render image element"""
        if not self.image_data:
            return ''
        
        return f'''
        <div class="element" style="{style}">
            <img src="data:image/png;base64,{self.image_data.decode()}" 
                 style="width: 100%; height: 100%; object-fit: contain;"/>
        </div>
        '''
    
    def _render_table(self, record, style):
        """Render table element"""
        if not self.table_data_source:
            return ''
        
        try:
            # Get table data (e.g., order_line)
            lines = getattr(record, self.table_data_source, [])
            if not lines:
                return ''
            
            # Parse columns
            columns = json.loads(self.table_columns_json or '[]')
            if not columns:
                return ''
            
            html = [f'<div class="element" style="{style}">']
            html.append('<table style="width: 100%; border-collapse: collapse;">')
            
            # Header
            if self.show_table_header:
                html.append('<thead><tr>')
                for col in columns:
                    html.append(f'<th style="border: 1px solid #ddd; padding: 5px;">{col.get("label", "")}</th>')
                html.append('</tr></thead>')
            
            # Body
            html.append('<tbody>')
            for line in lines:
                html.append(f'<tr style="height: {self.table_row_height}mm;">')
                for col in columns:
                    field_name = col.get('field', '')
                    value = getattr(line, field_name, '')
                    html.append(f'<td style="border: 1px solid #ddd; padding: 5px;">{value}</td>')
                html.append('</tr>')
            html.append('</tbody>')
            
            html.append('</table></div>')
            return ''.join(html)
        except Exception as e:
            _logger.warning(f"Error rendering table: {e}")
            return ''
    
    def _render_shape(self, style):
        """Render shape (rectangle)"""
        return f'<div class="element" style="{style}"></div>'
    
    def _render_line(self, style):
        """Render line"""
        line_style = style + f'; border-top: {self.border_width}px {self.border_style} {self.border_color}; height: 0;'
        return f'<div class="element" style="{line_style}"></div>'
    
    def _render_code(self, record, style):
        """Render barcode/QR code"""
        # TODO: Implement barcode generation
        return f'<div class="element" style="{style}">[Barcode/QR Code]</div>'
    
    def _eval_condition(self, condition, record):
        """Evaluate visibility condition"""
        try:
            # Simple evaluation - can be enhanced
            return eval(condition, {'record': record})
        except:
            return True

