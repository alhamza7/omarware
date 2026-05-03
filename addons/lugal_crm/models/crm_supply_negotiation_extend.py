# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LugalSupplyNegotiationExtend(models.Model):
    """Link supply POs to negotiations."""
    _inherit = 'lugal.supply.negotiation'

    supply_po_ids = fields.One2many(
        'lugal.crm.supply.po',
        'negotiation_id',
        string='Orders',
    )
    order_count = fields.Integer(compute='_compute_order_count')

    @api.depends('supply_po_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.supply_po_ids)
