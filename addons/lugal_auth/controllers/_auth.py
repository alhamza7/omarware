# -*- coding: utf-8 -*-
"""
Shared JWT guard helpers for the Lugal suite.

Usage in any Lugal controller:

    from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

    @http.route('/lugal/crm/...', auth='none', ...)
    def my_endpoint(self, **kw):
        uid = ensure_jwt_user_id()
        if not uid:
            return {'success': False, 'error': 'Unauthorized'}
        ...
"""

import logging

_logger = logging.getLogger(__name__)


def _verify_jwt_token():
    """Extract and verify the Bearer token from the Authorization header."""
    from odoo.http import request
    try:
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        if not hasattr(request, 'env') or not request.env:
            _logger.warning('lugal_auth._auth: request.env not initialized')
            return None
        payload = request.env['lugal.jwt.service'].sudo().verify_access_token(token)
        return payload['user_id'] if payload else None
    except Exception as exc:
        _logger.error('lugal_auth._auth: token verification error — %s', exc, exc_info=True)
        return None


def ensure_jwt_user_id():
    """
    Authenticate the request via Bearer JWT token OR active session cookie.

    Priority:
      1. Bearer JWT token in ``Authorization`` header (stateless, for mobile/API clients)
      2. Active Odoo session cookie (for browser-based clients)

    Returns the Odoo ``uid`` (int) on success or ``None`` on failure.
    Safe to call from ``auth='none'`` routes.
    """
    from odoo.http import request
    from odoo.api import Environment
    from odoo.modules.registry import Registry
    try:
        dbname = (
            getattr(request, 'db', None)
            or request.httprequest.headers.get('X-Odoo-Database')
        )
        if not dbname:
            _logger.warning('lugal_auth._auth: no database name in request')
            return None

        # Initialise request.env when route uses auth='none'
        if not hasattr(request, 'env') or not request.env:
            _logger.info('lugal_auth._auth: initialising request.env (db=%s)', dbname)
            cr = None
            try:
                registry = Registry(dbname)
                cr = registry.cursor()
                request._cr  = cr
                request.uid  = 1
                request.env  = Environment(cr, 1, {})
            except Exception as exc:
                _logger.error('lugal_auth._auth: failed to init env — %s', exc)
                if cr is not None:
                    try:
                        cr.close()
                    except Exception:
                        pass
                return None

        # 1. Bearer JWT — preferred for external/mobile clients
        auth_header = request.httprequest.headers.get('Authorization', '')
        if auth_header.lower().startswith('bearer '):
            uid = _verify_jwt_token()
            if not uid:
                return None
            request.update_env(user=uid)
            return uid

        # 2. Session cookie fallback — for browser clients (Odoo web/CRM frontend)
        session_uid = getattr(request.session, 'uid', None)
        if session_uid and session_uid not in (False, 0, 1):
            request.update_env(user=session_uid)
            return session_uid

        _logger.warning('lugal_auth._auth: no valid auth found (no Bearer token, no active session)')
        return None

    except Exception as exc:
        _logger.error('lugal_auth._auth: ensure_jwt_user_id error — %s', exc, exc_info=True)
        return None
