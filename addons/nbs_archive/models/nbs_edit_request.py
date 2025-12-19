# -*- coding: utf-8 -*-

import secrets
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class NBSEditRequest(models.Model):
    _name = 'nbs.edit.request'
    _description = 'Edit Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        required=True,
        ondelete='restrict',
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    document_name = fields.Char(
        related='document_id.name',
        string='Document Name',
        store=True
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        index=True
    )
    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    reason = fields.Text(
        string='Reason',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('expired', 'Expired')
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    approver_id = fields.Many2one(
        'res.users',
        string='Approved/Rejected By',
        readonly=True,
        tracking=True
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
        tracking=True
    )
    approval_notes = fields.Text(
        string='Approval Notes',
        readonly=True,
        tracking=True
    )
    
    unlock_token = fields.Char(
        string='Unlock Token',
        readonly=True,
        copy=False,
        help='One-time token for uploading new version'
    )
    token_expiry = fields.Datetime(
        string='Token Expiry',
        readonly=True,
        help='Token expires after 24 hours'
    )
    token_used = fields.Boolean(
        string='Token Used',
        default=False,
        readonly=True,
        help='Whether the unlock token has been used'
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True
    )
    response_date = fields.Datetime(
        string='Response Date',
        readonly=True
    )
    
    # Related fields
    department_id = fields.Many2one(
        related='document_id.department_id',
        string='Department',
        store=True,
        index=True
    )
    
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    can_approve = fields.Boolean(
        compute='_compute_permissions',
        string='Can Approve'
    )
    can_cancel = fields.Boolean(
        compute='_compute_permissions',
        string='Can Cancel'
    )
    
    @api.depends('document_id', 'requester_id', 'request_date')
    def _compute_display_name(self):
        for request in self:
            if request.document_id and request.requester_id:
                request.display_name = f'Edit Request: {request.document_id.name} by {request.requester_id.name}'
            else:
                request.display_name = 'Edit Request'
    
    @api.depends_context('uid')
    def _compute_permissions(self):
        for request in self:
            user = self.env.user
            is_manager = user in request.department_id.manager_ids
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            is_requester = user == request.requester_id
            
            request.can_approve = (is_manager or is_admin) and request.state == 'pending'
            request.can_cancel = is_requester and request.state == 'pending'
    
    @api.model
    def create(self, vals):
        request = super().create(vals)
        
        # Auto-submit if not draft
        if request.state == 'draft':
            request.action_submit()
        
        return request
    
    def action_submit(self):
        """Submit edit request for approval"""
        for request in self:
            if request.state != 'draft':
                continue
            
            request.write({'state': 'pending'})
            
            # Notify department managers
            managers = request.department_id.manager_ids
            for manager in managers:
                self.env['nbs.notification'].sudo().create({
                    'user_id': manager.id,
                    'title': _('Edit Request Pending'),
                    'message': _('%s requested to edit document: %s') % (
                        request.requester_id.name,
                        request.document_id.name
                    ),
                    'notification_type': 'edit_request',
                    'document_id': request.document_id.id,
                    'edit_request_id': request.id,
                })
            
            # Log action
            self.env['nbs.audit.log'].sudo().create({
                'user_id': request.requester_id.id,
                'action': 'edit_request',
                'document_id': request.document_id.id,
                'department_id': request.department_id.id,
                'details': request.reason
            })
    
    def action_approve(self):
        """Approve edit request"""
        self.ensure_one()
        
        if not self.can_approve:
            raise AccessError(_('You do not have permission to approve this request'))
        
        if self.state != 'pending':
            raise ValidationError(_('Only pending requests can be approved'))
        
        # Generate unlock token
        token = secrets.token_urlsafe(32)
        expiry = fields.Datetime.now() + timedelta(hours=24)
        
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'unlock_token': token,
            'token_expiry': expiry
        })
        
        # Unlock document
        self.document_id.write({
            'unlock_token': token,
            'unlock_expiry': expiry,
            'is_locked': False
        })
        
        # Notify requester
        self.env['nbs.notification'].sudo().create({
            'user_id': self.requester_id.id,
            'title': _('Edit Request Approved'),
            'message': _('Your edit request for "%s" has been approved. You have 24 hours to upload a new version.') % self.document_id.name,
            'notification_type': 'approval',
            'document_id': self.document_id.id,
            'edit_request_id': self.id,
        })
        
        # Log approval
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'approval',
            'document_id': self.document_id.id,
            'department_id': self.department_id.id,
        })
        
        return True
    
    def action_reject(self):
        """Reject edit request"""
        self.ensure_one()
        
        if not self.can_approve:
            raise AccessError(_('You do not have permission to reject this request'))
        
        if self.state != 'pending':
            raise ValidationError(_('Only pending requests can be rejected'))
        
        self.write({
            'state': 'rejected',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        
        # Notify requester
        self.env['nbs.notification'].sudo().create({
            'user_id': self.requester_id.id,
            'title': _('Edit Request Rejected'),
            'message': _('Your edit request for "%s" has been rejected.') % self.document_id.name,
            'notification_type': 'rejection',
            'document_id': self.document_id.id,
            'edit_request_id': self.id,
        })
        
        # Log rejection
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'rejection',
            'document_id': self.document_id.id,
            'department_id': self.department_id.id,
        })
        
        return True
    
    def action_cancel(self):
        """Cancel edit request"""
        self.ensure_one()
        
        if not self.can_cancel:
            raise AccessError(_('You can only cancel your own pending requests'))
        
        self.write({'state': 'expired'})
        return True
    
    def mark_completed(self):
        """Mark as completed after version upload"""
        self.ensure_one()
        self.write({'state': 'completed'})
        
        # Re-lock document
        self.document_id.write({
            'unlock_token': False,
            'unlock_expiry': False,
            'is_locked': True
        })
    
    def _generate_unlock_token(self):
        """Generate one-time unlock token"""
        self.ensure_one()
        
        if self.state != 'approved':
            return False
        
        token = secrets.token_urlsafe(32)
        expiry = fields.Datetime.now() + timedelta(hours=24)
        
        self.write({
            'unlock_token': token,
            'token_expiry': expiry,
            'token_used': False,
        })
        
        return token
    
    @api.model
    def _cron_expire_tokens(self):
        """Cron job to expire old tokens"""
        now = fields.Datetime.now()
        expired_requests = self.search([
            ('state', '=', 'approved'),
            ('token_expiry', '<', now)
        ])
        
        for request in expired_requests:
            request.write({'state': 'expired'})
            request.document_id.write({
                'unlock_token': False,
                'unlock_expiry': False,
                'is_locked': True
            })

