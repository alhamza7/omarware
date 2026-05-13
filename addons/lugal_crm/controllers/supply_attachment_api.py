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


def _supply_decode_base64_payload(b64):
    """Decode base64 string or bytes; strip data-URL prefix if present."""
    if b64 is None:
        return None
    if isinstance(b64, (bytes, bytearray)):
        raw = bytes(b64)
        if not raw:
            return None
        return raw
    s = str(b64).strip()
    if not s:
        return None
    if 'base64,' in s:
        s = s.split('base64,', 1)[-1]
    try:
        raw = base64.b64decode(s)
    except (binascii.Error, TypeError) as exc:
        raise ValueError('Invalid base64 in attachment_files') from exc
    if not raw:
        return None
    return raw


def supply_parse_attachment_files_kw(env, kwargs, res_model, res_id):
    """Create ir.attachment rows from base64 payloads. Returns new ids."""
    files = kwargs.get('attachment_files')
    if files is None:
        files = kwargs.get('attachments_base64')
    if not files:
        return []
    if isinstance(files, dict):
        files = [files]
    if not isinstance(files, (list, tuple)):
        raise ValueError('attachment_files must be a list')
    Attachment = env['ir.attachment'].sudo()
    new_ids = []
    for spec in files:
        if not isinstance(spec, dict):
            continue
        name = (
            spec.get('filename')
            or spec.get('name')
            or spec.get('file_name')
            or spec.get('original_filename')
            or 'upload'
        )
        name = str(name).strip() or 'upload'
        b64 = (
            spec.get('datas')
            or spec.get('data')
            or spec.get('base64')
            or spec.get('content')
            or spec.get('file')
        )
        try:
            raw = _supply_decode_base64_payload(b64)
        except ValueError:
            raise
        if raw is None:
            continue
        mimetype = spec.get('mimetype') or mimetypes.guess_type(name)[0] or 'application/octet-stream'
        token = uuid.uuid4().hex
        datas_b64 = base64.b64encode(raw).decode('ascii')
        att = Attachment.create({
            'name': name,
            'mimetype': mimetype,
            'datas': datas_b64,
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
    explicit_ids = kwargs.get('attachment_ids') is not None or kwargs.get('ids') is not None
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
    if kwargs.get('attachment_ids') is not None and len(kwargs['attachment_ids']) == 0 and not new_ids:
        return {'attachment_ids': [(5,)]}
    if kwargs.get('ids') is not None and len(kwargs['ids']) == 0 and not new_ids:
        return {'attachment_ids': [(5,)]}
    if not new_ids and not ids:
        return {}
    if explicit_ids:
        merged = ids + new_ids
        return {'attachment_ids': [(6, 0, merged)]}
    if new_ids:
        return {'attachment_ids': [(4, nid) for nid in new_ids]}
    return {}


ITEM_REQUEST_ATTACHMENT_MODEL = 'lugal.supply.item.request'


def supply_sync_item_request_attachment_m2m(env, item_requests):
    """Link M2M from res_model/res_id; set res_model/res_id on M2M rows when missing/wrong."""
    if not item_requests:
        return
    Att = env['ir.attachment'].sudo().with_context(active_test=False)
    rids = [int(x) for x in item_requests.ids]
    if not rids:
        return
    for rec in item_requests:
        for att in rec.with_context(active_test=False).attachment_ids:
            wrong = (
                (att.res_model or '') != ITEM_REQUEST_ATTACHMENT_MODEL
                or int(att.res_id or 0) != rec.id
            )
            if wrong:
                att.sudo().write({
                    'res_model': ITEM_REQUEST_ATTACHMENT_MODEL,
                    'res_id': rec.id,
                })
    atts = Att.search([
        ('res_model', '=', ITEM_REQUEST_ATTACHMENT_MODEL),
        ('res_id', 'in', rids),
    ])
    by_rid = {}
    for a in atts:
        rid = int(a.res_id)
        by_rid.setdefault(rid, []).append(a.id)
    for rec in item_requests:
        linked_ids = set(rec.with_context(active_test=False).attachment_ids.ids)
        extra = [aid for aid in by_rid.get(rec.id, []) if aid not in linked_ids]
        if extra:
            rec.write({'attachment_ids': [(4, x) for x in extra]})
    item_requests.invalidate_recordset(['attachment_ids'])
