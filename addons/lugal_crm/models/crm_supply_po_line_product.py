# -*- coding: utf-8 -*-
"""Optional link to stock.product for quantity checks."""

from odoo import fields, models


class CrmSupplyPoLineProduct(models.Model):
    _inherit = 'lugal.crm.supply.po.line'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        ondelete='set null',
        index=True,
        tracking=True,
        help='Optional. When set (or matched by item code), stock validation can use qty_available.',
    )
