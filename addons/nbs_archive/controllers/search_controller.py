# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSSearchController(http.Controller):
    """Document search controller"""
    
    @http.route('/api/search', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def search_documents(self, query, search_in_content=False, department_id=None, document_type_id=None,
                        date_from=None, date_to=None, fuzzy=False, page=1, per_page=20, **kwargs):
        """
        Search documents
        
        Params:
        - query: str - search query
        - search_in_content: bool - search in OCR content
        - department_id: int - filter by department
        - document_type_id: int - filter by type
        - date_from: str - filter by date
        - date_to: str - filter by date
        - fuzzy: bool - enable fuzzy matching
        - page: int
        - per_page: int
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            if not query:
                return {
                    'success': False,
                    'error': 'Search query is required'
                }
            
            # Build domain for metadata search (documents)
            domain = [
                ('state', '=', 'active'),
                '|', '|', '|', '|', '|',
                ('name', 'ilike', query),
                ('barcode', 'ilike', query),
                ('po_number', 'ilike', query),
                ('bl_number', 'ilike', query),
                ('container_number', 'ilike', query),
                ('invoice_number', 'ilike', query),
            ]
            
            # Apply filters
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            if document_type_id:
                domain.append(('document_type_id', '=', document_type_id))
            
            if date_from:
                domain.append(('upload_date', '>=', date_from))
            
            if date_to:
                domain.append(('upload_date', '<=', date_to))
            
            # Search in database
            Document = request.env['nbs.document']
            documents = Document.search(domain, limit=per_page, offset=(page-1)*per_page, order='upload_date desc')
            total = Document.search_count(domain)
            
            # If search_in_content is enabled and OpenSearch is available
            content_results = []
            if search_in_content:
                try:
                    # Try to search in OpenSearch
                    opensearch_service = request.env['nbs.opensearch.service']
                    if opensearch_service:
                        content_results = opensearch_service.search_content(query, fuzzy=fuzzy)
                except Exception as e:
                    _logger.warning(f'OpenSearch not available: {str(e)}')
            
            return {
                'success': True,
                'data': [{
                    'id': doc.id,
                    'title': doc.name,
                    'department_id': doc.department_id.id,
                    'department_name': doc.department_id.name,
                    'document_type_id': doc.document_type_id.id,
                    'document_type_name': doc.document_type_id.name,
                    'uploader_name': doc.uploader_id.name,
                    'upload_date': doc.upload_date.isoformat() if doc.upload_date else None,
                    'barcode': doc.barcode,
                    'file_name': doc.file_name,
                    'highlights': [],  # Will be populated by OpenSearch
                    'parent_document_id': doc.parent_document_id.id if doc.parent_document_id else None,
                    'relation_type': 'attachment' if doc.parent_document_id and doc.is_attachment else ('secondary_document' if doc.parent_document_id else None),
                } for doc in documents],
                'content_matches': content_results,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                }
            }
        
        except Exception as e:
            _logger.error(f'Search error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    @http.route('/api/search/global', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def global_search(self, query, search_in_content=True, fuzzy=True, page=1, per_page=20, **kwargs):
        """
        Global search across:
        - folders (name/code/description)
        - documents (name/barcode/reference numbers)
        - attachments (name/file_name/description)
        - notes (title/content)
        - OCR/content (if OpenSearch available)
        Returns a unified list with `entity_type`.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            q = (query or '').strip()
            if not q:
                return {'success': False, 'error': 'Search query is required', 'data': []}

            results = []

            # Folders
            Folder = request.env['nbs.document.folder'].sudo()
            folder_domain = [
                ('active', '=', True),
                '|', '|',
                ('name', 'ilike', q),
                ('code', 'ilike', q),
                ('description', 'ilike', q),
            ]
            folders = Folder.search(folder_domain, limit=per_page, order='create_date desc')
            for f in folders:
                results.append({
                    'entity_type': 'folder',
                    'id': f.id,
                    'title': f.name,
                    'code': f.code,
                    'description': f.description,
                    'department_name': f.department_id.name if f.department_id else None,
                    'create_date': f.create_date.isoformat() if f.create_date else None,
                    'document_count': getattr(f, 'document_count', None),
                })

            # Documents
            Document = request.env['nbs.document'].sudo()
            doc_domain = [
                ('state', '=', 'active'),
                ('is_deleted', '=', False),
                '|', '|', '|', '|', '|',
                ('name', 'ilike', q),
                ('barcode', 'ilike', q),
                ('po_number', 'ilike', q),
                ('bl_number', 'ilike', q),
                ('container_number', 'ilike', q),
                ('invoice_number', 'ilike', q),
            ]
            documents = Document.search(doc_domain, limit=per_page, order='upload_date desc')
            for doc in documents:
                results.append({
                    'entity_type': 'document',
                    'id': doc.id,
                    'document_id': doc.id,
                    'title': doc.name,
                    'barcode': doc.barcode,
                    'department_name': doc.department_id.name if doc.department_id else None,
                    'document_type_name': doc.document_type_id.name if doc.document_type_id else None,
                    'uploader_name': doc.uploader_id.name if doc.uploader_id else None,
                    'upload_date': doc.upload_date.isoformat() if doc.upload_date else None,
                    'parent_document_id': doc.parent_document_id.id if doc.parent_document_id else None,
                    'relation_type': 'attachment' if doc.parent_document_id and doc.is_attachment else ('secondary_document' if doc.parent_document_id else None),
                })

            # Attachments
            Attachment = request.env['nbs.document.attachment'].sudo()
            att_domain = [
                '|', '|',
                ('name', 'ilike', q),
                ('file_name', 'ilike', q),
                ('description', 'ilike', q),
            ]
            atts = Attachment.search(att_domain, limit=per_page, order='create_date desc')
            for a in atts:
                results.append({
                    'entity_type': 'attachment',
                    'id': a.id,
                    'document_id': a.document_id.id if a.document_id else None,
                    'title': a.name or a.file_name,
                    'file_name': a.file_name,
                    'description': a.description,
                    'uploader_name': a.uploader_id.name if a.uploader_id else None,
                    'upload_date': a.upload_date.isoformat() if a.upload_date else None,
                })

            # Notes
            Note = request.env['nbs.note'].sudo()
            note_domain = [
                ('active', '=', True),
                '|',
                ('title', 'ilike', q),
                ('content', 'ilike', q),
            ]
            notes = Note.search(note_domain, limit=per_page, order='write_date desc')
            for note in notes:
                # Check access for current user
                if note.can_user_access():
                    results.append({
                        'entity_type': 'note',
                        'id': note.id,
                        'title': note.title or (note.content[:50] + '...' if len(note.content) > 50 else note.content),
                        'content': note.content[:200] if len(note.content) > 200 else note.content,
                        'user_name': note.user_id.name if note.user_id else None,
                        'document_id': note.document_id.id if note.document_id else None,
                        'document_title': note.document_id.name if note.document_id else None,
                        'folder_id': note.folder_id.id if note.folder_id else None,
                        'folder_name': note.folder_id.name if note.folder_id else None,
                        'department_name': note.department_id.name if note.department_id else None,
                        'has_image': bool(note.image),
                        'is_pinned': note.is_pinned,
                        'color': note.color,
                        'created_at': note.create_date.isoformat() if note.create_date else None,
                        'updated_at': note.write_date.isoformat() if note.write_date else None,
                    })

            # OCR/content (optional)
            ocr_matches = []
            if search_in_content:
                try:
                    opensearch_service = request.env['nbs.opensearch.service']
                    if opensearch_service:
                        ocr_matches = opensearch_service.search_content(q, fuzzy=fuzzy) or []
                except Exception as e:
                    _logger.warning(f'OpenSearch not available: {str(e)}')

            return {
                'success': True,
                'data': results,
                'content_matches': ocr_matches,
                'pagination': {'total': len(results), 'page': int(page), 'per_page': int(per_page)},
            }
        except Exception as e:
            _logger.error(f'Global search error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e), 'data': []}
    
    @http.route('/api/search/barcode', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def search_by_barcode(self, barcode, **kwargs):
        """Search document by barcode"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not barcode:
                return {
                    'success': False,
                    'error': 'Barcode is required'
                }
            
            document = request.env['nbs.document'].search([
                ('barcode', '=', barcode),
                ('state', '=', 'active')
            ], limit=1)
            
            if not document:
                return {
                    'success': False,
                    'error': 'Document not found',
                    'found': False
                }
            
            return {
                'success': True,
                'found': True,
                'data': {
                    'id': document.id,
                    'title': document.name,
                    'department_name': document.department_id.name,
                    'document_type_name': document.document_type_id.name,
                    'barcode': document.barcode,
                }
            }
        
        except Exception as e:
            _logger.error(f'Barcode search error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
