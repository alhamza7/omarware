# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class AdvancedSearchController(http.Controller):
    
    @http.route('/api/search/advanced', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def advanced_search(self, query=None, department_ids=None, document_type_ids=None, 
                       folder_ids=None, date_from=None, date_to=None, state=None,
                       confidentiality=None, tags=None, uploader_ids=None, **kwargs):
        """Advanced search with multiple filters"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('is_deleted', '=', False)]
            
            if query:
                domain.append('|')
                domain.append(('name', 'ilike', query))
                domain.append(('barcode', 'ilike', query))
            
            if department_ids:
                domain.append(('department_id', 'in', department_ids))
            
            if document_type_ids:
                domain.append(('document_type_id', 'in', document_type_ids))
            
            if folder_ids:
                domain.append(('folder_id', 'in', folder_ids))
            
            if date_from:
                domain.append(('create_date', '>=', date_from))
            
            if date_to:
                domain.append(('create_date', '<=', date_to))
            
            if state:
                domain.append(('state', '=', state))
            
            if confidentiality:
                domain.append(('confidentiality_level', '=', confidentiality))
            
            if uploader_ids:
                domain.append(('uploader_id', 'in', uploader_ids))
            
            documents = request.env['nbs.document'].search(domain, limit=100)
            
            results = []
            for doc in documents:
                try:
                    doc_number = getattr(doc, 'document_number', None) or getattr(doc, 'barcode', None)
                except Exception:
                    doc_number = None
                results.append({
                    'id': doc.id,
                    'name': doc.name,
                    'document_number': doc_number,
                    'state': doc.state,
                    'department': doc.department_id.name,
                    'document_type': doc.document_type_id.name,
                    'folder': doc.folder_id.name if doc.folder_id else None,
                    'create_date': doc.create_date.isoformat() if doc.create_date else None,
                    'parent_document_id': doc.parent_document_id.id if doc.parent_document_id else None,
                    'relation_type': 'attachment' if doc.parent_document_id and doc.is_attachment else ('secondary_document' if doc.parent_document_id else None),
                })
            
            return {'success': True, 'data': results, 'count': len(results)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
