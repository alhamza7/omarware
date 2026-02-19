# -*- coding: utf-8 -*-

import logging
import base64
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSEditRequestController(http.Controller):
    """Edit request and approval controller"""
    
    @http.route('/api/edit-requests', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_edit_requests(self, state=None, document_id=None, page=1, per_page=20, **kwargs):
        """Get list of edit requests"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = []
            
            if state:
                domain.append(('state', '=', state))
            
            if document_id:
                domain.append(('document_id', '=', document_id))
            
            # Check user role
            user = request.env.user
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            # Regular users see only their requests
            if not (is_manager or is_admin):
                domain.append(('requester_id', '=', user.id))
            
            EditRequest = request.env['nbs.edit.request']
            requests_list = EditRequest.search(domain, limit=per_page, offset=(page-1)*per_page, order='request_date desc')
            total = EditRequest.search_count(domain)
            
            return {
                'success': True,
                'data': [{
                    'id': req.id,
                    'document_id': req.document_id.id,
                    'document_title': req.document_id.name,
                    'requester_id': req.requester_id.id,
                    'requester_name': req.requester_id.name,
                    'reason': req.reason,
                    'state': req.state,
                    'request_date': req.request_date.isoformat() if req.request_date else None,
                    'response_date': req.response_date.isoformat() if req.response_date else None,
                    'approver_id': req.approver_id.id if req.approver_id else None,
                    'approver_name': req.approver_id.name if req.approver_id else None,
                    'rejection_reason': req.rejection_reason,
                } for req in requests_list],
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                }
            }
        except Exception as e:
            _logger.error(f'Get edit requests error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/edit-requests/create', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_edit_request(self, document_id, reason, **kwargs):
        """Create new edit request"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not document_id or not reason:
                return {
                    'success': False,
                    'error': 'Document ID and reason are required'
                }
            
            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # Check if document is locked
            if not document.is_locked:
                return {
                    'success': False,
                    'error': 'Document is not locked'
                }
            
            # Check if there's already a pending request
            existing = request.env['nbs.edit.request'].search([
                ('document_id', '=', document_id),
                ('state', '=', 'pending')
            ])
            
            if existing:
                return {
                    'success': False,
                    'error': 'There is already a pending edit request for this document'
                }
            
            # Create edit request
            edit_request = request.env['nbs.edit.request'].create({
                'document_id': document_id,
                'requester_id': request.env.user.id,
                'reason': reason,
                'state': 'pending',
            })
            
            # Log audit
            request.env['nbs.audit.log'].create({
                'user_id': request.env.user.id,
                'action': 'edit_request_created',
                'document_id': document_id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'metadata': f'Request ID: {edit_request.id}',
            })
            
            # Notify managers
            self._notify_managers_edit_request(edit_request, 'created')
            
            return {
                'success': True,
                'data': {
                    'id': edit_request.id,
                    'message': 'Edit request created successfully'
                }
            }
        
        except Exception as e:
            _logger.error(f'Create edit request error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/edit-requests/<int:request_id>/approve', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def approve_edit_request(self, request_id, **kwargs):
        """Approve edit request (Manager/Admin only)"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            user = request.env.user
            
            # Check if user is manager or admin
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            if not (is_manager or is_admin):
                return {
                    'success': False,
                    'error': 'Only managers and admins can approve edit requests'
                }
            
            edit_request = request.env['nbs.edit.request'].browse(request_id)
            
            if not edit_request.exists():
                return {
                    'success': False,
                    'error': 'Edit request not found'
                }
            
            if edit_request.state != 'pending':
                return {
                    'success': False,
                    'error': f'Cannot approve request in state: {edit_request.state}'
                }
            
            # Approve the request
            edit_request.write({
                'state': 'approved',
                'approver_id': user.id,
            })
            
            # Generate one-time unlock token
            unlock_token = edit_request._generate_unlock_token()
            
            # Log audit
            request.env['nbs.audit.log'].create({
                'user_id': user.id,
                'action': 'edit_request_approved',
                'document_id': edit_request.document_id.id,
                'department_id': edit_request.document_id.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'metadata': f'Request ID: {request_id}',
            })
            
            # Notify requester
            request.env['nbs.notification'].create({
                'user_id': edit_request.requester_id.id,
                'title': 'Edit Request Approved',
                'message': f'Your edit request for "{edit_request.document_id.name}" has been approved by {user.name}',
                'notification_type': 'edit_approved',
                'related_document_id': edit_request.document_id.id,
            })
            
            return {
                'success': True,
                'data': {
                    'unlock_token': unlock_token,
                    'message': 'Edit request approved successfully'
                }
            }
        
        except Exception as e:
            _logger.error(f'Approve error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/edit-requests/<int:request_id>/reject', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def reject_edit_request(self, request_id, rejection_reason, **kwargs):
        """Reject edit request (Manager/Admin only)"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            user = request.env.user
            
            # Check if user is manager or admin
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            if not (is_manager or is_admin):
                return {
                    'success': False,
                    'error': 'Only managers and admins can reject edit requests'
                }
            
            edit_request = request.env['nbs.edit.request'].browse(request_id)
            
            if not edit_request.exists():
                return {
                    'success': False,
                    'error': 'Edit request not found'
                }
            
            if edit_request.state != 'pending':
                return {
                    'success': False,
                    'error': f'Cannot reject request in state: {edit_request.state}'
                }
            
            # Reject the request
            edit_request.write({
                'state': 'rejected',
                'approver_id': user.id,
                'rejection_reason': rejection_reason,
            })
            
            # Log audit
            request.env['nbs.audit.log'].create({
                'user_id': user.id,
                'action': 'edit_request_rejected',
                'document_id': edit_request.document_id.id,
                'department_id': edit_request.document_id.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'metadata': f'Request ID: {request_id}, Reason: {rejection_reason}',
            })
            
            # Notify requester
            request.env['nbs.notification'].create({
                'user_id': edit_request.requester_id.id,
                'title': 'Edit Request Rejected',
                'message': f'Your edit request for "{edit_request.document_id.name}" has been rejected by {user.name}. Reason: {rejection_reason}',
                'notification_type': 'edit_rejected',
                'related_document_id': edit_request.document_id.id,
            })
            
            return {
                'success': True,
                'message': 'Edit request rejected'
            }
        
        except Exception as e:
            _logger.error(f'Reject error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/documents/<int:document_id>/upload-version', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def upload_new_version(self, document_id, file_data, file_name, unlock_token=None, change_description=None, **kwargs):
        """Upload new version of document (unlock token validation DISABLED for development)"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # ===== UNLOCK TOKEN VALIDATION DISABLED =====
            # TODO: Re-enable for production by uncommenting below and removing bypass
            
            # # Find approved edit request with valid unlock token
            # edit_request = request.env['nbs.edit.request'].search([
            #     ('document_id', '=', document_id),
            #     ('state', '=', 'approved'),
            #     ('unlock_token', '=', unlock_token),
            #     ('token_used', '=', False),
            # ], limit=1)
            # 
            # if not edit_request:
            #     return {
            #         'success': False,
            #         'error': 'Invalid or expired unlock token'
            #     }
            # 
            # # Check if token belongs to the requester
            # if edit_request.requester_id.id != request.env.user.id:
            #     return {
            #         'success': False,
            #         'error': 'This unlock token does not belong to you'
            #     }
            
            # BYPASS: Allow upload without validation
            edit_request = None  # No edit request needed
            
            # Get current version number
            last_version = document.version_ids.sorted(key=lambda v: v.version_number, reverse=True)
            new_version_number = (last_version[0].version_number if last_version else 0) + 1
            
            # Create new version
            version = request.env['nbs.document.version'].create({
                'document_id': document_id,
                'version_number': new_version_number,
                'file_data': file_data,
                'file_name': file_name,
                'uploader_id': request.env.user.id,
                'notes': change_description or 'New version uploaded',
            })
            
            # Update document current version (keep unlocked for development)
            document.write({
                'current_version_id': version.id,
                'is_locked': False,  # Keep unlocked for development
            })
            
            # Invalidate cache and refresh document to ensure current_version_id is updated
            document.invalidate_recordset(['current_version_id'])
            document = request.env['nbs.document'].browse(document_id)
            
            # # Mark token as used and complete the edit request (DISABLED)
            # if edit_request:
            #     edit_request.write({
            #         'token_used': True,
            #         'state': 'completed',
            #     })
            
            # Log audit (use sudo to bypass permission checks)
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'new_version_uploaded',
                'document_id': document_id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'metadata': f'Version {new_version_number} (direct upload - no edit request)',
            })
            
            # # Notify relevant users (DISABLED - no edit request)
            # if edit_request and edit_request.approver_id:
            #     request.env['nbs.notification'].create({
            #         'user_id': edit_request.approver_id.id,
            #         'title': 'New Version Uploaded',
            #         'message': f'{request.env.user.name} uploaded version {new_version_number} of "{document.name}"',
            #         'notification_type': 'new_version',
            #         'related_document_id': document_id,
            #     })
            
            # Refresh document to get updated current_version_id
            document = request.env['nbs.document'].browse(document_id)
            
            return {
                'success': True,
                'data': {
                    'version_id': version.id,
                    'version_number': new_version_number,
                    'file_name': file_name,
                    'current_version_id': document.current_version_id.id if document.current_version_id else None,
                    'upload_date': version.upload_date.isoformat() if version.upload_date else None,
                    'timestamp': fields.Datetime.now().isoformat(),  # For cache busting
                    'message': f'Version {new_version_number} uploaded successfully (unlock validation disabled for development)'
                }
            }
        
        except Exception as e:
            _logger.error(f'Upload version error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/edit-requests/pending-approvals', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_pending_approvals(self, **kwargs):
        """Get pending edit requests for managers"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            user = request.env.user
            
            # Check if user is manager or admin
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            if not (is_manager or is_admin):
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Get pending requests
            pending_requests = request.env['nbs.edit.request'].search([
                ('state', '=', 'pending')
            ], order='request_date asc')
            
            return {
                'success': True,
                'data': [{
                    'id': req.id,
                    'document_id': req.document_id.id,
                    'document_title': req.document_id.name,
                    'requester_id': req.requester_id.id,
                    'requester_name': req.requester_id.name,
                    'reason': req.reason,
                    'request_date': req.request_date.isoformat() if req.request_date else None,
                    'department_name': req.document_id.department_id.name,
                } for req in pending_requests]
            }
        
        except Exception as e:
            _logger.error(f'Get pending approvals error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _notify_managers_edit_request(self, edit_request, action):
        """Notify managers about edit request"""
        try:
            managers = request.env['res.users'].search([
                ('group_ids', 'in', request.env.ref('nbs_archive.group_nbs_manager').id),
            ])
            
            Notification = request.env['nbs.notification']
            for manager in managers:
                Notification.create({
                    'user_id': manager.id,
                    'title': 'Edit Request Pending',
                    'message': f'{edit_request.requester_id.name} requested to edit "{edit_request.document_id.name}"',
                    'notification_type': 'edit_request',
                    'related_document_id': edit_request.document_id.id,
                })
        except Exception as e:
            _logger.error(f'Notification error: {str(e)}')
