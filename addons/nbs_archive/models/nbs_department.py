# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NBSDepartment(models.Model):
    _name = 'nbs.department'
    _description = 'NBS Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Department Name',
        required=True,
        translate=True,
        tracking=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        index=True,
        tracking=True,
        help='Short code for the department (e.g., SC for Supply Chain)'
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of appearance in lists'
    )
    
    # Users and Managers
    manager_ids = fields.Many2many(
        'res.users',
        'nbs_dept_manager_rel',
        'department_id',
        'user_id',
        string='Managers',
        tracking=True,
        help='Users who can approve edit requests and manage this department'
    )
    user_ids = fields.Many2many(
        'res.users',
        'nbs_dept_user_rel',
        'department_id',
        'user_id',
        string='Users',
        tracking=True,
        help='Regular users who can view and upload documents'
    )
    
    # Relations
    document_type_ids = fields.One2many(
        'nbs.document.type',
        'department_id',
        string='Document Types'
    )
    document_ids = fields.One2many(
        'nbs.document',
        'department_id',
        string='Documents'
    )
    
    # Computed fields
    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count',
        store=False
    )
    document_type_count = fields.Integer(
        string='Document Types',
        compute='_compute_document_type_count',
        store=False
    )
    user_count = fields.Integer(
        string='Users',
        compute='_compute_user_count',
        store=False
    )
    manager_count = fields.Integer(
        string='Managers',
        compute='_compute_manager_count',
        store=False
    )
    
    # UI
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='Color for Kanban view'
    )
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Department code must be unique!'),
        ('name_unique', 'UNIQUE(name)', 'Department name must be unique!'),
    ]
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        for dept in self:
            dept.document_count = len(dept.document_ids)
    
    @api.depends('document_type_ids')
    def _compute_document_type_count(self):
        for dept in self:
            dept.document_type_count = len(dept.document_type_ids)
    
    @api.depends('user_ids')
    def _compute_user_count(self):
        for dept in self:
            dept.user_count = len(dept.user_ids)
    
    @api.depends('manager_ids')
    def _compute_manager_count(self):
        for dept in self:
            dept.manager_count = len(dept.manager_ids)
    
    @api.constrains('code')
    def _check_code(self):
        for dept in self:
            if dept.code:
                if not dept.code.isalnum():
                    raise ValidationError(_('Department code must contain only letters and numbers'))
                if dept.code != dept.code.upper():
                    dept.code = dept.code.upper()
    
    @api.constrains('manager_ids', 'user_ids')
    def _check_users(self):
        """Ensure managers are also in user_ids"""
        for dept in self:
            if dept.manager_ids:
                # Auto-add managers to users if not present
                missing_users = dept.manager_ids - dept.user_ids
                if missing_users:
                    dept.user_ids = [(4, user.id) for user in missing_users]
    
    def name_get(self):
        result = []
        for dept in self:
            name = f'[{dept.code}] {dept.name}'
            result.append((dept.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
    
    def action_view_documents(self):
        """Action to view department documents"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents - %s') % self.name,
            'res_model': 'nbs.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('department_id', '=', self.id)],
            'context': {
                'default_department_id': self.id,
                'search_default_active': 1,
            }
        }
    
    def action_view_document_types(self):
        """Action to view department document types"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Document Types - %s') % self.name,
            'res_model': 'nbs.document.type',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.id)],
            'context': {
                'default_department_id': self.id,
            }
        }


