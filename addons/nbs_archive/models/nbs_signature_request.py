# -*- coding: utf-8 -*-

import secrets
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class NBSSignatureRequest(models.Model):
    _name = 'nbs.signature.request'
    _description = 'Signature Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        required=True,
        ondelete='restrict',
        index=True,
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        index=True,
    )
    signer_id = fields.Many2one(
        'res.users',
        string='Signer (Manager/Supervisor)',
        required=True,
        index=True,
    )
    request_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    message = fields.Text(string='Message/Notes')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved (Await Signed Upload)'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='pending', required=True, tracking=True, index=True)

    approver_id = fields.Many2one('res.users', string='Approved/Rejected By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)

    # One-time token to allow uploading signed version
    sign_token = fields.Char(string='Sign Token', readonly=True, copy=False)
    token_expiry = fields.Datetime(string='Token Expiry', readonly=True)
    token_used = fields.Boolean(default=False, readonly=True)

    signed_version_id = fields.Many2one('nbs.document.version', string='Signed Version', readonly=True)
    signed_date = fields.Datetime(string='Signed Date', readonly=True)

    department_id = fields.Many2one(related='document_id.department_id', store=True, index=True)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    can_approve = fields.Boolean(compute='_compute_permissions', store=False)
    can_cancel = fields.Boolean(compute='_compute_permissions', store=False)

    @api.depends('document_id', 'requester_id', 'request_date')
    def _compute_display_name(self):
        for r in self:
            if r.document_id and r.requester_id:
                r.display_name = f'Signature Request: {r.document_id.name} by {r.requester_id.name}'
            else:
                r.display_name = 'Signature Request'

    @api.depends_context('uid')
    def _compute_permissions(self):
        for r in self:
            user = self.env.user
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            is_signer = user == r.signer_id
            is_requester = user == r.requester_id
            r.can_approve = (is_admin or is_signer) and r.state == 'pending'
            r.can_cancel = is_requester and r.state in ('pending', 'approved')

    def _generate_sign_token(self):
        self.ensure_one()
        if self.state != 'pending':
            raise ValidationError(_('Only pending requests can be approved'))
        token = secrets.token_urlsafe(32)
        expiry = fields.Datetime.now() + timedelta(hours=48)
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'sign_token': token,
            'token_expiry': expiry,
        })
        return token

    def action_approve(self):
        self.ensure_one()
        if not self.can_approve:
            raise AccessError(_('You do not have permission to approve this signature request'))
        token = self._generate_sign_token()

        # notify requester
        self.env['nbs.notification'].sudo().create({
            'user_id': self.requester_id.id,
            'title': _('Signature Request Approved'),
            'message': _('Your signature request for "%s" was approved. Please upload the signed file within 48 hours.') % self.document_id.name,
            'notification_type': 'signature_approved',
            'document_id': self.document_id.id,
        })
        return token

    def action_reject(self, reason=None):
        self.ensure_one()
        if not self.can_approve:
            raise AccessError(_('You do not have permission to reject this signature request'))
        self.write({
            'state': 'rejected',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'rejection_reason': reason or '',
        })
        self.env['nbs.notification'].sudo().create({
            'user_id': self.requester_id.id,
            'title': _('Signature Request Rejected'),
            'message': _('Your signature request for "%s" was rejected.') % self.document_id.name,
            'notification_type': 'signature_rejected',
            'document_id': self.document_id.id,
        })
        return True

    def action_cancel(self):
        self.ensure_one()
        if not self.can_cancel:
            raise AccessError(_('You do not have permission to cancel this signature request'))
        self.write({'state': 'cancelled'})
        return True

    def mark_signed(self, version):
        """Called after signed version is uploaded."""
        self.ensure_one()
        self.write({
            'state': 'signed',
            'token_used': True,
            'signed_version_id': version.id,
            'signed_date': fields.Datetime.now(),
        })
        return True




















