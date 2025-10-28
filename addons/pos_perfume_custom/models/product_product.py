# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    foreign_name = fields.Char(
        string='Foreign Name',
        help='اسم المنتج الأجنبي'
    )
    
    price_iqd = fields.Monetary(
        string='Price (IQD)',
        compute='_compute_price_iqd',
        currency_field='currency_iqd_id',
        store=False
    )
    
    currency_iqd_id = fields.Many2one(
        'res.currency',
        string='IQD Currency',
        default=lambda self: self.env.ref('base.IQD', raise_if_not_found=False),
        store=False
    )
    
    @api.depends('list_price')
    def _compute_price_iqd(self):
        """Convert USD price to IQD using fixed exchange rate"""
        exchange_rate = 1300.0  # 1 USD = 1,300 IQD
        for product in self:
            product.price_iqd = product.list_price * exchange_rate


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Inherit from template
    foreign_name = fields.Char(related='product_tmpl_id.foreign_name', string='Foreign Name', readonly=False, store=True, copy=False)
    price_iqd = fields.Monetary(related='product_tmpl_id.price_iqd', string='Price (IQD)')

