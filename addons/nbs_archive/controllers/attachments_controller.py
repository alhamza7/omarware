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

            atts = request.env['nbs.document.attachment'].search([('document_id', '=', doc.id)], order='create_date desc')
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
                data = kwargs or {}
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


