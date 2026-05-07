# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LugalSupplyItemRequest(models.Model):
    """Internal procurement item request (Notion: request order)............................................................."""
    _name = 'lugal.supply.item.request'
    _description = 'Supply Item Request'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'lugal.supply.dynamic.extra.mixin',
        'lugal.supply.attachment.sync.mixin',
    ]
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Request ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True,
    )
    requested_by_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    item_name = fields.Char(string='Item Name', required=True, tracking=True)
    description = fields.Text(string='Item Description', tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0, digits=(16, 4), tracking=True)
    uom = fields.Char(
        string='Unit',
        help='Unit of measure label: pcs, carton, etc.',
        tracking=True,
    )
    capacity = fields.Char(
        string='Capacity',
        help='Bottle or pack capacity (e.g. 50ml, 100ml).',
        tracking=True,
    )
    packing_pcs_per_carton = fields.Float(
        string='Packing (pcs per carton)',
        digits=(16, 4),
        tracking=True,
        help='Number of pieces per carton when applicable.',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_item_request_attachment_rel',
        'request_id',
        'attachment_id',
        string='Reference Image / Files',
    )
    priority = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string='Priority',
        default='medium',
        tracking=True,
    )
    notes = fields.Text(string='Notes / Comments', tracking=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        tracking=True,
    )
    requester_confirm_user_id = fields.Many2one(
        'res.users',
        string='Requester Confirmation (e-sign)',
        readonly=True,
        help='User who confirmed submission of the request.',
    )
    requester_confirm_date = fields.Datetime(
        string='Requester Confirmation Date',
        readonly=True,
    )
    active = fields.Boolean(default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    negotiation_ids = fields.One2many(
        'lugal.supply.negotiation',
        'item_request_id',
        string='Negotiations',
    )
    negotiation_count = fields.Integer(compute='_compute_negotiation_count')

    @api.depends('negotiation_ids')
    def _compute_negotiation_count(self):
        for rec in self:
            rec.negotiation_count = len(rec.negotiation_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lugal.supply.item.request'
                ) or _('New')
        records = super().create(vals_list)
        records._lugal_sync_linked_attachments_res()
        return records

    def action_requester_confirm(self):
        """Basic e-sign: requester confirms their submission."""
        self.ensure_one()
        self.write({
            'requester_confirm_user_id': self.env.user.id,
            'requester_confirm_date': fields.Datetime.now(),
        })

    def action_start_progress(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft requests can be set to in progress.'))
            rec.write({'state': 'in_progress'})

    def action_mark_completed(self):
        for rec in self:
            if rec.state == 'completed':
                continue
            rec.write({'state': 'completed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def init(self):
        """Map legacy approval states to the new lifecycle (upgrade safety)."""
        self._cr.execute(
            """
            UPDATE lugal_supply_item_request
            SET state = 'completed'
            WHERE state = 'approved';
            UPDATE lugal_supply_item_request
            SET state = 'draft'
            WHERE state = 'rejected';
            """
        )
