# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LugalSupplyItemRequestExtend(models.Model):
    """Link supply POs to item requests (defined in lugal_crm where PO model lives)."""
    _inherit = 'lugal.supply.item.request'

    supply_po_ids = fields.One2many(
        'lugal.crm.supply.po',
        'item_request_id',
        string='Supply Orders',
    )
    order_count = fields.Integer(compute='_compute_order_count')

    @api.depends('supply_po_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.supply_po_ids)
