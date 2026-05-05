# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LugalSupplyContainerExtend(models.Model):
    """Multiple supply POs per container; relation lives in lugal_crm (PO model)."""
    _inherit = 'lugal.supply.container'

    purchase_order_ids = fields.Many2many(
        'lugal.crm.supply.po',
        'lugal_supply_container_crm_po_rel',
        'container_id',
        'po_id',
        string='Linked Orders',
    )
    planned_gate_in_date = fields.Date(
        string='Planned gate-in date',
        tracking=True,
        help='Optional milestone for port / yard gate-in (complements ETA).',
    )
    actual_gate_in_at = fields.Datetime(
        string='Actual gate-in',
        tracking=True,
    )
