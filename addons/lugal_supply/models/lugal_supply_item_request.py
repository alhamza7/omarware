# -*- coding: utf-8 -*-
from odoo import models, fields


class LugalSupplyItemRequest(models.Model):
    """Request from a branch/agent to replenish inventory of a specific product."""
    _name = 'lugal.supply.item.request'
    _description = 'Lugal Supply Item Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'product_name'

    product_id = fields.Many2one(
        'product.product',
        string='Product / المنتج',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_name = fields.Char(string='Product Name / اسم المنتج', tracking=True)
    item_code = fields.Char(string='Item Code / رمز الصنف', index=True, tracking=True)
    quantity = fields.Float(string='Quantity / الكمية', digits=(16, 4), default=1.0, tracking=True)
    uom = fields.Char(string='Unit of Measure / وحدة القياس', tracking=True)
    branch_id = fields.Integer(string='Branch ID / معرّف الفرع', index=True, tracking=True)
    requested_by_id = fields.Many2one(
        'res.users',
        string='Requested By / طلب بواسطة',
        ondelete='set null',
        default=lambda self: self.env.uid,
        index=True,
        tracking=True,
    )
    status = fields.Selection([
        ('pending', 'Pending / معلق'),
        ('approved', 'Approved / موافق عليه'),
        ('rejected', 'Rejected / مرفوض'),
        ('fulfilled', 'Fulfilled / منجز'),
    ], string='Status / الحالة', default='pending', required=True, index=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low / منخفض'),
        ('normal', 'Normal / عادي'),
        ('high', 'High / عالي'),
        ('urgent', 'Urgent / عاجل'),
    ], string='Priority / الأولوية', default='normal', tracking=True)
    note = fields.Text(string='Notes / ملاحظات', tracking=True)
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By / راجعه',
        ondelete='set null',
        tracking=True,
    )
    reviewed_at = fields.Datetime(string='Reviewed At / وقت المراجعة', tracking=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
