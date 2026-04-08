# -*- coding: utf-8 -*-
"""
CORS preflight handler for all /api/crm/* and /lugal/* routes.

In development the Vite proxy handles CORS transparently — these headers
are only needed when the frontend communicates directly with Odoo (staging
/ production or when testing via tools like curl / Postman).
"""

import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# Headers the browser is allowed to send
_ALLOW_HEADERS = ', '.join([
    'Content-Type',
    'Authorization',
    'Accept',
    'Origin',
    'X-Requested-With',
])

# Allowed origins — restrict to your domain in production
_ALLOW_ORIGINS = '*'


def _cors_response(status=200, body=''):
    """Return a Response with full CORS headers."""
    return Response(
        body,
        status=status,
        headers={
            'Access-Control-Allow-Origin':      _ALLOW_ORIGINS,
            'Access-Control-Allow-Methods':     'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers':     _ALLOW_HEADERS,
            'Access-Control-Max-Age':           '86400',
            'Access-Control-Allow-Credentials': 'true',
        },
    )


class CorsController(http.Controller):
    """Handle HTTP OPTIONS preflight for CRM and auth API routes."""

    @http.route(
        ['/api/crm/<path:subpath>', '/lugal/<path:subpath>'],
        type='http',
        auth='none',
        csrf=False,
        methods=['OPTIONS'],
        cors='*',
        save_session=False,
    )
    def options_handler(self, subpath, **kwargs):
        """Respond to CORS preflight (OPTIONS) for CRM and lugal auth routes.

        Do not register a catch-all OPTIONS for `/api/pos_perfume/...`: it would
        match before GET and cause 405. POS REST routes use `cors='*'` on each
        handler so Odoo can answer preflight for those URLs.
        """
        return _cors_response(200)
