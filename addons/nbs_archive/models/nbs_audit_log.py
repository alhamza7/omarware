# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NBSAuditLog(models.Model):
    _name = 'nbs.audit.log'
    _description = 'Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'action'
    
    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        readonly=True,
        index=True,
        ondelete='restrict'
    )
    action = fields.Selection([
        ('upload', 'Upload'),
        ('view', 'View'),
        ('download', 'Download'),
        ('edit_request', 'Edit Request'),
        ('edit_request_created', 'Edit Request Created'),
        ('edit_request_approved', 'Edit Request Approved'),
        ('edit_request_rejected', 'Edit Request Rejected'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('new_version', 'New Version'),
        ('new_version_uploaded', 'New Version Uploaded'),
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
        ('search', 'Search'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('attachment_upload', 'Attachment Upload'),
        ('signed_version_uploaded', 'Signed Version Uploaded'),
        ('relation_created', 'Relation Created'),
    ], string='Action', required=True, readonly=True, index=True)
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        readonly=True,
        index=True,
        ondelete='restrict'
    )
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        readonly=True,
        index=True,
        ondelete='restrict'
    )
    
    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
        index=True
    )
    user_agent = fields.Text(
        string='User Agent',
        readonly=True
    )
    
    details = fields.Text(
        string='Details',
        readonly=True,
        help='Additional details in JSON format'
    )
    metadata = fields.Text(
        string='Metadata',
        readonly=True,
        help='Additional metadata information about the action'
    )
    metadata_snapshot = fields.Text(
        string='Metadata Snapshot',
        readonly=True,
        help='Snapshot of document metadata at time of action'
    )
    
    _sql_constraints = [
        ('no_delete', 'CHECK(1=1)', 'Audit logs cannot be deleted!'),
    ]
    
    def unlink(self):
        """CRITICAL: Prevent deletion of audit logs"""
        from odoo.exceptions import ValidationError
        raise ValidationError('Audit logs cannot be deleted! They must be preserved for compliance.')
    
    @api.model
    def log_action(self, action, user_id=None, document_id=None, department_id=None, 
                   ip_address=None, user_agent=None, details=None, metadata=None):
        """
        Helper method to create audit log entries
        
        Usage:
            self.env['nbs.audit.log'].log_action(
                action='download',
                document_id=doc.id,
                department_id=doc.department_id.id,
                details='Downloaded version 2',
                metadata='Additional info'
            )
        """
        vals = {
            'action': action,
            'user_id': user_id or self.env.user.id,
        }
        
        if document_id:
            vals['document_id'] = document_id
        
        if department_id:
            vals['department_id'] = department_id
        
        if ip_address:
            vals['ip_address'] = ip_address
        
        if user_agent:
            vals['user_agent'] = user_agent
        
        if details:
            vals['details'] = details
        
        if metadata:
            vals['metadata'] = metadata
        
        return self.sudo().create(vals)
    
    def name_get(self):
        result = []
        for log in self:
            name = f'{log.user_id.name} - {log.action}'
            if log.document_id:
                name += f' - {log.document_id.name}'
            result.append((log.id, name))
        return result


