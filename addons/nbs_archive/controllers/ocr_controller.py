# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSOCRController(http.Controller):
    """OCR diagnostics, manual trigger, and backfill endpoints."""

    @http.route('/api/ocr/test', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def test_ocr(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            info = request.env['nbs.ocr.service'].sudo().test_tesseract()
            return {'success': True, 'data': info}
        except Exception as e:
            _logger.error('OCR test error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/ocr/run/<int:document_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def run_ocr(self, document_id, **kwargs):
        """Trigger OCR on a single document (uses its current version)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            doc = request.env['nbs.document'].sudo().browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Document not found'}

            ok = request.env['nbs.ocr.service'].sudo()._process_document_async(doc.id)
            return {
                'success': True,
                'data': {
                    'document_id': document_id,
                    'ok': bool(ok),
                    'ocr_status': doc.ocr_status,
                    'ocr_text_length': len(doc.ocr_text or ''),
                }
            }
        except Exception as e:
            _logger.error('OCR run error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/ocr/backfill', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def run_ocr_backfill(self, limit=50, **kwargs):
        """
        Run OCR on all existing documents that have no extracted text yet.

        Processes up to ``limit`` documents per call (default 50) to avoid
        HTTP timeouts.  Call repeatedly until ``remaining`` is 0.

        Response:
          {
            "success": true,
            "processed": 12,
            "successful": 11,
            "failed": 1,
            "remaining": 38,
            "results": [
              {"document_id": 5, "name": "Invoice April", "success": true, "chars": 842},
              ...
            ]
          }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            env  = request.env
            ocr  = env['nbs.ocr.service'].sudo()

            # Find documents that need OCR: have a version with file data but no text yet
            pending_docs = env['nbs.document'].sudo().search([
                ('ocr_status', 'in', ('pending', 'failed')),
                ('current_version_id', '!=', False),
            ], limit=int(limit), order='id asc')

            total_remaining = env['nbs.document'].sudo().search_count([
                ('ocr_status', 'in', ('pending', 'failed')),
                ('current_version_id', '!=', False),
            ])

            results      = []
            successful   = 0
            failed_count = 0

            for doc in pending_docs:
                try:
                    ok = ocr._process_document_async(doc.id)
                    chars = len(doc.ocr_text or '')
                    results.append({
                        'document_id': doc.id,
                        'name':        doc.name,
                        'success':     bool(ok),
                        'chars':       chars,
                    })
                    if ok:
                        successful += 1
                    else:
                        failed_count += 1
                except Exception as exc:
                    _logger.warning('Backfill OCR failed doc %s: %s', doc.id, exc)
                    results.append({
                        'document_id': doc.id,
                        'name':        doc.name,
                        'success':     False,
                        'error':       str(exc),
                    })
                    failed_count += 1

            return {
                'success':    True,
                'processed':  len(pending_docs),
                'successful': successful,
                'failed':     failed_count,
                'remaining':  max(0, total_remaining - len(pending_docs)),
                'results':    results,
            }

        except Exception as e:
            _logger.error('OCR backfill error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
























