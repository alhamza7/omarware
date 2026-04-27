import json
import logging

from odoo import http
from odoo.http import request, Response, root
from odoo.service.security import compute_session_token
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

SESSION_TTL = 3600  # 1 hour hint — actual Odoo session lives 7 days (SESSION_LIFETIME)


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
            session.uid = uid
            session.db = request.db
            session.login = (
                request.env['res.users'].sudo().browse(uid).login
            )
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

            # Build the Set-Cookie header manually so it works regardless of
            # which Odoo post_dispatch path is taken.
            # Use SameSite=Lax so the session cookie is sent when the browser
            # opens the WebSocket through the Vite proxy on the same origin.
            # Also set a Max-Age so the session persists across tabs/reopens.
            cookie_header = (
                f'session_id={session.sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400'
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

            # Derive the WebSocket URL from the request host + configured gevent_port.
            # We ALWAYS use gevent_port (8076) because that is the ONLY Odoo listener
            # that handles WebSocket upgrades — the HTTP workers (8075) do NOT.
            #
            # We take the hostname from the incoming request's Host header (the IP
            # the browser used to reach us) and combine it with the gevent port so
            # the FE can connect directly — no Vite proxy required.
            import odoo.tools.config as _odoo_cfg
            # configmanager IS the config dict — no .config attribute in this version
            try:
                gevent_port = int(_odoo_cfg.config.get('gevent_port', 8072))
            except AttributeError:
                gevent_port = int(_odoo_cfg.get('gevent_port', 8072))

            # Strip any port from the Host header — we'll add gevent_port ourselves.
            raw_host = request.httprequest.host or ''
            hostname = raw_host.split(':')[0]   # "192.168.116.204" (no port)
            scheme   = 'wss' if request.httprequest.is_secure else 'ws'
            ws_url   = f"{scheme}://{hostname}:{gevent_port}/websocket?version={ws_version}"

            return _json({
                'use_websocket': enabled,
                'fallback_on_error': True,
                'ws_version': ws_version,
                'ws_url': ws_url,
            })
        except Exception:
            return _json({'use_websocket': False, 'fallback_on_error': True})
