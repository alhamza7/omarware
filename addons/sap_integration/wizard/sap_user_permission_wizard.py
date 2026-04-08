# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP User Permission Wizard

Wizard for managing user permissions and role assignments.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

from ..core.sap_logger import SapLogger


class SapUserPermissionWizard(models.TransientModel):
    """Wizard for managing user permissions"""
    _name = 'sap.user.permission.wizard'
    _description = 'SAP User Permission Wizard'
    
    
    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        help="User to assign permissions to"
    )
    role_id = fields.Many2one(
        'sap.user.role',
        string='Role',
        required=True,
        help="Role to assign to the user"
    )
    
    # Backend Access
    backend_access_type = fields.Selection([
        ('all', 'All Backends'),
        ('assigned', 'Assigned Backends Only'),
        ('none', 'No Backend Access')
    ], string='Backend Access Type', default='assigned')
    
    backend_ids = fields.Many2many(
        'sap.backend',
        'sap_permission_wizard_backend_rel',
        'wizard_id',
        'backend_id',
        string='Assigned Backends',
        help="Backends this user can access (if assigned access type)"
    )
    
    # Permission Details
    expires_date = fields.Datetime(
        string='Expires Date',
        help="Permission expiration date (optional)"
    )
    expires_hours = fields.Integer(
        string='Expires in Hours',
        default=0,
        help="Permission expires in this many hours (0 = no expiration)"
    )
    
    # Current Permissions
    current_permissions = fields.Text(
        string='Current Permissions',
        readonly=True,
        help="Current permissions for this user"
    )
    
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        defaults = super().default_get(fields_list)
        
        # Set default role from context
        if 'default_role_id' in self.env.context:
            defaults['role_id'] = self.env.context['default_role_id']
        
        return defaults
    
    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Update current permissions when user changes"""
        if self.user_id:
            self._update_current_permissions()
    
    @api.onchange('role_id')
    def _onchange_role_id(self):
        """Update backend access type when role changes"""
        if self.role_id:
            self.backend_access_type = self.role_id.backend_access
    
    @api.onchange('expires_hours')
    def _onchange_expires_hours(self):
        """Update expires date when hours change"""
        if self.expires_hours and self.expires_hours > 0:
            self.expires_date = fields.Datetime.now() + timedelta(hours=self.expires_hours)
        else:
            self.expires_date = False
    
    def _update_current_permissions(self):
        """Update current permissions display"""
        try:
            if not self.user_id:
                self.current_permissions = ""
                return
            
            # Get user permissions
            permission_model = self.env['sap.user.permission']
            permissions = permission_model.get_user_permissions(self.user_id.id)
            
            if not permissions['permissions']:
                self.current_permissions = "No permissions assigned"
                return
            
            # Format permissions for display
            perm_text = "Current Permissions:\n\n"
            for perm in permissions['permissions']:
                perm_text += f"• {perm['role_name']} ({perm['role_code']})\n"
                if perm['backend_names']:
                    perm_text += f"  Backends: {', '.join(perm['backend_names'])}\n"
                if perm['expires_date']:
                    perm_text += f"  Expires: {perm['expires_date']}\n"
                perm_text += f"  Granted: {perm['granted_date']}\n\n"
            
            self.current_permissions = perm_text
            
        except Exception as e:
            _logger.error(f"Error updating current permissions: {str(e)}")
            self.current_permissions = "Error loading permissions"
    
    def action_grant_permission(self):
        """Grant permission to user"""
        try:
            if not self.user_id or not self.role_id:
                raise UserError("User and Role are required")
            
            # Validate backend access
            backend_ids = []
            if self.backend_access_type == 'assigned':
                if not self.backend_ids:
                    raise UserError("Please select backends for assigned access type")
                backend_ids = self.backend_ids.ids
            elif self.backend_access_type == 'all':
                # Get all active backends
                backend_ids = self.env['sap.backend'].search([('active', '=', True)]).ids
            
            # Grant permission
            permission_model = self.env['sap.user.permission']
            success = permission_model.grant_permission(
                user_id=self.user_id.id,
                role_id=self.role_id.id,
                backend_ids=backend_ids,
                expires_date=self.expires_date
            )
            
            if success:
                # Log activity
                self.env['sap.user.activity.log'].log_activity(
                    user_id=self.env.user.id,
                    activity_type='permission_grant',
                    description=f"Granted {self.role_id.name} role to {self.user_id.name}",
                    additional_data={
                        'target_user': self.user_id.name,
                        'role': self.role_id.name,
                        'backend_access': self.backend_access_type,
                        'backend_ids': backend_ids
                    }
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Permission Granted',
                        'message': f'Successfully granted {self.role_id.name} role to {self.user_id.name}',
                        'type': 'success'
                    }
                }
            else:
                raise UserError("Failed to grant permission")
                
        except Exception as e:
            _logger.error(f"Error granting permission: {str(e)}")
            raise UserError(f"Failed to grant permission: {str(e)}")
    
    def action_revoke_permission(self):
        """Revoke permission from user"""
        try:
            if not self.user_id or not self.role_id:
                raise UserError("User and Role are required")
            
            # Revoke permission
            permission_model = self.env['sap.user.permission']
            success = permission_model.revoke_permission(
                user_id=self.user_id.id,
                role_id=self.role_id.id
            )
            
            if success:
                # Log activity
                self.env['sap.user.activity.log'].log_activity(
                    user_id=self.env.user.id,
                    activity_type='permission_revoke',
                    description=f"Revoked {self.role_id.name} role from {self.user_id.name}",
                    additional_data={
                        'target_user': self.user_id.name,
                        'role': self.role_id.name
                    }
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Permission Revoked',
                        'message': f'Successfully revoked {self.role_id.name} role from {self.user_id.name}',
                        'type': 'success'
                    }
                }
            else:
                raise UserError("Permission not found or already revoked")
                
        except Exception as e:
            _logger.error(f"Error revoking permission: {str(e)}")
            raise UserError(f"Failed to revoke permission: {str(e)}")
    
    def action_view_user_permissions(self):
        """View all permissions for the user"""
        try:
            if not self.user_id:
                raise UserError("Please select a user first")
            
            return {
                'type': 'ir.actions.act_window',
                'name': f'Permissions for {self.user_id.name}',
                'res_model': 'sap.user.permission',
                'view_mode': 'list,form',
                'domain': [('user_id', '=', self.user_id.id)],
                'context': {'default_user_id': self.user_id.id}
            }
            
        except Exception as e:
            _logger.error(f"Error viewing user permissions: {str(e)}")
            raise UserError(f"Failed to view user permissions: {str(e)}")
    
    def action_view_role_details(self):
        """View role details"""
        try:
            if not self.role_id:
                raise UserError("Please select a role first")
            
            return {
                'type': 'ir.actions.act_window',
                'name': f'Role Details: {self.role_id.name}',
                'res_model': 'sap.user.role',
                'res_id': self.role_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
            
        except Exception as e:
            _logger.error(f"Error viewing role details: {str(e)}")
            raise UserError(f"Failed to view role details: {str(e)}")
    
    def action_bulk_assign_permissions(self):
        """Bulk assign permissions to multiple users"""
        try:
            if not self.role_id:
                raise UserError("Please select a role first")
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulk Assign Permissions',
                'res_model': 'sap.bulk.permission.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_role_id': self.role_id.id,
                    'default_backend_access_type': self.backend_access_type,
                    'default_backend_ids': self.backend_ids.ids,
                    'default_expires_date': self.expires_date
                }
            }
            
        except Exception as e:
            _logger.error(f"Error opening bulk assign wizard: {str(e)}")
            raise UserError(f"Failed to open bulk assign wizard: {str(e)}")


class SapBulkPermissionWizard(models.TransientModel):
    """Wizard for bulk permission assignment"""
    _name = 'sap.bulk.permission.wizard'
    _description = 'SAP Bulk Permission Wizard'
    
    
    # Basic Information
    role_id = fields.Many2one(
        'sap.user.role',
        string='Role',
        required=True,
        help="Role to assign to users"
    )
    
    # User Selection
    user_selection_type = fields.Selection([
        ('specific', 'Specific Users'),
        ('group', 'User Group'),
        ('all', 'All Active Users')
    ], string='User Selection Type', default='specific', required=True)
    
    user_ids = fields.Many2many(
        'res.users',
        'sap_bulk_permission_user_rel',
        'wizard_id',
        'user_id',
        string='Selected Users',
        help="Users to assign permissions to"
    )
    
    group_id = fields.Many2one(
        'res.groups',
        string='User Group',
        help="Group of users to assign permissions to"
    )
    
    # Backend Access
    backend_access_type = fields.Selection([
        ('all', 'All Backends'),
        ('assigned', 'Assigned Backends Only'),
        ('none', 'No Backend Access')
    ], string='Backend Access Type', default='assigned')
    
    backend_ids = fields.Many2many(
        'sap.backend',
        'sap_bulk_permission_backend_rel',
        'wizard_id',
        'backend_id',
        string='Assigned Backends',
        help="Backends users can access (if assigned access type)"
    )
    
    # Permission Details
    expires_date = fields.Datetime(
        string='Expires Date',
        help="Permission expiration date (optional)"
    )
    
    # Results
    assignment_results = fields.Text(
        string='Assignment Results',
        readonly=True,
        help="Results of the bulk assignment"
    )
    
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        defaults = super().default_get(fields_list)
        
        # Set default role from context
        if 'default_role_id' in self.env.context:
            defaults['role_id'] = self.env.context['default_role_id']
        if 'default_backend_access_type' in self.env.context:
            defaults['backend_access_type'] = self.env.context['default_backend_access_type']
        if 'default_backend_ids' in self.env.context:
            defaults['backend_ids'] = self.env.context['default_backend_ids']
        if 'default_expires_date' in self.env.context:
            defaults['expires_date'] = self.env.context['default_expires_date']
        
        return defaults
    
    @api.onchange('user_selection_type')
    def _onchange_user_selection_type(self):
        """Clear user selection when type changes"""
        self.user_ids = False
        self.group_id = False
    
    @api.onchange('group_id')
    def _onchange_group_id(self):
        """Update user selection when group changes"""
        if self.group_id:
            # Get users in the group
            users = self.env['res.users'].search([
                ('groups_id', 'in', self.group_id.id)
            ])
            self.user_ids = users.ids
    
    def action_assign_permissions(self):
        """Assign permissions to selected users"""
        try:
            if not self.role_id:
                raise UserError("Please select a role first")
            
            # Get target users
            target_users = self._get_target_users()
            if not target_users:
                raise UserError("No users selected for permission assignment")
            
            # Validate backend access
            backend_ids = []
            if self.backend_access_type == 'assigned':
                if not self.backend_ids:
                    raise UserError("Please select backends for assigned access type")
                backend_ids = self.backend_ids.ids
            elif self.backend_access_type == 'all':
                # Get all active backends
                backend_ids = self.env['sap.backend'].search([('active', '=', True)]).ids
            
            # Assign permissions
            permission_model = self.env['sap.user.permission']
            results = {
                'total': len(target_users),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for user in target_users:
                try:
                    success = permission_model.grant_permission(
                        user_id=user.id,
                        role_id=self.role_id.id,
                        backend_ids=backend_ids,
                        expires_date=self.expires_date
                    )
                    
                    if success:
                        results['successful'] += 1
                        # Log activity
                        self.env['sap.user.activity.log'].log_activity(
                            user_id=self.env.user.id,
                            activity_type='permission_grant',
                            description=f"Bulk granted {self.role_id.name} role to {user.name}",
                            additional_data={
                                'target_user': user.name,
                                'role': self.role_id.name,
                                'backend_access': self.backend_access_type,
                                'backend_ids': backend_ids
                            }
                        )
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to grant permission to {user.name}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error granting permission to {user.name}: {str(e)}")
                    _logger.error(f"Error granting permission to {user.name}: {str(e)}")
            
            # Update results
            self.assignment_results = self._format_assignment_results(results)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Bulk Assignment Complete',
                    'message': f'Successfully assigned permissions to {results["successful"]} out of {results["total"]} users',
                    'type': 'success' if results["failed"] == 0 else 'warning'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in bulk permission assignment: {str(e)}")
            raise UserError(f"Failed to assign permissions: {str(e)}")
    
    def _get_target_users(self):
        """Get target users based on selection type"""
        try:
            if self.user_selection_type == 'specific':
                return self.user_ids
            elif self.user_selection_type == 'group':
                if not self.group_id:
                    return self.env['res.users']
                return self.env['res.users'].search([
                    ('groups_id', 'in', self.group_id.id)
                ])
            elif self.user_selection_type == 'all':
                return self.env['res.users'].search([('active', '=', True)])
            
            return self.env['res.users']
            
        except Exception as e:
            _logger.error(f"Error getting target users: {str(e)}")
            return self.env['res.users']
    
    def _format_assignment_results(self, results):
        """Format assignment results for display"""
        try:
            result_text = f"Bulk Permission Assignment Results:\n\n"
            result_text += f"Total Users: {results['total']}\n"
            result_text += f"Successful: {results['successful']}\n"
            result_text += f"Failed: {results['failed']}\n\n"
            
            if results['errors']:
                result_text += "Errors:\n"
                for error in results['errors']:
                    result_text += f"• {error}\n"
            
            return result_text
            
        except Exception as e:
            _logger.error(f"Error formatting assignment results: {str(e)}")
            return "Error formatting results"
