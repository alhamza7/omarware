# -*- coding: utf-8 -*-

from odoo import fields, models


class LugalSupplyContainerPenalty(models.Model):
    """Penalties / storage charges linked to a supply container (CRM supply UI)."""
    _name = 'lugal.supply.container.penalty'
    _description = 'Supply Container Penalty'
    _order = 'penalty_date desc, id desc'

    container_id = fields.Many2one(
        'lugal.supply.container',
        string='Container',
        required=True,
        ondelete='cascade',
        index=True,
    )
    penalty_type = fields.Selection(
        [
            ('storage', 'Storage'),
            ('damage', 'Damage'),
            ('late', 'Late'),
            ('customs', 'Customs'),
            ('demurrage', 'Demurrage'),
            ('other', 'Other'),
        ],
        string='Type',
        required=True,
        default='other',
    )
    amount = fields.Float(string='Amount', required=True, default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency', ondelete='set null')
    reason = fields.Text(string='Reason')
    penalty_date = fields.Date(string='Penalty Date')
