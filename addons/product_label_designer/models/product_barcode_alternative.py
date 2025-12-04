# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductBarcodeAlternative(models.Model):
    """Alternative Barcodes for Products (Sub-unit barcodes from SAP)"""
    _name = 'product.barcode.alternative'
    _description = 'Product Alternative Barcodes'
    _order = 'product_id, sequence'
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        help="The product this barcode belongs to"
    )
    barcode = fields.Char(
        string='Barcode',
        required=True,
        index=True,
        help="Alternative barcode for this product"
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        help="Unit of measure for this barcode"
    )
    uom_name = fields.Char(
        string='UoM Name (SAP)',
        help="Unit of measure name from SAP"
    )
    sap_uom_entry = fields.Integer(
        string='SAP UoMEntry',
        help="SAP UoMEntry identifier"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order"
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True,
        help="Last synchronization date from SAP"
    )
    
    _sql_constraints = [
        ('barcode_product_uniq', 'UNIQUE(barcode, product_id)',
         'This barcode already exists for this product!'),
    ]
    
    @api.model
    def find_product_by_barcode(self, barcode):
        """Find product by alternative barcode"""
        alt_barcode = self.search([
            ('barcode', '=', barcode),
            ('active', '=', True)
        ], limit=1)
        
        if alt_barcode:
            return alt_barcode.product_id
        
        # Fallback: search in main product barcode
        product = self.env['product.product'].search([
            ('barcode', '=', barcode)
        ], limit=1)
        
        return product


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    alternative_barcode_ids = fields.One2many(
        'product.barcode.alternative',
        'product_id',
        string='Alt. Barcodes',
        help="Alternative barcodes for this product (e.g., sub-unit barcodes from SAP)"
    )
    alternative_barcode_count = fields.Integer(
        string='# Alt. Barcodes',
        compute='_compute_alternative_barcode_count',
        store=True
    )
    
    @api.depends('alternative_barcode_ids')
    def _compute_alternative_barcode_count(self):
        for product in self:
            product.alternative_barcode_count = len(product.alternative_barcode_ids)
    
    def action_view_alternative_barcodes(self):
        """Open alternative barcodes view"""
        self.ensure_one()
        return {
            'name': 'Alternative Barcodes',
            'type': 'ir.actions.act_window',
            'res_model': 'product.barcode.alternative',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }

