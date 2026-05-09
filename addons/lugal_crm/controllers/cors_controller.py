# -*- coding: utf-8 -*-
"""
CORS preflight handler for all API routes.

Covers:
  /api/crm/*     — CRM / supply / chat endpoints
  /api/lugal/*   — Email, rules, quick-steps endpoints
  /lugal/*       — Auth (login, refresh, logout, password reset)

CORS headers are also added to every actual response via each controller's
_json_response helper, so both preflight (OPTIONS) and real requests work
regardless of which port or host the frontend is served from.
"""

import logging
from odoo import http
from odoo.http import Response

_logger = logging.getLogger(__name__)

# Headers the browser is allowed to send
_ALLOW_HEADERS = ', '.join([
    'Content-Type',
    'Authorization',
    'Accept',
    'Origin',
    'X-Requested-With',
    'X-Odoo-Database',
])

# Allowed origins — open to any origin so any FE port works
_ALLOW_ORIGINS = '*'


def _cors_response(status=200, body=''):
    """Return a Response with full CORS headers."""
    return Response(
        body,
        status=status,
        headers={
            'Access-Control-Allow-Origin':      _ALLOW_ORIGINS,
            'Access-Control-Allow-Methods':     'GET, POST, PATCH, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers':     _ALLOW_HEADERS,
            'Access-Control-Max-Age':           '86400',
        },
    )


class CorsController(http.Controller):
    """Handle HTTP OPTIONS preflight for all Lugal API routes."""

    @http.route(
        [
            '/api/crm/<path:subpath>',   # CRM / supply / chat
            '/api/lugal/<path:subpath>', # Email, rules, quick-steps
            '/lugal/<path:subpath>',     # Auth endpoints
        ],
        type='http',
        auth='none',
        csrf=False,
        methods=['OPTIONS'],
        cors='*',
        save_session=False,
    )
    def options_handler(self, subpath, **kwargs):
        """Respond to CORS preflight (OPTIONS) for all API routes."""
        return _cors_response(200)
