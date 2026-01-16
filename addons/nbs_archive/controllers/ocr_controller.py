# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSOCRController(http.Controller):
    """OCR diagnostics and manual trigger endpoints (auto OCR still runs on upload)."""

    @http.route('/api/ocr/test', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def test_ocr(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            info = request.env['nbs.ocr.service'].sudo().test_tesseract()
            return {'success': True, 'data': info}
        except Exception as e:
            _logger.error(f'OCR test error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/ocr/run/<int:document_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def run_ocr(self, document_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            doc = request.env['nbs.document'].sudo().browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            ok = request.env['nbs.ocr.service'].sudo()._process_document_async(doc.id)
            return {'success': True, 'data': {'queued': True, 'ok': bool(ok), 'ocr_status': doc.ocr_status}}
        except Exception as e:
            _logger.error(f'OCR run error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}




















