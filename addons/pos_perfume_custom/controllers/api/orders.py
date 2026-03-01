# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Orders CRUD + Order Lines CRUD

Routes:
  GET    /api/pos_perfume/v1/orders                          List orders with filters
  POST   /api/pos_perfume/v1/orders                          Create order
  GET    /api/pos_perfume/v1/orders/<id>                     Get single order
  PUT    /api/pos_perfume/v1/orders/<id>                     Update order header
  DELETE /api/pos_perfume/v1/orders/<id>                     Cancel order (soft-delete)
  POST   /api/pos_perfume/v1/orders/<id>/lines               Add a line
  PUT    /api/pos_perfume/v1/orders/<id>/lines/<lid>         Update a line
  DELETE /api/pos_perfume/v1/orders/<id>/lines/<lid>         Delete a line
"""

import logging
from odoo import http
from odoo.http import request

from ._helpers import (
    _success, _error, _get_json_body,
    _serialize_order, _serialize_line, _build_line_vals, _check_auth,
)

_logger = logging.getLogger(__name__)


class PosPerfumeApiOrders(http.Controller):

    # -----------------------------------------------------------------------
    # Orders — list & create
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders', type='http', auth='none', methods=['GET'], csrf=False)
    def list_orders(self, query='', state='', limit='50', offset='0',
                    partner_id='', user_id='', date_from='', date_to='',
                    sap_synced='', **kwargs):
        """List POS orders with optional filters.

        GET /api/pos_perfume/v1/orders?state=sale&limit=20&offset=0
        Query params:
          - query      : search by order name
          - state      : draft | quotation | sale | done | cancel
          - partner_id : filter by customer ID
          - user_id    : filter by salesperson ID
          - date_from  : YYYY-MM-DD
          - date_to    : YYYY-MM-DD
          - sap_synced : true | false
          - limit / offset : pagination
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            limit = int(limit)
            offset = int(offset)

            domain = []
            if query:
                domain.append(('name', 'ilike', query))
            if state:
                domain.append(('state', '=', state))
            if partner_id:
                domain.append(('partner_id', '=', int(partner_id)))
            if user_id:
                domain.append(('user_id', '=', int(user_id)))
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to + ' 23:59:59'))
            if sap_synced != '':
                domain.append((
                    'sale_order_id.sap_synced', '=',
                    sap_synced.lower() in ('1', 'true', 'yes'),
                ))

            OrderModel = request.env['pos.perfume.order']
            orders = OrderModel.search(domain, limit=limit, offset=offset, order='date desc, id desc')
            total = OrderModel.search_count(domain)

            # Lightweight list — no order lines for performance
            items = [
                {
                    'id': o.id,
                    'name': o.name,
                    'date': o.date.isoformat() if o.date else None,
                    'state': o.state,
                    'partner_id': o.partner_id.id if o.partner_id else None,
                    'partner_name': o.partner_id.name if o.partner_id else '',
                    'user_id': o.user_id.id if o.user_id else None,
                    'user_name': o.user_id.name if o.user_id else '',
                    'invoice_type': o.invoice_type or '',
                    'amount_total': o.amount_total,
                    'amount_total_iqd': o.amount_total_iqd,
                    'sap_synced': o.sap_synced,
                    'sap_doc_num': o.sap_doc_num or '',
                    'note': o.note or '',
                }
                for o in orders
            ]

            return _success({'total': total, 'offset': offset, 'limit': limit, 'items': items})
        except Exception as e:
            _logger.error('[POS API] list_orders: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders', type='http', auth='none', methods=['POST'], csrf=False)
    def create_order(self, **kwargs):
        """Create a new POS order.

        POST /api/pos_perfume/v1/orders
        Body:
        {
            "partner_id": 10,
            "pricelist_id": 1,          (optional - default pricelist used if omitted)
            "invoice_type": "1",        (optional)
            "note": "...",              (optional)
            "exchange_rate": 1480.0,    (optional)
            "user_id": 3,               (optional)
            "order_lines": [            (optional - lines can be added later)
                {
                    "product_id": 42,
                    "product_uom_id": 3,
                    "warehouse_id": 1,
                    "quantity": 2.0,
                    "unit_price": 15.0,
                    "discount_percent": 0.0,
                    "custom_product_name": ""
                }
            ]
        }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            body = _get_json_body()
            partner_id = body.get('partner_id')
            if not partner_id:
                return _error('partner_id is required')

            partner = request.env['res.partner'].browse(int(partner_id))
            if not partner.exists():
                return _error('Customer not found', 404)

            # Pricelist — use provided or fall back to system default
            pricelist_id = body.get('pricelist_id')
            if pricelist_id:
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    return _error('Pricelist not found', 404)
            else:
                default_pl_id = request.env['pos.perfume.order']._get_default_pricelist()
                pricelist = request.env['product.pricelist'].browse(default_pl_id) if default_pl_id else None
                if not pricelist or not pricelist.exists():
                    return _error('No pricelist found. Please provide pricelist_id.')

            order_vals = {
                'partner_id': partner.id,
                'pricelist_id': pricelist.id,
                'state': 'draft',
            }
            if body.get('invoice_type'):
                order_vals['invoice_type'] = str(body['invoice_type'])
            if body.get('note'):
                order_vals['note'] = body['note']
            if body.get('exchange_rate'):
                order_vals['exchange_rate'] = float(body['exchange_rate'])
            if body.get('user_id'):
                order_vals['user_id'] = int(body['user_id'])

            # Build optional inline order lines
            line_vals_list = []
            for line_data in body.get('order_lines', []):
                lv = _build_line_vals(line_data)
                if isinstance(lv, str):
                    return _error(lv)
                line_vals_list.append((0, 0, lv))

            if line_vals_list:
                order_vals['order_line_ids'] = line_vals_list

            order = request.env['pos.perfume.order'].create(order_vals)
            return _success(_serialize_order(order), message='Order created')
        except Exception as e:
            _logger.error('[POS API] create_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Orders — get / update / delete
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_order(self, order_id, **kwargs):
        """Get full order details including all lines.

        GET /api/pos_perfume/v1/orders/123
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            return _success(_serialize_order(order))
        except Exception as e:
            _logger.error('[POS API] get_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_order(self, order_id, **kwargs):
        """Update order header fields (not lines).

        PUT /api/pos_perfume/v1/orders/123
        Body: { "partner_id": 10, "pricelist_id": 2, "note": "...", "invoice_type": "3",
                "exchange_rate": 1490.0, "user_id": 3 }
        Only allowed on draft / quotation orders.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot edit an order in '{order.state}' state")

            body = _get_json_body()
            allowed = ['partner_id', 'pricelist_id', 'note', 'invoice_type', 'exchange_rate', 'user_id']
            update_vals = {}

            for key in allowed:
                if key in body:
                    if key in ('partner_id', 'pricelist_id', 'user_id'):
                        update_vals[key] = int(body[key]) if body[key] else False
                    elif key == 'exchange_rate':
                        update_vals[key] = float(body[key])
                    else:
                        update_vals[key] = body[key]

            if update_vals:
                order.write(update_vals)

            return _success(_serialize_order(order), message='Order updated')
        except Exception as e:
            _logger.error('[POS API] update_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_order(self, order_id, **kwargs):
        """Cancel an order (soft-delete — sets state to 'cancel').

        DELETE /api/pos_perfume/v1/orders/123
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state == 'done':
                return _error("Cannot cancel a done order")

            order.action_cancel()
            return _success({'id': order_id, 'state': 'cancel'}, message='Order cancelled')
        except Exception as e:
            _logger.error('[POS API] delete_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Order lines — add / update / delete
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/lines',
                type='http', auth='none', methods=['POST'], csrf=False)
    def add_order_line(self, order_id, **kwargs):
        """Add a new line to an existing order.

        POST /api/pos_perfume/v1/orders/123/lines
        Body:
        {
            "product_id": 42,
            "product_uom_id": 3,
            "warehouse_id": 1,
            "quantity": 2.0,
            "unit_price": 15.0,
            "discount_percent": 0.0,
            "custom_product_name": ""
        }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot add lines to a '{order.state}' order")

            body = _get_json_body()
            lv = _build_line_vals(body)
            if isinstance(lv, str):
                return _error(lv)

            lv['order_id'] = order.id
            line = request.env['pos.perfume.order.line'].create(lv)
            return _success(_serialize_line(line), message='Line added')
        except Exception as e:
            _logger.error('[POS API] add_order_line: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/lines/<int:line_id>',
                type='http', auth='none', methods=['PUT'], csrf=False)
    def update_order_line(self, order_id, line_id, **kwargs):
        """Update an existing order line.

        PUT /api/pos_perfume/v1/orders/123/lines/456
        Body: { "quantity": 3.0, "unit_price": 20.0, "discount_percent": 5.0,
                "custom_product_name": "...", "product_id": 42, "warehouse_id": 1 }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot edit lines of a '{order.state}' order")

            line = request.env['pos.perfume.order.line'].browse(line_id)
            if not line.exists() or line.order_id.id != order_id:
                return _error('Line not found', 404)

            body = _get_json_body()
            update_vals = {}

            if 'product_id' in body:
                update_vals['product_id'] = int(body['product_id'])
            if 'product_uom_id' in body:
                update_vals['product_uom_id'] = int(body['product_uom_id'])
            if 'warehouse_id' in body:
                update_vals['warehouse_id'] = int(body['warehouse_id'])
            if 'location_id' in body:
                update_vals['location_id'] = int(body['location_id']) if body['location_id'] else False
            if 'quantity' in body:
                update_vals['quantity'] = float(body['quantity'])
            if 'unit_price' in body:
                update_vals['unit_price'] = float(body['unit_price'])
            if 'discount_percent' in body:
                update_vals['discount_percent'] = float(body['discount_percent'])
            if 'custom_product_name' in body:
                update_vals['custom_product_name'] = body['custom_product_name'] or False
            if 'sequence' in body:
                update_vals['sequence'] = int(body['sequence'])

            if update_vals:
                line.write(update_vals)

            return _success(_serialize_line(line), message='Line updated')
        except Exception as e:
            _logger.error('[POS API] update_order_line: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/lines/<int:line_id>',
                type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_order_line(self, order_id, line_id, **kwargs):
        """Delete an order line.

        DELETE /api/pos_perfume/v1/orders/123/lines/456
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot delete lines from a '{order.state}' order")

            line = request.env['pos.perfume.order.line'].browse(line_id)
            if not line.exists() or line.order_id.id != order_id:
                return _error('Line not found', 404)

            line.unlink()
            return _success({'deleted': True, 'line_id': line_id}, message='Line deleted')
        except Exception as e:
            _logger.error('[POS API] delete_order_line: %s', e, exc_info=True)
            return _error(str(e), 500)
