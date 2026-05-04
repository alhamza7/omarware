# -*- coding: utf-8 -*-
"""JSON-RPC helpers: attachment_ids + optional base64 file payloads for supply models."""

import base64
import binascii
import logging
import mimetypes
import uuid

_logger = logging.getLogger(__name__)

ATTACHMENT_KW_KEYS = frozenset({'attachment_ids', 'ids', 'attachment_files', 'attachments_base64'})


def supply_kwargs_has_attachments(kwargs):
    return bool(ATTACHMENT_KW_KEYS & kwargs.keys())


def supply_parse_attachment_files_kw(env, kwargs, res_model, res_id):
    """Create ir.attachment rows from base64 payloads. Returns new ids."""
    files = kwargs.get('attachment_files')
    if files is None:
        files = kwargs.get('attachments_base64')
    if not files:
        return []
    if not isinstance(files, (list, tuple)):
        raise ValueError('attachment_files must be a list')
    Attachment = env['ir.attachment'].sudo()
    new_ids = []
    for spec in files:
        if not isinstance(spec, dict):
            continue
        name = (spec.get('filename') or spec.get('name') or 'upload').strip() or 'upload'
        b64 = spec.get('datas') or spec.get('data') or spec.get('base64')
        if b64 is None:
            continue
        if isinstance(b64, (bytes, bytearray)):
            raw = bytes(b64)
        else:
            try:
                raw = base64.b64decode(b64)
            except (binascii.Error, TypeError) as exc:
                raise ValueError('Invalid base64 in attachment_files') from exc
        if not raw:
            continue
        mimetype = spec.get('mimetype') or mimetypes.guess_type(name)[0] or 'application/octet-stream'
        token = uuid.uuid4().hex
        att = Attachment.create({
            'name': name,
            'mimetype': mimetype,
            'raw': raw,
            'type': 'binary',
            'res_model': res_model,
            'res_id': int(res_id) if res_id else False,
            'access_token': token,
        })
        new_ids.append(att.id)
    return new_ids


def supply_build_attachment_m2m_write(env, kwargs, res_model, res_id):
    """Return {'attachment_ids': command} or {}. Supports clear via empty list."""
    if not supply_kwargs_has_attachments(kwargs):
        return {}
    ids = []
    if kwargs.get('attachment_ids') is not None:
        aid = kwargs['attachment_ids']
        if not isinstance(aid, (list, tuple)):
            raise ValueError('attachment_ids must be a list')
        ids = [int(x) for x in aid]
    elif kwargs.get('ids') is not None:
        ids_kw = kwargs['ids']
        if not isinstance(ids_kw, (list, tuple)):
            raise ValueError('ids must be a list')
        ids = [int(x) for x in ids_kw]
    new_ids = supply_parse_attachment_files_kw(env, kwargs, res_model, res_id)
    merged = ids + new_ids
    if kwargs.get('attachment_ids') is not None and len(kwargs['attachment_ids']) == 0 and not new_ids:
        return {'attachment_ids': [(5,)]}
    if kwargs.get('ids') is not None and len(kwargs['ids']) == 0 and not new_ids:
        return {'attachment_ids': [(5,)]}
    if not merged:
        return {}
    return {'attachment_ids': [(6, 0, merged)]}
