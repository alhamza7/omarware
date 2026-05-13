# -*- coding: utf-8 -*-
"""Configurable multi-level approval rows linked to one supply document."""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LugalSupplyWorkflowApprovalLine(models.Model):
    _name = 'lugal.supply.workflow.approval.line'
    _description = 'Supply Workflow Approval Line'
    _inherit = ['mail.thread']
    _order = 'level asc, id asc'

    level = fields.Integer(string='Level', required=True, index=True, default=1)
    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('skipped', 'Skipped'),
        ],
        string='State',
        default='pending',
        required=True,
        tracking=True,
    )
    approver_user_id = fields.Many2one(
        'res.users',
        string='Approver',
        ondelete='set null',
        tracking=True,
    )
    decided_at = fields.Datetime(string='Decision date', readonly=True)
    notes = fields.Text(string='Notes')

    item_request_id = fields.Many2one(
        'lugal.supply.item.request',
        string='Item Request',
        ondelete='cascade',
        index=True,
    )
    negotiation_id = fields.Many2one(
        'lugal.supply.negotiation',
        string='Negotiation',
        ondelete='cascade',
        index=True,
    )
    po_id = fields.Many2one(
        'lugal.crm.supply.po',
        string='Purchase Order',
        ondelete='cascade',
        index=True,
    )

    @api.constrains('item_request_id', 'negotiation_id', 'po_id')
    def _check_single_parent_document(self):
        for rec in self:
            n = sum(1 for x in (rec.item_request_id, rec.negotiation_id, rec.po_id) if x)
            if n != 1:
                raise ValidationError(
                    _('Each approval line must be linked to exactly one parent document.')
                )

    def action_mark_approved(self):
        self.write({
            'state': 'approved',
            'decided_at': fields.Datetime.now(),
        })

    def action_mark_rejected(self):
        self.write({
            'state': 'rejected',
            'decided_at': fields.Datetime.now(),
        })
