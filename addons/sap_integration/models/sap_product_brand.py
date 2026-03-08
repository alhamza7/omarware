# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductBrand(models.Model):
    """Product Brand — synchronized from SAP U_ST_MainBrand"""
    _name = 'product.brand'
    _description = 'Product Brand'
    _order = 'name'

    name = fields.Char(string='Brand Name', required=True, index=True)
    sap_name = fields.Char(
        string='SAP Name',
        help="Original brand name as received from SAP U_ST_MainBrand"
    )
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count'
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Brand name must be unique!')
    ]

    @api.depends('name')
    def _compute_product_count(self):
        """Count products linked to this brand"""
        for brand in self:
            brand.product_count = self.env['product.template'].search_count([
                ('sap_brand_id', '=', brand.id)
            ])

    @api.model
    def get_or_create_by_sap_name(self, sap_brand_name):
        """
        Find existing brand by SAP name or create it.
        Returns the brand record.
        """
        if not sap_brand_name or not sap_brand_name.strip():
            return False

        brand_name = sap_brand_name.strip()

        # Search by sap_name first (exact SAP source), then by name
        brand = self.search([('sap_name', '=', brand_name)], limit=1)
        if not brand:
            brand = self.search([('name', '=ilike', brand_name)], limit=1)

        if not brand:
            brand = self.create({
                'name': brand_name,
                'sap_name': brand_name,
            })
            _logger.info("Created new brand from SAP: %s", brand_name)

        return brand

    def action_view_products(self):
        """Open products list filtered by this brand"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Products — {self.name}',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('sap_brand_id', '=', self.id)],
            'context': {'default_sap_brand_id': self.id},
        }
