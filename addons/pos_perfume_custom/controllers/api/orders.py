# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Orders CRUD + Order Lines CRUD

Routes:
  GET    /api/pos_perfume/v1/orders                              List orders
  POST   /api/pos_perfume/v1/orders                              Create order (draft)
  GET    /api/pos_perfume/v1/orders/<id>                         Get single order
  PUT    /api/pos_perfume/v1/orders/<id>                         Update order header + optionally replace lines (save)
  DELETE /api/pos_perfume/v1/orders/<id>                         Cancel order

Order Lines:
  POST   /api/pos_perfume/v1/orders/<id>/lines                   Add a line
  PUT    /api/pos_perfume/v1/orders/<id>/lines/<lid>             Update a line
  DELETE /api/pos_perfume/v1/orders/<id>/lines/<lid>             Delete a line

State Transitions (in order_actions.py):
  POST   /api/pos_perfume/v1/orders/<id>/confirm                 Draft/Quotation → Sale Order
  POST   /api/pos_perfume/v1/orders/<id>/quotation               Draft → Quotation
  POST   /api/pos_perfume/v1/orders/<id>/draft                   Quotation → Draft (reset)
  POST   /api/pos_perfume/v1/orders/<id>/cancel                  Any → Cancelled
"""

import logging
from odoo import http
from odoo.http import request

from ._helpers import (
    _success, _error, _get_json_body,
    _serialize_order, _serialize_line, _build_line_vals, _check_auth,
)

_logger = logging.getLogger(__name__)

# States that allow editing header and lines
_EDITABLE_STATES = ('draft', 'quotation')
# States that allow cancellation
_CANCELLABLE_STATES = ('draft', 'quotation', 'sale')


def _get_order(order_id):
    """Browse and return a pos.perfume.order or None if not found."""
    order = request.env['pos.perfume.order'].browse(order_id)
    return order if order.exists() else None


class PosPerfumeApiOrders(http.Controller):

    # -----------------------------------------------------------------------
    # List & Create
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders', type='http', auth='none',
                methods=['GET'], csrf=False)
    def list_orders(self, query='', state='', limit='50', offset='0',
                    partner_id='', user_id='', date_from='', date_to='',
                    sap_synced='', **kwargs):
        """List POS orders with optional filters.

        Query params:
          query       search by order name
          state       draft | quotation | sale | done | cancel
          partner_id  filter by customer ID
          user_id     filter by salesperson ID
          date_from   YYYY-MM-DD
          date_to     YYYY-MM-DD
          sap_synced  true | false
          limit / offset
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            limit  = int(limit)
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
            orders = OrderModel.search(domain, limit=limit, offset=offset,
                                       order='date desc, id desc')
            total = OrderModel.search_count(domain)

            items = [
                {
                    'id':              o.id,
                    'name':            o.name,
                    'date':            o.date.isoformat() if o.date else None,
                    'state':           o.state,
                    'partner_id':      o.partner_id.id if o.partner_id else None,
                    'partner_name':    o.partner_id.name if o.partner_id else '',
                    'user_id':         o.user_id.id if o.user_id else None,
                    'user_name':       o.user_id.name if o.user_id else '',
                    'invoice_type':    o.invoice_type or '',
                    'amount_total':    o.amount_total,
                    'amount_total_iqd': o.amount_total_iqd,
                    'sap_synced':      o.sap_synced,
                    'sap_doc_num':     o.sap_doc_num or '',
                    'note':            o.note or '',
                    'lines_count':     len(o.order_line_ids),
                }
                for o in orders
            ]

            return _success({'total': total, 'offset': offset, 'limit': limit,
                             'items': items})
        except Exception as e:
            _logger.error('[POS API] list_orders: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders', type='http', auth='none',
                methods=['POST'], csrf=False)
    def create_order(self, **kwargs):
        """Create a new POS order in draft state.

        Body:
        {
            "partner_id":   10,           required
            "pricelist_id": 1,            optional
            "invoice_type": "1",          optional  (1-8)
            "note":         "...",        optional
            "exchange_rate": 1480.0,      optional
            "user_id":      3,            optional
            "order_lines": [              optional — can be added later
                {
                    "product_id":       42,
                    "warehouse_id":     1,
                    "quantity":         2.0,
                    "unit_price":       15.0,
                    "product_uom_id":   3,    optional
                    "discount_percent": 0.0,  optional
                    "custom_product_name": "" optional
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

            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            if not partner.exists():
                return _error('Customer not found', 404)

            # Resolve pricelist
            pricelist_id = body.get('pricelist_id')
            if pricelist_id:
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    return _error('Pricelist not found', 404)
            else:
                default_pl_id = request.env['pos.perfume.order']._get_default_pricelist()
                pricelist = (request.env['product.pricelist'].browse(default_pl_id)
                             if default_pl_id else None)
                if not pricelist or not pricelist.exists():
                    return _error('No pricelist found. Please provide pricelist_id.')

            order_vals = {
                'partner_id':   partner.id,
                'pricelist_id': pricelist.id,
                'state':        'draft',
            }
            if body.get('invoice_type'):
                order_vals['invoice_type'] = str(body['invoice_type'])
            if body.get('note'):
                order_vals['note'] = body['note']
            if body.get('exchange_rate'):
                order_vals['exchange_rate'] = float(body['exchange_rate'])
            if body.get('user_id'):
                order_vals['user_id'] = int(body['user_id'])

            # Build inline order lines (optional)
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
    # Get / Update / Delete
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http',
                auth='none', methods=['GET'], csrf=False)
    def get_order(self, order_id, **kwargs):
        """Get full order details including all lines."""
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            return _success(_serialize_order(order))
        except Exception as e:
            _logger.error('[POS API] get_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http',
                auth='none', methods=['PUT'], csrf=False)
    def update_order(self, order_id, **kwargs):
        """Update order header and optionally replace all order lines.

        Only allowed on draft / quotation orders.
        Body: { "partner_id", "pricelist_id", "note", "invoice_type",
                "exchange_rate", "user_id", "order_lines" }  — all optional
        "order_lines" replaces ALL existing lines when provided.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            if order.state not in _EDITABLE_STATES:
                return _error(
                    f"Cannot edit an order in '{order.state}' state. "
                    f"Editable states: {list(_EDITABLE_STATES)}")

            body = _get_json_body()
            update_vals = {}
            for key in ('partner_id', 'pricelist_id', 'user_id'):
                if key in body:
                    update_vals[key] = int(body[key]) if body[key] else False
            if 'exchange_rate' in body:
                update_vals['exchange_rate'] = float(body['exchange_rate'])
            if 'invoice_type' in body:
                update_vals['invoice_type'] = str(body['invoice_type']) if body['invoice_type'] else False
            if 'note' in body:
                update_vals['note'] = body['note'] or False

            # Replace all order lines if provided (for auto-save use-case)
            if 'order_lines' in body:
                new_lines = []
                for line_data in body['order_lines']:
                    lv = _build_line_vals(line_data)
                    if isinstance(lv, str):
                        return _error(lv)
                    new_lines.append((0, 0, lv))
                update_vals['order_line_ids'] = [(5, 0, 0)] + new_lines

            if update_vals:
                order.write(update_vals)
                # Invalidate ORM cache so serialiser reads fresh data from DB
                order.invalidate_recordset()

            return _success(_serialize_order(order), message='Order updated')
        except Exception as e:
            _logger.error('[POS API] update_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>', type='http',
                auth='none', methods=['DELETE'], csrf=False)
    def delete_order(self, order_id, **kwargs):
        """Cancel an order (sets state to 'cancel')."""
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            if order.state == 'done':
                return _error("Cannot cancel a done order")

            order.action_cancel()
            return _success({'id': order_id, 'state': 'cancel'},
                            message='Order cancelled')
        except Exception as e:
            _logger.error('[POS API] delete_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Order Lines — add / update / delete
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/lines',
                type='http', auth='none', methods=['POST'], csrf=False)
    def add_order_line(self, order_id, **kwargs):
        """Add a new line to an existing order.

        Body:
        {
            "product_id":       42,   required
            "warehouse_id":     1,    required
            "quantity":         2.0,
            "unit_price":       15.0,
            "product_uom_id":   3,    optional — defaults to product sales UoM
            "discount_percent": 0.0,
            "custom_product_name": ""
        }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(
                    f"Cannot add lines to a '{order.state}' order.")

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

        Body (all optional):
        {
            "product_id": 42, "product_uom_id": 3, "warehouse_id": 1,
            "quantity": 3.0, "unit_price": 20.0, "discount_percent": 5.0,
            "custom_product_name": "...", "sequence": 20
        }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(
                    f"Cannot edit lines of a '{order.state}' order.")

            line = request.env['pos.perfume.order.line'].browse(line_id)
            if not line.exists() or line.order_id.id != order_id:
                return _error('Line not found', 404)

            body = _get_json_body()
            update_vals = {}
            _int_fields   = ('product_id', 'product_uom_id', 'warehouse_id')
            _float_fields = ('quantity', 'unit_price', 'discount_percent')
            _str_fields   = ('custom_product_name',)

            for f in _int_fields:
                if f in body:
                    update_vals[f] = int(body[f]) if body[f] else False
            for f in _float_fields:
                if f in body:
                    update_vals[f] = float(body[f])
            for f in _str_fields:
                if f in body:
                    update_vals[f] = body[f] or False
            if 'sequence' in body:
                update_vals['sequence'] = int(body['sequence'])
            if 'location_id' in body:
                update_vals['location_id'] = int(body['location_id']) if body['location_id'] else False

            if update_vals:
                line.write(update_vals)

            return _success(_serialize_line(line), message='Line updated')
        except Exception as e:
            _logger.error('[POS API] update_order_line: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/lines/<int:line_id>',
                type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_order_line(self, order_id, line_id, **kwargs):
        """Delete an order line."""
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = _get_order(order_id)
            if not order:
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(
                    f"Cannot delete lines from a '{order.state}' order.")

            line = request.env['pos.perfume.order.line'].browse(line_id)
            if not line.exists() or line.order_id.id != order_id:
                return _error('Line not found', 404)

            line.unlink()
            return _success({'deleted': True, 'line_id': line_id},
                            message='Line deleted')
        except Exception as e:
            _logger.error('[POS API] delete_order_line: %s', e, exc_info=True)
            return _error(str(e), 500)
