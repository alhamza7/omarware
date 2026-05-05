# -*- coding: utf-8 -*-

from odoo import models, fields, api

from .supply_workflow_config import supply_workflow_level_count


class LugalSupplyNegotiationExtend(models.Model):
    """Link supply POs to negotiations."""
    _inherit = 'lugal.supply.negotiation'

    supply_po_ids = fields.One2many(
        'lugal.crm.supply.po',
        'negotiation_id',
        string='Orders',
    )
    order_count = fields.Integer(compute='_compute_order_count')
    expected_lead_time_days = fields.Integer(
        string='Expected lead time (days)',
        tracking=True,
        help='Indicative lead time for this negotiation (headline).',
    )
    quoted_delivery_date = fields.Date(
        string='Quoted delivery date',
        tracking=True,
    )
    supply_workflow_approval_line_ids = fields.One2many(
        'lugal.supply.workflow.approval.line',
        'negotiation_id',
        string='Negotiation approvals',
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._supply_bootstrap_negotiation_approval_lines()
        return records

    @api.depends('supply_po_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.supply_po_ids)

    def _supply_bootstrap_negotiation_approval_lines(self):
        n = supply_workflow_level_count(self.env)
        if n <= 0:
            return
        Line = self.env['lugal.supply.workflow.approval.line'].sudo()
        for neg in self:
            if Line.search([('negotiation_id', '=', neg.id)], limit=1):
                continue
            for level in range(1, n + 1):
                Line.create({
                    'negotiation_id': neg.id,
                    'level': level,
                    'state': 'pending',
                })
