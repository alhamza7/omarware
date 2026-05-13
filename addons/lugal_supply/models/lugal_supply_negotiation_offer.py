# -*- coding: utf-8 -*-
"""Price offer history rows for a negotiation — one row per round of pricing."""
from odoo import models, fields


class LugalSupplyNegotiationOffer(models.Model):
    _name = 'lugal.supply.negotiation.offer'
    _description = 'Negotiation Price Offer'
    _order = 'sequence, offer_date desc, id desc'

    negotiation_id = fields.Many2one(
        'lugal.supply.negotiation',
        string='Negotiation / المفاوضة',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    price = fields.Float(string='Price / السعر', digits=(16, 4), default=0.0)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency / العملة',
        ondelete='set null',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Offered By / مُقدَّم من',
        ondelete='set null',
        default=lambda self: self.env.uid,
    )
    offer_date = fields.Datetime(
        string='Offer Date / تاريخ العرض',
        default=fields.Datetime.now,
        index=True,
    )
    notes = fields.Text(string='Notes / ملاحظات')
