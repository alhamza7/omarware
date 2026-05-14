"""Shared helpers for lugal_inventory API controllers."""
import json
import jwt
import functools
from datetime import datetime, timezone

from odoo import http
from odoo.http import request


JWT_SECRET = 'lugal_inventory_secret_2024'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24


def _success(data=None, message='success', status=200):
    """Return a standardized success JSON response."""
    return request.make_response(
        json.dumps({'success': True, 'message': message, 'data': data}),
        headers=[('Content-Type', 'application/json')],
        status=status,
    )


def _error(message='error', status=400, details=None):
    """Return a standardized error JSON response."""
    body = {'success': False, 'message': message}
    if details:
        body['details'] = details
    return request.make_response(
        json.dumps(body),
        headers=[('Content-Type', 'application/json')],
        status=status,
    )


def _generate_token(user_id, username, role, warehouse_id):
    """Generate a JWT token for an inventory user."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'warehouse_id': warehouse_id,
        'exp': int(datetime.now(timezone.utc).timestamp()) + JWT_EXPIRY_HOURS * 3600,
        'iat': int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token):
    """Decode and validate a JWT token. Returns payload dict or raises jwt exceptions."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def require_auth(func):
    """Decorator that validates Bearer JWT token before executing the route handler."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return _error('Unauthorized: missing token', status=401)
        token = auth_header[7:]
        try:
            payload = _decode_token(token)
            request._inv_token_payload = payload
        except jwt.ExpiredSignatureError:
            return _error('Unauthorized: token expired', status=401)
        except jwt.InvalidTokenError:
            return _error('Unauthorized: invalid token', status=401)
        return func(*args, **kwargs)
    return wrapper


def _parse_body():
    """Parse JSON request body, return dict or empty dict on failure."""
    try:
        data = request.httprequest.get_data(as_text=True)
        return json.loads(data) if data else {}
    except Exception:
        return {}


def _extract_translatable(val):
    """Safely extract a string from Odoo translatable fields (plain str or jsonb dict)."""
    if not val:
        return ''
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get('en_US') or val.get('ar_001') or next(iter(val.values()), '')
    return str(val)


def _serialize_product(product):
    """Serialize a product.product record to a dict for API response."""
    return {
        'id': product.id,
        'code': product.default_code or '',
        'name': _extract_translatable(product.name),
        'barcode': product.barcode or '',
        'uom': _extract_translatable(product.uom_id.name) if product.uom_id else '',
        'category': _extract_translatable(product.categ_id.name) if product.categ_id else '',
        'active': product.active,
    }


def _serialize_audit(audit):
    """Serialize a lugal.inventory.audit record to API dict."""
    return {
        'id': audit.id,
        'code': audit.product_code or '',
        'name': audit.product_name or '',
        'warehouse': audit.warehouse_name or '',
        'warehouse_id': audit.warehouse_id.id if audit.warehouse_id else None,
        'quantity': str(audit.quantity),
        'user': audit.user_name or '',
        'date': audit.create_date.isoformat() if audit.create_date else '',
        'session_id': audit.session_id.id if audit.session_id else None,
        'uom': _extract_translatable(audit.uom_id.name) if audit.uom_id else '',
        'barcode_used': audit.barcode_used or '',
        'product_id': audit.product_id.id if audit.product_id else None,
    }


def _serialize_inv_user(inv_user):
    """Serialize a lugal.inventory.user record to API dict."""
    return {
        'id': inv_user.id,
        'fullName': inv_user.full_name or '',
        'username': inv_user.username or '',
        'role': dict(inv_user._fields['role'].selection).get(inv_user.role, ''),
        'warehouse': inv_user.warehouse_id.code or str(inv_user.warehouse_id.id),
        'dateAdded': inv_user.create_date.isoformat() if inv_user.create_date else '',
    }
