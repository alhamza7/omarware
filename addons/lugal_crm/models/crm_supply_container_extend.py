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
