# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def _verify_jwt_token():
    """Verify JWT token from Authorization header"""
    from odoo.http import request
    try:
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        if not hasattr(request, 'env') or not request.env:
            _logger.warning('Request environment not initialized')
            return None
        jwt_service = request.env['nbs.jwt.service'].sudo()
        payload = jwt_service.verify_access_token(token)
        if payload:
            return payload['user_id']
        return None
    except Exception as e:
        _logger.error(f'JWT verification error: {str(e)}', exc_info=True)
        return None


def ensure_jwt_user_id():
    """Validate Authorization: Bearer <jwt> and update request env."""
    from odoo.http import request
    from odoo.api import Environment
    from odoo.modules.registry import Registry
    try:
        # Get database name
        dbname = getattr(request, 'db', None) or request.httprequest.headers.get('X-Odoo-Database')
        if not dbname:
            _logger.warning('No database in request for JWT auth')
            return None
        
        # Initialize request.env if not set (for auth='none' routes).
        # The cursor is stored on request._cr; Odoo's request lifecycle calls
        # request._cr.close() (or rolls back) when the request ends, so we do
        # NOT close it ourselves here — doing so would break the request env.
        # We still guard the *creation* with a try/except so that a failure
        # during cursor acquisition doesn't silently leak a connection.
        if not hasattr(request, 'env') or not request.env:
            _logger.info(f'Initializing request.env for JWT auth (db: {dbname})')
            cr = None
            try:
                registry = Registry(dbname)
                cr = registry.cursor()
                request._cr = cr
                uid = 1  # Temporary, will update after token verification
                request.uid = uid
                request.env = Environment(cr, uid, {})
            except Exception as e:
                _logger.error(f'Failed to initialize request.env: {e}')
                if cr is not None:
                    try:
                        cr.close()
                    except Exception:
                        pass
                return None
        
        # Verify token
        uid = _verify_jwt_token()
        if not uid:
            return None
        
        # Update env with authenticated user
        request.update_env(user=uid)
        return uid
    except Exception as e:
        _logger.error(f'ensure_jwt_user_id error: {str(e)}', exc_info=True)
        return None
