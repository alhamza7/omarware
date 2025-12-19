# -*- coding: utf-8 -*-

import logging
from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NBSDocumentService(models.AbstractModel):
    _name = 'nbs.document.service'
    _description = 'Document Business Logic Service'
    
    @api.model
    def create_document_with_file(self, document_data, file_data, file_name):
        """
        Create document with initial file version
        
        Args:
            document_data: Dict with document fields
            file_data: Binary file data (base64)
            file_name: Original filename
        
        Returns:
            Document record
        """
        Document = self.env['nbs.document']
        Version = self.env['nbs.document.version']
        
        # Create document
        document = Document.create(document_data)
        
        # Create first version
        version = Version.create({
            'document_id': document.id,
            'file_data': file_data,
            'file_name': file_name,
            'notes': 'Initial version'
        })
        
        # Update document
        document.write({'current_version_id': version.id})
        
        # Activate document
        document.action_activate()
        
        return document
    
    @api.model
    def upload_new_version(self, document_id, file_data, file_name, unlock_token, notes=''):
        """
        Upload new version with unlock token
        
        Args:
            document_id: Document ID
            file_data: Binary file data (base64)
            file_name: Filename
            unlock_token: One-time unlock token
            notes: Version notes
        
        Returns:
            Version record or raises exception
        """
        Document = self.env['nbs.document']
        Version = self.env['nbs.document.version']
        
        document = Document.browse(document_id)
        
        if not document.exists():
            raise ValidationError(_('Document not found'))
        
        # Verify unlock token
        if document.unlock_token != unlock_token:
            raise ValidationError(_('Invalid unlock token'))
        
        if not document.unlock_expiry or document.unlock_expiry < self.env.cr.now():
            raise ValidationError(_('Unlock token has expired'))
        
        # Create new version
        version = Version.create({
            'document_id': document.id,
            'file_data': file_data,
            'file_name': file_name,
            'notes': notes
        })
        
        # Update document
        document.write({
            'current_version_id': version.id,
            'unlock_token': False,
            'unlock_expiry': False,
            'is_locked': True
        })
        
        # Mark edit request as completed
        edit_request = self.env['nbs.edit.request'].search([
            ('document_id', '=', document.id),
            ('unlock_token', '=', unlock_token),
            ('state', '=', 'approved')
        ], limit=1)
        
        if edit_request:
            edit_request.mark_completed()
        
        # Notify requester
        if edit_request and edit_request.requester_id:
            self.env['nbs.notification'].sudo().create({
                'user_id': edit_request.requester_id.id,
                'title': _('New Version Uploaded'),
                'message': _('New version of "%s" has been uploaded successfully') % document.name,
                'notification_type': 'new_version',
                'document_id': document.id,
            })
        
        # Schedule OCR
        document._schedule_ocr()
        
        return version
    
    @api.model
    def get_user_documents(self, user_id=None, filters=None, limit=20, offset=0):
        """
        Get documents accessible to user with filters
        
        Args:
            user_id: User ID (default: current user)
            filters: Dict of filters
            limit: Max results
            offset: Offset for pagination
        
        Returns:
            List of document records
        """
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        
        domain = []
        
        # Department access
        if user.nbs_department_ids:
            domain.append(('department_id', 'in', user.nbs_department_ids.ids))
        
        # Apply filters
        if filters:
            if filters.get('department_id'):
                domain.append(('department_id', '=', filters['department_id']))
            
            if filters.get('document_type_id'):
                domain.append(('document_type_id', '=', filters['document_type_id']))
            
            if filters.get('state'):
                domain.append(('state', '=', filters['state']))
            else:
                domain.append(('state', '=', 'active'))  # Default to active
            
            if filters.get('uploader_id'):
                domain.append(('uploader_id', '=', filters['uploader_id']))
        
        # Search
        documents = self.env['nbs.document'].search(
            domain,
            limit=limit,
            offset=offset,
            order='create_date desc'
        )
        
        # Filter by confidentiality level
        accessible_docs = []
        for doc in documents:
            if self._can_user_access_document(user, doc):
                accessible_docs.append(doc)
        
        return accessible_docs
    
    def _can_user_access_document(self, user, document):
        """Check if user can access document based on confidentiality"""
        is_admin = user.has_group('nbs_archive.group_nbs_admin')
        is_manager = user in document.department_id.manager_ids
        
        if is_admin:
            return True
        
        level = document.confidentiality_level
        
        if level == 'strict':
            return is_admin
        elif level == 'confidential':
            return is_manager or is_admin
        elif level in ['public', 'internal']:
            return user in document.department_id.user_ids
        
        return False


