# -*- coding: utf-8 -*-

import logging
from odoo import models, api, _

_logger = logging.getLogger(__name__)


class NBSNotificationService(models.AbstractModel):
    _name = 'nbs.notification.service'
    _description = 'Notification Service'
    
    @api.model
    def notify_upload(self, document):
        """Notify department managers about new upload"""
        managers = document.department_id.manager_ids
        
        for manager in managers:
            if manager != document.uploader_id:  # Don't notify uploader
                self.env['nbs.notification'].sudo().create({
                    'user_id': manager.id,
                    'title': _('New Document Uploaded'),
                    'message': _('%s uploaded "%s" to %s') % (
                        document.uploader_id.name,
                        document.name,
                        document.department_id.name
                    ),
                    'notification_type': 'upload',
                    'document_id': document.id,
                })
    
    @api.model
    def notify_edit_request(self, edit_request):
        """Notify managers about edit request"""
        managers = edit_request.department_id.manager_ids
        
        for manager in managers:
            self.env['nbs.notification'].sudo().create({
                'user_id': manager.id,
                'title': _('Edit Request Pending'),
                'message': _('%s requested to edit "%s"') % (
                    edit_request.requester_id.name,
                    edit_request.document_id.name
                ),
                'notification_type': 'edit_request',
                'document_id': edit_request.document_id.id,
                'edit_request_id': edit_request.id,
            })
    
    @api.model
    def notify_approval(self, edit_request):
        """Notify requester about approval"""
        self.env['nbs.notification'].sudo().create({
            'user_id': edit_request.requester_id.id,
            'title': _('Edit Request Approved'),
            'message': _('Your edit request for "%s" has been approved. You have 24 hours to upload a new version.') % edit_request.document_id.name,
            'notification_type': 'approval',
            'document_id': edit_request.document_id.id,
            'edit_request_id': edit_request.id,
        })
    
    @api.model
    def notify_rejection(self, edit_request):
        """Notify requester about rejection"""
        self.env['nbs.notification'].sudo().create({
            'user_id': edit_request.requester_id.id,
            'title': _('Edit Request Rejected'),
            'message': _('Your edit request for "%s" has been rejected.') % edit_request.document_id.name,
            'notification_type': 'rejection',
            'document_id': edit_request.document_id.id,
            'edit_request_id': edit_request.id,
        })
    
    @api.model
    def notify_new_version(self, document, version):
        """Notify department users about new version"""
        # Notify department managers
        for manager in document.department_id.manager_ids:
            if manager != version.uploader_id:
                self.env['nbs.notification'].sudo().create({
                    'user_id': manager.id,
                    'title': _('New Version Available'),
                    'message': _('New version (v%s) of "%s" has been uploaded') % (
                        version.version_number,
                        document.name
                    ),
                    'notification_type': 'new_version',
                    'document_id': document.id,
                })
    
    @api.model
    def notify_archive(self, document):
        """Notify uploader about document archive"""
        self.env['nbs.notification'].sudo().create({
            'user_id': document.uploader_id.id,
            'title': _('Document Archived'),
            'message': _('Your document "%s" has been archived') % document.name,
            'notification_type': 'archive',
            'document_id': document.id,
        })
    
    @api.model
    def send_system_notification(self, user_ids, title, message):
        """Send system notification to multiple users"""
        for user_id in user_ids:
            self.env['nbs.notification'].sudo().create({
                'user_id': user_id,
                'title': title,
                'message': message,
                'notification_type': 'system',
            })


