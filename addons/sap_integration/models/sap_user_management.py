# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP User Management

User management system with role-based access control for SAP integration.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

from ..core.sap_logger import SapLogger, SapValidationError


class SapUserRole(models.Model):
    """SAP User Roles"""
    _name = 'sap.user.role'
    _description = 'SAP User Role'
    _order = 'sequence, name'
    
    
    # Basic Information
    name = fields.Char(
        string='Role Name',
        required=True,
        index=True
    )
    code = fields.Char(
        string='Role Code',
        required=True,
        index=True,
        help="Unique code for the role"
    )
    description = fields.Text(
        string='Description',
        help="Role description and responsibilities"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of preference"
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Permissions
    can_view_dashboard = fields.Boolean(
        string='Can View Dashboard',
        default=True,
        help="Can view the main dashboard"
    )
    can_manage_sync = fields.Boolean(
        string='Can Manage Sync',
        default=False,
        help="Can start, stop, and manage sync operations"
    )
    can_configure_backend = fields.Boolean(
        string='Can Configure Backend',
        default=False,
        help="Can configure SAP backends"
    )
    can_manage_mappings = fields.Boolean(
        string='Can Manage Mappings',
        default=False,
        help="Can manage UoM mappings and data mappings"
    )
    can_view_logs = fields.Boolean(
        string='Can View Logs',
        default=True,
        help="Can view sync logs and error logs"
    )
    can_manage_alerts = fields.Boolean(
        string='Can Manage Alerts',
        default=False,
        help="Can manage alert rules and notifications"
    )
    can_export_data = fields.Boolean(
        string='Can Export Data',
        default=False,
        help="Can export data and reports"
    )
    can_manage_users = fields.Boolean(
        string='Can Manage Users',
        default=False,
        help="Can manage user roles and permissions"
    )
    
    # Backend Access
    backend_access = fields.Selection([
        ('all', 'All Backends'),
        ('assigned', 'Assigned Backends Only'),
        ('none', 'No Backend Access')
    ], string='Backend Access', default='assigned', required=True)
    
    # Constraints
    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Role code must be unique.'),
    ]
    
    @api.model
    def create(self, vals):
        """Override create to set default permissions"""
        if 'code' not in vals:
            vals['code'] = vals.get('name', '').lower().replace(' ', '_')
        
        return super().create(vals)
    
    def action_assign_permissions(self):
        """Assign permissions to users with this role"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Permissions',
            'res_model': 'sap.user.permission.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_role_id': self.id}
        }


class SapUserPermission(models.Model):
    """SAP User Permissions"""
    _name = 'sap.user.permission'
    _description = 'SAP User Permission'
    _order = 'user_id, role_id'
    
    
    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True
    )
    role_id = fields.Many2one(
        'sap.user.role',
        string='Role',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Backend Access
    backend_ids = fields.Many2many(
        'sap.backend',
        'sap_user_permission_backend_rel',
        'permission_id',
        'backend_id',
        string='Assigned Backends',
        help="Backends this user can access"
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    granted_by = fields.Many2one(
        'res.users',
        string='Granted By',
        default=lambda self: self.env.user,
        readonly=True
    )
    granted_date = fields.Datetime(
        string='Granted Date',
        default=fields.Datetime.now,
        readonly=True
    )
    expires_date = fields.Datetime(
        string='Expires Date',
        help="Permission expiration date (optional)"
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_user_role', 'UNIQUE(user_id, role_id)', 
         'A user can only have one permission per role.'),
    ]
    
    @api.model
    def create(self, vals):
        """Override create to validate permissions"""
        record = super().create(vals)
        record._validate_permissions()
        return record
    
    def write(self, vals):
        """Override write to validate permissions"""
        result = super().write(vals)
        self._validate_permissions()
        return result
    
    def _validate_permissions(self):
        """Validate user permissions"""
        for record in self:
            try:
                # Check if user is active
                if not record.user_id.active:
                    raise SapValidationError(f"User {record.user_id.name} is not active")
                
                # Check if role is active
                if not record.role_id.active:
                    raise SapValidationError(f"Role {record.role_id.name} is not active")
                
                # Check expiration
                if record.expires_date and record.expires_date < fields.Datetime.now():
                    record.active = False
                    _logger.warning(f"Permission expired for user {record.user_id.name}")
                
            except Exception as e:
                _logger.error(f"Error validating permissions: {str(e)}")
                raise
    
    @api.model
    def get_user_permissions(self, user_id):
        """Get all permissions for a user"""
        try:
            permissions = self.search([
                ('user_id', '=', user_id),
                ('active', '=', True)
            ])
            
            return {
                'user_id': user_id,
                'permissions': [{
                    'role_id': perm.role_id.id,
                    'role_name': perm.role_id.name,
                    'role_code': perm.role_id.code,
                    'backend_ids': [b.id for b in perm.backend_ids],
                    'backend_names': [b.name for b in perm.backend_ids],
                    'expires_date': perm.expires_date,
                    'granted_date': perm.granted_date
                } for perm in permissions]
            }
            
        except Exception as e:
            _logger.error(f"Error getting user permissions: {str(e)}")
            return {'user_id': user_id, 'permissions': []}
    
    @api.model
    def check_permission(self, user_id, permission_type, backend_id=None):
        """Check if user has specific permission"""
        try:
            permissions = self.search([
                ('user_id', '=', user_id),
                ('active', '=', True)
            ])
            
            for perm in permissions:
                # Check role permissions
                if hasattr(perm.role_id, permission_type):
                    if getattr(perm.role_id, permission_type):
                        # Check backend access
                        if backend_id:
                            if (perm.role_id.backend_access == 'all' or
                                backend_id in perm.backend_ids.ids):
                                return True
                        else:
                            return True
            
            return False
            
        except Exception as e:
            _logger.error(f"Error checking permission: {str(e)}")
            return False
    
    @api.model
    def grant_permission(self, user_id, role_id, backend_ids=None, expires_date=None):
        """Grant permission to user"""
        try:
            # Check if permission already exists
            existing = self.search([
                ('user_id', '=', user_id),
                ('role_id', '=', role_id)
            ])
            
            if existing:
                # Update existing permission
                existing.write({
                    'backend_ids': [(6, 0, backend_ids or [])],
                    'expires_date': expires_date,
                    'active': True
                })
                _logger.info(f"Updated permission for user {user_id}")
            else:
                # Create new permission
                self.create({
                    'user_id': user_id,
                    'role_id': role_id,
                    'backend_ids': [(6, 0, backend_ids or [])],
                    'expires_date': expires_date
                })
                _logger.info(f"Granted permission to user {user_id}")
            
            return True
            
        except Exception as e:
            _logger.error(f"Error granting permission: {str(e)}")
            return False
    
    @api.model
    def revoke_permission(self, user_id, role_id):
        """Revoke permission from user"""
        try:
            permission = self.search([
                ('user_id', '=', user_id),
                ('role_id', '=', role_id)
            ])
            
            if permission:
                permission.write({'active': False})
                _logger.info(f"Revoked permission from user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            _logger.error(f"Error revoking permission: {str(e)}")
            return False


class SapUserActivityLog(models.Model):
    """SAP User Activity Log"""
    _name = 'sap.user.activity.log'
    _description = 'SAP User Activity Log'
    _order = 'activity_date desc'
    
    
    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True
    )
    activity_type = fields.Selection([
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('sync_start', 'Sync Start'),
        ('sync_stop', 'Sync Stop'),
        ('config_change', 'Configuration Change'),
        ('data_export', 'Data Export'),
        ('alert_acknowledge', 'Alert Acknowledge'),
        ('permission_grant', 'Permission Grant'),
        ('permission_revoke', 'Permission Revoke'),
        ('other', 'Other')
    ], string='Activity Type', required=True)
    
    activity_description = fields.Text(
        string='Description',
        required=True
    )
    activity_date = fields.Datetime(
        string='Activity Date',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    # Context Information
    backend_id = fields.Many2one(
        'sap.backend',
        string='Backend',
        help="Related backend (if applicable)"
    )
    ip_address = fields.Char(
        string='IP Address',
        help="User's IP address"
    )
    user_agent = fields.Char(
        string='User Agent',
        help="User's browser/client information"
    )
    
    # Additional Data
    additional_data = fields.Text(
        string='Additional Data',
        help="Additional data in JSON format"
    )
    
    @api.model
    def log_activity(self, user_id, activity_type, description, backend_id=None, 
                    ip_address=None, user_agent=None, additional_data=None):
        """Log user activity"""
        try:
            self.create({
                'user_id': user_id,
                'activity_type': activity_type,
                'activity_description': description,
                'backend_id': backend_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'additional_data': json.dumps(additional_data) if additional_data else None
            })
            
        except Exception as e:
            _logger.error(f"Error logging activity: {str(e)}")
    
    @api.model
    def get_user_activities(self, user_id, days=30, activity_type=None):
        """Get user activities"""
        try:
            domain = [
                ('user_id', '=', user_id),
                ('activity_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            
            if activity_type:
                domain.append(('activity_type', '=', activity_type))
            
            activities = self.search(domain, limit=100)
            
            return [{
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.activity_description,
                'date': activity.activity_date,
                'backend': activity.backend_id.name if activity.backend_id else None,
                'ip_address': activity.ip_address,
                'additional_data': json.loads(activity.additional_data) if activity.additional_data else None
            } for activity in activities]
            
        except Exception as e:
            _logger.error(f"Error getting user activities: {str(e)}")
            return []
    
    @api.model
    def get_activity_statistics(self, days=30):
        """Get activity statistics"""
        try:
            domain = [
                ('activity_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            
            activities = self.search(domain)
            
            stats = {
                'total_activities': len(activities),
                'by_type': {},
                'by_user': {},
                'by_backend': {},
                'unique_users': len(activities.mapped('user_id')),
                'unique_backends': len(activities.mapped('backend_id'))
            }
            
            # Group by activity type
            for activity in activities:
                activity_type = activity.activity_type
                if activity_type not in stats['by_type']:
                    stats['by_type'][activity_type] = 0
                stats['by_type'][activity_type] += 1
            
            # Group by user
            for activity in activities:
                user_name = activity.user_id.name
                if user_name not in stats['by_user']:
                    stats['by_user'][user_name] = 0
                stats['by_user'][user_name] += 1
            
            # Group by backend
            for activity in activities:
                if activity.backend_id:
                    backend_name = activity.backend_id.name
                    if backend_name not in stats['by_backend']:
                        stats['by_backend'][backend_name] = 0
                    stats['by_backend'][backend_name] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting activity statistics: {str(e)}")
            return {}


class SapUserSession(models.Model):
    """SAP User Session Management"""
    _name = 'sap.user.session'
    _description = 'SAP User Session'
    _order = 'last_activity desc'
    
    
    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True
    )
    session_id = fields.Char(
        string='Session ID',
        required=True,
        index=True
    )
    
    # Session Information
    login_time = fields.Datetime(
        string='Login Time',
        default=fields.Datetime.now,
        required=True
    )
    last_activity = fields.Datetime(
        string='Last Activity',
        default=fields.Datetime.now,
        required=True
    )
    ip_address = fields.Char(
        string='IP Address',
        required=True
    )
    user_agent = fields.Char(
        string='User Agent'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    expires_at = fields.Datetime(
        string='Expires At',
        help="Session expiration time"
    )
    
    @api.model
    def create_session(self, user_id, session_id, ip_address, user_agent=None, expires_hours=24):
        """Create new user session"""
        try:
            # Invalidate existing sessions for user
            self.search([('user_id', '=', user_id), ('active', '=', True)]).write({'active': False})
            
            # Create new session
            expires_at = fields.Datetime.now() + timedelta(hours=expires_hours)
            
            session = self.create({
                'user_id': user_id,
                'session_id': session_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'expires_at': expires_at
            })
            
            _logger.info(f"Created session for user {user_id}")
            
            return session
            
        except Exception as e:
            _logger.error(f"Error creating session: {str(e)}")
            return None
    
    @api.model
    def validate_session(self, session_id):
        """Validate user session"""
        try:
            session = self.search([
                ('session_id', '=', session_id),
                ('active', '=', True)
            ], limit=1)
            
            if not session:
                return None
            
            # Check if session is expired
            if session.expires_at and session.expires_at < fields.Datetime.now():
                session.write({'active': False})
                return None
            
            # Update last activity
            session.write({'last_activity': fields.Datetime.now()})
            
            return session
            
        except Exception as e:
            _logger.error(f"Error validating session: {str(e)}")
            return None
    
    @api.model
    def invalidate_session(self, session_id):
        """Invalidate user session"""
        try:
            session = self.search([
                ('session_id', '=', session_id),
                ('active', '=', True)
            ])
            
            if session:
                session.write({'active': False})
                _logger.info(f"Invalidated session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            _logger.error(f"Error invalidating session: {str(e)}")
            return False
    
    @api.model
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            expired_sessions = self.search([
                ('expires_at', '<', fields.Datetime.now()),
                ('active', '=', True)
            ])
            
            if expired_sessions:
                expired_sessions.write({'active': False})
                _logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            _logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
