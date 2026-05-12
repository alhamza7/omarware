# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error
from ._permissions import require_permission

_logger = logging.getLogger(__name__)


def _order_to_dict(order):
    """Serialize a pos.perfume.order to a delivery-tracking-friendly dict."""
    lines = []
    for line in order.order_line_ids:
        lines.append({
            'product_name': line.product_id.name if line.product_id else '',
            'item_code': line.product_id.default_code if line.product_id else '',
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'line_total': line.line_total,
        })
    return {
        'id': order.id,
        'name': order.name or '',
        'state': order.state or '',
        'date_order': order.date_order.isoformat() if order.date_order else None,
        'amount_total': order.amount_total,
        'currency': order.currency_id.name if order.currency_id else 'USD',
        'partner_id': order.partner_id.id if order.partner_id else None,
        'customer_name': order.partner_id.name if order.partner_id else '',
        'warehouse': order.warehouse_id.name if order.warehouse_id else '',
        'sale_order_name': getattr(order, 'sale_order_name', '') or '',
        'delivery_status': getattr(order, 'delivery_status', '') or '',
        'lines': lines,
    }


class DeliveryController(http.Controller):

    @http.route('/api/crm/delivery/customer_orders', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_orders(self, customer_id=None, partner_id=None, page=1, per_page=20, state=None, **kwargs):
        """
        Fetch POS orders for a CRM customer.
        Resolves customer → partner_id → pos.perfume.order.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('orders.list')
            if denied:
                return denied

            # Resolve partner_id from CRM customer if needed
            resolved_partner_id = partner_id
            if customer_id and not resolved_partner_id:
                crm_customer = request.env['lugal.crm.customer'].sudo().browse(int(customer_id))
                if crm_customer.exists() and crm_customer.partner_id:
                    resolved_partner_id = crm_customer.partner_id.id

            if not resolved_partner_id:
                return {'success': True, 'data': {'items': [], 'total': 0, 'note': 'No linked partner'}}

            if not request.env.get('pos.perfume.order'):
                return {'success': True, 'data': {'items': [], 'total': 0, 'note': 'pos_perfume_custom not installed'}}

            domain = [('partner_id', '=', resolved_partner_id)]
            if state:
                domain.append(('state', '=', state))

            Order = request.env['pos.perfume.order'].sudo()
            total = Order.search_count(domain)
            orders = Order.search(domain, limit=per_page, offset=(page - 1) * per_page, order='date_order desc')

            return {
                'success': True,
                'data': {
                    'items': [_order_to_dict(o) for o in orders],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'customer_orders')

    @http.route('/api/crm/delivery/order/<int:order_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_order(self, order_id, **kwargs):
        """Get a single POS order with full line detail and delivery status."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('orders.view')
            if denied:
                return denied

            if not request.env.get('pos.perfume.order'):
                return {'success': False, 'error': 'pos_perfume_custom not installed'}

            order = request.env['pos.perfume.order'].sudo().browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Order not found'}

            data = _order_to_dict(order)

            # Attach stock picking / delivery info if available
            if hasattr(order, 'picking_ids') and order.picking_ids:
                data['deliveries'] = [{
                    'id': p.id,
                    'name': p.name,
                    'state': p.state,
                    'scheduled_date': p.scheduled_date.isoformat() if p.scheduled_date else None,
                    'date_done': p.date_done.isoformat() if p.date_done else None,
                    'carrier_name': p.carrier_id.name if hasattr(p, 'carrier_id') and p.carrier_id else '',
                    'tracking_ref': getattr(p, 'carrier_tracking_ref', '') or '',
                } for p in order.picking_ids]
            else:
                data['deliveries'] = []

            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'get_order')

    @http.route('/api/crm/delivery/orders/search', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def search_orders(self, query, limit=20, branch_id=None, **kwargs):
        """Search POS orders by order name, customer name, or item code."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('orders.list')
            if denied:
                return denied

            if not request.env.get('pos.perfume.order'):
                return {'success': True, 'data': {'items': []}}

            domain = ['|', '|',
                      ('name', 'ilike', query),
                      ('partner_id.name', 'ilike', query),
                      ('sale_order_name', 'ilike', query) if hasattr(request.env['pos.perfume.order'], 'sale_order_name') else ('name', 'ilike', query),
                      ]
            orders = request.env['pos.perfume.order'].sudo().search(domain, limit=limit, order='date_order desc')
            return {'success': True, 'data': {'items': [_order_to_dict(o) for o in orders]}}
        except Exception as e:
            return crm_error(e, 'search_orders')
