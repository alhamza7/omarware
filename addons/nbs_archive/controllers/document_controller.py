# -*- coding: utf-8 -*-

import logging
import base64
import json
import traceback
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


def format_error_response(error, include_traceback=True):
    """Format error response with diagnostic information for frontend debugging"""
    import sys
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
    }
    
    if include_traceback:
        try:
            tb_lines = traceback.format_exc().split('\n')
            # Get last file/line from traceback
            for line in reversed(tb_lines):
                if 'File "' in line and 'line' in line:
                    error_data['error_location'] = line.strip()
                    break
            # Full traceback (limit to last 10 lines)
            error_data['traceback'] = '\n'.join(tb_lines[-10:])
        except Exception:
            pass
    
    return error_data


class NBSDocumentController(http.Controller):
    """Document management controller"""
    
    @http.route('/api/documents', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_documents(self, department_id=None, document_type_id=None, status=None, search=None,
                      company_id=None, from_date=None, to_date=None, page=1, per_page=20, **kwargs):
        """Get list of documents with filters (department, type, status, company/brand, search, date range).
        
        Date range filters (both optional, checked against upload_date only):
            from_date: ISO 8601 string — include documents uploaded on or after this date (e.g. "2026-01-01" or "2026-01-01T00:00:00")
            to_date:   ISO 8601 string — include documents uploaded on or before this date (e.g. "2026-12-31" or "2026-12-31T23:59:59")
        """
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
            
            # Company/Brand filter
            if company_id:
                domain.append(('company_id', '=', company_id))
            
            # Status filter - default returns all statuses (draft, active, archived, trash)
            if status:
                domain.append(('state', '=', status))
            
            # Date range filter — checked against upload_date (creation date) only
            if from_date:
                try:
                    # Accept "YYYY-MM-DD" or full ISO datetime; normalise to datetime for ORM
                    if 'T' not in str(from_date) and ' ' not in str(from_date):
                        from_date = f"{from_date} 00:00:00"
                    domain.append(('upload_date', '>=', from_date))
                except Exception:
                    return {'success': False, 'error': 'Invalid from_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'}

            if to_date:
                try:
                    if 'T' not in str(to_date) and ' ' not in str(to_date):
                        to_date = f"{to_date} 23:59:59"
                    domain.append(('upload_date', '<=', to_date))
                except Exception:
                    return {'success': False, 'error': 'Invalid to_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'}

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
                    'po_number': doc.po_number,
                    'bl_number': doc.bl_number,
                    'container_number': doc.container_number,
                    'invoice_number': doc.invoice_number,
                    'envoy_number': doc.envoy_number,
                    'file_name': doc.current_version_id.file_name if doc.current_version_id else None,
                    'file_size': doc.current_version_id.file_size if doc.current_version_id else 0,
                    'folder_id': doc.folder_id.id if doc.folder_id else (doc.folder_ids[0].id if doc.folder_ids else None),
                    'folder_name': doc.folder_id.name if doc.folder_id else (doc.folder_ids[0].name if doc.folder_ids else None),
                    'parent_folder_id': doc.folder_id.id if doc.folder_id else (doc.folder_ids[0].id if doc.folder_ids else None),
                    'parent_folder_name': doc.folder_id.name if doc.folder_id else (doc.folder_ids[0].name if doc.folder_ids else None),
                    'company_id': doc.company_id.id if doc.company_id else None,
                    'company_name': doc.company_id.name if doc.company_id else None,
                    'parent_document_id': doc.parent_document_id.id if doc.parent_document_id else None,
                    'is_main_document': (doc.folder_role == 'main'),
                    'document_role': doc.folder_role or 'other',
                    'relation_type': 'attachment' if doc.folder_role == 'attachment' or (doc.parent_document_id and doc.is_attachment) else ('secondary_document' if doc.folder_role == 'sub' or doc.parent_document_id else ('main' if doc.folder_role == 'main' else 'other')),
                    'note_count': doc.note_count,
                    'last_modified': doc.last_modified.isoformat() if doc.last_modified else None,
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
    
    @http.route('/api/documents/trash', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_trash_documents(self, department_id=None, document_type_id=None, search=None,
                            from_date=None, to_date=None, page=1, per_page=20, **kwargs):
        """Get trashed documents with optional filters and pagination"""
        try:
            if not ensure_jwt_user_id():
                return {
                    'success': False,
                    'error': 'Unauthorized',
                    'data': [],
                    'pagination': {'total': 0, 'page': page, 'per_page': per_page, 'total_pages': 0}
                }

            domain = [('state', '=', 'trash'), ('is_deleted', '=', True)]

            if department_id:
                domain.append(('department_id', '=', department_id))
            if document_type_id:
                domain.append(('document_type_id', '=', document_type_id))
            if search:
                domain.append(('name', 'ilike', search))
            if from_date:
                domain.append(('deleted_at', '>=', from_date))
            if to_date:
                domain.append(('deleted_at', '<=', to_date))

            Document = request.env['nbs.document'].sudo()
            per_page = int(per_page)
            page     = int(page)
            offset   = (page - 1) * per_page
            documents = Document.search(domain, limit=per_page, offset=offset, order='deleted_at desc')
            total     = Document.search_count(domain)

            result = []
            for doc in documents:
                result.append({
                    'id':                  doc.id,
                    'name':                doc.name,
                    'title':               doc.name,
                    'document_number':     getattr(doc, 'document_number', None) or doc.barcode,
                    'department_id':       doc.department_id.id,
                    'department_name':     doc.department_id.name,
                    'document_type_id':    doc.document_type_id.id if doc.document_type_id else None,
                    'document_type_name':  doc.document_type_id.name if doc.document_type_id else None,
                    'uploader_id':         doc.uploader_id.id if doc.uploader_id else None,
                    'uploader_name':       doc.uploader_id.name if doc.uploader_id else None,
                    'upload_date':         doc.upload_date.isoformat() if doc.upload_date else None,
                    'deleted_at':          doc.deleted_at.isoformat() if doc.deleted_at else None,
                    'deleted_by':          doc.deleted_by.name if doc.deleted_by else None,
                    'deletion_reason':     doc.deletion_reason,
                    'restore_deadline':    doc.restore_deadline.isoformat() if doc.restore_deadline else None,
                    'state_before_trash':  doc.state_before_trash,
                    'status':              doc.state,
                    'confidentiality_level': doc.confidentiality_level,
                    'barcode':             doc.barcode,
                    'file_name':           doc.current_version_id.file_name if doc.current_version_id else None,
                    'file_size':           doc.current_version_id.file_size if doc.current_version_id else 0,
                    'is_main_document':    (doc.folder_role == 'main'),
                    'document_role':       doc.folder_role or 'other',
                })

            return {
                'success': True,
                'data':    result,
                'count':   len(result),
                'pagination': {
                    'total':       total,
                    'page':        page,
                    'per_page':    per_page,
                    'total_pages': (total + per_page - 1) // per_page if per_page else 1,
                },
            }
        except Exception as e:
            _logger.error('get_trash_documents error: %s', e, exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'pagination': {'total': 0, 'page': 1, 'per_page': 20, 'total_pages': 0}
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
                    'po_number': document.po_number,
                    'bl_number': document.bl_number,
                    'container_number': document.container_number,
                    'invoice_number': document.invoice_number,
                    'envoy_number': document.envoy_number,
                    'folder_id': document.folder_id.id if document.folder_id else (document.folder_ids[0].id if document.folder_ids else None),
                    'folder_name': document.folder_id.name if document.folder_id else (document.folder_ids[0].name if document.folder_ids else None),
                    'parent_folder_id': document.folder_id.id if document.folder_id else (document.folder_ids[0].id if document.folder_ids else None),
                    'parent_folder_name': document.folder_id.name if document.folder_id else (document.folder_ids[0].name if document.folder_ids else None),
                    'company_id': document.company_id.id if document.company_id else None,
                    'company_name': document.company_id.name if document.company_id else None,
                    'parent_document_id': document.parent_document_id.id if document.parent_document_id else None,
                    'is_main_document': (document.folder_role == 'main'),
                    'document_role': document.folder_role or 'other',
                    'relation_type': 'attachment' if document.folder_role == 'attachment' or (document.parent_document_id and document.is_attachment) else ('secondary_document' if document.folder_role == 'sub' or document.parent_document_id else ('main' if document.folder_role == 'main' else 'other')),
                    'note_count': document.note_count,
                    'last_modified': document.last_modified.isoformat() if document.last_modified else None,
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
            # Parse JSON body (must be a dict; if list, take first element)
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except Exception:
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                })
            if isinstance(data, list):
                data = data[0] if data and isinstance(data[0], dict) else {}
            if not isinstance(data, dict):
                return request.make_json_response({
                    'success': False,
                    'error': 'Request body must be a JSON object'
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
            folder_company_id = data.get('company_id')  # For auto-created folder

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
            else:
                # If upload_kind not specified, determine based on folder and parent
                if create_folder:
                    # Creating new folder = main document
                    vals['folder_role'] = 'main'
                    vals['is_attachment'] = False
                elif parent_document_id:
                    # Has parent = secondary document
                    vals['folder_role'] = 'sub'
                    vals['is_attachment'] = False
                    try:
                        vals['parent_document_id'] = int(parent_document_id)
                    except Exception:
                        return request.make_json_response({'success': False, 'error': 'Invalid parent_document_id'}, status=400)
                elif folder_ids_to_link:
                    # Adding to existing folder - check if folder already has a main document
                    existing_main = Document.search_count([
                        ('folder_id', 'in', folder_ids_to_link),
                        ('folder_role', '=', 'main'),
                        ('is_deleted', '=', False)
                    ])
                    if existing_main > 0:
                        # Folder has main doc - this is a secondary document
                        vals['folder_role'] = 'sub'
                    else:
                        # No main doc - this becomes the main document
                        vals['folder_role'] = 'main'
                    vals['is_attachment'] = False
                else:
                    # Standalone document (not in folder system)
                    vals['folder_role'] = 'other'
                    vals['is_attachment'] = False

            if folder_ids_to_link:
                vals['folder_ids'] = [(6, 0, folder_ids_to_link)]
                # IMPORTANT: Also set folder_id (Many2one) for company_id inheritance
                vals['folder_id'] = folder_ids_to_link[0]
            
            document = Document.create(vals)

            # Auto-create folder for main uploads when requested
            created_folder = None
            if upload_kind == 'main' and create_folder:
                Folder = request.env['nbs.document.folder'].sudo()
                if not folder_code:
                    folder_code = f"F-{document.id}"
                if not folder_name:
                    folder_name = document.name

                folder_vals = {
                    'name': folder_name,
                    'code': folder_code,
                    'department_id': int(department_id),
                    'description': folder_description,
                    'owner_id': request.env.user.id,
                }
                # Set company_id for auto-created folder if provided
                if folder_company_id:
                    folder_vals['company_id'] = int(folder_company_id)
                
                created_folder = Folder.create(folder_vals)
                # Link document to folder (both Many2one and Many2many)
                document.sudo().write({
                    'folder_id': created_folder.id,  # Set main folder (for company_id inheritance)
                    'folder_ids': [(4, created_folder.id)]  # Add to Many2many
                })

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
            
            # Get folder information for response
            folder_info = None
            folder_ids_info = []
            if created_folder:
                folder_info = {
                    'id': created_folder.id,
                    'name': created_folder.name,
                    'code': created_folder.code
                }
                folder_ids_info = [folder_info]
            elif document.folder_ids:
                folder_ids_info = [{
                    'id': f.id,
                    'name': f.name,
                    'code': f.code
                } for f in document.folder_ids]
                folder_info = folder_ids_info[0] if folder_ids_info else None
            
            return request.make_json_response({
                'success': True,
                'data': {
                    'id': document.id,
                    'barcode': document.barcode,
                    'message': 'Document uploaded successfully',
                    'folder_id': folder_info['id'] if folder_info else None,
                    'folder_name': folder_info['name'] if folder_info else None,
                    'parent_folder_id': folder_info['id'] if folder_info else None,
                    'parent_folder_name': folder_info['name'] if folder_info else None,
                    'folder': folder_info,
                    'folders': folder_ids_info
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
    def download_document(self, document_id, version_id=None, preview=None, **kwargs):
        """
        Download or preview a document version.

        Query parameters:
          version_id  int   – specific version (defaults to current)
          preview     1|0   – if "1", serve inline so the browser can render PDFs
          token       str   – JWT bearer token (use when Authorization header
                              cannot be sent, e.g. browser <iframe>/<embed>)

        Large files are streamed directly from the Odoo filestore — no base64
        copy is ever loaded into Python memory.
        """
        import os
        import mimetypes
        import werkzeug.wrappers

        try:
            if not ensure_jwt_user_id():
                return request.make_response(
                    'Unauthorized', status=401,
                    headers=[('Content-Type', 'text/plain')],
                )

            env = request.env
            document = env['nbs.document'].sudo().browse(document_id)
            if not document.exists():
                return request.not_found()

            # ── Audit log ────────────────────────────────────────────────────
            try:
                env['nbs.audit.log'].sudo().create({
                    'user_id':       env.user.id,
                    'action':        'download',
                    'document_id':   document.id,
                    'department_id': document.department_id.id,
                    'ip_address':    request.httprequest.remote_addr,
                    'user_agent':    request.httprequest.headers.get('User-Agent', ''),
                })
            except Exception:
                pass  # audit failure must never block the download

            # ── Resolve version ───────────────────────────────────────────────
            if version_id:
                version = env['nbs.document.version'].sudo().browse(int(version_id))
                if not version.exists() or version.document_id.id != document_id:
                    return request.not_found()
            else:
                version = document.current_version_id
                if not version:
                    return request.not_found()

            file_name = version.file_name or f'document_{document_id}'

            # ── MIME type and disposition ────────────────────────────────────
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            is_preview = str(preview or '').lower() in ('1', 'true', 'yes')
            if is_preview:
                disposition = f'inline; filename="{file_name}"'
                # Keep the detected mime type so the browser renders it
            else:
                disposition = f'attachment; filename="{file_name}"'

            # ── Try streaming directly from filestore ────────────────────────
            # This avoids loading any base64 into memory — peak RAM = 0 extra.
            IrAttachment = env['ir.attachment'].sudo()
            attachment = IrAttachment.search([
                ('res_model', '=', 'nbs.document.version'),
                ('res_field', '=', 'file_data'),
                ('res_id',    '=', version.id),
            ], limit=1)

            if attachment and attachment.store_fname:
                full_path = IrAttachment._full_path(attachment.store_fname)
                if os.path.isfile(full_path):
                    file_size = os.path.getsize(full_path)
                    response = werkzeug.wrappers.Response(
                        response=open(full_path, 'rb'),
                        status=200,
                        direct_passthrough=True,
                    )
                    response.headers['Content-Type']        = mime_type
                    response.headers['Content-Disposition'] = disposition
                    response.headers['Content-Length']      = str(file_size)
                    response.headers['Cache-Control']       = 'private, max-age=3600'
                    response.headers['Accept-Ranges']       = 'bytes'
                    return response

            # ── Fallback: read raw bytes (attachment.raw handles filestore) ──
            if attachment and attachment.raw:
                raw_bytes = attachment.raw
            elif version.file_data:
                raw_bytes = base64.b64decode(version.file_data)
            else:
                return request.not_found()

            return request.make_response(
                raw_bytes,
                headers=[
                    ('Content-Type',        mime_type),
                    ('Content-Disposition', disposition),
                    ('Content-Length',      str(len(raw_bytes))),
                    ('Cache-Control',       'private, max-age=3600'),
                ],
            )

        except Exception as exc:
            _logger.error('Download error doc=%s ver=%s: %s', document_id, version_id, exc, exc_info=True)
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
    
    @http.route('/api/documents/<int:document_id>/update', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_document(self, document_id, **kwargs):
        """Update document metadata"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})
            
            # Parse JSON body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                
                # Handle JSON-RPC format (extract params if present)
                if isinstance(data, dict) and 'params' in data:
                    data = data['params']
                
            except Exception as e:
                _logger.error(f'JSON parse error: {str(e)}')
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                })
            
            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return request.make_json_response({
                    'success': False,
                    'error': 'Document not found'
                })
            
            # Build update values
            vals = {}
            
            # Log received data for debugging
            _logger.info(f'[UPDATE] Document {document_id} - Received data: {data}')
            
            # Allow updating these fields
            # Accept both 'name' and 'title' for document name
            if 'name' in data:
                vals['name'] = data['name']
            elif 'title' in data:
                vals['name'] = data['title']
            
            if 'confidentiality_level' in data:
                vals['confidentiality_level'] = data['confidentiality_level']
            if 'po_number' in data:
                vals['po_number'] = data['po_number']
            if 'bl_number' in data:
                vals['bl_number'] = data['bl_number']
            if 'container_number' in data:
                vals['container_number'] = data['container_number']
            if 'invoice_number' in data:
                vals['invoice_number'] = data['invoice_number']
            if 'envoy_number' in data:
                vals['envoy_number'] = data['envoy_number']
            if 'custom_fields' in data:
                vals['custom_fields_data'] = json.dumps(data['custom_fields'], ensure_ascii=False)
            
            # Update folder if provided
            if 'folder_id' in data:
                if data['folder_id']:
                    vals['folder_id'] = data['folder_id']
                    # Also update Many2many relation
                    vals['folder_ids'] = [(6, 0, [data['folder_id']])]
                else:
                    vals['folder_id'] = False
                    vals['folder_ids'] = [(5, 0, 0)]  # Remove all folders
            
            # Update tags if provided
            if 'tag_ids' in data:
                vals['tag_ids'] = [(6, 0, data['tag_ids'])]
            
            _logger.info(f'[UPDATE] Document {document_id} - Update vals: {vals}')
            
            if vals:
                document.write(vals)
                _logger.info(f'[UPDATE] Document {document_id} - Write completed')
                # Invalidate cache and refresh document to get updated values
                document.invalidate_recordset()
                # Re-browse to get fresh data from database
                document = request.env['nbs.document'].browse(document_id)
                _logger.info(f'[UPDATE] Document {document_id} - After refresh: name={document.name}, po={document.po_number}')
            else:
                _logger.warning(f'[UPDATE] Document {document_id} - No values to update!')
            
            # Log audit
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'document_updated',
                'document_id': document.id,
                'department_id': document.department_id.id,
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', ''),
                'metadata': json.dumps(vals, ensure_ascii=False)
            })
            
            # Return full document data
            return request.make_json_response({
                'success': True,
                'message': 'Document updated successfully',
                'data': {
                    'id': document.id,
                    'title': document.name,
                    'name': document.name,
                    'department_id': document.department_id.id,
                    'department_name': document.department_id.name,
                    'document_type_id': document.document_type_id.id,
                    'document_type_name': document.document_type_id.name,
                    'confidentiality_level': document.confidentiality_level,
                    'folder_id': document.folder_id.id if document.folder_id else (document.folder_ids[0].id if document.folder_ids else None),
                    'folder_name': document.folder_id.name if document.folder_id else (document.folder_ids[0].name if document.folder_ids else None),
                    'parent_folder_id': document.folder_id.id if document.folder_id else (document.folder_ids[0].id if document.folder_ids else None),
                    'parent_folder_name': document.folder_id.name if document.folder_id else (document.folder_ids[0].name if document.folder_ids else None),
                    'barcode': document.barcode,
                    'po_number': document.po_number,
                    'bl_number': document.bl_number,
                    'container_number': document.container_number,
                    'invoice_number': document.invoice_number,
                    'envoy_number': document.envoy_number,
                    'is_main_document': (document.folder_role == 'main'),
                    'document_role': document.folder_role or 'other',
                    'relation_type': 'attachment' if document.folder_role == 'attachment' or (document.parent_document_id and document.is_attachment) else ('secondary_document' if document.folder_role == 'sub' or document.parent_document_id else ('main' if document.folder_role == 'main' else 'other')),
                }
            })
            
        except Exception as e:
            _logger.error(f'Update document error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                'error': str(e)
            })
    
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
            
            # Log audit (non-blocking: do not fail response if audit create fails)
            try:
                request.env['nbs.audit.log'].sudo().create({
                    'user_id': user.id,
                    'action': 'archive',
                    'document_id': document.id,
                    'department_id': document.department_id.id,
                    'ip_address': request.httprequest.remote_addr or '',
                    'user_agent': (request.httprequest.headers.get('User-Agent') or '')[:4095],
                })
            except Exception as audit_e:
                _logger.warning('Archive audit log failed (non-blocking): %s', audit_e)
            
            return {
                'success': True,
                'message': 'Document archived successfully'
            }
        
        except Exception as e:
            _logger.error(f'Archive error: {str(e)}')
            return {
                'success': False,
                **format_error_response(e)
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
            
            # Log audit (non-blocking: do not fail response if audit create fails)
            try:
                request.env['nbs.audit.log'].sudo().create({
                    'user_id': user.id,
                    'action': 'unarchive',
                    'document_id': document.id,
                    'department_id': document.department_id.id,
                    'ip_address': request.httprequest.remote_addr or '',
                    'user_agent': (request.httprequest.headers.get('User-Agent') or '')[:4095],
                })
            except Exception as audit_e:
                _logger.warning('Unarchive audit log failed (non-blocking): %s', audit_e)
            
            return {
                'success': True,
                'message': 'Document unarchived successfully'
            }
        
        except Exception as e:
            _logger.error(f'Unarchive error: {str(e)}')
            return {
                'success': False,
                **format_error_response(e)
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
            Notification = request.env['nbs.notification'].sudo()
            for manager in managers:
                Notification.create({
                    'user_id': manager.id,
                    'title': f'New document uploaded',
                    'message': f'{document.uploader_id.name} uploaded "{document.name}" in {document.department_id.name}',
                    'notification_type': 'upload',
                    'document_id': document.id,
                })
        except Exception as e:
            _logger.error(f'Notification error: {str(e)}')
    
    # ==================== SOFT DELETE APIS ====================
    
    @http.route('/api/documents/<int:document_id>/trash', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def move_to_trash(self, document_id, reason=None, **kwargs):
        """Soft delete - move document to trash"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {'success': False, 'error': 'Document not found'}

            # Check permission
            if not document.check_access_rights('write', raise_exception=False):
                return {'success': False, 'error': 'No permission to delete document'}

            # Soft delete
            document.soft_delete(reason=reason)
            
            return {
                'success': True,
                'message': 'تم نقل المستند إلى سلة المحذوفات',
                'data': {
                    'restore_deadline': document.restore_deadline.isoformat() if document.restore_deadline else None
                }
            }
        except Exception as e:
            _logger.error(f'Move to trash error: {str(e)}', exc_info=True)
            return {'success': False, **format_error_response(e)}
    
    @http.route('/api/documents/<int:document_id>/restore', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def restore_from_trash(self, document_id, **kwargs):
        """
        Restore single document from trash.
        For batch restore of multiple documents, use POST /api/documents/restore with {"ids": [...]}.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {'success': False, 'error': 'Document not found'}

            if not document.is_deleted:
                return {'success': False, 'error': 'Document is not in trash'}

            # Restore
            document.restore_from_trash()
            
            return {
                'success': True,
                'message': 'تم استعادة المستند بنجاح',
                'data': {
                    'state': document.state
                }
            }
        except Exception as e:
            _logger.error(f'Restore from trash error: {str(e)}', exc_info=True)
            return {'success': False, **format_error_response(e)}
    
    @http.route('/api/documents/restore', 
                type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def restore_batch(self, **kwargs):
        """
        Unified endpoint for single or batch restore from trash.
        
        Request body: {"ids": [1, 2, 3]}
        Response: {"restored": [1, 2], "failed": [3]}
        
        Continues processing all IDs even if some fail.
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)

            # Parse JSON body
            try:
                raw_body = request.httprequest.get_data(as_text=True)
                if not raw_body:
                    return request.make_json_response({
                        'success': False,
                        'error': 'Request body is required'
                    }, status=400)
                
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                }, status=400)
            
            # Validate ids field
            if 'ids' not in body:
                return request.make_json_response({
                    'success': False,
                    'error': 'Field "ids" is required in request body'
                }, status=400)
            
            ids = body.get('ids')
            
            # Validate ids is a list
            if not isinstance(ids, list):
                return request.make_json_response({
                    'success': False,
                    'error': '"ids" must be an array'
                }, status=400)
            
            # Validate ids is not empty
            if not ids:
                return request.make_json_response({
                    'success': False,
                    'error': '"ids" array cannot be empty'
                }, status=400)
            
            # Validate all ids are integers
            if not all(isinstance(id, int) for id in ids):
                return request.make_json_response({
                    'success': False,
                    'error': 'All values in "ids" must be integers'
                }, status=400)
            
            # Process each document
            restored = []
            failed = []
            
            for doc_id in ids:
                try:
                    document = request.env['nbs.document'].browse(doc_id)
                    
                    if not document.exists():
                        _logger.warning(f'Document {doc_id} not found for restore')
                        failed.append(doc_id)
                        continue
                    
                    if not document.is_deleted:
                        _logger.warning(f'Document {doc_id} is not in trash')
                        failed.append(doc_id)
                        continue
                    
                    # Restore from trash
                    document.restore_from_trash()
                    restored.append(doc_id)
                    
                    _logger.info(f'Successfully restored document {doc_id} from trash')
                    
                except Exception as e:
                    _logger.error(f'Failed to restore document {doc_id}: {str(e)}', exc_info=True)
                    failed.append(doc_id)
            
            # Return results
            return request.make_json_response({
                'restored': restored,
                'failed': failed
            }, status=200)
            
        except Exception as e:
            _logger.error(f'Batch restore error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                'error': str(e),
                **format_error_response(e, include_traceback=True)
            }, status=500)
    
    # DEPRECATED: Old endpoint kept for backward compatibility (remove in future version)
    @http.route('/api/documents/<int:document_id>/permanent', 
                type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def permanent_delete_legacy(self, document_id, confirmation=None, **kwargs):
        """DEPRECATED: Use POST /api/documents/permanent-delete with {"ids": [id]} instead."""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({
                    'success': False, 
                    'error': 'Admin permission required'
                })

            # GET confirmation: from kwargs, query param, or JSON body
            conf = confirmation or kwargs.get('confirmation')
            
            if not conf and request.httprequest.args:
                conf = request.httprequest.args.get('confirmation')
            
            if not conf:
                try:
                    raw_body = request.httprequest.get_data(as_text=True)
                    if raw_body:
                        body = json.loads(raw_body)
                        conf = body.get('confirmation') if isinstance(body, dict) else None
                except Exception:
                    pass
            
            confirmation = conf or ''

            if not confirmation or confirmation != 'DELETE_PERMANENT':
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid confirmation. Use "DELETE_PERMANENT"'
                })

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return request.make_json_response({'success': False, 'error': 'Not found'})

            document.permanent_delete(confirmation=confirmation)
            
            return request.make_json_response({
                'success': True,
                'message': 'تم حذف المستند نهائياً'
            })
        except Exception as e:
            _logger.error(f'Permanent delete (legacy) error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                **format_error_response(e, include_traceback=True)
            })
    
    @http.route('/api/documents/permanent-delete', 
                type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def permanent_delete_bulk(self, **kwargs):
        """
        Unified endpoint for single or bulk permanent deletion.
        
        Request body: {"ids": [1, 2, 3]}
        Response: {"deleted": [1, 2], "failed": [3]}
        
        Continues processing all IDs even if some fail.
        Admin permission required.
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)

            # Check admin permission
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({
                    'success': False, 
                    'error': 'Admin permission required'
                }, status=403)

            # Parse JSON body
            try:
                raw_body = request.httprequest.get_data(as_text=True)
                if not raw_body:
                    return request.make_json_response({
                        'success': False,
                        'error': 'Request body is required'
                    }, status=400)
                
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                }, status=400)
            
            # Validate ids field
            if 'ids' not in body:
                return request.make_json_response({
                    'success': False,
                    'error': 'Field "ids" is required in request body'
                }, status=400)
            
            ids = body.get('ids')
            
            # Validate ids is a list
            if not isinstance(ids, list):
                return request.make_json_response({
                    'success': False,
                    'error': '"ids" must be an array'
                }, status=400)
            
            # Validate ids is not empty
            if not ids:
                return request.make_json_response({
                    'success': False,
                    'error': '"ids" array cannot be empty'
                }, status=400)
            
            # Validate all ids are integers
            if not all(isinstance(id, int) for id in ids):
                return request.make_json_response({
                    'success': False,
                    'error': 'All values in "ids" must be integers'
                }, status=400)
            
            # Process each document
            deleted = []
            failed = []
            
            for doc_id in ids:
                try:
                    document = request.env['nbs.document'].browse(doc_id)
                    
                    if not document.exists():
                        _logger.warning(f'Document {doc_id} not found for permanent deletion')
                        failed.append(doc_id)
                        continue
                    
                    # Permanent delete with confirmation
                    document.permanent_delete(confirmation='DELETE_PERMANENT')
                    deleted.append(doc_id)
                    
                    _logger.info(f'Successfully permanently deleted document {doc_id}')
                    
                except Exception as e:
                    _logger.error(f'Failed to permanently delete document {doc_id}: {str(e)}', exc_info=True)
                    failed.append(doc_id)
            
            # Return results
            return request.make_json_response({
                'deleted': deleted,
                'failed': failed
            }, status=200)
            
        except Exception as e:
            _logger.error(f'Bulk permanent delete error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                'error': str(e),
                **format_error_response(e, include_traceback=True)
            }, status=500)
    
    @http.route('/api/trash/documents',
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_trash_alias(self, department_id=None, document_type_id=None, search=None,
                         from_date=None, to_date=None, page=1, per_page=20, **kwargs):
        """Alias at a different URL — same as /api/documents/trash"""
        return self.get_trash_documents(
            department_id=department_id,
            document_type_id=document_type_id,
            search=search,
            from_date=from_date,
            to_date=to_date,
            page=page,
            per_page=per_page,
        )