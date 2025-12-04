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
    
    # ========================
    # SAP Integration Settings (Uses existing sap_integration module)
    # ========================
    sap_mode_enabled = fields.Boolean(
        string='Enable SAP Mode',
        default=False,
        help='Enable integration with SAP for product data. Uses existing SAP Integration module.'
    )
    sap_backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        help='Select the SAP backend connection to use for fetching product data.'
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
    
    def get_sap_product_info(self, barcode):
        """
        Get product information from SAP by barcode using existing sap_integration module
        Returns: dict with product_name, uom, and other info
        """
        self.ensure_one()
        
        if not self.sap_mode_enabled:
            return {
                'success': False,
                'error': 'SAP mode not enabled for this template'
            }
        
        if not self.sap_backend_id:
            return {
                'success': False,
                'error': 'No SAP backend configured for this template'
            }
        
        try:
            # Get SAP connection using existing sap_integration module
            backend = self.sap_backend_id
            
            if not backend.active:
                return {
                    'success': False,
                    'error': f'SAP backend "{backend.name}" is not active'
                }
            
            connection = backend.get_connection()
            
            _logger.info(f"Searching SAP for barcode: {barcode}")
            
            # IMPORTANT: In SAP B1 10, ItemBarCodeCollection is NOT a navigation property
            # and cannot be searched/expanded directly. Sub-unit barcodes are NOT searchable via OData.
            # We can ONLY search by the main BarCode field.
            
            # First, try to find in local Odoo cache (faster)
            # Check main barcode
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            alt_barcode = None
            
            # If not found, check alternative barcodes
            if not product:
                alt_barcode = self.env['product.barcode.alternative'].search([
                    ('barcode', '=', barcode),
                    ('active', '=', True)
                ], limit=1)
                
                if alt_barcode:
                    product = alt_barcode.product_id
                    _logger.info(f"Product found via alternative barcode: {product.default_code}")
            
            if product and product.last_sap_sync and \
               (fields.Datetime.now() - product.last_sap_sync).total_seconds() < 3600:
                # Found in cache and synced within last hour
                _logger.info(f"Product found in cache: {product.default_code}")
                
                # Get UoM from alternative barcode if available
                uom_name = ''
                if alt_barcode:
                    uom_name = alt_barcode.uom_name or product.sap_uom or ''
                else:
                    uom_name = product.sap_uom or ''
                
                return {
                    'success': True,
                    'product_id': product.id,
                    'product_name': product.name,
                    'sap_product_name': product.sap_product_name or product.name,
                    'sap_uom': uom_name,
                    'barcode': barcode,
                    'price': product.list_price,
                    'code': product.default_code,
                    'sap_item_code': product.default_code,
                }
            
            # Not in cache or cache expired, search SAP by main BarCode field
            _logger.info(f"Searching SAP Items by main BarCode field...")
            filter_query = f"BarCode eq '{barcode}'"
            result = connection.get('Items', params={'$filter': filter_query, '$top': 1})
            
            if not result or not result.get('value') or len(result['value']) == 0:
                # Try by ItemCode as fallback
                _logger.info(f"Not found by BarCode, trying ItemCode...")
                filter_query = f"ItemCode eq '{barcode}'"
                result = connection.get('Items', params={'$filter': filter_query, '$top': 1})
                
                if not result or not result.get('value') or len(result['value']) == 0:
                    _logger.warning(f"Product not found in SAP for barcode: {barcode}")
                    return {
                        'success': False,
                        'error': f'Product with barcode {barcode} not found in SAP.\n\n'
                                f'Note: Sub-unit barcodes cannot be searched directly in this SAP version.\n'
                                f'Please use the main product barcode or ItemCode.'
                    }
            
            sap_item = result['value'][0]
            item_code = sap_item.get('ItemCode', '')
            item_name = sap_item.get('ItemName', '')
            uom_name = sap_item.get('SalesUnit', '')
            
            _logger.info(f"SAP product found: {item_code} - {item_name}, UoM: {uom_name}")
            
            # Try to find or create product in Odoo
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            
            if not product:
                # Try to search by ItemCode as default_code
                product = self.env['product.product'].search([('default_code', '=', item_code)], limit=1)
            
            if not product:
                # Create new product in Odoo
                _logger.info(f"Creating new product in Odoo for SAP item: {item_code}")
                product = self.env['product.product'].create({
                    'name': item_name,
                    'default_code': item_code,
                    'barcode': barcode,
                    'list_price': sap_item.get('Price', 0.0),
                    'standard_price': sap_item.get('PurchasePrice', 0.0),
                    'type': 'product',
                    'sap_product_name': item_name,
                    'sap_uom': uom_name,
                    'last_sap_sync': fields.Datetime.now(),
                })
            else:
                # Update existing product with SAP data
                product.write({
                    'sap_product_name': item_name,
                    'sap_uom': uom_name,
                    'last_sap_sync': fields.Datetime.now(),
                })
            
            return {
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'sap_product_name': item_name,
                'sap_uom': uom_name,
                'barcode': barcode,
                'price': product.list_price,
                'code': product.default_code,
                'sap_item_code': item_code,
            }
            
        except Exception as e:
            _logger.error(f"Error getting SAP product info for barcode {barcode}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error connecting to SAP: {str(e)}'
            }


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
    def get_sap_product_info_from_barcode(self, barcode):
        """
        Public method to get product info from SAP by barcode.
        Can be called via RPC from the web interface.
        Uses the first active SAP-enabled label template.
        """
        # Find a SAP-enabled template
        template = self.env['product.label.template'].search([
            ('sap_mode_enabled', '=', True),
            ('sap_backend_id', '!=', False)
        ], limit=1)
        
        if not template:
            return {
                'success': False,
                'error': 'No SAP-enabled label template found. Please configure SAP integration in a label template.'
            }
        
        # Use the template's SAP connection method
        return template.get_sap_product_info(barcode)

