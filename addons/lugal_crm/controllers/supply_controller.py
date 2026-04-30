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
    is_allowed_crm_image_mime,
)

_logger = logging.getLogger(__name__)

# Multipart chat uploads — images, docs, audio, video, archives
ALLOWED_SUPPLY_CHAT_MIMES = set(ALLOWED_IMAGE_MIMES) | set(ALLOWED_DOC_MIMES) | {
    'text/plain',
    'text/csv',
    # Archives
    'application/zip',
    'application/x-zip-compressed',
    'application/x-rar-compressed',  # .rar (legacy MIME)
    'application/vnd.rar',           # .rar (official MIME)
    'application/x-rar',             # .rar (some systems)
    'application/x-7z-compressed',   # .7z
    'application/x-tar',             # .tar
    'application/gzip',              # .gz
    'application/x-bzip2',           # .bz2
    'application/x-xz',              # .xz
    # Audio — voice notes and audio messages
    'audio/mpeg',           # .mp3
    'audio/mp4',            # .m4a (AAC in MP4)
    'audio/ogg',            # .ogg (Opus/Vorbis)
    'audio/webm',           # .webm audio
    'audio/wav',            # .wav
    'audio/x-wav',
    'audio/aac',            # .aac
    'audio/x-m4a',          # .m4a
    'audio/3gpp',           # .3gp audio
    'audio/amr',            # .amr (phone voice notes)
    # Video
    'video/mp4',            # .mp4 — preferred, plays in all browsers
    'video/webm',           # .webm — browser-native
    'video/ogg',            # .ogv
    'video/quicktime',      # .mov
    'video/x-msvideo',      # .avi
    'video/3gpp',           # .3gp
    'video/x-matroska',     # .mkv
}

# All uploads up to 1 GB (images, audio, docs, video)
MAX_SUPPLY_CHAT_UPLOAD_MB = 1024
MAX_SUPPLY_CHAT_VIDEO_MB  = 1024

AUDIO_MIMES = frozenset(m for m in ALLOWED_SUPPLY_CHAT_MIMES if m.startswith('audio/'))
VIDEO_MIMES  = frozenset(m for m in ALLOWED_SUPPLY_CHAT_MIMES if m.startswith('video/'))


def _supply_chat_mime_allowed(mime: str) -> bool:
    """Chat attachments: allowlisted docs/audio/video plus any image/* subtype."""
    if not mime:
        return False
    if mime in ALLOWED_SUPPLY_CHAT_MIMES:
        return True
    return is_allowed_crm_image_mime(mime)


def _create_supply_chat_attachment(filename, mimetype, data_bytes, res_model=False, res_id=False):
    """Like upload_controller._create_attachment but allows unattached chat files."""
    Attachment = request.env['ir.attachment'].sudo()
    token = uuid.uuid4().hex
    # ir.attachment requires res_model to be a non-empty string
    vals = {
        'name': filename,
        'mimetype': mimetype,
        'datas': base64.b64encode(data_bytes).decode('utf-8'),
        'type': 'binary',
        'res_model': res_model or 'lugal.supply.conversation',
        'res_id': int(res_id) if res_id else False,
        'access_token': token,
    }
    attachment = Attachment.create(vals)
    attachment.flush_recordset(['access_token'])
    return attachment


def _serialize_attachment(att):
    return {
        'id': att.id,
        'name': att.name or '',
        'mimetype': att.mimetype or 'application/octet-stream',
        'size': int(att.file_size or 0),
        'url': _build_attachment_url(att),
        'file_url': _build_attachment_url(att),
        'uploaded_by_name': att.create_uid.name if att.create_uid else '',
        'created_at': att.create_date.isoformat() if att.create_date else '',
    }


def _supply_delete_is_for_me(kwargs):
    """JSON-RPC params: delete for this user only (not global soft-delete)."""
    if kwargs.get('for_me') is True:
        return True
    mode = (kwargs.get('mode') or '').strip().lower()
    if mode in ('for_me', 'personal', 'me', 'hide'):
        return True
    # API doc: for_everyone true = everyone; false = this device only
    if kwargs.get('for_everyone') is False:
        return True
    return False


def _supply_user_can_see_conversation(conv, uid):
    if not conv or not conv.exists():
        return False
    if conv.type == 'team':
        return True
    return uid in conv.participant_ids.ids


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


def _serialize_container_tracking_view(c):
    """HTTP GET tracking/view — core container fields plus optional tracking_data JSON."""
    assigned = c.assigned_user_id
    payload = c.tracking_data
    if payload in (False, None):
        tracking_payload = {}
    elif isinstance(payload, dict):
        tracking_payload = payload
    else:
        tracking_payload = {'_raw': payload}
    return {
        'id': c.id,
        'name': c.name or '',
        'container_number': c.container_number or '',
        'bl_number': c.bl_number or '',
        'tracking_url': c.tracking_url or '',
        'status': c.status or '',
        'division': c.division or '',
        'clearance_company': c.clearance_company or '',
        'origin_location': c.origin_location or '',
        'departure_date': c.departure_date.isoformat() if c.departure_date else None,
        'eta': c.eta.isoformat() if c.eta else None,
        'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
        'assigned_user_id': assigned.id if assigned else None,
        'assigned_user_name': assigned.name if assigned else '',
        'tracking_data': tracking_payload,
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
        '/api/crm/supply/containers/tracking/view',
        type='http',
        auth='none',
        methods=['GET', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
    )
    def supply_container_tracking_view(self, **kwargs):
        """
        GET: return container tracking fields and optional JSON snapshot (`tracking_data`).
        Query string: container_id (required). JWT: Authorization: Bearer <token>.
        """
        try:
            if request.httprequest.method == 'OPTIONS':
                return request.make_response(
                    '',
                    status=204,
                    headers=[
                        ('Access-Control-Allow-Origin', '*'),
                        ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                        ('Access-Control-Allow-Headers', 'Authorization, Content-Type, Accept'),
                        ('Access-Control-Max-Age', '86400'),
                    ],
                )
            if not ensure_jwt_user_id():
                return request.make_json_response(
                    {'success': False, 'error': 'Unauthorized', 'data': None},
                    status=401,
                )
            raw = (
                kwargs.get('container_id')
                or request.params.get('container_id')
                or request.httprequest.args.get('container_id')
            )
            if raw is None or str(raw).strip() == '':
                return request.make_json_response(
                    {'success': False, 'error': 'container_id is required', 'data': None},
                    status=400,
                )
            try:
                cid = int(raw)
            except (TypeError, ValueError):
                return request.make_json_response(
                    {'success': False, 'error': 'container_id must be a number', 'data': None},
                    status=400,
                )
            Container = request.env['lugal.supply.container'].sudo()
            c = Container.search([('id', '=', cid), ('is_deleted', '=', False)], limit=1)
            if not c:
                return request.make_json_response(
                    {'success': False, 'error': 'Container not found', 'data': None},
                    status=404,
                )
            return request.make_json_response({
                'success': True,
                'data': _serialize_container_tracking_view(c),
            })
        except Exception as e:
            return request.make_json_response(crm_error(e, 'supply_container_tracking_view'), status=500)

    @http.route(
        '/api/crm/supply/messages/<int:message_id>/delete',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_message_delete(self, message_id, **kwargs):
        """
        Soft-delete for everyone (sender only) or hide for current user only.

        Params:
          - mode: 'for_me' (or for_me: true)
          - for_everyone: false => same as delete-for-me
          - for_everyone: true  => placeholder for all (sender only)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if 'lugal.supply.message' not in request.env:
                return {'success': False, 'error': 'Supply messages are not available'}
            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}

            conv = msg.conversation_id
            if not _supply_user_can_see_conversation(conv, uid):
                return {'success': False, 'error': 'Forbidden'}

            for_me = _supply_delete_is_for_me(kwargs)

            if for_me:
                if uid in msg.hidden_user_ids.ids:
                    return {'success': True, 'data': {'id': msg.id, 'deleted': True, 'scope': 'for_me'}}
                msg.write({'hidden_user_ids': [(4, uid)]})
                return {'success': True, 'data': {'id': msg.id, 'deleted': True, 'scope': 'for_me'}}

            # Global soft-delete — sender only
            if msg.sender_id.id != uid:
                return {'success': False, 'error': 'Only the sender can delete this message'}
            if msg.is_deleted:
                return {'success': True, 'data': {'id': msg.id, 'deleted': True, 'scope': 'for_everyone'}}
            msg.write({
                'is_deleted': True,
                'content': '[This message was deleted]',
                'attachments_json': '[]',
            })
            # Notify all conversation participants in real-time
            try:
                request.env['bus.bus'].sudo()._sendone(
                    f'supply_chat.{conv.id}',
                    'supply.chat.message.deleted',
                    {
                        'message_id': msg.id,
                        'conversation_id': conv.id,
                        'deleted_by': uid,
                        'scope': 'for_everyone',
                    },
                )
            except Exception as _bus_exc:
                import logging as _lg
                _lg.getLogger(__name__).debug('delete bus publish error: %s', _bus_exc)
            return {'success': True, 'data': {'id': msg.id, 'deleted': True, 'scope': 'for_everyone'}}
        except Exception as e:
            return crm_error(e, 'supply_message_delete')

    @http.route(
        '/api/crm/supply/chat/upload',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
        # Odoo's http.py sets DEFAULT_MAX_CONTENT_LENGTH = 128 MiB on every request.
        # This per-route override raises the ceiling to 1 GB so large files (RAR, ZIP,
        # video, etc.) are not rejected by Werkzeug before reaching our controller.
        max_content_length=1073741824,
    )
    def supply_chat_upload(self, **kwargs):
        """
        Multipart upload for supply chat attachments.

        Supports: images, documents, audio (voice notes), video.

        Form fields:
          - files[] | files | file : one or more binary parts
          - conversation_id (optional): link ir.attachment to conversation
          - kind (optional): hint — 'image'|'video'|'audio'|'voice'|'file'
          - duration_seconds (optional): for audio/video, length in seconds

        Size limits:
          - Video files: up to 100 MB
          - All other files: up to 25 MB

        Response JSON:
          { "success": true, "data": { "files": [{id, name, mimetype, size, url, kind}] } }
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

            # Optional kind hint and duration from the form
            kind_hint = (
                (kwargs.get('kind') or '').strip().lower()
                or (request.httprequest.form.get('kind') or '').strip().lower()
            )
            try:
                duration_hint = float(
                    kwargs.get('duration_seconds')
                    or request.httprequest.form.get('duration_seconds')
                    or 0
                )
            except (ValueError, TypeError):
                duration_hint = 0.0

            conv = None
            raw_cid = (
                (kwargs.get('conversation_id') or '').strip()
                or (request.httprequest.form.get('conversation_id') or '').strip()
            )
            if raw_cid:
                if 'lugal.supply.conversation' not in request.env:
                    return _json(
                        {'success': False, 'error': 'Supply chat is not available'},
                        400,
                    )
                Conv = request.env['lugal.supply.conversation'].sudo()
                conv = Conv.browse(int(raw_cid)).exists()
                if not conv:
                    return _json({'success': False, 'error': 'Conversation not found'}, 404)
                if conv.type != 'team' and uid not in conv.participant_ids.ids:
                    return _json({'success': False, 'error': 'Forbidden'}, 403)

            ir_rows = []

            for f in files:
                data = f.read()
                mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''

                # Per-type size limit
                is_video = mime in VIDEO_MIMES
                limit_mb = MAX_SUPPLY_CHAT_VIDEO_MB if is_video else MAX_SUPPLY_CHAT_UPLOAD_MB
                limit_bytes = limit_mb * 1024 * 1024

                if len(data) > limit_bytes:
                    return _json(
                        {'success': False, 'error': f'{f.filename or "file"}: exceeds {limit_mb} MB'},
                        400,
                    )
                if not _supply_chat_mime_allowed(mime):
                    return _json(
                        {'success': False, 'error': f'{f.filename or "file"}: unsupported type ({mime})'},
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
                    att = _create_supply_chat_attachment(filename, mime, data)

                url = _build_attachment_url(att)

                # Auto-detect kind if not provided
                if kind_hint:
                    kind = kind_hint
                elif mime in AUDIO_MIMES:
                    kind = 'voice' if 'voice' in (f.filename or '').lower() else 'audio'
                elif mime in VIDEO_MIMES:
                    kind = 'video'
                elif is_allowed_crm_image_mime(mime):
                    kind = 'image'
                else:
                    kind = 'file'

                ir_rows.append({
                    'id':               att.id,
                    'name':             att.name or filename,
                    'mimetype':         mime,
                    'size':             len(data),
                    'url':              url,
                    'kind':             kind,
                    'duration_seconds': duration_hint if kind in ('audio', 'voice', 'video') else 0,
                })

            # Legacy "attachments" key kept for backwards compat
            attachments_out = [{'name': r['name'], 'url': r['url']} for r in ir_rows]

            return _json({
                'success': True,
                'data': {
                    'files':             ir_rows,
                    'attachments':       attachments_out,
                    'uploaded_count':    len(ir_rows),
                    'total_attachments': len(ir_rows),
                },
            })
        except Exception as e:
            _logger.exception('supply_chat_upload')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _json({'success': False, 'error': str(e)}, 500)
