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
    try:
        uid = _verify_jwt_token()
        if not uid:
            return None
        if not hasattr(request, 'env') or not request.env:
            _logger.error('Request environment not initialized, cannot update user')
            return None
        request.update_env(user=uid)
        return uid
    except Exception as e:
        _logger.error(f'ensure_jwt_user_id error: {str(e)}', exc_info=True)
        return None
