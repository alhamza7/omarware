# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class NBSNotification(models.Model):
    _name = 'nbs.notification'
    _description = 'Notification'
    _order = 'create_date desc'
    _rec_name = 'title'
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        ondelete='cascade'
    )
    title = fields.Char(
        string='Title',
        required=True,
        translate=True
    )
    message = fields.Text(
        string='Message',
        translate=True
    )
    
    notification_type = fields.Selection([
        ('upload', 'New Upload'),
        ('edit_request', 'Edit Request'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('new_version', 'New Version'),
        ('archive', 'Archive'),
        ('mention', 'Mention'),
        ('system', 'System'),
    ], string='Type', index=True)
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        ondelete='cascade'
    )
    edit_request_id = fields.Many2one(
        'nbs.edit.request',
        string='Edit Request',
        ondelete='cascade'
    )
    
    is_read = fields.Boolean(
        string='Read',
        default=False,
        index=True
    )
    read_date = fields.Datetime(
        string='Read Date'
    )
    
    create_date = fields.Datetime(
        string='Created',
        readonly=True
    )
    
    # Related fields for easy filtering
    department_id = fields.Many2one(
        related='document_id.department_id',
        string='Department',
        store=True,
        index=True
    )
    
    @api.model
    def create(self, vals):
        notif = super().create(vals)
        
        # Send via Odoo bus (WebSocket) for real-time notification
        notif._send_bus_notification()
        
        return notif
    
    def _send_bus_notification(self):
        """Send notification via Odoo bus for real-time updates"""
        self.ensure_one()
        
        channel = f'nbs_notification_{self.user_id.id}'
        message = {
            'type': 'nbs_notification',
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'document_id': self.document_id.id if self.document_id else None,
            'created_date': fields.Datetime.to_string(self.create_date),
            'is_read': self.is_read,
        }
        
        # Send to specific user channel
        self.env['bus.bus']._sendone(
            self.user_id.partner_id,
            'nbs_notification',
            message
        )
    
    def action_mark_read(self):
        """Mark notification as read"""
        for notif in self:
            if not notif.is_read:
                notif.write({
                    'is_read': True,
                    'read_date': fields.Datetime.now()
                })
        return True
    
    def action_mark_unread(self):
        """Mark notification as unread"""
        self.write({
            'is_read': False,
            'read_date': False
        })
        return True
    
    @api.model
    def mark_all_read(self, user_id=None):
        """Mark all notifications as read for a user"""
        if not user_id:
            user_id = self.env.user.id
        
        unread = self.search([
            ('user_id', '=', user_id),
            ('is_read', '=', False)
        ])
        unread.action_mark_read()
        
        return len(unread)
    
    @api.model
    def get_unread_count(self, user_id=None):
        """Get count of unread notifications"""
        if not user_id:
            user_id = self.env.user.id
        
        return self.search_count([
            ('user_id', '=', user_id),
            ('is_read', '=', False)
        ])
    
    @api.model
    def get_recent_notifications(self, user_id=None, limit=20):
        """Get recent notifications for a user"""
        if not user_id:
            user_id = self.env.user.id
        
        notifications = self.search([
            ('user_id', '=', user_id)
        ], limit=limit, order='create_date desc')
        
        return notifications.read([
            'id', 'title', 'message', 'notification_type',
            'is_read', 'create_date', 'document_id', 'edit_request_id'
        ])


