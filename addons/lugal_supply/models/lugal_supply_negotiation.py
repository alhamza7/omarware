# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LugalSupplyNegotiation(models.Model):
    """Supplier/agent price and terms discussion linked to an item request."""
    _name = 'lugal.supply.negotiation'
    _description = 'Supply Negotiation'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'lugal.supply.dynamic.extra.mixin',
        'lugal.supply.attachment.sync.mixin',
    ]
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Negotiation ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True,
    )
    item_request_id = fields.Many2one(
        'lugal.supply.item.request',
        string='Linked Item Request',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Supplier',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.partner',
        string='Agent',
        ondelete='set null',
        index=True,
        tracking=True,
        domain=[('is_company', '=', True)],
    )
    item_name = fields.Char(string='Item Name', tracking=True)
    quantity = fields.Float(string='Quantity', digits=(16, 4), tracking=True)
    capacity = fields.Char(
        string='Capacity',
        help='Bottle or pack capacity (e.g. 50ml, 100ml).',
        tracking=True,
    )
    packing_pcs_per_carton = fields.Float(
        string='Packing (pcs per carton)',
        digits=(16, 4),
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_negotiation_attachment_rel',
        'negotiation_id',
        'attachment_id',
        string='Images / Files',
    )
    offered_price = fields.Float(
        string='Current Offered Price',
        digits=(16, 4),
        compute='_compute_offer_prices',
        store=True,
        help='Latest price from offer history.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        tracking=True,
    )
    terms = fields.Text(
        string='Terms',
        help='MOQ, packaging, lead time, etc.',
        tracking=True,
    )
    offer_ids = fields.One2many(
        'lugal.supply.negotiation.offer',
        'negotiation_id',
        string='Offer History',
    )
    final_agreed_price = fields.Float(string='Final Agreed Price', digits=(16, 4), tracking=True)
    final_currency_id = fields.Many2one(
        'res.currency',
        string='Final Currency',
        ondelete='set null',
        tracking=True,
    )
    notes = fields.Text(string='Notes / Discussion', tracking=True)
    state = fields.Selection(
        [
            ('ongoing', 'Ongoing'),
            ('finalized', 'Finalized'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='ongoing',
        required=True,
        tracking=True,
        index=True,
    )
    finalized_by_id = fields.Many2one(
        'res.users',
        string='Approval By',
        readonly=True,
        tracking=True,
    )
    finalized_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
        tracking=True,
    )
    e_sign_user_id = fields.Many2one(
        'res.users',
        string='E-sign By',
        readonly=True,
        tracking=True,
    )
    e_sign_date = fields.Datetime(
        string='E-sign Date',
        readonly=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.depends('offer_ids.price', 'offer_ids.offer_date')
    def _compute_offer_prices(self):
        for neg in self:
            last = neg.offer_ids.sorted(lambda o: (o.offer_date, o.id), reverse=True)[:1]
            neg.offered_price = last.price if last else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lugal.supply.negotiation'
                ) or _('New')
        records = super().create(vals_list)
        records._lugal_sync_linked_attachments_res()
        return records

    def action_e_sign_approve(self):
        """Record negotiation e-sign; does not change state (use action_finalize to close)."""
        for rec in self:
            if rec.state != 'ongoing':
                raise UserError(_('E-sign approval is only allowed for ongoing negotiations.'))
            rec.write({
                'e_sign_user_id': self.env.user.id,
                'e_sign_date': fields.Datetime.now(),
            })

    def action_finalize(self):
        for rec in self:
            if rec.state != 'ongoing':
                raise UserError(_('Only ongoing negotiations can be finalized.'))
            rec.write({
                'state': 'finalized',
                'finalized_by_id': self.env.user.id,
                'finalized_date': fields.Datetime.now(),
            })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_ongoing(self):
        self.write({
            'state': 'ongoing',
            'finalized_by_id': False,
            'finalized_date': False,
        })


class LugalSupplyNegotiationOffer(models.Model):
    """Single offer line in negotiation history."""
    _name = 'lugal.supply.negotiation.offer'
    _description = 'Supply Negotiation Offer'
    _order = 'offer_date desc, id desc'

    negotiation_id = fields.Many2one(
        'lugal.supply.negotiation',
        string='Negotiation',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(default=10)
    price = fields.Float(string='Offered Price', required=True, digits=(16, 4))
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        ondelete='set null',
    )
    notes = fields.Text(string='Notes')
    user_id = fields.Many2one(
        'res.users',
        string='Recorded By',
        default=lambda self: self.env.user,
    )
    offer_date = fields.Datetime(
        string='Offer Date',
        default=fields.Datetime.now,
        required=True,
    )
