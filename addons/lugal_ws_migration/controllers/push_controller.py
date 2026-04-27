# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, Response

from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class PushNotificationController(http.Controller):

    # ------------------------------------------------------------------
    # GET /api/crm/push/vapid-public-key
    # Returns the VAPID public key so the browser can subscribe.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/vapid-public-key',
        type='http',
        auth='none',
        methods=['GET', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def push_vapid_public_key(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        ICP = request.env['ir.config_parameter'].sudo()
        public_key = ICP.get_param('lugal.push.vapid.public_key', '').strip()

        return Response(
            json.dumps({'public_key': public_key}),
            headers=[
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ],
        )

    # ------------------------------------------------------------------
    # POST /api/crm/push/subscribe
    # Register or refresh a browser push subscription for the current user.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/subscribe',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def push_subscribe(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            endpoint = (kwargs.get('endpoint') or '').strip()
            auth_key = (kwargs.get('auth') or '').strip()
            p256dh_key = (kwargs.get('p256dh') or '').strip()
            user_agent = (kwargs.get('user_agent') or '').strip()[:200]

            if not endpoint:
                return {'success': False, 'error': 'endpoint is required'}

            Sub = request.env['lugal.push.subscription'].sudo()
            existing = Sub.search([('endpoint', '=', endpoint)], limit=1)
            if existing:
                existing.write({
                    'user_id': uid,
                    'auth_key': auth_key,
                    'p256dh_key': p256dh_key,
                    'user_agent': user_agent,
                    'active': True,
                })
            else:
                Sub.create({
                    'user_id': uid,
                    'endpoint': endpoint,
                    'auth_key': auth_key,
                    'p256dh_key': p256dh_key,
                    'user_agent': user_agent,
                })
            return {'success': True, 'data': {'subscribed': True}}
        except Exception as exc:
            _logger.exception('push_subscribe failed')
            return {'success': False, 'error': str(exc)}

    # ------------------------------------------------------------------
    # POST /api/crm/push/unsubscribe
    # Deactivate a push subscription (e.g. user revokes permission).
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/push/unsubscribe',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def push_unsubscribe(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            endpoint = (kwargs.get('endpoint') or '').strip()
            if not endpoint:
                return {'success': False, 'error': 'endpoint is required'}

            Sub = request.env['lugal.push.subscription'].sudo()
            sub = Sub.search([('endpoint', '=', endpoint), ('user_id', '=', uid)], limit=1)
            if sub:
                sub.write({'active': False})
            return {'success': True, 'data': {'unsubscribed': True}}
        except Exception as exc:
            _logger.exception('push_unsubscribe failed')
            return {'success': False, 'error': str(exc)}
