# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LugalAuthController(http.Controller):
    """
    Centralized login, refresh, and logout endpoints for the Lugal suite.

    POST /lugal/auth/login    — obtain tokens (rate-limited per username+IP)
    POST /lugal/auth/refresh  — renew access token
    POST /lugal/auth/logout   — revoke current token immediately
    """

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/login', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        """
        Authenticate with username + password and return JWT tokens.

        Params: username (str), password (str)
        Response: access_token, refresh_token, token_type, user
        """
        try:
            username = (kwargs.get('username') or '').strip()
            password = kwargs.get('password') or ''

            if not username or not password:
                return {'success': False, 'error': 'username and password are required'}

            dbname = getattr(request, 'db', None) or \
                     request.httprequest.headers.get('X-Odoo-Database')
            if not dbname:
                return {'success': False, 'error': 'Database not specified'}

            rate_limiter = request.env['lugal.auth.rate.limit'].sudo()

            # Use username + IP as composite identifier
            client_ip  = request.httprequest.remote_addr or 'unknown'
            identifier = f'{username}:{client_ip}'

            if rate_limiter.is_locked(identifier):
                _logger.warning('lugal_auth: login blocked for %s (rate limit)', identifier)
                return {
                    'success': False,
                    'error':   'Too many failed attempts. Please try again later.',
                }

            result = request.env['lugal.jwt.service'].sudo().authenticate_user(
                username, password
            )

            if not result:
                locked = rate_limiter.record_failure(identifier)
                msg = ('Too many failed attempts. Please try again later.'
                       if locked else 'Invalid credentials')
                return {'success': False, 'error': msg}

            # Success — clear failure counter
            rate_limiter.record_success(identifier)
            return {'success': True, 'data': result}

        except Exception as exc:
            _logger.error('lugal_auth login error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Authentication error'}

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/refresh', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def refresh(self, **kwargs):
        """
        Exchange a refresh token for a new access token.

        Params: refresh_token (str)
        Response: access_token, token_type
        """
        try:
            refresh_token = kwargs.get('refresh_token') or ''
            if not refresh_token:
                return {'success': False, 'error': 'refresh_token is required'}

            result = request.env['lugal.jwt.service'].sudo().refresh_access_token(
                refresh_token
            )
            if not result:
                return {'success': False, 'error': 'Invalid or expired refresh token'}

            return {'success': True, 'data': result}

        except Exception as exc:
            _logger.error('lugal_auth refresh error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Token refresh error'}

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/logout', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def logout(self, **kwargs):
        """
        Revoke the current access token immediately.

        The token is extracted from the Authorization: Bearer header.
        After logout the token is blacklisted — further requests with it
        will receive 401 Unauthorized.

        Params: (none — token is read from header)
        Response: { success: true }
        """
        try:
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {'success': False, 'error': 'No Bearer token in Authorization header'}

            token = auth_header.split(' ', 1)[1]
            request.env['lugal.jwt.service'].sudo().revoke_token(token, reason='logout')
            return {'success': True, 'data': {'message': 'Logged out successfully'}}

        except Exception as exc:
            _logger.error('lugal_auth logout error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Logout error'}
