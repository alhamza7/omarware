# -*- coding: utf-8 -*-

import logging
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSAdminController(http.Controller):
    """Admin and management controller"""
    
    @http.route('/api/departments', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_departments(self, **kwargs):
        """Get list of all departments"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            departments = request.env['nbs.department'].search([('active', '=', True)])
            
            return {
                'success': True,
                'data': [{
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                } for dept in departments]
            }
        
        except Exception as e:
            _logger.error(f'Get departments error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/document-types', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_document_types(self, department_id=None, **kwargs):
        """Get list of document types"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = []
            
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            doc_types = request.env['nbs.document.type'].search(domain)
            
            return {
                'success': True,
                'data': [{
                    'id': dt.id,
                    'name': dt.name,
                    'code': dt.code,
                    'department_id': dt.department_id.id,
                    'department_name': dt.department_id.name,
                } for dt in doc_types]
            }
        
        except Exception as e:
            _logger.error(f'Get document types error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/tags', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_tags(self, **kwargs):
        """Get list of all tags"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            tags = request.env['nbs.document.tag'].search([])
            
            return {
                'success': True,
                'data': [{
                    'id': tag.id,
                    'name': tag.name,
                } for tag in tags]
            }
        
        except Exception as e:
            _logger.error(f'Get tags error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/stats/dashboard', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def dashboard_stats(self, **kwargs):
        """Get dashboard statistics"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'stats': {}}

            user = request.env.user
            
            # Total documents (accessible by user, excluding deleted)
            total_documents = request.env['nbs.document'].search_count([
                ('state', '=', 'active'),
                ('is_deleted', '=', False)
            ])
            
            # My uploaded documents
            my_documents = request.env['nbs.document'].search_count([
                ('uploader_id', '=', user.id),
                ('state', '=', 'active'),
                ('is_deleted', '=', False)
            ])
            
            # Pending approvals (if manager)
            pending_approvals = 0
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            if is_manager:
                pending_approvals = request.env['nbs.edit.request'].search_count([
                    ('state', '=', 'pending')
                ])
            
            # Recent uploads (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_uploads = request.env['nbs.document'].search_count([
                ('upload_date', '>=', week_ago),
                ('state', '=', 'active'),
                ('is_deleted', '=', False)
            ])
            
            # Unread notifications
            unread_notifications = request.env['nbs.notification'].search_count([
                ('user_id', '=', user.id),
                ('is_read', '=', False)
            ])
            
            # Documents by department (excluding deleted)
            departments = request.env['nbs.department'].search([('active', '=', True)])
            by_department = []
            for dept in departments:
                count = request.env['nbs.document'].search_count([
                    ('department_id', '=', dept.id),
                    ('state', '=', 'active'),
                    ('is_deleted', '=', False)
                ])
                if count > 0:  # Only include departments with documents
                    by_department.append({
                        'department': dept.name,
                        'count': count
                    })
            
            return {
                'success': True,
                'stats': {
                    'total_documents': total_documents,
                    'my_documents': my_documents,
                    'pending_ocr': 0,
                    'pending_approvals': pending_approvals,
                    'recent_uploads': recent_uploads,
                    'unread_notifications': unread_notifications,
                    'by_department': by_department,
                }
            }
        
        except Exception as e:
            _logger.error(f'Dashboard stats error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_documents': 0,
                    'my_documents': 0,
                    'pending_approvals': 0,
                    'recent_uploads': 0,
                }
            }

    @http.route('/api/users/managers', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_managers(self, **kwargs):
        """Get manager/supervisor users (for signer selection)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            department_id = kwargs.get('department_id')

            if department_id:
                dept = request.env['nbs.department'].browse(int(department_id))
                if dept.exists():
                    users = dept.manager_ids
                else:
                    users = request.env['res.users'].search([
                        ('group_ids', 'in', request.env.ref('nbs_archive.group_nbs_manager').id),
                    ])
            else:
                users = request.env['res.users'].search([
                    ('group_ids', 'in', request.env.ref('nbs_archive.group_nbs_manager').id),
                ])

            return {
                'success': True,
                'data': [{'id': u.id, 'name': u.name, 'login': u.login} for u in users]
            }
        except Exception as e:
            _logger.error(f'Get managers error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/audit-logs', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_audit_logs(self, document_id=None, folder_id=None, action=None, date_from=None, date_to=None, page=1, per_page=50, **kwargs):
        """
        Get audit logs (Admin only)
        
        Args:
            document_id: Filter by specific document
            folder_id: Filter by folder (includes folder logs + all document logs in that folder)
            action: Filter by action type
            date_from: Start date
            date_to: End date
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Check if user is admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {
                    'success': False,
                    'error': 'Access denied: Admin only'
                }
            
            domain = []

            # --- Filter by folder_id and/or document_id ---
            # When both are provided we treat them as independent constraints joined
            # with AND (the caller wants logs for that document AND for that folder).
            # When only folder_id is given we return all logs that touch the folder
            # (folder-level actions + every document inside it).
            if folder_id and document_id:
                # Specific document inside (or related to) a specific folder.
                # Return logs that match the document OR the folder-level actions,
                # i.e.  (document_id = Y  OR  folder_id = X)
                domain += ['|',
                           ('document_id', '=', document_id),
                           ('folder_id', '=', folder_id)]

            elif folder_id:
                # All logs for the folder: folder-level entries plus every
                # document that lives in it.
                folder_docs = request.env['nbs.document'].search([
                    ('folder_id', '=', folder_id)
                ])
                doc_ids_in_folder = folder_docs.ids

                if doc_ids_in_folder:
                    domain += ['|',
                               ('folder_id', '=', folder_id),
                               ('document_id', 'in', doc_ids_in_folder)]
                else:
                    # No documents in folder yet — only folder-level logs
                    domain.append(('folder_id', '=', folder_id))

            elif document_id:
                domain.append(('document_id', '=', document_id))
            
            if action:
                domain.append(('action', '=', action))
            
            if date_from:
                domain.append(('timestamp', '>=', date_from))
            
            if date_to:
                domain.append(('timestamp', '<=', date_to))
            
            AuditLog = request.env['nbs.audit.log']
            logs = AuditLog.search(domain, limit=per_page, offset=(page-1)*per_page, order='timestamp desc')
            total = AuditLog.search_count(domain)
            
            return {
                'success': True,
                'data': [{
                    'id': log.id,
                    'user_id': log.user_id.id,
                    'user_name': log.user_id.name,
                    'action': log.action,
                    'document_id': log.document_id.id if log.document_id else None,
                    'document_title': log.document_id.name if log.document_id else None,
                    'folder_id': log.folder_id.id if log.folder_id else None,
                    'folder_name': log.folder_id.name if log.folder_id else None,
                    'department_id': log.department_id.id if log.department_id else None,
                    'department_name': log.department_id.name if log.department_id else None,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'ip_address': log.ip_address,
                    'metadata': log.metadata,
                } for log in logs],
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                }
            }
        
        except Exception as e:
            _logger.error(f'Get audit logs error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
