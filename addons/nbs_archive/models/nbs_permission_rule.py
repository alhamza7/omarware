# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NBSPermissionRule(models.Model):
    _name = 'nbs.permission.rule'
    _description = 'Advanced Permission Rules'
    
    name = fields.Char(string='Rule Name', required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    
    # Rule scope
    department_id = fields.Many2one('nbs.department', string='Department')
    document_type_id = fields.Many2one('nbs.document.type', string='Document Type')
    folder_id = fields.Many2one('nbs.document.folder', string='Folder')
    
    # Permissions
    group_id = fields.Many2one('res.groups', string='Group', required=True)
    user_ids = fields.Many2many('res.users', string='Specific Users')
    
    can_read = fields.Boolean(string='Can Read', default=True)
    can_create = fields.Boolean(string='Can Create', default=False)
    can_write = fields.Boolean(string='Can Update', default=False)
    can_delete = fields.Boolean(string='Can Delete', default=False)
    can_archive = fields.Boolean(string='Can Archive', default=False)
    can_share = fields.Boolean(string='Can Share', default=False)
    
    # Confidentiality access
    max_confidentiality = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], string='Max Confidentiality Level', default='internal')


class NBSDocumentShare(models.Model):
    _name = 'nbs.document.share'
    _description = 'Document Sharing'
    
    document_id = fields.Many2one('nbs.document', string='Document', required=True, ondelete='cascade')
    shared_with_user_id = fields.Many2one('res.users', string='Shared With')
    shared_with_group_id = fields.Many2one('res.groups', string='Shared With Group')
    
    can_edit = fields.Boolean(string='Can Edit', default=False)
    can_download = fields.Boolean(string='Can Download', default=True)
    expires_at = fields.Datetime(string='Expires At')
    
    shared_by = fields.Many2one('res.users', string='Shared By', default=lambda self: self.env.user)
    share_date = fields.Datetime(string='Shared Date', default=fields.Datetime.now)
    
    share_link = fields.Char(string='Share Link', compute='_compute_share_link')
    
    def _compute_share_link(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for share in self:
            share.share_link = f"{base_url}/api/shared-documents/{share.id}"
