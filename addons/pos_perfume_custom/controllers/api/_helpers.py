# -*- coding: utf-8 -*-
"""
Shared helpers for the POS Perfume External API v1.

Provides:
  - JSON response builders  : _json_response, _success, _error
  - Request body parser     : _get_json_body
  - Record serialisers      : _serialize_order, _serialize_line,
                              _serialize_customer, _serialize_product
  - Line builder            : _build_line_vals
"""

import json
import logging
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------
# WHY auth='none' + _check_auth()?
# ─────────────────────────────────────────────────────────────────────────────
# auth='user'  → Odoo middleware handles auth via session cookie only.
#                If the session is invalid it redirects to /web/login (303 HTML).
#                Bearer tokens are NOT processed by this middleware.
#
# auth='none'  → Odoo does nothing. We call _check_auth() manually.
#                On success: request.update_env(user=uid) sets the user env.
#                On failure: we return JSON 401 — never HTML, never redirect.
# ─────────────────────────────────────────────────────────────────────────────

def _json_response(data, status=200):
    """Return a Werkzeug Response with JSON body and CORS headers."""
    body = json.dumps(data, default=str)
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    }
    return Response(body, status=status, headers=headers)


def _success(data=None, message='OK'):
    """Wrap a successful payload into the standard envelope."""
    return _json_response({'success': True, 'message': message, 'data': data})


def _error(message, status=400):
    """Wrap an error message into the standard envelope."""
    return _json_response({'success': False, 'error': message}, status=status)


# ---------------------------------------------------------------------------
# Request body parser
# ---------------------------------------------------------------------------

def _get_json_body():
    """
    Parse JSON from the incoming HTTP request body.
    Odoo type='http' controllers must read body from request.httprequest.data.
    Returns an empty dict on any parsing failure.
    """
    try:
        raw = request.httprequest.data
        if not raw:
            return {}
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _check_auth():
    """
    Authenticate the request via Bearer API key OR active session cookie.

    Called manually at the top of every route handler (routes use auth='none'
    so Odoo never redirects to /web/login — we always return JSON 401 instead).

    On success  → calls request.update_env(user=uid) and returns None.
    On failure  → returns a JSON 401 Response (caller must return it immediately).

    How to use in a route:
        auth_err = _check_auth()
        if auth_err:
            return auth_err
        # ... rest of handler
    """
    # 1. Bearer token (API key) — stateless, recommended for external apps ----
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
        try:
            uid = request.env['res.users.apikeys'].sudo()._check_credentials(
                scope='rpc', key=token
            )
            if not uid:
                return _error('Invalid API key', 401)
            request.update_env(user=uid)
            return None  # success
        except Exception as e:
            return _error(f'API key authentication failed: {e}', 401)

    # 2. Session cookie — for browser-based apps -------------------------------
    uid = request.session.uid
    if uid and uid not in (None, False, 0, 1):
        request.update_env(user=uid)
        return None  # success

    return _error(
        'Authentication required. '
        'Use "Authorization: Bearer <api_key>" header '
        'or log in via POST /web/session/authenticate.',
        401,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _serialize_order(order):
    """Serialise a pos.perfume.order record to a plain dict."""
    return {
        'id': order.id,
        'name': order.name,
        'date': order.date.isoformat() if order.date else None,
        'state': order.state,
        'user_id': {
            'id': order.user_id.id,
            'name': order.user_id.name,
        } if order.user_id else None,
        'partner_id': {
            'id': order.partner_id.id,
            'name': order.partner_id.name,
            'phone': order.partner_id.phone or '',
            'mobile': getattr(order.partner_id, 'mobile', '') or '',
            'email': order.partner_id.email or '',
        } if order.partner_id else None,
        'pricelist_id': {
            'id': order.pricelist_id.id,
            'name': order.pricelist_id.name,
        } if order.pricelist_id else None,
        'currency_id': {
            'id': order.currency_id.id,
            'name': order.currency_id.name,
        } if order.currency_id else None,
        'exchange_rate': order.exchange_rate,
        'amount_subtotal': order.amount_subtotal,
        'amount_discount': order.amount_discount,
        'amount_tax': order.amount_tax,
        'amount_total': order.amount_total,
        'amount_total_iqd': order.amount_total_iqd,
        'invoice_type': order.invoice_type or '',
        'note': order.note or '',
        'sale_order_id': {
            'id': order.sale_order_id.id,
            'name': order.sale_order_id.name,
            'state': order.sale_order_id.state,
        } if order.sale_order_id else None,
        'sap_doc_num': order.sap_doc_num or '',
        'sap_doc_entry': order.sap_doc_entry or 0,
        'sap_synced': order.sap_synced,
        'sap_error_message': order.sap_error_message or '',
        'sap_last_sync_date': order.sap_last_sync_date.isoformat() if order.sap_last_sync_date else None,
        'order_lines': [_serialize_line(l) for l in order.order_line_ids],
    }


def _serialize_line(line):
    """Serialise a pos.perfume.order.line record to a plain dict."""
    return {
        'id': line.id,
        'sequence': line.sequence,
        'product_id': {
            'id': line.product_id.id,
            'name': line.product_id.name,
            'default_code': line.product_id.default_code or '',
            'foreign_name': getattr(line.product_id, 'foreign_name', '') or '',
        } if line.product_id else None,
        'product_uom_id': {
            'id': line.product_uom_id.id,
            'name': line.product_uom_id.name,
        } if line.product_uom_id else None,
        'warehouse_id': {
            'id': line.warehouse_id.id,
            'name': line.warehouse_id.name,
            'code': line.warehouse_id.code,
        } if line.warehouse_id else None,
        'location_id': {
            'id': line.location_id.id,
            'name': line.location_id.name,
        } if line.location_id else None,
        'quantity': line.quantity,
        'unit_price': line.unit_price,
        'discount_percent': line.discount_percent,
        'price_after_discount': line.price_after_discount,
        'line_subtotal': line.line_subtotal,
        'discount_amount': line.discount_amount,
        'line_total': line.line_total,
        'available_qty': line.available_qty,
        'custom_product_name': line.custom_product_name or '',
    }


def _serialize_customer(partner):
    """Serialise a res.partner record to a plain dict."""
    return {
        'id': partner.id,
        'name': partner.name,
        'ref': partner.ref or '',
        'phone': partner.phone or '',
        'mobile': getattr(partner, 'mobile', '') or '',
        'email': partner.email or '',
        'street': partner.street or '',
        'city': partner.city or '',
        'country_id': {
            'id': partner.country_id.id,
            'name': partner.country_id.name,
        } if partner.country_id else None,
        'pricelist_id': {
            'id': partner.property_product_pricelist.id,
            'name': partner.property_product_pricelist.name,
        } if partner.property_product_pricelist else None,
    }


def _serialize_product(product):
    """Serialise a product.product record to a summary dict."""
    foreign_name = getattr(product, 'foreign_name', '') or ''
    priority, color_class, badge_text = product._get_product_priority_and_color(
        product.default_code
    )
    return {
        'id': product.id,
        'name': product.name,
        'default_code': product.default_code or '',
        'foreign_name': foreign_name,
        'uom_id': {'id': product.uom_id.id, 'name': product.uom_id.name},
        'list_price': product.list_price,
        'qty_available': product.qty_available,
        'color_class': color_class,
        'badge_text': badge_text,
        'active': product.active,
        'sale_ok': product.sale_ok,
        'categ_id': {
            'id': product.categ_id.id,
            'name': product.categ_id.name,
        } if product.categ_id else None,
    }


# ---------------------------------------------------------------------------
# Order line builder
# ---------------------------------------------------------------------------

def _build_line_vals(data):
    """
    Build a field-value dict for creating/updating a pos.perfume.order.line.
    Returns a dict on success, or an error string on validation failure.
    """
    product_id = data.get('product_id')
    product_uom_id = data.get('product_uom_id')
    warehouse_id = data.get('warehouse_id')

    if not product_id:
        return 'product_id is required for each order line'
    if not warehouse_id:
        return 'warehouse_id is required for each order line'

    product = request.env['product.product'].browse(int(product_id))
    if not product.exists():
        return f'Product {product_id} not found'

    # Default UoM to product's base UoM if not provided
    if product_uom_id:
        uom = request.env['uom.uom'].browse(int(product_uom_id))
        if not uom.exists():
            return f'UoM {product_uom_id} not found'
    else:
        uom = product.uom_id

    warehouse = request.env['stock.warehouse'].browse(int(warehouse_id))
    if not warehouse.exists():
        return f'Warehouse {warehouse_id} not found'

    # Default location to the main stock location of the warehouse
    location_id = data.get('location_id')
    if location_id:
        location_id = int(location_id)
    else:
        location_id = warehouse.lot_stock_id.id if warehouse.lot_stock_id else False

    return {
        'product_id': product.id,
        'product_uom_id': uom.id,
        'warehouse_id': warehouse.id,
        'location_id': location_id,
        'quantity': float(data.get('quantity', 1.0)),
        'unit_price': float(data.get('unit_price', product.list_price)),
        'discount_percent': float(data.get('discount_percent', 0.0)),
        'custom_product_name': data.get('custom_product_name') or False,
        'sequence': int(data.get('sequence', 10)),
    }
