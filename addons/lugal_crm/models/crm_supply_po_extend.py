# -*- coding: utf-8 -*-

from odoo import models, fields, api

from .supply_workflow_config import supply_workflow_level_count


class CrmSupplyPoExtend(models.Model):
    """Supply chain links: item request → negotiation → order; payments; e-sign confirmation."""
    _name = 'lugal.crm.supply.po'
    _inherit = ['lugal.crm.supply.po', 'lugal.supply.attachment.sync.mixin']

    item_request_id = fields.Many2one(
        'lugal.supply.item.request',
        string='Linked Request',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    negotiation_id = fields.Many2one(
        'lugal.supply.negotiation',
        string='Linked Negotiation',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.partner',
        string='Agent',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    order_date = fields.Date(
        string='Order Date',
        default=fields.Date.context_today,
        tracking=True,
    )
    production_completion_date = fields.Date(
        string='Production Completion Date',
        tracking=True,
        oldname='expected_delivery_date',
    )
    payment_term = fields.Selection(
        [
            ('deposit', 'Deposit'),
            ('partial', 'Partial'),
            ('full', 'Full'),
        ],
        string='Payment Term',
        tracking=True,
    )
    shipping_method = fields.Selection(
        [
            ('sea', 'Sea'),
            ('air', 'Air'),
            ('land', 'Land'),
        ],
        string='Shipping Method',
        tracking=True,
    )
    notes = fields.Text(string='Notes', tracking=True)
    exchange_rate = fields.Float(
        string='Exchange Rate',
        digits=(16, 6),
        tracking=True,
        help='Optional FX rate vs company currency (for display / reporting).',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_crm_supply_po_order_attachment_rel',
        'po_id',
        'attachment_id',
        string='Attachments',
    )
    order_confirmed_user_id = fields.Many2one(
        'res.users',
        string='Order Confirmed By (e-sign)',
        readonly=True,
        tracking=True,
    )
    order_confirmed_date = fields.Datetime(string='Order Confirmation Date', readonly=True, tracking=True)

    payment_ids = fields.One2many(
        'lugal.supply.payment',
        'po_id',
        string='Payments',
    )
    amount_paid_total = fields.Monetary(
        string='Total Paid',
        compute='_compute_payment_summary',
        currency_field='currency_id',
        store=True,
    )
    balance_remaining = fields.Monetary(
        string='Remaining Balance',
        compute='_compute_payment_summary',
        currency_field='currency_id',
        store=True,
    )
    payment_state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        compute='_compute_payment_summary',
        store=True,
    )

    @api.depends(
        'payment_ids.amount',
        'total_amount',
        'currency_id',
    )
    def _compute_payment_summary(self):
        for po in self:
            paid = sum(po.payment_ids.mapped('amount'))
            po.amount_paid_total = paid
            total = po.total_amount or 0.0
            po.balance_remaining = max(total - paid, 0.0)
            if total <= 0.0 and paid <= 0.0:
                po.payment_state = 'pending'
            elif paid <= 0.00001:
                po.payment_state = 'pending'
            elif paid + 0.0001 < total:
                po.payment_state = 'partial'
            else:
                po.payment_state = 'paid'

    @api.model_create_multi
    def create(self, vals_list):
        company_currency = self.env.company.currency_id.id
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if not vals.get('currency_id'):
                vals['currency_id'] = company_currency
            name = vals.get('name')
            if not name or (isinstance(name, str) and not name.strip()):
                vals['name'] = seq.next_by_code('lugal.crm.supply.po') or '/'
        records = super().create(vals_list)
        records._sync_container_purchase_orders()
        records._lugal_sync_linked_attachments_res()
        records._bootstrap_supply_po_workflow_lines()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'container_id' in vals:
            self._sync_container_purchase_orders()
        return res

    def _bootstrap_supply_po_workflow_lines(self):
        """Create empty approval rows when multi-level count > 0 (see supply_workflow_config)."""
        n = supply_workflow_level_count(self.env)
        if n <= 0:
            return
        Line = self.env['lugal.supply.workflow.approval.line'].sudo()
        for po in self:
            if Line.search([('po_id', '=', po.id)], limit=1):
                continue
            for level in range(1, n + 1):
                Line.create({
                    'po_id': po.id,
                    'level': level,
                    'state': 'pending',
                })

    def _sync_container_purchase_orders(self):
        """When a PO is linked to a container, include it in container.purchase_order_ids."""
        for po in self:
            c = po.container_id
            if c and po.id not in c.purchase_order_ids.ids:
                c.write({'purchase_order_ids': [(4, po.id)]})

    def action_confirm_order_e_sign(self):
        """Record user confirmation for the order (basic e-sign)."""
        self.write({
            'order_confirmed_user_id': self.env.user.id,
            'order_confirmed_date': fields.Datetime.now(),
        })
