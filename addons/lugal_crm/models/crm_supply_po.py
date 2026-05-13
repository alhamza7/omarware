# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmSupplyPo(models.Model):
    """Supply chain purchase order — vendor, container, division, lines."""
    _name = 'lugal.crm.supply.po'
    _description = 'CRM Supply Purchase Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.dynamic.extra.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Order ID / اسم أمر الشراء',
        required=True,
        index=True,
        tracking=True,
        help='Supply order reference; can be auto-generated on create.',
    )
    vendor_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Vendor / المورد',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    division = fields.Selection([
        ('europe', 'Europe / أوروبا'),
        ('china', 'China / الصين'),
    ], string='Division / القسم', index=True, tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency / العملة',
        ondelete='set null',
        tracking=True,
    )
    container_id = fields.Many2one(
        'lugal.supply.container',
        string='Container / الحاوية',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    status = fields.Selection([
        ('draft', 'Draft / مسودة'),
        ('confirmed', 'Confirmed / مؤكد'),
        ('cancelled', 'Cancelled / ملغي'),
    ], string='Status / الحالة', default='draft', required=True, index=True, tracking=True)
    line_ids = fields.One2many(
        'lugal.crm.supply.po.line',
        'po_id',
        string='Lines / السطور',
    )
    total_amount = fields.Float(
        string='Total Amount / المبلغ الإجمالي',
        compute='_compute_total_amount',
        store=True,
        digits=(16, 2),
    )
    is_suggested = fields.Boolean(string='Suggested PO / أمر مقترح', default=False, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.depends('line_ids.total_price')
    def _compute_total_amount(self):
        """Sum all line totals to get PO grand total."""
        for po in self:
            po.total_amount = sum(line.total_price for line in po.line_ids)

    def init(self):
        """Legacy status cleanup; ensure columns for extended PO fields exist (DB sync safety)."""
        self.env.cr.execute(
            """
            UPDATE lugal_crm_supply_po
            SET status = 'confirmed'
            WHERE status IN ('shipped', 'received');
            """
        )
