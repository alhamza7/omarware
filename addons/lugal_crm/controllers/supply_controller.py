# -*- coding: utf-8 -*-
"""Supply chain JSON-RPC API used by the 44 SPA (containers, PO, vendors)."""

import base64
import json
import logging
import mimetypes
import uuid

from odoo import http
from odoo.http import request, Response

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .upload_controller import (
    ALLOWED_DOC_MIMES,
    ALLOWED_IMAGE_MIMES,
    _build_attachment_url,
    _create_attachment,
)

_logger = logging.getLogger(__name__)

# Multipart chat uploads (broader than customer image/doc endpoints)
ALLOWED_SUPPLY_CHAT_MIMES = set(ALLOWED_IMAGE_MIMES) | set(ALLOWED_DOC_MIMES) | {
    'text/plain',
    'text/csv',
    'application/zip',
    'application/x-zip-compressed',
}
MAX_SUPPLY_CHAT_UPLOAD_MB = 25


def _create_supply_chat_attachment(filename, mimetype, data_bytes, res_model=False, res_id=False):
    """Like upload_controller._create_attachment but allows unattached files (no customer row)."""
    Attachment = request.env['ir.attachment'].sudo()
    token = uuid.uuid4().hex
    vals = {
        'name': filename,
        'mimetype': mimetype,
        'datas': base64.b64encode(data_bytes).decode('utf-8'),
        'type': 'binary',
        'access_token': token,
    }
    if res_model:
        vals['res_model'] = res_model
        vals['res_id'] = int(res_id) if res_id else False
    attachment = Attachment.create(vals)
    attachment.flush_recordset(['access_token'])
    return attachment


def _serialize_attachment(att):
    return {
        'id': att.id,
        'name': att.name or '',
        'mimetype': att.mimetype or 'application/octet-stream',
        'size': int(att.file_size or 0),
        'url': f'/web/content/{att.id}?download=true',
        'uploaded_by_name': att.create_uid.name if att.create_uid else '',
        'created_at': att.create_date.isoformat() if att.create_date else '',
    }


def _serialize_penalty(p, container):
    cur = p.currency_id
    return {
        'id': p.id,
        'container_id': container.id,
        'container_name': container.name or '',
        'penalty_type': p.penalty_type or 'other',
        'amount': float(p.amount or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'reason': p.reason or '',
        'penalty_date': p.penalty_date.isoformat() if p.penalty_date else '',
        'created_by_name': p.create_uid.name if p.create_uid else '',
        'created_at': p.create_date.isoformat() if p.create_date else '',
    }


class CrmSupplyController(http.Controller):
    @http.route(
        '/api/crm/supply/containers/<int:container_id>/attachments/list',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_attachments_list(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            Container = request.env['lugal.supply.container'].sudo()
            c = Container.browse(container_id).exists()
            if not c:
                return {'success': False, 'error': 'Container not found', 'data': None}
            attachments = []
            for att in c.attachment_ids.sorted('id', reverse=True):
                attachments.append(_serialize_attachment(att))
            return {
                'success': True,
                'data': {
                    'container_id': c.id,
                    'attachments': attachments,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_attachments_list')

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/penalties/list',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_penalties_list(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            Container = request.env['lugal.supply.container'].sudo()
            c = Container.browse(container_id).exists()
            if not c:
                return {'success': False, 'error': 'Container not found', 'data': None}
            Penalty = request.env['lugal.supply.container.penalty'].sudo()
            rows = Penalty.search([('container_id', '=', c.id)], order='penalty_date desc, id desc')
            items = [_serialize_penalty(p, c) for p in rows]
            total_amount = sum(float(p.amount or 0.0) for p in rows)
            return {
                'success': True,
                'data': {
                    'container_id': c.id,
                    'container_name': c.name or '',
                    'total': len(items),
                    'total_amount': total_amount,
                    'items': items,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_penalties_list')

    @http.route(
        '/api/crm/supply/chat/upload',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
    )
    def supply_chat_upload(self, **kwargs):
        """
        Multipart upload for supply chat attachments (used before messages/create).

        Form fields:
          - files[] | files | file: one or more binary parts
          - conversation_id (optional): link ir.attachment to lugal.supply.conversation;
            caller must be a participant.

        Response JSON:
          { "success": true, "data": { "attachments": [{ "name", "url" }], ... } }
        """

        def _json(payload, status=200):
            return Response(
                json.dumps(payload),
                status=status,
                headers=[('Content-Type', 'application/json')],
            )

        try:
            if request.httprequest.method == 'OPTIONS':
                return Response(status=204, headers=[
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
                    ('Access-Control-Max-Age', '86400'),
                ])

            uid = ensure_jwt_user_id()
            if not uid:
                return _json({'success': False, 'error': 'Unauthorized'}, 401)

            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json(
                    {'success': False, 'error': 'No files provided (use file, files, or files[])'},
                    400,
                )

            conv = None
            raw_cid = (
                (kwargs.get('conversation_id') or '').strip()
                or (request.httprequest.form.get('conversation_id') or '').strip()
            )
            if raw_cid:
                if 'lugal.supply.conversation' not in request.env:
                    return _json(
                        {
                            'success': False,
                            'error': 'Supply chat is not available (lugal.supply.conversation missing)',
                        },
                        400,
                    )
                Conv = request.env['lugal.supply.conversation'].sudo()
                conv = Conv.browse(int(raw_cid)).exists()
                if not conv:
                    return _json({'success': False, 'error': 'Conversation not found'}, 404)
                # Team channels are open to any authenticated user; DM/group require membership.
                if conv.type != 'team' and uid not in conv.participant_ids.ids:
                    return _json({'success': False, 'error': 'Forbidden'}, 403)

            max_bytes = MAX_SUPPLY_CHAT_UPLOAD_MB * 1024 * 1024
            attachments_out = []
            ir_rows = []

            for f in files:
                data = f.read()
                if len(data) > max_bytes:
                    return _json(
                        {
                            'success': False,
                            'error': f'{f.filename or "file"}: exceeds {MAX_SUPPLY_CHAT_UPLOAD_MB} MB',
                        },
                        400,
                    )
                mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''
                if mime not in ALLOWED_SUPPLY_CHAT_MIMES:
                    return _json(
                        {
                            'success': False,
                            'error': f'{f.filename or "file"}: unsupported type ({mime})',
                        },
                        400,
                    )
                filename = f.filename or 'upload'
                if conv:
                    att = _create_attachment(
                        filename=filename,
                        mimetype=mime,
                        data_bytes=data,
                        res_model='lugal.supply.conversation',
                        res_id=conv.id,
                    )
                else:
                    att = _create_supply_chat_attachment(
                        filename, mime, data,
                    )
                url = _build_attachment_url(att)
                attachments_out.append({'name': att.name or filename, 'url': url})
                ir_rows.append(
                    {
                        'id': att.id,
                        'name': att.name or filename,
                        'mimetype': mime,
                        'size': len(data),
                        'url': url,
                    },
                )

            return _json({
                'success': True,
                'data': {
                    'attachments': attachments_out,
                    'uploaded_count': len(ir_rows),
                    'total_attachments': len(ir_rows),
                    'files': ir_rows,
                },
            })
        except Exception as e:
            _logger.exception('supply_chat_upload')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _json({'success': False, 'error': str(e)}, 500)
