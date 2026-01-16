# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSDocumentHierarchyController(http.Controller):
    @http.route('/api/documents/<int:document_id>/set-parent', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def set_parent(self, document_id, parent_document_id=None, **kwargs):
        """Set or clear parent_document_id to model main/sub document relation."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            doc = request.env['nbs.document'].browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            # Clear parent
            if not parent_document_id:
                doc.write({'parent_document_id': False})
                return {'success': True}

            parent = request.env['nbs.document'].browse(int(parent_document_id))
            if not parent.exists():
                return {'success': False, 'error': 'Parent document not found'}

            # Prevent cycles
            if parent.id == doc.id:
                return {'success': False, 'error': 'Document cannot be its own parent'}
            if doc.parent_document_id and doc.parent_document_id.id == parent.id:
                return {'success': True}

            # Basic cycle check (walk up parents)
            cur = parent
            while cur and cur.parent_document_id:
                if cur.parent_document_id.id == doc.id:
                    return {'success': False, 'error': 'Invalid parent (cycle detected)'}
                cur = cur.parent_document_id

            doc.write({'parent_document_id': parent.id})
            return {'success': True}
        except Exception as e:
            _logger.error(f'Set parent error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}




















