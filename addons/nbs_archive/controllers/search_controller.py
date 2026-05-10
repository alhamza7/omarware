# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


def _ocr_snippet(ocr_text: str, query: str, radius: int = 120) -> str:
    """
    Return a short excerpt from ``ocr_text`` centred around the first
    occurrence of ``query`` (case-insensitive).  Falls back to the first
    ``radius`` characters if the query is not found.
    """
    if not ocr_text:
        return ''
    low_text  = ocr_text.lower()
    low_query = (query or '').lower()
    pos = low_text.find(low_query) if low_query else -1
    if pos == -1:
        return ocr_text[:radius].strip() + ('…' if len(ocr_text) > radius else '')
    start = max(0, pos - radius // 2)
    end   = min(len(ocr_text), pos + len(query) + radius // 2)
    snippet = ocr_text[start:end].strip()
    if start > 0:
        snippet = '…' + snippet
    if end < len(ocr_text):
        snippet = snippet + '…'
    return snippet


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
            
            # Build domain for metadata + OCR content search
            domain = [
                ('state', '=', 'active'),
                '|', '|', '|', '|', '|', '|',
                ('name', 'ilike', query),
                ('barcode', 'ilike', query),
                ('po_number', 'ilike', query),
                ('bl_number', 'ilike', query),
                ('container_number', 'ilike', query),
                ('invoice_number', 'ilike', query),
                ('ocr_text', 'ilike', query),
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

            # Documents — search metadata AND OCR-extracted content
            Document = request.env['nbs.document'].sudo()
            doc_domain = [
                ('state', '=', 'active'),
                ('is_deleted', '=', False),
                '|', '|', '|', '|', '|', '|',
                ('name', 'ilike', q),
                ('barcode', 'ilike', q),
                ('po_number', 'ilike', q),
                ('bl_number', 'ilike', q),
                ('container_number', 'ilike', q),
                ('invoice_number', 'ilike', q),
                ('ocr_text', 'ilike', q),
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
                    'ocr_status': doc.ocr_status,
                    'ocr_snippet': _ocr_snippet(doc.ocr_text, q),
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

    # ─────────────────────────────────────────────────────────────────────────
    # POST /api/documents/report
    # ─────────────────────────────────────────────────────────────────────────
    @http.route(
        '/api/documents/report',
        type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*',
    )
    def documents_report(
        self,
        from_date=None,
        to_date=None,
        company_id=None,
        company_name=None,
        department_id=None,
        department_name=None,
        document_type_id=None,
        document_type=None,
        confidentiality_level=None,
        uploader_id=None,
        uploader_name=None,
        folder_id=None,
        folder_name=None,
        document_role=None,
        state=None,
        page=1,
        per_page=50,
        **kwargs,
    ):
        """
        Return a paginated list of documents uploaded within a date range,
        with optional filters on company, department, document type,
        confidentiality level, uploader, and folder.

        ── Request body (all fields optional) ──────────────────────────────
        {
          "from_date":            "2026-01-01",          // default: earliest upload ever
          "to_date":              "2026-12-31",          // default: today
          "company_id":           7436,
          "company_name":         "ALCAN",               // partial, case-insensitive
          "department_id":        4,
          "department_name":      "Supply Chain",        // partial, case-insensitive
          "document_type_id":     5,
          "document_type":        "Invoice",             // partial, case-insensitive
          "confidentiality_level":"internal",            // public|internal|confidential|strict
          "uploader_id":          2,
          "uploader_name":        "admin",               // partial, case-insensitive
          "folder_id":            45,
          "folder_name":          "ALCAN-386",           // partial, case-insensitive
          "document_role":        "main",                // main|sub|attachment|other
          "state":                "active",              // active|archived|all  (default: active)
          "page":                 1,
          "per_page":             50
        }

        ── Response ────────────────────────────────────────────────────────
        {
          "success": true,
          "summary": {
            "total":        407,
            "from_date":    "2026-05-03T08:11:31",
            "to_date":      "2026-05-04T10:33:00",
            "filters": { "company": "ALCAN", ... }
          },
          "data": [
            {
              "id":                   123,
              "name":                 "Invoice April 2026",
              "barcode":              "NBS000123",
              "upload_date":          "2026-05-03T09:00:00",
              "uploader_id":          2,
              "uploader_name":        "admin",
              "department_id":        4,
              "department_name":      "Supply Chain",
              "document_type_id":     5,
              "document_type_name":   "Invoice",
              "company_id":           7436,
              "company_name":         "ALCAN",
              "folder_id":            45,
              "folder_name":          "ALCAN-386",
              "confidentiality_level":"internal",
              "document_role":        "main",            // main|sub|attachment|other
              "is_attachment":        false,
              "parent_document_id":   null,
              "state":                "active",
              "version_count":        2,
              "ocr_status":           "completed"
            }
          ],
          "pagination": {
            "page":        1,
            "per_page":    50,
            "total":       407,
            "total_pages": 9
          }
        }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            env = request.env
            Doc = env['nbs.document'].sudo()

            # ── Resolve default date boundaries ──────────────────────────────
            from odoo.fields import Datetime as OdooDatetime
            from datetime import datetime, timezone

            # Default from_date: earliest upload_date ever recorded
            if not from_date:
                env.cr.execute(
                    "SELECT MIN(upload_date) FROM nbs_document WHERE upload_date IS NOT NULL"
                )
                row = env.cr.fetchone()
                earliest = row[0] if row and row[0] else None
                effective_from = earliest.isoformat() if earliest else '2000-01-01T00:00:00'
            else:
                effective_from = from_date

            # Default to_date: now (end of day)
            if not to_date:
                effective_to = datetime.now(timezone.utc).strftime('%Y-%m-%dT23:59:59')
            else:
                # If date only (no time), set to end-of-day
                effective_to = to_date if 'T' in str(to_date) else f'{to_date}T23:59:59'

            if 'T' not in str(effective_from):
                effective_from = f'{effective_from}T00:00:00'

            # ── Build Odoo domain ─────────────────────────────────────────────
            domain = [
                ('upload_date', '>=', effective_from),
                ('upload_date', '<=', effective_to),
            ]

            # State filter (default: active only, 'all' = active + archived)
            if state == 'all':
                domain.append(('is_deleted', '=', False))
            elif state == 'archived':
                domain.append(('state', '=', 'archived'))
            else:
                domain.append(('state', '=', 'active'))

            # Filters: prefer ID, fall back to name ilike
            filters_applied = {}

            if company_id:
                domain.append(('company_id', '=', int(company_id)))
                filters_applied['company_id'] = int(company_id)
            elif company_name:
                domain.append(('company_id.name', 'ilike', company_name))
                filters_applied['company_name'] = company_name

            if department_id:
                domain.append(('department_id', '=', int(department_id)))
                filters_applied['department_id'] = int(department_id)
            elif department_name:
                domain.append(('department_id.name', 'ilike', department_name))
                filters_applied['department_name'] = department_name

            if document_type_id:
                domain.append(('document_type_id', '=', int(document_type_id)))
                filters_applied['document_type_id'] = int(document_type_id)
            elif document_type:
                domain.append(('document_type_id.name', 'ilike', document_type))
                filters_applied['document_type'] = document_type

            if confidentiality_level:
                domain.append(('confidentiality_level', '=', confidentiality_level))
                filters_applied['confidentiality_level'] = confidentiality_level

            if uploader_id:
                domain.append(('uploader_id', '=', int(uploader_id)))
                filters_applied['uploader_id'] = int(uploader_id)
            elif uploader_name:
                domain.append(('uploader_id.name', 'ilike', uploader_name))
                filters_applied['uploader_name'] = uploader_name

            if folder_id:
                domain.append(('folder_id', '=', int(folder_id)))
                filters_applied['folder_id'] = int(folder_id)
            elif folder_name:
                domain.append(('folder_id.name', 'ilike', folder_name))
                filters_applied['folder_name'] = folder_name

            if document_role:
                domain.append(('folder_role', '=', document_role))
                filters_applied['document_role'] = document_role

            # ── Pagination ────────────────────────────────────────────────────
            try:
                page     = max(1, int(page))
                per_page = min(500, max(1, int(per_page)))
            except (TypeError, ValueError):
                page, per_page = 1, 50

            total       = Doc.search_count(domain)
            total_pages = max(1, (total + per_page - 1) // per_page)
            offset      = (page - 1) * per_page

            docs = Doc.search(domain, limit=per_page, offset=offset, order='upload_date desc')

            # ── Build response rows ───────────────────────────────────────────
            data = []
            for doc in docs:
                data.append({
                    'id':                    doc.id,
                    'name':                  doc.name,
                    'barcode':               doc.barcode or None,
                    'upload_date':           doc.upload_date.isoformat() if doc.upload_date else None,
                    'uploader_id':           doc.uploader_id.id if doc.uploader_id else None,
                    'uploader_name':         doc.uploader_id.name if doc.uploader_id else None,
                    'department_id':         doc.department_id.id if doc.department_id else None,
                    'department_name':       doc.department_id.name if doc.department_id else None,
                    'document_type_id':      doc.document_type_id.id if doc.document_type_id else None,
                    'document_type_name':    doc.document_type_id.name if doc.document_type_id else None,
                    'company_id':            doc.company_id.id if doc.company_id else None,
                    'company_name':          doc.company_id.name if doc.company_id else None,
                    'folder_id':             doc.folder_id.id if doc.folder_id else None,
                    'folder_name':           doc.folder_id.name if doc.folder_id else None,
                    'confidentiality_level': doc.confidentiality_level,
                    'document_role':         doc.folder_role or 'other',
                    'is_attachment':         doc.is_attachment,
                    'parent_document_id':    doc.parent_document_id.id if doc.parent_document_id else None,
                    'state':                 doc.state,
                    'version_count':         doc.version_count or 0,
                    'ocr_status':            doc.ocr_status or 'pending',
                    'po_number':             doc.po_number or None,
                    'bl_number':             doc.bl_number or None,
                    'invoice_number':        doc.invoice_number or None,
                    'container_number':      doc.container_number or None,
                    'document_date':         doc.document_date.strftime('%d-%m-%Y') if doc.document_date else None,
                })

            return {
                'success': True,
                'summary': {
                    'total':       total,
                    'from_date':   effective_from,
                    'to_date':     effective_to,
                    'filters':     filters_applied,
                },
                'data': data,
                'pagination': {
                    'page':        page,
                    'per_page':    per_page,
                    'total':       total,
                    'total_pages': total_pages,
                },
            }

        except Exception as exc:
            _logger.error('documents_report error: %s', exc, exc_info=True)
            return {'success': False, 'error': str(exc)}
