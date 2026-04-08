# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class LugalPermission(models.Model):
    _name = 'lugal.permission'
    _description = 'Lugal AI Permission Rules'
    _rec_name = 'role'

    role = fields.Selection([
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('customer', 'Customer'),
    ], string='Role', required=True)
    
    # Access Rights
    can_access_sales = fields.Boolean(string='Access Sales Data', default=False)
    can_access_products = fields.Boolean(string='Access Products', default=False)
    can_access_customers = fields.Boolean(string='Access Customers', default=False)
    can_access_employees = fields.Boolean(string='Access Employees', default=False)
    can_access_analytics = fields.Boolean(string='Access Analytics', default=False)
    can_access_operations = fields.Boolean(string='Access Operations', default=False)
    can_access_inventory = fields.Boolean(string='Access Inventory', default=False)
    can_access_accounting = fields.Boolean(string='Access Accounting', default=False)
    
    # Data Scope
    own_data_only = fields.Boolean(string='Own Data Only', default=False, 
                                     help='If checked, user can only see their own data')
    assigned_data_only = fields.Boolean(string='Assigned Data Only', default=False,
                                         help='If checked, user can only see data assigned to them')
    
    # Query Limits
    max_queries_per_hour = fields.Integer(string='Max Queries/Hour', default=100)
    max_records_per_query = fields.Integer(string='Max Records/Query', default=100)
    
    # Description
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('role_unique', 'unique(role)', 'Each role can only have one permission record!')
    ]
    
    @api.model
    def get_user_role(self, user=None):
        """Determine user's role based on groups"""
        if not user:
            user = self.env.user
        
        # Check if admin
        if user.has_group('base.group_system'):
            return 'admin'
        
        # Check if employee
        if user.has_group('base.group_user'):
            return 'employee'
        
        # Check if portal/customer
        if user.has_group('base.group_portal'):
            return 'customer'
        
        # Default to most restricted
        return 'customer'
    
    @api.model
    def check_permission(self, user, permission_name):
        """Check if user has specific permission"""
        role = self.get_user_role(user)
        permission = self.search([('role', '=', role)], limit=1)
        
        if not permission:
            _logger.warning(f"No permission record found for role: {role}")
            return False
        
        return getattr(permission, permission_name, False)
    
    @api.model
    def enforce_permission(self, user, permission_name):
        """Enforce permission or raise AccessError"""
        if not self.check_permission(user, permission_name):
            role = self.get_user_role(user)
            raise AccessError(f"Access Denied: Role '{role}' does not have permission '{permission_name}'")
        return True
    
    @api.model
    def get_data_scope(self, user):
        """Get data scope restrictions for user"""
        role = self.get_user_role(user)
        permission = self.search([('role', '=', role)], limit=1)
        
        if not permission:
            return {'own_data_only': True, 'assigned_data_only': True}
        
        return {
            'own_data_only': permission.own_data_only,
            'assigned_data_only': permission.assigned_data_only,
            'max_records': permission.max_records_per_query,
        }

