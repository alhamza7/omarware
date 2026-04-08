# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # NBS-specific fields
    nbs_department_ids = fields.Many2many(
        'nbs.department',
        'nbs_dept_user_rel',
        'user_id',
        'department_id',
        string='NBS Departments',
        help='Departments this user has access to'
    )
    
    nbs_manager_department_ids = fields.Many2many(
        'nbs.department',
        'nbs_dept_manager_rel',
        'user_id',
        'department_id',
        string='Managed Departments',
        help='Departments this user manages'
    )
    
    preferred_nbs_language = fields.Selection([
        ('ar_SA', 'العربية (Arabic)'),
        ('en_US', 'English'),
    ], string='Preferred Language', default='ar_SA')
    
    # Statistics
    uploaded_document_count = fields.Integer(
        string='Uploaded Documents',
        compute='_compute_document_stats',
        store=False
    )
    pending_edit_request_count = fields.Integer(
        string='Pending Edit Requests',
        compute='_compute_edit_request_stats',
        store=False
    )
    unread_notification_count = fields.Integer(
        string='Unread Notifications',
        compute='_compute_notification_stats',
        store=False
    )
    
    @api.depends_context('uid')
    def _compute_document_stats(self):
        for user in self:
            user.uploaded_document_count = self.env['nbs.document'].search_count([
                ('uploader_id', '=', user.id)
            ])
    
    @api.depends_context('uid')
    def _compute_edit_request_stats(self):
        for user in self:
            # Count pending requests where user is manager of the department
            pending_count = 0
            for dept in user.nbs_manager_department_ids:
                pending_count += self.env['nbs.edit.request'].search_count([
                    ('department_id', '=', dept.id),
                    ('state', '=', 'pending')
                ])
            user.pending_edit_request_count = pending_count
    
    @api.depends_context('uid')
    def _compute_notification_stats(self):
        for user in self:
            user.unread_notification_count = self.env['nbs.notification'].search_count([
                ('user_id', '=', user.id),
                ('is_read', '=', False)
            ])
    
    def action_toggle_nbs_language(self):
        """Toggle between Arabic and English"""
        self.ensure_one()
        new_lang = 'en_US' if self.preferred_nbs_language == 'ar_SA' else 'ar_SA'
        self.write({'preferred_nbs_language': new_lang})
        
        # Update Odoo context language
        self.env.context = dict(self.env.context, lang=new_lang)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
    
    def action_view_my_documents(self):
        """View documents uploaded by this user"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Documents',
            'res_model': 'nbs.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('uploader_id', '=', self.id)],
            'context': {'default_uploader_id': self.id}
        }
    
    def action_view_pending_approvals(self):
        """View pending edit requests for managed departments"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pending Approvals',
            'res_model': 'nbs.edit.request',
            'view_mode': 'tree,form',
            'domain': [
                ('department_id', 'in', self.nbs_manager_department_ids.ids),
                ('state', '=', 'pending')
            ]
        }
    
    def action_view_notifications(self):
        """View all notifications"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Notifications',
            'res_model': 'nbs.notification',
            'view_mode': 'tree,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        }
    
    @api.model
    def get_user_departments_with_roles(self, user_id=None):
        """Get user's departments with their roles"""
        if not user_id:
            user_id = self.env.user.id
        
        user = self.browse(user_id)
        result = []
        
        for dept in user.nbs_department_ids:
            role = 'manager' if dept in user.nbs_manager_department_ids else 'user'
            result.append({
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'role': role
            })
        
        return result


