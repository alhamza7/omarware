# -*- coding: utf-8 -*-

import logging
import base64
import json
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSDocumentController(http.Controller):
    """Document management controller"""
    
    @http.route('/api/documents', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_documents(self, department_id=None, document_type_id=None, status=None, search=None, page=1, per_page=20, **kwargs):
        """Get list of documents with filters"""
        try:
            if not ensure_jwt_user_id():
                return {
                    'success': False,
                    'error': 'Unauthorized',
                    'data': [],
                    'pagination': {
                        'total': 0,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': 0,
                    }
                }

            domain = []
            
            # Department filter
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            # Document type filter
            if document_type_id:
                domain.append(('document_type_id', '=', document_type_id))
            
            # Status filter (default to active only) - field is 'state' not 'status'
            if status:
                domain.append(('state', '=', status))
            else:
                domain.append(('state', '=', 'active'))
            
            # Search in name/title
            if search:
                domain.append(('name', 'ilike', search))
            
            # Get documents with department access check
            Document = request.env['nbs.document']
            documents = Document.search(domain, limit=per_page, offset=(page-1)*per_page, order='upload_date desc')
            total = Document.search_count(domain)
            
            return {
                'success': True,
                'data': [{
                    'id': doc.id,
                    'title': doc.name,
                    'department_id': doc.department_id.id,
                    'department_name': doc.department_id.name,
                    'document_type_id': doc.document_type_id.id,
                    'document_type_name': doc.document_type_id.name,
                    'uploader_id': doc.uploader_id.id,
                    'uploader_name': doc.uploader_id.name,
                    'upload_date': doc.upload_date.isoformat() if doc.upload_date else None,
                    'status': doc.state,
                    'confidentiality_level': doc.confidentiality_level,
                    'barcode': doc.barcode,
                    'file_name': doc.current_version_id.file_name if doc.current_version_id else None,
                    'file_size': doc.current_version_id.file_size if doc.current_version_id else 0,
                } for doc in documents],
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page,
                }
            }
        except AccessError as e:
            _logger.error(f'Access denied: {str(e)}')
            return {
                'success': False,
                'error': 'Access denied'
            }
        except Exception as e:
            _logger.error(f'Get documents error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'pagination': {
                    'total': 0,
                    'page': 1,
                    'per_page': 20,
                    'total_pages': 0,
                }
            }
    
    @http.route('/api/documents/<int:document_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_document(self, document_id, **kwargs):
        """Get single document details with versions"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # Get versions
            versions = document.version_ids.sorted(key=lambda v: v.version_number, reverse=True)
            current_v = document.current_version_id
            
            return {
                'success': True,
                'data': {
                    'id': document.id,
                    'title': document.name,
                    'department_id': document.department_id.id,
                    'department_name': document.department_id.name,
                    'document_type_id': document.document_type_id.id,
                    'document_type_name': document.document_type_id.name,
                    'uploader_id': document.uploader_id.id,
                    'uploader_name': document.uploader_id.name,
                    'upload_date': document.upload_date.isoformat() if document.upload_date else None,
                    'status': document.state,
                    'confidentiality_level': document.confidentiality_level,
                    'file_name': document.current_version_id.file_name if document.current_version_id else None,
                    'file_size': document.current_version_id.file_size if document.current_version_id else 0,
                    'barcode': document.barcode,
                    'is_locked': document.is_locked,
                    'ocr_status': document.ocr_status,
                    'ocr': {
                        'current_version_id': current_v.id if current_v else None,
                        'current_version_ocr_completed': bool(current_v.ocr_completed) if current_v else False,
                        'current_version_ocr_date': current_v.ocr_date.isoformat() if (current_v and current_v.ocr_date) else None,
                        # Send a safe preview only (avoid huge payloads)
                        'extracted_text_preview': (current_v.extracted_text or '')[:2000] if current_v else '',
                        'extracted_text_length': len(current_v.extracted_text or '') if current_v else 0,
                    },
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in document.tag_ids],
                    'versions': [{
                        'id': v.id,
                        'version_number': v.version_number,
                        'file_name': v.file_name,
                        'file_size': v.file_size,
                        'uploaded_by': v.uploader_id.name if v.uploader_id else None,
                        'upload_date': v.upload_date.isoformat() if v.upload_date else None,
                        'change_description': v.notes,
                        'ocr_completed': v.ocr_completed,
                        'ocr_date': v.ocr_date.isoformat() if v.ocr_date else None,
                    } for v in versions],
                }
            }
        except AccessError:
            return {
                'success': False,
                'error': 'Access denied'
            }
        except Exception as e:
            _logger.error(f'Get document error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/documents/upload', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def upload_document(self, **kwargs):
        """Upload new document via HTTP POST with JWT authentication"""
        try:
            # Parse JSON body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except:
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                })
            
            # Verify JWT authentication
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return request.make_json_response({
                    'success': False,
                    'error': 'Unauthorized - Missing token'
                })
            
            token = auth_header.split(' ')[1]
            jwt_service = request.env['nbs.jwt.service'].sudo()
            payload = jwt_service.verify_access_token(token)
            
            if not payload:
                return request.make_json_response({
                    'success': False,
                    'error': 'Unauthorized - Invalid token'
                })
            
            # Update request environment with authenticated user
            request.update_env(user=payload['user_id'])
            
            # Extract params from data
            department_id = data.get('department_id')
            document_type_id = data.get('document_type_id')
            title = data.get('title')
            file_data = data.get('file_data')
            file_name = data.get('file_name')
            confidentiality_level = data.get('confidentiality_level', 'internal')
            po_number = data.get('po_number')
            bl_number = data.get('bl_number')
            container_number = data.get('container_number')
            invoice_number = data.get('invoice_number')
            envoy_number = data.get('envoy_number')
            tags = data.get('tags')
            custom_fields = data.get('custom_fields')
            folder_id = data.get('folder_id')
            folder_ids = data.get('folder_ids')
            upload_kind = (data.get('upload_kind') or '').strip().lower()  # main|sub|attachment
            parent_document_id = data.get('parent_document_id')

            # Optional folder auto-create (main upload)
            create_folder = bool(data.get('create_folder'))
            folder_name = data.get('folder_name')
            folder_code = data.get('folder_code')
            folder_type = data.get('folder_type') or 'other'
            folder_description = data.get('folder_description')

            # Validate inputs
            if not all([department_id, document_type_id, title, file_data, file_name]):
                return request.make_json_response({
                    'success': False,
                    'error': 'Missing required fields'
                })
            
            # Create document
            Document = request.env['nbs.document']
            
            vals = {
                'department_id': department_id,
                'document_type_id': document_type_id,
                'name': title,
                'confidentiality_level': confidentiality_level,
                'uploader_id': request.env.user.id,
                'state': 'active',
                'is_locked': True,
            }

            # Store searchable reference numbers if provided
            if po_number:
                vals['po_number'] = po_number
            if bl_number:
                vals['bl_number'] = bl_number
            if container_number:
                vals['container_number'] = container_number
            if invoice_number:
                vals['invoice_number'] = invoice_number
            if envoy_number:
                vals['envoy_number'] = envoy_number
            
            # Add tags
            if tags:
                vals['tag_ids'] = [(6, 0, tags)]
            
            # Add custom fields
            if custom_fields:
                vals['custom_fields_data'] = json.dumps(custom_fields, ensure_ascii=False)

            # Link to folders if provided
            folder_ids_to_link = []
            if folder_ids and isinstance(folder_ids, list):
                folder_ids_to_link = [int(x) for x in folder_ids if x]
            elif folder_id:
                try:
                    folder_ids_to_link = [int(folder_id)]
                except Exception:
                    folder_ids_to_link = []

            # Enforce folder for sub/attachment
            if upload_kind in ('sub', 'attachment') and not folder_ids_to_link and not create_folder:
                return request.make_json_response({
                    'success': False,
                    'error': 'folder_id is required for sub/attachment uploads'
                }, status=400)

            # Apply parent / role flags
            if upload_kind in ('sub', 'attachment'):
                if parent_document_id:
                    try:
                        vals['parent_document_id'] = int(parent_document_id)
                    except Exception:
                        return request.make_json_response({'success': False, 'error': 'Invalid parent_document_id'}, status=400)
                vals['folder_role'] = 'attachment' if upload_kind == 'attachment' else 'sub'
                vals['is_attachment'] = True if upload_kind == 'attachment' else False
            elif upload_kind == 'main':
                vals['folder_role'] = 'main'
                vals['is_attachment'] = False

            if folder_ids_to_link:
                vals['folder_ids'] = [(6, 0, folder_ids_to_link)]
            
            document = Document.create(vals)

            # Auto-create folder for main uploads when requested
            created_folder = None
            if upload_kind == 'main' and create_folder:
                Folder = request.env['nbs.document.folder'].sudo()
                if not folder_code:
                    folder_code = f"F-{document.id}"
                if not folder_name:
                    folder_name = document.name

                created_folder = Folder.create({
                    'name': folder_name,
                    'code': folder_code,
                    'department_id': int(department_id),
                    'folder_type': folder_type,
                    'description': folder_description,
                    'state': 'active',
                    'main_document_id': document.id,
                    'document_ids': [(4, document.id)],
                })
                document.sudo().write({'folder_ids': [(4, created_folder.id)]})
            else:
                # If linked to folder(s) and upload is main, set main_document_id if empty
                if upload_kind == 'main' and folder_ids_to_link:
                    folders = request.env['nbs.document.folder'].sudo().browse(folder_ids_to_link)
                    for f in folders:
                        if not f.main_document_id:
                            f.write({'main_document_id': document.id})

            # Create initial version
            version = request.env['nbs.document.version'].create({
                'document_id': document.id,
                'version_number': 1,
                'file_data': file_data,
                'file_name': file_name,
                'uploader_id': request.env.user.id,
                'notes': 'Initial upload',
            })

            document.sudo().write({'current_version_id': version.id})

            # Auto OCR for supported files (pdf/images)
            try:
                fname = (file_name or '').lower()
                if any(fname.endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']):
                    request.env['nbs.ocr.service'].sudo()._process_document_async(document.id)
            except Exception as e:
                _logger.warning(f'OCR trigger failed for document {document.id}: {str(e)}')
            
            # Log audit (use sudo to bypass permission check)
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'upload',
                'document_id': document.id,
                'department_id': department_id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
            })
            
            # Create notification for managers
            self._notify_managers(document, 'upload')
            
            return request.make_json_response({
                'success': True,
                'data': {
                    'id': document.id,
                    'barcode': document.barcode,
                    'message': 'Document uploaded successfully',
                    'folder_id': created_folder.id if created_folder else None
                }
            })
        
        except ValidationError as e:
            _logger.error(f'Upload validation error: {str(e)}')
            return request.make_json_response({
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            _logger.error(f'Upload error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                'error': f'Failed to upload document: {str(e)}'
            })
    
    @http.route('/api/documents/<int:document_id>/download', type='http', auth='none', methods=['GET'], csrf=False)
    def download_document(self, document_id, version_id=None, **kwargs):
        """Download document or specific version"""
        try:
            if not ensure_jwt_user_id():
                return request.not_found()

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return request.not_found()
            
            # Log audit
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'download',
                'document_id': document.id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
            })
            
            # Get file data
            if version_id:
                version = request.env['nbs.document.version'].browse(int(version_id))
                if version.exists() and version.document_id.id == document_id:
                    file_data = version.file_data
                    file_name = version.file_name
                else:
                    return request.not_found()
            else:
                if not document.current_version_id:
                    return request.not_found()
                file_data = document.current_version_id.file_data
                file_name = document.current_version_id.file_name
            
            if not file_data:
                return request.not_found()
            
            # Return file
            return request.make_response(
                base64.b64decode(file_data),
                headers=[
                    ('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{file_name}"'),
                ]
            )
        
        except Exception as e:
            _logger.error(f'Download error: {str(e)}')
            return request.not_found()
    
    @http.route('/api/documents/<int:document_id>/versions', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_versions(self, document_id, **kwargs):
        """Get all versions of a document"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            versions = document.version_ids.sorted(key=lambda v: v.version_number, reverse=True)
            
            return {
                'success': True,
                'data': [{
                    'id': v.id,
                    'version_number': v.version_number,
                    'file_name': v.file_name,
                    'file_size': v.file_size,
                    'uploaded_by': v.uploader_id.name if v.uploader_id else None,
                    'upload_date': v.upload_date.isoformat() if v.upload_date else None,
                    'change_description': v.notes,
                } for v in versions]
            }
        except Exception as e:
            _logger.error(f'Get versions error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/documents/<int:document_id>/archive', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def archive_document(self, document_id, **kwargs):
        """Archive a document (soft delete)"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # Check if user is manager or admin
            user = request.env.user
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            if not (is_manager or is_admin):
                return {
                    'success': False,
                    'error': 'Only managers and admins can archive documents'
                }
            
            # Archive
            document.write({'state': 'archived'})
            
            # Log audit
            request.env['nbs.audit.log'].create({
                'user_id': user.id,
                'action': 'archive',
                'document_id': document.id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
            })
            
            return {
                'success': True,
                'message': 'Document archived successfully'
            }
        
        except Exception as e:
            _logger.error(f'Archive error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/documents/<int:document_id>/unarchive', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def unarchive_document(self, document_id, **kwargs):
        """Unarchive a document"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # Check permissions
            user = request.env.user
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            
            if not (is_manager or is_admin):
                return {
                    'success': False,
                    'error': 'Only managers and admins can unarchive documents'
                }
            
            document.write({'state': 'active'})
            
            # Log audit
            request.env['nbs.audit.log'].create({
                'user_id': user.id,
                'action': 'unarchive',
                'document_id': document.id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
            })
            
            return {
                'success': True,
                'message': 'Document unarchived successfully'
            }
        
        except Exception as e:
            _logger.error(f'Unarchive error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _notify_managers(self, document, action):
        """Create notifications for department managers"""
        try:
            # Get managers of the department
            managers = request.env['res.users'].search([
                ('group_ids', 'in', request.env.ref('nbs_archive.group_nbs_manager').id),
                ('group_ids', 'in', request.env.ref('nbs_archive.group_nbs_manager').id),
            ])
            
            # Create notifications
            Notification = request.env['nbs.notification']
            for manager in managers:
                Notification.create({
                    'user_id': manager.id,
                    'title': f'New document uploaded',
                    'message': f'{document.uploader_id.name} uploaded "{document.name}" in {document.department_id.name}',
                    'notification_type': 'upload',
                    'related_document_id': document.id,
                })
        except Exception as e:
            _logger.error(f'Notification error: {str(e)}')
