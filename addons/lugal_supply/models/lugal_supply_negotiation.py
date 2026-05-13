# -*- coding: utf-8 -*-
from odoo import models, fields


class LugalSupplyNegotiation(models.Model):
    """Price negotiation with a vendor — linked to supply vendor and optional product."""
    _name = 'lugal.supply.negotiation'
    _description = 'Lugal Supply Negotiation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.dynamic.extra.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'title'

    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    supply_vendor_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Supply Vendor / المورد',
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        'res.partner',
        string='Odoo Partner / شريك أودو',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product / المنتج',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_name = fields.Char(string='Product Name (free) / اسم المنتج', tracking=True)
    description = fields.Text(string='Description / الوصف', tracking=True)
    quantity = fields.Float(string='Quantity / الكمية', digits=(16, 4), tracking=True)
    uom = fields.Char(string='Unit of Measure / وحدة القياس', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency / العملة', ondelete='set null', tracking=True)
    expected_price = fields.Float(string='Expected Price / السعر المتوقع', digits=(16, 4), tracking=True)
    agreed_price = fields.Float(string='Agreed Price / السعر المتفق عليه', digits=(16, 4), tracking=True)
    status = fields.Selection([
        ('open', 'Open / مفتوح'),
        ('pending', 'Pending / معلق'),
        ('closed', 'Closed / مغلق'),
    ], string='Status / الحالة', default='open', required=True, index=True, tracking=True)
    due_date = fields.Date(string='Due Date / تاريخ الاستحقاق', tracking=True)
    notes = fields.Text(string='Notes / ملاحظات', tracking=True)
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
