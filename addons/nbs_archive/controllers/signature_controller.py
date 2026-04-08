# -*- coding: utf-8 -*-

import logging
import json
import base64
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSSignatureController(http.Controller):
    """Signature request endpoints (print -> sign -> upload signed version)."""

    @http.route('/api/signatures', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_requests(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            state = kwargs.get('state')
            document_id = kwargs.get('document_id')
            page = int(kwargs.get('page', 1))
            per_page = int(kwargs.get('per_page', 20))

            domain = []
            if state:
                domain.append(('state', '=', state))
            if document_id:
                domain.append(('document_id', '=', int(document_id)))

            user = request.env.user
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            is_manager = user.has_group('nbs_archive.group_nbs_manager')

            # employees: only their requests or requests assigned to them as signer
            if not (is_admin or is_manager):
                domain = ['|', ('requester_id', '=', user.id), ('signer_id', '=', user.id)] + domain

            SR = request.env['nbs.signature.request']
            recs = SR.search(domain, limit=per_page, offset=(page - 1) * per_page, order='create_date desc')
            total = SR.search_count(domain)

            return {
                'success': True,
                'data': [{
                    'id': r.id,
                    'document_id': r.document_id.id,
                    'document_title': r.document_id.name,
                    'requester_id': r.requester_id.id,
                    'requester_name': r.requester_id.name,
                    'signer_id': r.signer_id.id,
                    'signer_name': r.signer_id.name,
                    'state': r.state,
                    'request_date': r.request_date.isoformat() if r.request_date else None,
                    'approval_date': r.approval_date.isoformat() if r.approval_date else None,
                    'signed_date': r.signed_date.isoformat() if r.signed_date else None,
                    'rejection_reason': r.rejection_reason,
                } for r in recs],
                'pagination': {'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            _logger.error(f'List signatures error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/signatures/create', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_request(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document_id = kwargs.get('document_id')
            signer_id = kwargs.get('signer_id')
            message = kwargs.get('message')

            # Employee-only (admins allowed). Managers/supervisors should not create signature requests.
            user = request.env.user
            if user.has_group('nbs_archive.group_nbs_manager') and not user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Only employees can create signature requests'}

            doc = request.env['nbs.document'].browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            signer = request.env['res.users'].browse(signer_id)
            if not signer.exists():
                return {'success': False, 'error': 'Signer not found'}

            # Create request
            sr = request.env['nbs.signature.request'].create({
                'document_id': doc.id,
                'requester_id': request.env.user.id,
                'signer_id': signer.id,
                'message': message or '',
                'state': 'pending',
            })

            # Notify signer
            request.env['nbs.notification'].sudo().create({
                'user_id': signer.id,
                'title': 'Signature Request Pending',
                'message': f'{request.env.user.name} requested signature for: {doc.name}',
                'notification_type': 'signature_request',
                'document_id': doc.id,
            })

            return {'success': True, 'data': {'id': sr.id}}
        except Exception as e:
            _logger.error(f'Create signature request error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/signatures/<int:request_id>/approve', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def approve_request(self, request_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            sr = request.env['nbs.signature.request'].browse(request_id)
            if not sr.exists():
                return {'success': False, 'error': 'Signature request not found'}

            token = sr.action_approve()
            return {'success': True, 'data': {'sign_token': token, 'expires_at': sr.token_expiry.isoformat() if sr.token_expiry else None}}
        except Exception as e:
            _logger.error(f'Approve signature request error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/signatures/<int:request_id>/reject', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def reject_request(self, request_id, rejection_reason=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            sr = request.env['nbs.signature.request'].browse(request_id)
            if not sr.exists():
                return {'success': False, 'error': 'Signature request not found'}

            sr.action_reject(rejection_reason)
            return {'success': True}
        except Exception as e:
            _logger.error(f'Reject signature request error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/signatures/<int:request_id>/upload-signed', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def upload_signed(self, request_id, file_data=None, file_name=None, sign_token=None, notes=None, **kwargs):
        """
        Upload signed file (print -> sign -> scan/upload).
        This creates a new document version and makes it the CURRENT version (A).
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            sr = request.env['nbs.signature.request'].browse(request_id)
            if not sr.exists():
                return {'success': False, 'error': 'Signature request not found'}

            if sr.state != 'approved':
                return {'success': False, 'error': f'Cannot upload signed file in state: {sr.state}'}

            if sr.token_used or not sr.sign_token or sr.sign_token != sign_token:
                return {'success': False, 'error': 'Invalid or already used sign token'}

            if sr.token_expiry and sr.token_expiry < request.env.cr.now():
                sr.sudo().write({'state': 'expired'})
                return {'success': False, 'error': 'Sign token expired'}

            # Only requester can upload the signed file (default behavior)
            if sr.requester_id.id != request.env.user.id and not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Only the requester can upload the signed file'}

            doc = sr.document_id
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            # Compute next version number
            last_version = doc.version_ids.sorted(key=lambda v: v.version_number, reverse=True)
            new_version_number = (last_version[0].version_number if last_version else 0) + 1

            version = request.env['nbs.document.version'].create({
                'document_id': doc.id,
                'version_number': new_version_number,
                'file_data': file_data,
                'file_name': file_name,
                'uploader_id': request.env.user.id,
                'notes': notes or 'Signed version upload',
            })

            # Ensure document is locked after signed upload
            doc.sudo().write({'is_locked': True})

            # Mark request as signed (and token used)
            sr.sudo().mark_signed(version)

            # Audit
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'signed_version_uploaded',
                'document_id': doc.id,
                'department_id': doc.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'details': f'SignatureRequest={sr.id}, Version={new_version_number}',
            })

            # Notify signer + requester
            if sr.signer_id:
                request.env['nbs.notification'].sudo().create({
                    'user_id': sr.signer_id.id,
                    'title': 'Signed File Uploaded',
                    'message': f'{request.env.user.name} uploaded the signed version for: {doc.name}',
                    'notification_type': 'signature_signed',
                    'document_id': doc.id,
                })
            request.env['nbs.notification'].sudo().create({
                'user_id': sr.requester_id.id,
                'title': 'Signed File Uploaded',
                'message': f'Signed version uploaded successfully for: {doc.name}',
                'notification_type': 'signature_signed',
                'document_id': doc.id,
            })

            return {
                'success': True,
                'data': {
                    'version_id': version.id,
                    'version_number': new_version_number,
                    'document_id': doc.id,
                }
            }
        except Exception as e:
            _logger.error(f'Upload signed error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}


