# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


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
    
    # Rotation
    rotate_label = fields.Boolean(
        string='Rotate Label 180°',
        default=False,
        help='Rotate the entire label 180 degrees for printing (useful for upside-down label printers)'
    )
    
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
    name_rotation = fields.Float(string='Name Rotation (degrees)', default=0.0, help='Rotation angle in degrees (0-360)')
    
    foreign_name_x = fields.Float(string='Foreign Name X Position', default=5.0)
    foreign_name_y = fields.Float(string='Foreign Name Y Position', default=12.0)
    foreign_name_rotation = fields.Float(string='Foreign Name Rotation (degrees)', default=0.0)
    
    code_x = fields.Float(string='Code X Position', default=40.0)
    code_y = fields.Float(string='Code Y Position', default=25.0)
    code_rotation = fields.Float(string='Code Rotation (degrees)', default=0.0)
    
    price_x = fields.Float(string='Price X Position', default=40.0)
    price_y = fields.Float(string='Price Y Position', default=35.0)
    price_rotation = fields.Float(string='Price Rotation (degrees)', default=0.0)
    
    barcode_x = fields.Float(string='Barcode X Position', default=5.0)
    barcode_y = fields.Float(string='Barcode Y Position', default=45.0)
    barcode_width = fields.Float(string='Barcode Width (mm)', default=60.0, help='Width of barcode')
    barcode_height = fields.Float(string='Barcode Height (mm)', default=12.0, help='Height of barcode')
    barcode_rotation = fields.Float(string='Barcode Rotation (degrees)', default=0.0, help='Rotation (e.g., 90 for vertical)')
    barcode_scale = fields.Float(string='Barcode Scale', default=1.0, help='Scale factor (0.5 = 50%, 2.0 = 200%)')
    
    qr_x = fields.Float(string='QR Code X Position', default=60.0)
    qr_y = fields.Float(string='QR Code Y Position', default=45.0)
    qr_size = fields.Float(string='QR Code Size (mm)', default=15.0)
    qr_rotation = fields.Float(string='QR Rotation (degrees)', default=0.0)
    
    logo_x = fields.Float(string='Logo X Position', default=5.0)
    logo_y = fields.Float(string='Logo Y Position', default=5.0)
    logo_width = fields.Float(string='Logo Width', default=20.0)
    logo_height = fields.Float(string='Logo Height', default=15.0)
    logo_rotation = fields.Float(string='Logo Rotation (degrees)', default=0.0)
    
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
    ], string='Name Alignment', default='center')
    
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
    
    # Auto Font Sizing Settings (Smart font adjustment based on text length)
    enable_auto_font_sizing = fields.Boolean(
        string='Enable Auto Font Sizing',
        default=True,
        help='Automatically adjust font size based on text length'
    )
    # Font multipliers for different text lengths
    font_multiplier_very_short = fields.Float(
        string='Very Short Text (< 10 chars)',
        default=1.8,
        help='Font size multiplier for very short text (less than 10 characters)'
    )
    font_multiplier_short = fields.Float(
        string='Short Text (10-20 chars)',
        default=1.4,
        help='Font size multiplier for short text (10-20 characters)'
    )
    font_multiplier_medium = fields.Float(
        string='Medium Text (21-35 chars)',
        default=1.0,
        help='Font size multiplier for medium text (21-35 characters)'
    )
    font_multiplier_long = fields.Float(
        string='Long Text (36-50 chars)',
        default=0.75,
        help='Font size multiplier for long text (36-50 characters)'
    )
    font_multiplier_very_long = fields.Float(
        string='Very Long Text (> 50 chars)',
        default=0.6,
        help='Font size multiplier for very long text (more than 50 characters)'
    )
    # Character count thresholds
    char_threshold_very_short = fields.Integer(
        string='Very Short Threshold',
        default=10,
        help='Character count threshold for very short text'
    )
    char_threshold_short = fields.Integer(
        string='Short Threshold',
        default=20,
        help='Character count threshold for short text'
    )
    char_threshold_medium = fields.Integer(
        string='Medium Threshold',
        default=35,
        help='Character count threshold for medium text'
    )
    char_threshold_long = fields.Integer(
        string='Long Threshold',
        default=50,
        help='Character count threshold for long text'
    )
    
    # Price settings
    show_currency_symbol = fields.Boolean(string='Show Currency Symbol', default=False)
    
    # ========================
    # SAP Integration Settings (Uses existing sap_integration module)
    # ========================
    sap_mode_enabled = fields.Boolean(
        string='Enable SAP Mode',
        default=False,
        help='Enable printing using synced SAP data (products and alternative barcodes). No direct SAP connection needed during printing.'
    )
    sap_backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend (للمزامنة فقط)',
        help='Optional: SAP backend for reference. Not used during printing - system uses synced data only.'
    )
    show_sap_uom = fields.Boolean(
        string='Show SAP Unit of Measure',
        default=False,
        help='Display the sub-unit of measure from SAP on the label.'
    )
    sap_uom_format = fields.Selection([
        ('full', 'Full Name'),
        ('code', 'Code Only'),
        ('abbr', 'Abbreviation')
    ], string='UoM Format', default='full', help='How to display the unit of measure.')
    
    # SAP Element Positions
    sap_name_x = fields.Float(string='SAP Name X Position', default=5.0)
    sap_name_y = fields.Float(string='SAP Name Y Position', default=5.0)
    sap_name_width = fields.Float(string='SAP Name Width (mm)', default=70.0)
    sap_name_height = fields.Float(string='SAP Name Height (mm)', default=10.0)
    sap_uom_x = fields.Float(string='SAP UoM X Position', default=5.0)
    sap_uom_y = fields.Float(string='SAP UoM Y Position', default=15.0)
    sap_uom_width = fields.Float(string='SAP UoM Width (mm)', default=70.0)
    sap_uom_height = fields.Float(string='SAP UoM Height (mm)', default=8.0)
    
    # SAP Fonts
    font_size_sap_name = fields.Integer(string='SAP Name Font Size', default=14)
    font_size_sap_uom = fields.Integer(string='SAP UoM Font Size', default=12)
    
    # SAP Text Alignment
    sap_name_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='SAP Name Alignment', default='right')
    sap_uom_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='SAP UoM Alignment', default='right')
    
    # SAP Font Weight
    sap_name_bold = fields.Boolean(string='SAP Name Bold', default=True)
    sap_uom_bold = fields.Boolean(string='SAP UoM Bold', default=False)
    
    # SAP Font Style
    sap_name_italic = fields.Boolean(string='SAP Name Italic', default=False)
    sap_uom_italic = fields.Boolean(string='SAP UoM Italic', default=False)

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
    
    def get_product_info_by_barcode(self, barcode):
        """
        Get product information from local database only
        Searches in local Odoo database for products
        Returns: dict with product_name, uom, and other info
        """
        self.ensure_one()
        
        try:
            # Clean barcode: remove leading/trailing slashes and spaces
            original_barcode = barcode
            barcode = str(barcode).strip().strip('/')
            
            _logger.info(f"Searching local products for barcode: {barcode} (original: {original_barcode})")
            
            # Search in local Odoo database only
            # 1. Check main barcode
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            alt_barcode = None
            
            # 2. If not found, check alternative barcodes
            if not product:
                alt_barcode = self.env['product.barcode.alternative'].search([
                    ('barcode', '=', barcode),
                    ('active', '=', True)
                ], limit=1)
                
                if alt_barcode:
                    product = alt_barcode.product_id
                    _logger.info(f"✓ Product found via alternative barcode: {product.default_code}")
            
            # 3. If product found
            if product:
                _logger.info(f"✓ Product found in local data: {product.default_code}")
                
                # Get UoM from alternative barcode if available
                uom_name = ''
                if alt_barcode and alt_barcode.uom_name:
                    uom_name = alt_barcode.uom_name
                
                return {
                    'success': True,
                    'product_id': product.id,
                    'product_name': product.name,
                    'display_name': product.name,
                    'uom': uom_name,
                    'barcode': barcode,  # Use cleaned barcode for QR code
                    'price': product.list_price,
                    'code': product.default_code,
                }
            
            # Not found
            _logger.warning(f"✗ Product not found for barcode: {barcode} (original: {original_barcode})")
            return {
                'success': False,
                'error': f'المنتج غير موجود.\n\nالباركود: {barcode}\n\nتأكد من أن المنتج موجود في النظام.'
            }
            
        except Exception as e:
            _logger.error(f"Error searching products for barcode {barcode}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'خطأ في البحث عن المنتج: {str(e)}'
            }
    
    # Keep old method name for backward compatibility
    def get_sap_product_info(self, barcode):
        """Legacy method name - redirects to get_product_info_by_barcode"""
        return self.get_product_info_by_barcode(barcode)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    foreign_name = fields.Char(string='Foreign Name', help='Product name in foreign language (e.g., English)')
    sap_product_name = fields.Char(string='SAP Product Name', readonly=True,
                                   help='Product name from SAP')
    sap_uom = fields.Char(string='SAP Unit of Measure', readonly=True,
                          help='Unit of measure from SAP')
    last_sap_sync = fields.Datetime(string='Last SAP Sync', readonly=True)

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
    
    @api.model
    def get_product_info_from_barcode(self, barcode):
        """
        Public method to get product info from local data by barcode.
        Can be called via RPC from the web interface.
        Works with any active template.
        """
        # Find any active template
        template = self.env['product.label.template'].search([
            ('active', '=', True),
        ], limit=1)
        
        if not template:
            return {
                'success': False,
                'error': 'لا يوجد قالب نشط. قم بإنشاء قالب للطباعة.'
            }
        
        # Use the template's method (searches local data only)
        return template.get_product_info_by_barcode(barcode)
    
    # Legacy method name for compatibility
    @api.model
    def get_sap_product_info_from_barcode(self, barcode):
        """Legacy method - redirects to get_product_info_from_barcode"""
        return self.get_product_info_from_barcode(barcode)

