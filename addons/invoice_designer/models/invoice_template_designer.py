# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import base64
import logging

_logger = logging.getLogger(__name__)


class InvoiceTemplateDesigner(models.Model):
    """مصمم قوالب الفواتير - Visual Invoice Template Designer"""
    _name = 'invoice.template.designer'
    _description = 'Invoice Template Designer'
    _order = 'sequence, name'

    # ==================== Basic Information ====================
    name = fields.Char('Template Name', required=True, translate=True)
    code = fields.Char('Template Code', required=True, copy=False)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Description', translate=True)
    
    # ==================== Template Type ====================
    template_type = fields.Selection([
        ('sale_order', 'Sale Order'),
        ('quotation', 'Quotation'),
        ('invoice', 'Invoice'),
        ('pos_receipt', 'POS Receipt'),
        ('delivery_note', 'Delivery Note'),
        ('draft', 'Draft'),
        ('custom', 'Custom'),
    ], string='Document Type', required=True, default='sale_order')
    
    # ==================== Currency & Language ====================
    currency_id = fields.Many2one('res.currency', 'Currency')
    language_id = fields.Many2one('res.lang', 'Language')
    is_default = fields.Boolean('Default Template', default=False)
    
    # ==================== Canvas Settings ====================
    # Page Size
    page_format = fields.Selection([
        ('A4', 'A4 (210 x 297 mm)'),
        ('A5', 'A5 (148 x 210 mm)'),
        ('letter', 'Letter (216 x 279 mm)'),
        ('legal', 'Legal (216 x 356 mm)'),
        ('custom', 'Custom'),
    ], string='Page Format', default='A4', required=True)
    
    page_width = fields.Float('Page Width (mm)', default=210.0)
    page_height = fields.Float('Page Height (mm)', default=297.0)
    
    page_orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='Orientation', default='portrait')
    
    # Margins
    margin_top = fields.Float('Top Margin (mm)', default=10.0)
    margin_right = fields.Float('Right Margin (mm)', default=10.0)
    margin_bottom = fields.Float('Bottom Margin (mm)', default=10.0)
    margin_left = fields.Float('Left Margin (mm)', default=10.0)
    
    # Background
    background_color = fields.Char('Background Color', default='#FFFFFF')
    background_image = fields.Binary('Background Image')
    background_image_filename = fields.Char('Background Image Filename')
    background_image_position = fields.Selection([
        ('center', 'Center'),
        ('top-left', 'Top Left'),
        ('top-center', 'Top Center'),
        ('top-right', 'Top Right'),
        ('bottom-left', 'Bottom Left'),
        ('bottom-center', 'Bottom Center'),
        ('bottom-right', 'Bottom Right'),
        ('stretch', 'Stretch'),
        ('tile', 'Tile'),
    ], string='Background Position', default='center')
    background_image_opacity = fields.Float('Background Opacity', default=1.0)
    
    # Default Font for Entire Invoice
    default_font_family = fields.Selection([
        ('Almarai', 'Almarai (عربي - افتراضي)'),
        ('Cairo', 'Cairo (عربي)'),
        ('Tajawal', 'Tajawal (عربي)'),
        ('Amiri', 'Amiri (عربي)'),
        ('Arial', 'Arial'),
        ('Helvetica', 'Helvetica'),
        ('Times New Roman', 'Times New Roman'),
        ('custom', 'Custom'),
    ], string='Default Font Family', default='Almarai',
       help='Default font for the entire invoice. Elements can override this.')
    
    default_custom_font = fields.Char('Custom Default Font')
    default_font_size = fields.Integer('Default Font Size (pt)', default=11)
    
    # Default Direction for Entire Invoice
    default_direction = fields.Selection([
        ('rtl', 'Right to Left (RTL) - Arabic'),
        ('ltr', 'Left to Right (LTR) - English'),
    ], string='Default Direction', default='rtl',
       help='Default text direction for the entire invoice')
    
    # Grid & Snap
    show_grid = fields.Boolean('Show Grid', default=True)
    grid_size = fields.Integer('Grid Size (mm)', default=5)
    snap_to_grid = fields.Boolean('Snap to Grid', default=True)
    show_rulers = fields.Boolean('Show Rulers', default=True)
    show_guides = fields.Boolean('Show Guides', default=True)
    
    # ==================== Multi-Page Settings ====================
    enable_multi_page = fields.Boolean('Enable Multi-Page', default=True)
    header_height = fields.Float('Header Height (mm)', default=30.0)
    footer_height = fields.Float('Footer Height (mm)', default=20.0)
    repeat_header = fields.Boolean('Repeat Header on Each Page', default=True)
    repeat_footer = fields.Boolean('Repeat Footer on Each Page', default=True)
    
    # ==================== Elements ====================
    element_ids = fields.One2many(
        'invoice.template.element',
        'template_id',
        string='Template Elements'
    )
    
    # ==================== Fonts Library ====================
    available_font_ids = fields.Many2many(
        'invoice.template.font',
        'template_font_rel',
        'template_id',
        'font_id',
        string='Available Fonts'
    )
    
    # ==================== SAP Integration ====================
    show_sap_doc_number = fields.Boolean('Show SAP Document Number', default=True)
    sap_doc_number_label = fields.Char('SAP Doc Label', default='SAP Doc #:', translate=True)
    
    # ==================== PDF Settings ====================
    # PDF Rendering Engine
    render_engine = fields.Selection([
        ('playwright', 'Playwright (Chromium) - Best Quality'),
        ('weasyprint', 'WeasyPrint - Fast & Good'),
        ('wkhtmltopdf', 'wkhtmltopdf - Fast but Basic'),
    ], string='PDF Engine', default='playwright', required=True,
       help="Playwright: 100% accurate but slower (2-3s)\n"
            "WeasyPrint: Fast and accurate for most cases (1s)\n"
            "wkhtmltopdf: Fastest but limited CSS support (<1s)")
    
    pdf_quality = fields.Selection([
        ('draft', 'Draft (Fast)'),
        ('normal', 'Normal'),
        ('high', 'High Quality'),
    ], string='PDF Quality', default='normal')
    
    pdf_compression = fields.Boolean('Compress PDF', default=True)
    pdf_encryption = fields.Boolean('Encrypt PDF', default=False)
    pdf_password = fields.Char('PDF Password')
    
    # ==================== Preview ====================
    preview_html = fields.Html('Preview HTML', compute='_compute_preview_html')
    preview_pdf = fields.Binary('Preview PDF', attachment=True)
    
    # ==================== Statistics ====================
    usage_count = fields.Integer('Usage Count', default=0, readonly=True)
    last_used_date = fields.Datetime('Last Used Date', readonly=True)
    
    # Backwards compatibility computed fields (for old views in DB)
    last_used = fields.Datetime('Last Used', compute='_compute_backwards_compat', store=False)
    canvas_width = fields.Float('Canvas Width', compute='_compute_backwards_compat', store=False)
    canvas_height = fields.Float('Canvas Height', compute='_compute_backwards_compat', store=False)
    paper_format = fields.Char('Paper Format', compute='_compute_backwards_compat', store=False)
    orientation = fields.Char('Orientation', compute='_compute_backwards_compat', store=False)
    
    @api.depends('last_used_date', 'page_width', 'page_height', 'page_format', 'page_orientation')
    def _compute_backwards_compat(self):
        """Computed fields for backwards compatibility with old views"""
        for record in self:
            record.last_used = record.last_used_date
            record.canvas_width = record.page_width
            record.canvas_height = record.page_height
            record.paper_format = record.page_format
            record.orientation = record.page_orientation
    
    # ==================== Company ====================
    company_id = fields.Many2one('res.company', 'Company', 
                                  default=lambda self: self.env.company)

    # ==================== SQL Constraints ====================
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Template code must be unique!'),
    ]

    # ==================== Computed Fields ====================
    @api.depends('element_ids', 'page_width', 'page_height')
    def _compute_preview_html(self):
        """Generate HTML preview"""
        for template in self:
            html = template._generate_html_preview()
            template.preview_html = html

    # ==================== Page Format Change ====================
    @api.onchange('page_format')
    def _onchange_page_format(self):
        """تحديث أبعاد الصفحة عند تغيير الحجم"""
        if self.page_format == 'A4':
            if self.page_orientation == 'portrait':
                self.page_width = 210.0
                self.page_height = 297.0
            else:
                self.page_width = 297.0
                self.page_height = 210.0
        elif self.page_format == 'A5':
            if self.page_orientation == 'portrait':
                self.page_width = 148.0
                self.page_height = 210.0
            else:
                self.page_width = 210.0
                self.page_height = 148.0
        elif self.page_format == 'letter':
            if self.page_orientation == 'portrait':
                self.page_width = 216.0
                self.page_height = 279.0
            else:
                self.page_width = 279.0
                self.page_height = 216.0
        elif self.page_format == 'legal':
            if self.page_orientation == 'portrait':
                self.page_width = 216.0
                self.page_height = 356.0
            else:
                self.page_width = 356.0
                self.page_height = 216.0

    @api.onchange('page_orientation')
    def _onchange_page_orientation(self):
        """عكس الأبعاد عند تغيير الاتجاه"""
        if self.page_format != 'custom':
            self.page_width, self.page_height = self.page_height, self.page_width

    # ==================== Default Template ====================
    @api.constrains('is_default', 'template_type')
    def _check_default_template(self):
        """التأكد من وجود قالب افتراضي واحد فقط لكل نوع"""
        for template in self:
            if template.is_default:
                other_defaults = self.search([
                    ('id', '!=', template.id),
                    ('template_type', '=', template.template_type),
                    ('is_default', '=', True),
                ])
                if other_defaults:
                    raise ValidationError(_(
                        'Only one default template is allowed per document type!'
                    ))

    # ==================== Actions ====================
    def action_open_visual_designer(self):
        """فتح المصمم المرئي"""
        self.ensure_one()
        # Use URL with hash to pass template_id
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web#action=invoice_designer_canvas&template_id={self.id}',
            'target': 'self',
        }

    def action_preview_pdf(self):
        """معاينة PDF"""
        self.ensure_one()
        # Generate preview with dummy data
        pdf_data = self._generate_pdf_preview()
        self.preview_pdf = base64.b64encode(pdf_data)
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/invoice.template.designer/{self.id}/preview_pdf/preview.pdf?download=true',
            'target': 'new',
        }

    def action_duplicate(self):
        """نسخ القالب"""
        self.ensure_one()
        new_template = self.copy({
            'name': _('%s (Copy)') % self.name,
            'code': f"{self.code}_copy_{self.id}",
            'is_default': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.template.designer',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ==================== PDF Generation ====================
    def _generate_html_preview(self):
        """Generate HTML preview for canvas"""
        self.ensure_one()
        
        html = f'''
        <div class="invoice-template-preview" style="
            width: {self.page_width}mm;
            height: {self.page_height}mm;
            background-color: {self.background_color};
            position: relative;
            overflow: hidden;
        ">
        '''
        
        # Background Image
        if self.background_image:
            bg_style = self._get_background_image_style()
            html += f'<div class="background-image" style="{bg_style}"></div>'
        
        # Elements
        for element in self.element_ids.sorted(key=lambda e: e.z_index):
            html += element._render_html()
        
        html += '</div>'
        return html

    def _get_background_image_style(self):
        """Get background image CSS style"""
        self.ensure_one()
        if not self.background_image:
            return ''
        
        bg_url = f"data:image/png;base64,{self.background_image.decode('utf-8')}"
        
        position_map = {
            'center': 'center center',
            'top-left': 'top left',
            'top-center': 'top center',
            'top-right': 'top right',
            'bottom-left': 'bottom left',
            'bottom-center': 'bottom center',
            'bottom-right': 'bottom right',
            'stretch': 'center center',
            'tile': 'top left',
        }
        
        size_map = {
            'stretch': 'cover',
            'tile': 'auto',
        }
        
        style = f'''
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("{bg_url}");
            background-position: {position_map.get(self.background_image_position, 'center')};
            background-size: {size_map.get(self.background_image_position, 'contain')};
            background-repeat: {'repeat' if self.background_image_position == 'tile' else 'no-repeat'};
            opacity: {self.background_image_opacity};
            z-index: 0;
        '''
        
        return style

    def _generate_pdf_preview(self):
        """Generate PDF preview with dummy data"""
        self.ensure_one()
        
        # Create HTML with styles
        html = self._generate_full_html_for_pdf({
            'name': 'Sample Customer',
            'order_number': 'SO001',
            'date_order': fields.Date.today(),
            'order_line': [
                {'product_id': {'name': 'Product 1'}, 'product_uom_qty': 2, 'price_unit': 100},
                {'product_id': {'name': 'Product 2'}, 'product_uom_qty': 1, 'price_unit': 200},
            ],
        })
        
        # Generate PDF using wkhtmltopdf
        pdf = self.env['ir.actions.report']._run_wkhtmltopdf(
            [html.encode('utf-8')],
            landscape=(self.page_orientation == 'landscape'),
        )
        
        return pdf

    def _generate_full_html_for_pdf(self, data_dict):
        """Generate complete HTML for PDF generation with Google Fonts support"""
        self.ensure_one()
        
        # Get used fonts from elements
        used_fonts = set()
        
        # Add default font
        if self.default_font_family and self.default_font_family != 'custom':
            used_fonts.add(self.default_font_family)
        elif self.default_font_family == 'custom' and self.default_custom_font:
            used_fonts.add(self.default_custom_font)
        
        # Add fonts from elements
        for element in self.element_ids:
            if element.font_family_name and element.font_family_name != 'custom':
                used_fonts.add(element.font_family_name)
            elif element.font_family_name == 'custom' and element.custom_font_name:
                used_fonts.add(element.custom_font_name)
            # Add table font
            if element.element_type == 'table' and element.table_font_family and element.table_font_family != 'custom' and element.table_font_family != 'inherit':
                used_fonts.add(element.table_font_family)
            elif element.element_type == 'table' and element.table_font_family == 'custom' and element.table_custom_font:
                used_fonts.add(element.table_custom_font)
        
        # Google Fonts imports for Arabic and other fonts
        google_fonts_import = ""
        if used_fonts:
            # Arabic + English fonts from Google Fonts
            arabic_fonts = {
                'Almarai': 'Almarai:300,400,700,800',
                'Cairo': 'Cairo:200,300,400,600,700,900',
                'Tajawal': 'Tajawal:200,300,400,500,700,800,900',
                'Amiri': 'Amiri:400,700',
                'Scheherazade New': 'Scheherazade+New:400,700',
                'Noto Sans Arabic': 'Noto+Sans+Arabic:100,200,300,400,500,600,700,800,900',
                'IBM Plex Sans Arabic': 'IBM+Plex+Sans+Arabic:100,200,300,400,500,600,700',
                'Markazi Text': 'Markazi+Text:400,500,600,700',
                'El Messiri': 'El+Messiri:400,500,600,700',
                'Lateef': 'Lateef:200,300,400,500,600,700,800',
            }
            
            fonts_to_import = []
            for font in used_fonts:
                if font in arabic_fonts:
                    fonts_to_import.append(arabic_fonts[font])
            
            if fonts_to_import:
                google_fonts_import = f"@import url('https://fonts.googleapis.com/css2?{('&').join([f'family={f}' for f in fonts_to_import])}&display=swap');"
        
        # Determine default direction
        direction = self.default_direction or 'rtl'
        lang = 'ar' if direction == 'rtl' else 'en'
        
        # Determine default font
        default_font = 'Almarai'
        if self.default_font_family and self.default_font_family != 'custom':
            default_font = self.default_font_family
        elif self.default_font_family == 'custom' and self.default_custom_font:
            default_font = self.default_custom_font
        
        html = f'''<!DOCTYPE html>
<html dir="{direction}" lang="{lang}">
<head>
    <meta charset="utf-8"/>
    <style>
        {google_fonts_import}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        @page {{
            size: {self.page_width}mm {self.page_height}mm;
            margin: {self.margin_top}mm {self.margin_right}mm {self.margin_bottom}mm {self.margin_left}mm;
        }}
        
        body {{
            font-family: '{default_font}', 'Almarai', 'Arial', 'Helvetica', sans-serif;
            font-size: {self.default_font_size or 11}pt;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            direction: {direction};
        }}
        
        .page {{
            width: {self.page_width - self.margin_left - self.margin_right}mm;
            height: {self.page_height - self.margin_top - self.margin_bottom}mm;
            background-color: {self.background_color};
            position: relative;
            overflow: visible;
        }}
        
        .element {{
            box-sizing: border-box;
            overflow: visible;
        }}
        
        .element-field, .element-text {{
            white-space: normal;
            word-wrap: break-word;
            overflow: visible;
        }}
        
        .element-table {{
            border-collapse: collapse;
            width: 100%;
        }}
        
        .element-table th, .element-table td {{
            padding: 8px;
            border: 1px solid #ddd;
            vertical-align: middle;
        }}
        
        .element-table thead {{
            background-color: #4a5568;
            color: white;
        }}
        
        .element-image {{
            display: block;
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
    </style>
</head>
<body>
    <div class="page">
        {self._render_elements_for_pdf(data_dict)}
    </div>
</body>
</html>'''
        
        return html

    def _render_elements_for_pdf(self, data_dict):
        """Render all elements for PDF"""
        self.ensure_one()
        html = ''
        
        for element in self.element_ids.sorted(key=lambda e: e.z_index):
            html += element._render_for_pdf(data_dict)
        
        return html

    # ==================== Public Methods ====================
    def generate_invoice_pdf(self, order_id, model_name='sale.order'):
        """Generate PDF for a specific order using configured render engine
        
        Supports multiple rendering engines:
        - Playwright: Best quality, 100% accurate, slower (2-3s)
        - WeasyPrint: Good quality, fast (1s)  
        - wkhtmltopdf: Basic quality, fastest (<1s)
        """
        self.ensure_one()
        
        # Get order data based on model
        order = self.env[model_name].browse(order_id)
        data_dict = self._prepare_order_data(order)
        
        # Generate HTML
        html = self._generate_full_html_for_pdf(data_dict)
        
        # Ensure html is string
        if isinstance(html, bytes):
            html = html.decode('utf-8')
        
        # Choose rendering engine
        pdf_bytes = None
        
        if self.render_engine == 'playwright':
            try:
                pdf_bytes = self._generate_pdf_with_playwright(html)
            except ImportError:
                _logger.warning('Playwright not available, falling back to WeasyPrint')
                self.render_engine = 'weasyprint'
            except Exception as e:
                _logger.error(f'Playwright PDF generation failed: {e}, falling back to WeasyPrint')
                self.render_engine = 'weasyprint'
        
        if self.render_engine == 'weasyprint' and not pdf_bytes:
            try:
                pdf_bytes = self._generate_pdf_with_weasyprint(html)
            except ImportError:
                _logger.warning('WeasyPrint not available, falling back to wkhtmltopdf')
                self.render_engine = 'wkhtmltopdf'
            except Exception as e:
                _logger.error(f'WeasyPrint PDF generation failed: {e}, falling back to wkhtmltopdf')
                self.render_engine = 'wkhtmltopdf'
        
        if self.render_engine == 'wkhtmltopdf' and not pdf_bytes:
            try:
                pdf_bytes = self.env['ir.actions.report']._run_wkhtmltopdf(
                    [html],
                    landscape=(self.page_orientation == 'landscape'),
                )
            except Exception as e:
                raise UserError(_('PDF generation failed with all engines: %s') % str(e))
        
        # Update statistics
        self.usage_count += 1
        self.last_used_date = fields.Datetime.now()
        
        return pdf_bytes
    
    def _generate_pdf_with_playwright(self, html):
        """Generate PDF using Playwright (Headless Chrome)"""
        from playwright.sync_api import sync_playwright
        import tempfile
        import os
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.html', delete=False) as f:
            f.write(html)
            temp_html_path = f.name
        
        try:
            # Generate PDF using Playwright
            with sync_playwright() as p:
                # Launch browser with optimized settings
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox',
                    ]
                )
                
                page = browser.new_page()
                
                # Set viewport to match page size (mm to px at 96 DPI)
                page.set_viewport_size({
                    'width': int(self.page_width * 3.7795275591),
                    'height': int(self.page_height * 3.7795275591)
                })
                
                # Load HTML file
                page.goto(f'file:///{temp_html_path.replace(chr(92), "/")}')
                
                # Wait for page to load completely
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Generate PDF with exact dimensions
                pdf_bytes = page.pdf(
                    format=None,  # Use custom size
                    width=f'{self.page_width}mm',
                    height=f'{self.page_height}mm',
                    margin={
                        'top': f'{self.margin_top}mm',
                        'right': f'{self.margin_right}mm',
                        'bottom': f'{self.margin_bottom}mm',
                        'left': f'{self.margin_left}mm'
                    },
                    print_background=True,
                    prefer_css_page_size=False,
                    display_header_footer=False,
                )
                
                browser.close()
                
                return pdf_bytes
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_html_path)
            except:
                pass
    
    def _generate_pdf_with_weasyprint(self, html):
        """Generate PDF using WeasyPrint (Fast and lightweight)"""
        from weasyprint import HTML, CSS
        from io import BytesIO
        
        # Convert HTML string to PDF using WeasyPrint
        pdf_bytes = HTML(string=html, encoding='utf-8').write_pdf()
        
        return pdf_bytes

    def _prepare_order_data(self, order):
        """Prepare order data for rendering - supports multiple models"""
        # Basic customer info
        data = {
            # Customer/Partner Fields
            'partner_id.name': order.partner_id.name if hasattr(order, 'partner_id') and order.partner_id else '',
            'partner_id.street': order.partner_id.street if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.street else '',
            'partner_id.street2': order.partner_id.street2 if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.street2 else '',
            'partner_id.city': order.partner_id.city if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.city else '',
            'partner_id.state_id.name': order.partner_id.state_id.name if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.state_id else '',
            'partner_id.zip': order.partner_id.zip if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.zip else '',
            'partner_id.country_id.name': order.partner_id.country_id.name if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.country_id else '',
            'partner_id.phone': order.partner_id.phone if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.phone else '',
            'partner_id.mobile': order.partner_id.mobile if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.mobile else '',
            'partner_id.email': order.partner_id.email if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.email else '',
            'partner_id.vat': order.partner_id.vat if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.vat else '',
            'partner_id.ref': order.partner_id.ref if hasattr(order, 'partner_id') and order.partner_id and order.partner_id.ref else '',
            
            # Order info
            'name': order.name if hasattr(order, 'name') else '',
            'state': dict(order._fields['state'].selection).get(order.state) if hasattr(order, 'state') else '',
            
            # Invoice Type
            'invoice_type': 'فاتورة مبيعات' if hasattr(order, 'order_line') else 'فاتورة POS',
            'invoice_type_code': 'SALES' if hasattr(order, 'order_line') else 'POS',
            
            # Company info
            'company_id.name': order.company_id.name if hasattr(order, 'company_id') and order.company_id else self.env.company.name,
            'company_id.street': order.company_id.street if hasattr(order, 'company_id') and order.company_id else self.env.company.street,
            'company_id.street2': order.company_id.street2 if hasattr(order, 'company_id') and order.company_id else self.env.company.street2,
            'company_id.city': order.company_id.city if hasattr(order, 'company_id') and order.company_id else self.env.company.city,
            'company_id.zip': order.company_id.zip if hasattr(order, 'company_id') and order.company_id else self.env.company.zip,
            'company_id.country_id.name': order.company_id.country_id.name if hasattr(order, 'company_id') and order.company_id and order.company_id.country_id else self.env.company.country_id.name,
            'company_id.phone': order.company_id.phone if hasattr(order, 'company_id') and order.company_id else self.env.company.phone,
            'company_id.email': order.company_id.email if hasattr(order, 'company_id') and order.company_id else self.env.company.email,
            'company_id.vat': order.company_id.vat if hasattr(order, 'company_id') and order.company_id else self.env.company.vat,
            
            # Currency
            'currency_id': order.currency_id if hasattr(order, 'currency_id') else self.env.company.currency_id,
            'currency_id.symbol': order.currency_id.symbol if hasattr(order, 'currency_id') and order.currency_id else self.env.company.currency_id.symbol,
        }
        
        # Date field (different names in different models)
        if hasattr(order, 'date_order'):
            data['date'] = order.date_order
        elif hasattr(order, 'date'):
            data['date'] = order.date
        else:
            data['date'] = fields.Datetime.now()
        
        # SAP doc number (if available)
        data['sap_doc_number'] = order.sap_doc_number if hasattr(order, 'sap_doc_number') else ''
        
        # Order lines (different names in different models)
        if hasattr(order, 'order_line'):
            data['order_line'] = order.order_line
        elif hasattr(order, 'order_line_ids'):
            data['order_line'] = order.order_line_ids
        else:
            data['order_line'] = []
        
        # Amounts
        if hasattr(order, 'amount_untaxed'):
            data['amount_subtotal'] = order.amount_untaxed
        elif hasattr(order, 'amount_subtotal'):
            data['amount_subtotal'] = order.amount_subtotal
        else:
            data['amount_subtotal'] = 0.0
        
        data['amount_tax'] = order.amount_tax if hasattr(order, 'amount_tax') else 0.0
        data['amount_total'] = order.amount_total if hasattr(order, 'amount_total') else 0.0
        
        # Additional fields for pos.perfume.order
        data['amount_discount'] = order.amount_discount if hasattr(order, 'amount_discount') else 0.0
        data['amount_total_iqd'] = order.amount_total_iqd if hasattr(order, 'amount_total_iqd') else 0.0
        data['exchange_rate'] = order.exchange_rate if hasattr(order, 'exchange_rate') else 0.0
        data['note'] = order.note if hasattr(order, 'note') else ''
        
        if hasattr(order, 'user_id'):
            data['user_name'] = order.user_id.name if order.user_id else ''
        
        # Payment info
        if hasattr(order, 'payment_term_id'):
            data['payment_term'] = order.payment_term_id.name if order.payment_term_id else ''
        
        return data


