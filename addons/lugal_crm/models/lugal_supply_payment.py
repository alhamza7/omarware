# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LugalSupplyPayment(models.Model):
    """Payment lines against a supply PO (deposit / installment / final / other)."""
    _name = 'lugal.supply.payment'
    _description = 'Supply Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.attachment.sync.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Payment ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    po_id = fields.Many2one(
        'lugal.crm.supply.po',
        string='Linked Order',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    paid_to = fields.Selection(
        [
            ('supplier', 'Supplier'),
            ('agent', 'Agent'),
        ],
        string='Paid To',
        tracking=True,
    )
    payee_partner_id = fields.Many2one(
        'res.partner',
        string='Payee',
        help='Supplier or agent receiving the payment.',
        ondelete='set null',
        tracking=True,
    )
    payment_type = fields.Selection(
        [
            ('deposit', 'Deposit'),
            ('installment', 'Installment'),
            ('final', 'Final'),
            ('other', 'Other'),
        ],
        string='Payment Type',
        required=True,
        default='installment',
        tracking=True,
    )
    amount = fields.Monetary(string='Amount', required=True, tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    payment_date = fields.Date(string='Payment Date', tracking=True)
    payment_method = fields.Char(
        string='Payment Method',
        tracking=True,
        help='Bank transfer, LC, cash, etc.',
    )
    notes = fields.Text(string='Notes', tracking=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_payment_receipt_attachment_rel',
        'payment_id',
        'attachment_id',
        string='Attachments',
    )
    remaining_balance = fields.Monetary(
        string='Remaining Balance',
        compute='_compute_payment_position',
        currency_field='currency_id',
        store=True,
        help='Order balance remaining after this payment (same currency as payment).',
    )
    payment_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        compute='_compute_payment_position',
        store=True,
    )
    active = fields.Boolean(default=True)

    @api.depends(
        'amount',
        'payment_date',
        'po_id',
        'po_id.total_amount',
        'po_id.payment_ids',
        'po_id.payment_ids.amount',
        'po_id.payment_ids.payment_date',
    )
    def _compute_payment_position(self):
        for pay in self:
            po = pay.po_id
            if not po:
                pay.remaining_balance = 0.0
                pay.payment_status = 'pending'
                continue
            total = po.total_amount or 0.0
            ordered = po.payment_ids.sorted(
                lambda p: (p.payment_date or fields.Date.today(), p.id or 0)
            )
            cumul = 0.0
            for p in ordered:
                cumul += p.amount or 0.0
                if p == pay:
                    remaining = max(total - cumul, 0.0)
                    if total <= 0 and cumul <= 0:
                        pay.payment_status = 'pending'
                    elif cumul + 0.0001 >= total and total > 0:
                        pay.payment_status = 'paid'
                    elif cumul > 0.0001:
                        pay.payment_status = 'partial'
                    else:
                        pay.payment_status = 'pending'
                    pay.remaining_balance = remaining
                    break
            else:
                pay.remaining_balance = max(total, 0.0)
                pay.payment_status = 'pending'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lugal.supply.payment'
                ) or _('New')
        records = super().create(vals_list)
        records._lugal_sync_linked_attachments_res()
        return records
