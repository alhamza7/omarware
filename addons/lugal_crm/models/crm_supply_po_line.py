# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmSupplyPoLine(models.Model):
    """Supply PO line — product, UoM, qty, price, last purchase for reference."""
    _name = 'lugal.crm.supply.po.line'
    _description = 'CRM Supply PO Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, id asc'
    _rec_name = 'product_name'

    po_id = fields.Many2one(
        'lugal.crm.supply.po',
        string='Purchase Order / أمر الشراء',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    product_name = fields.Char(string='Product Name / اسم المنتج', tracking=True)
    item_code = fields.Char(string='Item Code / رمز الصنف', index=True, tracking=True)
    uom = fields.Char(string='UoM / وحدة القياس', tracking=True)
    quantity = fields.Float(string='Quantity / الكمية', digits=(16, 4), default=1.0, tracking=True)
    unit_price = fields.Float(string='Unit Price / سعر الوحدة', digits=(16, 4), tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency / العملة',
        ondelete='set null',
        tracking=True,
    )
    last_purchase_price = fields.Float(string='Last Purchase Price / آخر سعر شراء', digits=(16, 4), tracking=True)
    last_purchase_date = fields.Date(string='Last Purchase Date / تاريخ آخر شراء', tracking=True)
    total_price = fields.Float(
        string='Total Price / الإجمالي',
        compute='_compute_total_price',
        store=True,
        digits=(16, 2),
    )
    min_qty = fields.Float(string='Min Qty / الحد الأدنى', digits=(16, 4), tracking=True)
    max_qty = fields.Float(string='Max Qty / الحد الأقصى', digits=(16, 4), tracking=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Compute line total = quantity × unit_price."""
        for line in self:
            line.total_price = (line.quantity or 0.0) * (line.unit_price or 0.0)
