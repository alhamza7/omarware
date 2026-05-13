# -*- coding: utf-8 -*-
"""Lead-time style timestamps on payments (do not replace payment_date)."""

from odoo import fields, models


class LugalSupplyPaymentTrace(models.Model):
    _inherit = 'lugal.supply.payment'

    funds_cleared_at = fields.Datetime(
        string='Funds cleared at',
        tracking=True,
        help='When payment was confirmed cleared by finance (optional).',
    )
    value_date = fields.Date(
        string='Value date',
        tracking=True,
        help='Bank value date if different from payment_date.',
    )
