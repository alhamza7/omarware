# -*- coding: utf-8 -*-
"""
CRM File Upload Controller
Endpoints:
  POST /api/crm/upload/image     – upload one or more shop images
  POST /api/crm/upload/document  – upload a customer document with type metadata
"""

import logging
import mimetypes
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)

# Allowed MIME types (explicit set + any other image/* via is_allowed_crm_image_mime)
ALLOWED_IMAGE_MIMES = {
    'image/jpeg', 'image/jpg', 'image/pjpeg',
    'image/png', 'image/apng',
    'image/gif', 'image/webp',
    'image/avif', 'image/heic', 'image/heif', 'image/heic-sequence',
    'image/tiff', 'image/x-tiff', 'image/bmp', 'image/x-ms-bmp',
    'image/svg+xml',
    'image/x-icon', 'image/vnd.microsoft.icon',
    'image/jp2', 'image/jpx', 'image/jpm',
    'image/x-adobe-dng',
}


def is_allowed_crm_image_mime(mime: str) -> bool:
    """True for known raster/vector images or any non-empty image/* subtype."""
    if not mime:
        return False
    if mime in ALLOWED_IMAGE_MIMES:
        return True
    return mime.startswith('image/')
ALLOWED_DOC_MIMES = {
    'application/pdf',
    'image/jpeg', 'image/png', 'image/webp',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

# Max sizes
MAX_IMAGE_SIZE_MB = 10
MAX_DOC_SIZE_MB = 20

VALID_DOC_TYPES = {
    'national_id', 'shop_license', 'tax_certificate',
    'commerce_registration', 'residence_card', 'other',
}


def _build_attachment_url(attachment):
    """Return a stable public URL for an ir.attachment record."""
    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
    token = attachment.access_token or ''
    return f"{base_url}/web/content/{attachment.id}?access_token={token}"


def _create_attachment(filename, mimetype, data_bytes, res_model='lugal.crm.customer', res_id=None):
    """Create an ir.attachment record with a public access token and return it."""
    import base64
    import uuid
    Attachment = request.env['ir.attachment'].sudo()

    # Generate the token ourselves so it's available immediately after create()
    token = uuid.uuid4().hex

    vals = {
        'name':         filename,
        'mimetype':     mimetype,
        'datas':        base64.b64encode(data_bytes).decode('utf-8'),
        'type':         'binary',
        'res_model':    res_model,
        'access_token': token,
    }
    if res_id:
        vals['res_id'] = res_id

    attachment = Attachment.create(vals)
    # Flush so the token is committed to DB before we build the URL
    attachment.flush_recordset(['access_token'])
    return attachment


class CrmUploadController(http.Controller):

    @http.route(
        '/api/crm/upload/image',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
    )
    def upload_image(self, **kwargs):
        """
        Upload one or more shop images.

        Request: multipart/form-data
          - files[]: one or more image files  (field name can also be 'file' or 'image')
          - customer_id: (optional) integer – link image to a specific customer

        Response (200):
          {
            "success": true,
            "data": {
              "files": [
                { "id": 123, "url": "http://..." , "filename": "photo.jpg" }
              ]
            }
          }

        Errors (400 / 401):
          { "success": false, "error": "..." }
        """
        import json
        from odoo.http import Response

        def _json(payload, status=200):
            return Response(
                json.dumps(payload),
                status=status,
                headers=[('Content-Type', 'application/json')],
            )

        try:
            # Return CORS preflight response immediately
            if request.httprequest.method == 'OPTIONS':
                return Response(status=204, headers=[
                    ('Access-Control-Allow-Origin',  '*'),
                    ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
                    ('Access-Control-Max-Age',        '86400'),
                ])

            if not ensure_jwt_user_id():
                return _json({'success': False, 'error': 'Unauthorized'}, 401)

            customer_id = kwargs.get('customer_id')
            res_id = int(customer_id) if customer_id else None

            # Accept 'files[]', 'file', or 'image' field names
            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
                or request.httprequest.files.getlist('image')
            )

            if not files:
                return _json({'success': False, 'error': 'No files provided. Use field name: files[] or file'}, 400)

            results = []
            max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024

            for f in files:
                data = f.read()

                # Size check
                if len(data) > max_bytes:
                    return _json({'success': False, 'error': f'{f.filename}: exceeds {MAX_IMAGE_SIZE_MB} MB limit'}, 400)

                # MIME check
                mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''
                if not is_allowed_crm_image_mime(mime):
                    return _json({'success': False, 'error': f'{f.filename}: unsupported image type ({mime})'}, 400)

                attachment = _create_attachment(
                    filename=f.filename or 'upload',
                    mimetype=mime,
                    data_bytes=data,
                    res_model='lugal.crm.customer',
                    res_id=res_id,
                )
                results.append({
                    'id':       attachment.id,
                    'url':      _build_attachment_url(attachment),
                    'filename': attachment.name,
                })

            return _json({'success': True, 'data': {'files': results}})

        except Exception as e:
            request.env.cr.rollback()
            return _json({'success': False, 'error': str(e)}, 500)

    @http.route(
        '/api/crm/upload/document',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
    )
    def upload_document(self, **kwargs):
        """
        Upload a single customer document with metadata.

        Request: multipart/form-data
          - file:        the document file (required)
          - type:        document type  (required) – one of:
                         national_id | shop_license | tax_certificate |
                         commerce_registration | residence_card | other
          - name:        human-readable name  (optional, defaults to filename)
          - customer_id: (optional) integer – link document to a specific customer

        Response (200):
          {
            "success": true,
            "data": {
              "id":       123,
              "url":      "http://...",
              "type":     "national_id",
              "name":     "My ID",
              "filename": "id_card.pdf"
            }
          }

        Errors (400 / 401):
          { "success": false, "error": "..." }
        """
        import json
        from odoo.http import Response

        def _json(payload, status=200):
            return Response(
                json.dumps(payload),
                status=status,
                headers=[('Content-Type', 'application/json')],
            )

        try:
            # Return CORS preflight response immediately
            if request.httprequest.method == 'OPTIONS':
                return Response(status=204, headers=[
                    ('Access-Control-Allow-Origin',  '*'),
                    ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
                    ('Access-Control-Max-Age',        '86400'),
                ])

            if not ensure_jwt_user_id():
                return _json({'success': False, 'error': 'Unauthorized'}, 401)

            # Accept field names: 'file' or 'document'
            f = (
                request.httprequest.files.get('file')
                or request.httprequest.files.get('document')
            )
            if not f:
                return _json({'success': False, 'error': 'No file provided. Use field name: file or document'}, 400)

            doc_type = (kwargs.get('type') or '').strip()
            if not doc_type:
                return _json({'success': False, 'error': 'type is required. Allowed: ' + ', '.join(sorted(VALID_DOC_TYPES))}, 400)
            if doc_type not in VALID_DOC_TYPES:
                return _json({'success': False, 'error': f'Invalid type "{doc_type}". Allowed: ' + ', '.join(sorted(VALID_DOC_TYPES))}, 400)

            doc_name = (kwargs.get('name') or f.filename or doc_type).strip()
            customer_id = kwargs.get('customer_id')
            res_id = int(customer_id) if customer_id else None

            data = f.read()
            max_bytes = MAX_DOC_SIZE_MB * 1024 * 1024
            if len(data) > max_bytes:
                return _json({'success': False, 'error': f'File exceeds {MAX_DOC_SIZE_MB} MB limit'}, 400)

            mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''
            if mime not in ALLOWED_DOC_MIMES and not is_allowed_crm_image_mime(mime):
                return _json({'success': False, 'error': f'Unsupported file type ({mime}). Allowed: pdf, images, doc, docx, xls, xlsx'}, 400)

            attachment = _create_attachment(
                filename=f.filename or doc_name,
                mimetype=mime,
                data_bytes=data,
                res_model='lugal.crm.customer',
                res_id=res_id,
            )

            return _json({
                'success': True,
                'data': {
                    'id':       attachment.id,
                    'url':      _build_attachment_url(attachment),
                    'type':     doc_type,
                    'name':     doc_name,
                    'filename': attachment.name,
                },
            })

        except Exception as e:
            request.env.cr.rollback()
            return _json({'success': False, 'error': str(e)}, 500)
