import json
import logging

from odoo import http
from odoo.http import request, Response, root
from odoo.service.security import compute_session_token
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

# Keep the WebSocket session bridge valid across long inactive workdays.
# The user asked for background tabs to stay connected for at least 24 hours;
# one week matches Odoo's default server-side session lifetime and avoids the
# FE refreshing/rotating the WS cookie after only 1 hour while a tab is idle.
SESSION_TTL = 60 * 60 * 24 * 7


class WsSessionController(http.Controller):

    # ------------------------------------------------------------------
    # POST /api/crm/ws/session
    # Exchange a valid JWT Bearer token for a short-lived Odoo session_id.
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/ws/session',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def get_ws_session(self, **kwargs):
        """
        Exchange a valid JWT Bearer token for an Odoo session_id cookie.

        The response includes Set-Cookie: session_id=... so the browser
        automatically stores it. The FE does NOT need to parse the JSON body
        and manually call document.cookie — just make the request and the
        browser handles the rest.

        The cookie is then forwarded by the Vite proxy when the FE opens
        the WebSocket: ws://<vite-host>/websocket → ws://192.168.116.204:8076

        Authorization: Bearer <jwt>    ← JWT read from header
        Body: {}                       ← body ignored
        """
        def _json(payload, status=200, extra_headers=None):
            headers = [('Content-Type', 'application/json')]
            if extra_headers:
                headers.extend(extra_headers)
            return Response(json.dumps(payload), status=status, headers=headers)

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        # Validate JWT — reads Authorization: Bearer <token> from header
        uid = ensure_jwt_user_id()
        if not uid:
            return _json({'success': False, 'error': 'Unauthorized'}, 401)

        try:
            session = request.session
            old_uid = session.uid  # capture before overwriting

            session.uid = uid
            session.db = request.db
            session.login = (
                request.env['res.users'].sudo().browse(uid).login
            )

            if old_uid and old_uid != uid:
                # Different user taking over this session — keep old token so
                # check_session() fails on the next WS dispatch and the stale
                # connection closes with code 4001.  See auth_controller.py's
                # _attach_ws_session for the full explanation.
                pass
            else:
                # Compute and store the session token so Odoo's check_session()
                # can verify it.  Without this, check_session calls
                # consteq(str, None) → TypeError → AccessDenied → 403 for every
                # HTTP-type route (notifications, ws/config, WebSocket).
                session.session_token = compute_session_token(session, request.env)

            # Force-save the session.  Odoo normally sets can_save=False when
            # the X-Odoo-Database header is present (stateless mode), which
            # prevents the Set-Cookie from being emitted in post_dispatch.
            # We need the cookie in the browser so the WS upgrade (which goes
            # through the Vite proxy) carries it automatically.
            session.can_save = True
            request.session.touch()
            root.session_store.save(session)

            # When a DIFFERENT user is taking over this session, push a bus signal
            # so any open WS connection for the old user can close immediately.
            # The _authenticate() override in lugal_ir_websocket.py will also detect
            # the uid change and raise SessionExpiredException (close 4001) on the
            # next WS frame, but the bus push provides an immediate fast-path close.
            if old_uid and old_uid != uid:
                try:
                    session_sid = session.sid
                    bus = request.env['bus.bus'].sudo()
                    bus._sendone(
                        f'supply_session.{session_sid}',
                        'session.reconnect_required',
                        {'reason': 'user_changed', 'old_uid': old_uid, 'new_uid': uid},
                    )
                    bus._sendone(
                        f'supply_user.{old_uid}',
                        'session.reconnect_required',
                        {'reason': 'user_changed', 'session_id': session_sid},
                    )
                    _logger.info(
                        'ws_session: pushed reconnect — session %s uid %s → %s',
                        session_sid[:8], old_uid, uid,
                    )
                except Exception as be:
                    _logger.debug('ws_session: bus signal failed: %s', be)

            # Build the Set-Cookie header manually so it works regardless of
            # which Odoo post_dispatch path is taken.
            # Use SameSite=Lax so the session cookie is sent when the browser
            # opens the WebSocket through the Vite proxy on the same origin.
            # Also set a Max-Age so the session persists across tabs/reopens.
            cookie_header = (
                f'session_id={session.sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL}'
            )

            return _json(
                {
                    'success': True,
                    'data': {
                        'session_id': session.sid,
                        'expires_in': SESSION_TTL,
                    },
                },
                extra_headers=[('Set-Cookie', cookie_header)],
            )
        except Exception as exc:
            _logger.exception('ws_session: session creation failed: %s', exc)
            return _json({'success': False, 'error': 'Session creation failed'}, 500)

    # ------------------------------------------------------------------
    # GET /api/crm/ws/config
    # Returns whether WebSocket mode is enabled for this user.
    # Controls the FE startup router (BusClient vs long-poll fallback).
    # ------------------------------------------------------------------
    @http.route(
        '/api/crm/ws/config',
        type='http',
        auth='none',
        methods=['GET', 'OPTIONS'],
        csrf=False,
        cors='*',
    )
    def ws_config(self, **kwargs):
        """
        Returns the current WebSocket rollout flag.
        FE calls this once on startup to decide WS vs long-poll.
        Safe to call even without authentication — returns use_websocket: false
        on any auth failure so the FE always has a safe fallback.
        """
        def _json(payload):
            return Response(
                json.dumps(payload),
                headers=[('Content-Type', 'application/json')],
            )

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json({'use_websocket': False, 'fallback_on_error': True, 'ws_version': None})

            ICP = request.env['ir.config_parameter'].sudo()
            enabled = ICP.get_param('ws.rollout.enabled', 'False').lower() == 'true'

            # Return the required WS version so the FE can include it in the
            # connection URL: ws://.../websocket?version=<ws_version>
            # Odoo immediately closes connections whose version param doesn't
            # match _VERSION (close code 1000, reason "OUTDATED_VERSION").
            from odoo.addons.bus.websocket import WebsocketConnectionHandler
            ws_version = WebsocketConnectionHandler._VERSION

            # Build the WebSocket URL using X-Forwarded-Host (set by our proxy)
            # so the returned URL reflects the client-facing host:port (e.g.
            # 192.168.116.228:3003) rather than the internal Odoo address.
            # The proxy already routes /websocket → gevent worker.
            forwarded_host = request.httprequest.headers.get('X-Forwarded-Host', '')
            raw_host = forwarded_host or request.httprequest.host or ''
            scheme   = 'wss' if request.httprequest.is_secure else 'ws'
            ws_url   = f"{scheme}://{raw_host}/websocket?version={ws_version}"

            return _json({
                'use_websocket': enabled,
                'fallback_on_error': True,
                'ws_version': ws_version,
                'ws_url': ws_url,
            })
        except Exception as _exc:
            _logger.exception('ws_config error: %s', _exc)
            return _json({'use_websocket': False, 'fallback_on_error': True})
