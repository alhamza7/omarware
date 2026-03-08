# -*- coding: utf-8 -*-
"""
POS Bridge — CRM Call Dialog "Create Invoice" linked to pos.perfume.order (same Odoo instance).
Uses ORM only; requires pos_perfume_custom (and thus sale, product, stock) when using order endpoints.
"""

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _pos_available():
    """Return True if pos.perfume.order model is available."""
    return 'pos.perfume.order' in request.env


def _get_setup_data():
    """Return pricelists, warehouses, invoice_types, exchange_rate (same shape as POS /setup)."""
    env = request.env
    pricelists = env['product.pricelist'].search([('active', '=', True)])
    pricelist_data = [{'id': p.id, 'name': p.name, 'currency_id': p.currency_id.id} for p in pricelists]
    warehouses = env['stock.warehouse'].search([('active', '=', True)])
    warehouse_data = [{'id': w.id, 'name': w.name, 'code': w.code} for w in warehouses]
    exchange_rate = float(
        env['ir.config_parameter'].sudo().get_param('pos_perfume.default_exchange_rate_usd_iqd', '1470.0')
    )
    invoice_types = [
        {'key': '1', 'label': 'زبون محل'},
        {'key': '2', 'label': 'شركات توصيل'},
        {'key': '3', 'label': 'نقليات'},
        {'key': '4', 'label': 'ديلفري'},
        {'key': '5', 'label': 'NBS'},
        {'key': '6', 'label': 'شورجة'},
        {'key': '7', 'label': 'NA'},
        {'key': '8', 'label': 'مكاتب الشورجة'},
    ]
    default_pl_id = False
    if _pos_available():
        default_pl_id = request.env['pos.perfume.order']._get_default_pricelist()
    if not default_pl_id and pricelist_data:
        default_pl_id = pricelist_data[0]['id']
    return {
        'pricelists': pricelist_data,
        'default_pricelist_id': default_pl_id,
        'warehouses': warehouse_data,
        'invoice_types': invoice_types,
        'exchange_rate': exchange_rate,
        'currency': 'USD',
        'secondary_currency': 'IQD',
    }


def _build_line_vals(data):
    """Build order line vals for pos.perfume.order.line. Returns (vals_dict, error_message)."""
    product_id = data.get('product_id')
    product_uom_id = data.get('product_uom_id')
    warehouse_id = data.get('warehouse_id')
    if not product_id:
        return None, 'product_id is required for each order line'
    if not warehouse_id:
        return None, 'warehouse_id is required for each order line'
    product = request.env['product.product'].browse(int(product_id))
    if not product.exists():
        return None, 'Product not found'
    uom = product.uom_id
    if product_uom_id:
        uom = request.env['uom.uom'].browse(int(product_uom_id))
        if not uom.exists():
            return None, 'UoM not found'
    warehouse = request.env['stock.warehouse'].browse(int(warehouse_id))
    if not warehouse.exists():
        return None, 'Warehouse not found'
    location_id = warehouse.lot_stock_id.id if warehouse.lot_stock_id else False
    return {
        'product_id': product.id,
        'product_uom_id': uom.id,
        'warehouse_id': warehouse.id,
        'location_id': location_id,
        'quantity': float(data.get('quantity', 1.0)),
        'unit_price': float(data.get('unit_price', product.list_price)),
        'discount_percent': float(data.get('discount_percent', 0.0)),
        'custom_product_name': data.get('custom_product_name') or '',
        'sequence': int(data.get('sequence', 10)),
    }, None


class PosBridgeController(http.Controller):

    @http.route('/api/crm/pos/invoice_context', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def invoice_context(self, call_id=None, customer_id=None, **kwargs):
        """Return setup data + partner_id + last order for the call's customer. Pre-fills invoice form."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            data = _get_setup_data()
            partner_id = None
            last_order = None
            if customer_id:
                customer = request.env['lugal.crm.customer'].browse(customer_id)
                if customer.exists():
                    if customer.partner_id:
                        partner_id = customer.partner_id.id
                    else:
                        # Match by phone
                        for phone in [customer.phone_1, customer.phone_2, customer.phone_3]:
                            if not phone:
                                continue
                            partner = request.env['res.partner'].search([
                                ('customer_rank', '>', 0),
                                '|', ('phone', 'ilike', phone), ('mobile', 'ilike', phone),
                            ], limit=1)
                            if partner:
                                partner_id = partner.id
                                break
                    if partner_id and _pos_available():
                        last = request.env['pos.perfume.order'].search(
                            [('partner_id', '=', partner_id), ('state', 'in', ['sale', 'done'])],
                            limit=1, order='date desc'
                        )
                        if last:
                            last_order = {
                                'id': last.id,
                                'name': last.name,
                                'date': last.date.isoformat() if last.date else None,
                                'amount_total': last.amount_total,
                                'state': last.state,
                            }
            data['partner_id'] = partner_id
            data['last_order'] = last_order
            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'invoice_context')

    @http.route('/api/crm/pos/products', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def products(self, query='', pricelist_id=None, limit=80, offset=0, **kwargs):
        """Product search for POS (product.product)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('sale_ok', '=', True), ('active', '=', True)]
            if query:
                if hasattr(request.env['product.product'], 'foreign_name'):
                    domain += ['|', '|', ('name', 'ilike', query), ('default_code', 'ilike', query), ('foreign_name', 'ilike', query)]
                else:
                    domain += ['|', ('name', 'ilike', query), ('default_code', 'ilike', query)]
            products = request.env['product.product'].search(domain, limit=limit, offset=offset, order='name asc')
            total = request.env['product.product'].search_count(domain)
            items = []
            for p in products:
                foreign_name = getattr(p, 'foreign_name', '') or ''
                items.append({
                    'id': p.id,
                    'name': p.name,
                    'default_code': p.default_code or '',
                    'foreign_name': foreign_name,
                    'uom_id': {'id': p.uom_id.id, 'name': p.uom_id.name},
                    'list_price': p.list_price,
                    'qty_available': p.qty_available,
                })
            return {'success': True, 'data': {'total': total, 'offset': offset, 'limit': limit, 'items': items}}
        except Exception as e:
            return crm_error(e, 'products')

    @http.route('/api/crm/pos/product_detail', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def product_detail(self, product_id, pricelist_id=None, **kwargs):
        """Full product data: UoMs, warehouses, price (for adding to order)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            product = request.env['product.product'].browse(int(product_id))
            if not product.exists():
                return {'success': False, 'error': 'Product not found'}
            pricelist = None
            if pricelist_id:
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
            if not pricelist or not pricelist.exists():
                pl_id = _get_setup_data().get('default_pricelist_id')
                if pl_id:
                    pricelist = request.env['product.pricelist'].browse(pl_id)
            price_unit = product.list_price
            if pricelist and pricelist.exists():
                try:
                    price_unit = pricelist._get_product_price(product, 1.0) or product.list_price
                except Exception:
                    price_unit = product.list_price
            # Simple UoM list (base UoM only if no multi-uom)
            available_uoms = [{'id': product.uom_id.id, 'name': product.uom_id.name, 'price': price_unit}]
            warehouses = request.env['stock.warehouse'].search([('active', '=', True)])
            warehouse_data = []
            for w in warehouses:
                quants = request.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', 'child_of', w.lot_stock_id.id if w.lot_stock_id else 0),
                ])
                qty = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
                warehouse_data.append({'id': w.id, 'name': w.name, 'code': w.code, 'quantity': qty})
            return {
                'success': True,
                'data': {
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_uom_id': product.uom_id.id,
                    'product_uom_name': product.uom_id.name,
                    'price_unit': price_unit,
                    'available_qty': product.qty_available,
                    'default_code': product.default_code or '',
                    'foreign_name': getattr(product, 'foreign_name', '') or '',
                    'available_uoms': available_uoms,
                    'warehouses': warehouse_data,
                },
            }
        except Exception as e:
            return crm_error(e, 'product_detail')

    @http.route('/api/crm/pos/uom_price', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def uom_price(self, product_id, pricelist_id, uom_id, **kwargs):
        """Price when UoM changes on a line."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            product = request.env['product.product'].browse(int(product_id))
            if not product.exists():
                return {'success': False, 'error': 'Product not found'}
            pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
            if not pricelist or not pricelist.exists():
                return {'success': False, 'error': 'Pricelist not found'}
            uom = request.env['uom.uom'].browse(int(uom_id))
            if not uom.exists():
                return {'success': False, 'error': 'UoM not found'}
            try:
                price = pricelist._get_product_price(product, 1.0, uom=uom) or product.list_price
            except Exception:
                price = product.list_price
            return {'success': True, 'data': {'price_unit': price}}
        except Exception as e:
            return crm_error(e, 'uom_price')

    @http.route('/api/crm/pos/orders/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def orders_create(self, call_id=None, partner_id=None, pricelist_id=None, invoice_type='1', order_lines=None, exchange_rate=None, **kwargs):
        """Create POS order, confirm it, and link to crm_call."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not _pos_available():
                return {'success': False, 'error': 'POS Perfume module (pos_perfume_custom) is required'}
            if not partner_id:
                return {'success': False, 'error': 'partner_id is required'}
            partner = request.env['res.partner'].browse(int(partner_id))
            if not partner.exists():
                return {'success': False, 'error': 'Customer not found'}
            Order = request.env['pos.perfume.order']
            pl = None
            if pricelist_id:
                pl = request.env['product.pricelist'].browse(int(pricelist_id))
            if not pl or not pl.exists():
                pl_id = Order._get_default_pricelist()
                pl = request.env['product.pricelist'].browse(pl_id) if pl_id else None
            if not pl or not pl.exists():
                return {'success': False, 'error': 'Pricelist not found'}
            order_vals = {
                'partner_id': partner.id,
                'pricelist_id': pl.id,
                'state': 'draft',
                'invoice_type': str(invoice_type),
                'user_id': request.env.uid,
            }
            if exchange_rate is not None:
                order_vals['exchange_rate'] = float(exchange_rate)
            line_vals_list = []
            for line_data in (order_lines or []):
                lv, err = _build_line_vals(line_data)
                if err:
                    return {'success': False, 'error': err}
                line_vals_list.append((0, 0, lv))
            if line_vals_list:
                order_vals['order_line_ids'] = line_vals_list
            order = Order.create(order_vals)
            if line_vals_list:
                order.action_confirm()
            if call_id:
                call = request.env['lugal.crm.call'].browse(call_id)
                if call.exists():
                    call.write({
                        'pos_order_id': order.id,
                        'pos_order_name': order.name,
                        'pos_order_total': order.amount_total,
                        'pos_order_total_iqd': getattr(order, 'amount_total_iqd', 0),
                        'pos_order_state': order.state,
                        'pos_sale_order_name': order.sale_order_id.name if order.sale_order_id else '',
                        'pos_sap_synced': getattr(order, 'sap_synced', False),
                    })
            return {
                'success': True,
                'data': {
                    'order_id': order.id,
                    'order_name': order.name,
                    'state': order.state,
                    'amount_total': order.amount_total,
                    'sale_order_name': order.sale_order_id.name if order.sale_order_id else '',
                },
            }
        except Exception as e:
            return crm_error(e, 'orders_create')

    @http.route('/api/crm/pos/orders/<int:order_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def order_get(self, order_id, **kwargs):
        """Get full POS order details."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not _pos_available():
                return {'success': False, 'error': 'POS Perfume module is required'}
            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Order not found'}
            data = {
                'id': order.id,
                'name': order.name,
                'state': order.state,
                'partner_id': order.partner_id.id if order.partner_id else None,
                'amount_total': order.amount_total,
                'amount_total_iqd': getattr(order, 'amount_total_iqd', 0),
                'sale_order_id': order.sale_order_id.id if order.sale_order_id else None,
                'sale_order_name': order.sale_order_id.name if order.sale_order_id else '',
                'sap_synced': getattr(order, 'sap_synced', False),
            }
            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'order_get')

    @http.route('/api/crm/pos/customer_orders', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_orders(self, partner_id, limit=20, **kwargs):
        """Order history for a partner (for last order / outstanding in call dialog)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not _pos_available():
                return {'success': True, 'data': {'items': []}}
            domain = [('partner_id', '=', int(partner_id))]
            orders = request.env['pos.perfume.order'].search(domain, limit=limit, order='date desc')
            items = [{
                'id': o.id,
                'name': o.name,
                'date': o.date.isoformat() if o.date else None,
                'state': o.state,
                'amount_total': o.amount_total,
            } for o in orders]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'customer_orders')
