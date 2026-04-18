# -*- coding: utf-8 -*-
"""Supply chain JSON-RPC API used by the 44 SPA (containers, PO, vendors)."""

import logging

from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)


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
