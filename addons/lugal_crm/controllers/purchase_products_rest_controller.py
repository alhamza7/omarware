# -*- coding: utf-8 -*-
"""
REST-style JSON APIs for supply-chain product search and PO creation (product_id-based).

- GET  /api/products/search
- GET  /api/products/<id>
- POST /api/purchase-orders

Auth: same JWT as other CRM supply routes (`Authorization: Bearer …`).
"""

import json
import logging

from odoo import http
from odoo.http import request, Response

from ._auth import ensure_jwt_user_id
from .supply_controller import _serialize_supply_po

_logger = logging.getLogger(__name__)

CORS_HEADERS = [
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
    ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
]


def _json_response(payload, status=200):
    body = json.dumps(payload)
    headers = [('Content-Type', 'application/json')] + CORS_HEADERS
    return Response(body, status=status, headers=headers)


def _ok(data):
    return _json_response({'status': True, 'data': data})


def _err(message, status=400):
    return _json_response({'status': False, 'error': message}, status=status)


def _unauthorized():
    return _err('Unauthorized', 401)


def _purchase_unit(product):
    return product.uom_po_id or product.uom_id


def _purchase_price(product):
    """Prefer cost (standard_price); fallback to list_price for display."""
    try:
        cost = float(product.standard_price or 0.0)
    except (TypeError, ValueError):
        cost = 0.0
    if cost > 0.0:
        return cost
    try:
        return float(product.list_price or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _product_description(product):
    tmpl = product.product_tmpl_id
    if not tmpl:
        return ''
    desc = getattr(tmpl, 'description_purchase', None) or ''
    if not desc:
        desc = tmpl.description_sale or ''
    return (desc or '').strip()


def _serialize_product_row(product):
    uom = _purchase_unit(product)
    unit_name = uom.name if uom else 'pcs'
    code = (product.default_code or '').strip()
    name = (product.name or '').strip()
    if code:
        base = f'{code} | {name}'
    else:
        base = name or f'Product #{product.id}'
    display_name = f'{base} ({unit_name})' if unit_name else base
    price = _purchase_price(product)
    try:
        qty_av = float(product.qty_available or 0.0)
    except (TypeError, ValueError):
        qty_av = 0.0
    return {
        'id': product.id,
        'code': code,
        'name': name,
        'display_name': display_name,
        'unit': unit_name,
        'price': round(price, 4),
        'description': _product_description(product)[:2000],
        'is_available': qty_av > 0.0001,
    }


def _norm_supply_division(raw):
    if raw is None or raw is False:
        return False
    s = str(raw).strip().lower()
    if s in ('europe', 'eu'):
        return 'europe'
    if s in ('china', 'cn'):
        return 'china'
    return False


class PurchaseProductsRestController(http.Controller):

    @http.route('/api/products/search', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def products_search(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=CORS_HEADERS)
        try:
            if not ensure_jwt_user_id():
                return _unauthorized()
            search = (request.params.get('search') or '').strip()
            try:
                limit = int(request.params.get('limit') or 20)
            except (TypeError, ValueError):
                limit = 20
            limit = max(1, min(limit, 100))
            supplier_id = request.params.get('supplier_id')
            partner_for_supplier = None
            if supplier_id not in (None, '', False):
                try:
                    sid = int(supplier_id)
                except (TypeError, ValueError):
                    return _err('supplier_id must be an integer', 400)
                vendor = request.env['lugal.supply.vendor'].sudo().browse(sid).exists()
                if not vendor or vendor.is_deleted:
                    return _err('Invalid supplier_id', 400)
                partner_for_supplier = vendor.partner_id.id if vendor.partner_id else None

            Product = request.env['product.product'].sudo()
            domain = [('active', '=', True), ('purchase_ok', '=', True)]
            if search:
                domain += ['|', ('default_code', 'ilike', search), ('name', 'ilike', search)]
            elif not partner_for_supplier:
                return _ok([])
            Template = request.env['product.template'].sudo()
            if partner_for_supplier:
                if 'seller_ids' not in Template._fields:
                    return _err(
                        'supplier_id filter is not available: product templates have no vendor links '
                        '(install the Purchase app or configure product vendors / seller_ids).',
                        501,
                    )
                domain.append(('product_tmpl_id.seller_ids.partner_id', '=', partner_for_supplier))

            products = Product.search(domain, limit=limit, order='default_code asc, name asc')
            rows = [_serialize_product_row(p) for p in products]
            return _ok(rows)
        except Exception as e:
            _logger.exception('products_search')
            return _err(str(e), 500)

    @http.route('/api/products/<int:product_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def products_get(self, product_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=CORS_HEADERS)
        try:
            if not ensure_jwt_user_id():
                return _unauthorized()
            product = request.env['product.product'].sudo().browse(product_id).exists()
            if not product or not product.active or not product.purchase_ok:
                return _err('Product not found', 404)
            data = _serialize_product_row(product)
            tmpl = product.product_tmpl_id
            data['barcode'] = product.barcode or ''
            data['currency_id'] = request.env.company.currency_id.id
            data['currency_name'] = request.env.company.currency_id.name or ''
            if tmpl:
                data['categ_id'] = tmpl.categ_id.id if tmpl.categ_id else None
                data['categ_name'] = tmpl.categ_id.name if tmpl.categ_id else ''
            return _ok(data)
        except Exception as e:
            _logger.exception('products_get')
            return _err(str(e), 500)

    @http.route('/api/purchase-orders', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def purchase_orders_create(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=CORS_HEADERS + [('Access-Control-Max-Age', '86400')])
        try:
            if not ensure_jwt_user_id():
                return _unauthorized()
            raw = request.httprequest.data
            if not raw:
                return _err('JSON body required', 400)
            try:
                body = json.loads(raw.decode('utf-8'))
            except (ValueError, UnicodeDecodeError) as exc:
                return _err(f'Invalid JSON: {exc}', 400)

            supplier_id = body.get('supplier_id')
            if supplier_id is None:
                return _err('supplier_id is required', 400)
            try:
                vendor = request.env['lugal.supply.vendor'].sudo().browse(int(supplier_id)).exists()
            except (TypeError, ValueError):
                return _err('supplier_id must be an integer', 400)
            if not vendor or vendor.is_deleted:
                return _err('Invalid supplier_id', 400)

            division = _norm_supply_division(body.get('division'))
            items = body.get('items')
            if not isinstance(items, list) or not items:
                return _err('items must be a non-empty list', 400)

            exchange_rate = body.get('exchange_rate')
            Po = request.env['lugal.crm.supply.po'].sudo()
            Line = request.env['lugal.crm.supply.po.line'].sudo()
            Product = request.env['product.product'].sudo()

            vals = {'vendor_id': vendor.id}
            if division:
                vals['division'] = division
            if exchange_rate is not None and 'exchange_rate' in Po._fields:
                try:
                    vals['exchange_rate'] = float(exchange_rate)
                except (TypeError, ValueError):
                    return _err('exchange_rate must be a number', 400)

            po = Po.create(vals)
            seq = 10
            for idx, row in enumerate(items):
                if not isinstance(row, dict):
                    return _err(f'items[{idx}] must be an object', 400)
                pid = row.get('product_id')
                if pid is None:
                    return _err(f'items[{idx}].product_id is required', 400)
                try:
                    pid = int(pid)
                except (TypeError, ValueError):
                    return _err(f'items[{idx}].product_id must be an integer', 400)
                product = Product.browse(pid).exists()
                if not product or not product.active or not product.purchase_ok:
                    return _err(f'items[{idx}]: invalid or non-purchasable product_id {pid}', 400)
                try:
                    qty = float(row.get('qty'))
                except (TypeError, ValueError):
                    return _err(f'items[{idx}].qty must be a number', 400)
                if qty <= 0:
                    return _err(f'items[{idx}].qty must be greater than 0', 400)
                try:
                    price = float(row.get('price', 0.0))
                except (TypeError, ValueError):
                    return _err(f'items[{idx}].price must be a number', 400)
                if price < 0:
                    return _err(f'items[{idx}].price must be >= 0', 400)
                try:
                    discount = float(row.get('discount', 0.0) or 0.0)
                except (TypeError, ValueError):
                    return _err(f'items[{idx}].discount must be a number', 400)
                if discount < 0 or discount > 100:
                    return _err(f'items[{idx}].discount must be between 0 and 100', 400)
                unit_price = price * (1.0 - discount / 100.0)
                uom = _purchase_unit(product)
                lv = {
                    'po_id': po.id,
                    'sequence': seq,
                    'product_id': product.id,
                    'product_name': product.name or '',
                    'item_code': product.default_code or '',
                    'uom': uom.name if uom else '',
                    'quantity': qty,
                    'unit_price': unit_price,
                }
                Line.create(lv)
                seq += 10

            po.invalidate_recordset()
            return _ok(_serialize_supply_po(po))
        except Exception as e:
            _logger.exception('purchase_orders_create')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _err(str(e), 500)
