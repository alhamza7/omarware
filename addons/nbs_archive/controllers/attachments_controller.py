# -*- coding: utf-8 -*-

import logging
import base64
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSAttachmentsController(http.Controller):
    """
    Demo parity: attachments list + add attachment + download/view.
    Uses nbs.document.attachment model.
    """

    @http.route('/api/documents/<int:document_id>/attachments', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_attachments(self, document_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            doc = request.env['nbs.document'].browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found', 'data': []}

            # Filter out soft-deleted attachments
            atts = request.env['nbs.document.attachment'].search([
                ('document_id', '=', doc.id),
                ('is_deleted', '=', False)
            ], order='create_date desc')
            return {
                'success': True,
                'data': [{
                    'id': a.id,
                    'document_id': a.document_id.id,
                    'name': a.name,
                    'description': a.description,
                    'file_name': a.file_name,
                    'file_size': a.file_size,
                    'file_type': a.file_type,
                    'uploader_id': a.uploader_id.id if a.uploader_id else None,
                    'uploader_name': a.uploader_id.name if a.uploader_id else None,
                    'upload_date': a.upload_date.isoformat() if a.upload_date else None,
                } for a in atts]
            }
        except Exception as e:
            _logger.error(f'List attachments error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e), 'data': []}

    @http.route('/api/documents/<int:document_id>/add-attachment', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def add_attachment(self, document_id, name=None, file_data=None, file_name=None, description=None, attachment_type='supporting', **kwargs):
        """
        JSON-RPC params:
          { name, description?, file_data(base64|dataurl), file_name, attachment_type? }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            doc = request.env['nbs.document'].browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            # Support both direct args (JSON-RPC params mapping) and legacy dict payloads
            if not (name and file_data and file_name):
                data = kwargs if isinstance(kwargs, dict) else {}
                if isinstance(data, list):
                    data = data[0] if data and isinstance(data[0], dict) else {}
                if not isinstance(data, dict):
                    data = {}
                name = name or data.get('name') or data.get('attachment_name') or data.get('file_name')
                description = description or data.get('description')
                file_data = file_data or data.get('file_data')
                file_name = file_name or data.get('file_name')
                attachment_type = attachment_type or data.get('attachment_type') or 'supporting'

            if not name or not file_data or not file_name:
                return {'success': False, 'error': 'name, file_data, file_name are required'}

            # Strip DataURL prefix if present
            if isinstance(file_data, str) and 'base64,' in file_data:
                file_data = file_data.split('base64,', 1)[1]

            size = 0
            try:
                size = len(base64.b64decode(file_data)) if file_data else 0
            except Exception:
                size = 0

            att = request.env['nbs.document.attachment'].create({
                'document_id': doc.id,
                'name': name,
                'description': description,
                'file_data': file_data,
                'file_name': file_name,
                'file_size': size,
                'attachment_type': attachment_type,
                'uploader_id': request.env.user.id,
            })

            return {'success': True, 'data': {'id': att.id, 'message': 'تم إضافة المرفق بنجاح'}}
        except Exception as e:
            _logger.error(f'Add attachment error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>/download', type='http', auth='none', methods=['GET'], csrf=False)
    def download_attachment(self, document_id, attachment_id, **kwargs):
        """Download attachment file"""
        try:
            if not ensure_jwt_user_id():
                return request.not_found()

            attachment = request.env['nbs.document.attachment'].browse(attachment_id)

            if not attachment.exists() or attachment.document_id.id != document_id:
                return request.not_found()

            return request.make_response(
                base64.b64decode(attachment.file_data),
                headers=[
                    ('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{attachment.file_name}"'),
                ]
            )
        except Exception as e:
            _logger.error(f'Download attachment error: {str(e)}', exc_info=True)
            return request.not_found()
    
    @http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>/update', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_attachment(self, document_id, attachment_id, name=None, description=None, 
                         file_data=None, file_name=None, **kwargs):
        """Update attachment"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            attachment = request.env['nbs.document.attachment'].browse(attachment_id)
            
            if not attachment.exists() or attachment.document_id.id != document_id:
                return {'success': False, 'error': 'Attachment not found'}

            # Check permission
            if not attachment.document_id.check_access_rights('write', raise_exception=False):
                return {'success': False, 'error': 'No permission to edit'}

            updates = {}
            
            if name:
                updates['name'] = name
            
            if description is not None:
                updates['description'] = description
            
            # If new file is uploaded
            if file_data and file_name:
                # Strip DataURL prefix if present
                if isinstance(file_data, str) and 'base64,' in file_data:
                    file_data = file_data.split('base64,', 1)[1]
                
                try:
                    size = len(base64.b64decode(file_data))
                    updates.update({
                        'file_data': file_data,
                        'file_name': file_name,
                        'file_size': size,
                    })
                except Exception as e:
                    return {'success': False, 'error': f'Invalid file data: {str(e)}'}
            
            if updates:
                attachment.write(updates)
                
                # Log activity (non-blocking)
                try:
                    request.env['nbs.audit.log'].sudo().create({
                        'action': 'attachment_updated',
                        'document_id': document_id,
                        'user_id': request.env.user.id,
                        'department_id': attachment.document_id.department_id.id,
                        'metadata': f'Updated attachment: {attachment.name}'
                    })
                except Exception:
                    pass  # non-blocking
            
            return {
                'success': True,
                'message': 'تم تحديث المرفق بنجاح',
                'data': {
                    'id': attachment.id,
                    'name': attachment.name,
                    'file_name': attachment.file_name,
                    'file_size': attachment.file_size
                }
            }
        except Exception as e:
            _logger.error(f'Update attachment error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>', 
                type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_attachment(self, document_id, attachment_id, reason=None, **kwargs):
        """Soft delete attachment"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            attachment = request.env['nbs.document.attachment'].browse(attachment_id)
            
            if not attachment.exists() or attachment.document_id.id != document_id:
                return request.make_json_response({'success': False, 'error': 'Not found'})

            # Check permission
            if not attachment.document_id.check_access_rights('write', raise_exception=False):
                return request.make_json_response({'success': False, 'error': 'No permission'})

            # Soft delete
            attachment.soft_delete(reason=reason)
            
            return request.make_json_response({
                'success': True,
                'message': 'تم نقل المرفق إلى سلة المحذوفات'
            })
        except Exception as e:
            _logger.error(f'Delete attachment error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
    
    @http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>/restore', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def restore_attachment(self, document_id, attachment_id, **kwargs):
        """Restore attachment from trash"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            attachment = request.env['nbs.document.attachment'].browse(attachment_id)
            
            if not attachment.exists() or attachment.document_id.id != document_id:
                return {'success': False, 'error': 'Not found'}

            if not attachment.is_deleted:
                return {'success': False, 'error': 'Attachment is not in trash'}

            attachment.restore()
            
            return {'success': True, 'message': 'تم استعادة المرفق بنجاح'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>/permanent', 
                type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def permanent_delete_attachment(self, document_id, attachment_id, **kwargs):
        """Permanently delete attachment (admin only)"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            # Check if admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({'success': False, 'error': 'Admin permission required'})

            attachment = request.env['nbs.document.attachment'].browse(attachment_id)
            
            if not attachment.exists() or attachment.document_id.id != document_id:
                return request.make_json_response({'success': False, 'error': 'Not found'})

            attachment.permanent_delete()
            
            return request.make_json_response({
                'success': True,
                'message': 'تم حذف المرفق نهائياً'
            })
        except Exception as e:
            return request.make_json_response({'success': False, 'error': str(e)})
    
    @http.route('/api/documents/<int:document_id>/attachments/multiple', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def upload_multiple_attachments(self, document_id, attachments, **kwargs):
        """
        Upload multiple attachments at once
        
        attachments: list of dicts with keys:
        - name: str
        - file_name: str
        - file_data: str (base64)
        - description: str (optional)
        - attachment_type: str (optional, default: 'supporting')
        
        Example:
        {
            "attachments": [
                {
                    "name": "Contract Page 1",
                    "file_name": "contract_p1.pdf",
                    "file_data": "base64_data...",
                    "description": "First page"
                },
                {
                    "name": "Contract Page 2",
                    "file_name": "contract_p2.pdf",
                    "file_data": "base64_data..."
                }
            ]
        }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {'success': False, 'error': 'Document not found'}

            # Check permission
            if not document.check_access_rights('write', raise_exception=False):
                return {'success': False, 'error': 'No permission to add attachments'}

            uploaded = []
            errors = []
            if not isinstance(attachments, list):
                attachments = [attachments] if isinstance(attachments, dict) else []
            for idx, att_info in enumerate(attachments):
                if not isinstance(att_info, dict):
                    errors.append(f"File {idx+1}: invalid format (expected dict)")
                    continue
                try:
                    # Strip DataURL prefix if present
                    file_data = att_info.get('file_data', '')
                    if isinstance(file_data, str) and 'base64,' in file_data:
                        file_data = file_data.split('base64,', 1)[1]
                    
                    # Validate
                    if not att_info.get('name'):
                        raise ValueError('Name is required')
                    if not att_info.get('file_name'):
                        raise ValueError('File name is required')
                    if not file_data:
                        raise ValueError('File data is required')
                    
                    # Create attachment
                    attachment = request.env['nbs.document.attachment'].create({
                        'document_id': document_id,
                        'name': att_info.get('name'),
                        'description': att_info.get('description', ''),
                        'file_data': file_data,
                        'file_name': att_info.get('file_name'),
                        'file_size': len(base64.b64decode(file_data)),
                        'attachment_type': att_info.get('attachment_type', 'supporting'),
                    })
                    
                    uploaded.append({
                        'id': attachment.id,
                        'name': attachment.name,
                        'file_name': attachment.file_name,
                        'file_size': attachment.file_size
                    })
                    
                except Exception as e:
                    error_msg = f"File {idx+1} ({att_info.get('file_name', 'unknown')}): {str(e)}"
                    errors.append(error_msg)
                    _logger.error(f"Multiple upload error: {error_msg}", exc_info=True)
            
            # Log activity (non-blocking)
            if uploaded:
                try:
                    request.env['nbs.audit.log'].sudo().create({
                        'action': 'multiple_attachments_upload',
                        'document_id': document_id,
                        'user_id': request.env.user.id,
                        'department_id': document.department_id.id,
                        'metadata': f'Uploaded {len(uploaded)} attachments. Failed: {len(errors)}'
                    })
                except Exception:
                    pass  # non-blocking: do not fail upload if audit log fails
            
            return {
                'success': True,
                'message': f'تم رفع {len(uploaded)} مرفق بنجاح',
                'data': {
                    'uploaded': uploaded,
                    'total': len(attachments),
                    'successful': len(uploaded),
                    'failed': len(errors),
                    'errors': errors
                }
            }
        except Exception as e:
            _logger.error(f'Upload multiple attachments error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}


