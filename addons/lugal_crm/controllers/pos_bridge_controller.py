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
from ._permissions import require_permission

_logger = logging.getLogger(__name__)


def _pos_available():
    """Return True if pos.perfume.order model is available."""
    return 'pos.perfume.order' in request.env


def _get_sales_uom(product):
    """
    Return the sales UoM for a product.
    Priority: sap.product.extended.sales_uom_id → product.uom_id (Odoo default).
    """
    try:
        ext = request.env['sap.product.extended'].sudo().search(
            [('product_id', '=', product.id)], limit=1
        )
        if ext and ext.sales_uom_id:
            return ext.sales_uom_id
    except Exception:
        pass
    return product.uom_id


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
    # Default to sales UoM (SAP-linked), not the inventory UoM
    uom = _get_sales_uom(product)
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
            denied = require_permission('orders.view')
            if denied:
                return denied
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
    def products(
        self,
        query='',
        search=None,
        pricelist_id=None,
        limit=80,
        offset=0,
        page=None,
        per_page=None,
        fetch_all=False,
        category_id=None,
        include_inactive=False,
        sale_ok=True,
        **kwargs,
    ):
        """Product search for POS (product.product). Supports pagination, fetch_all, category_id.

        ``search`` is an alias for ``query`` (CRM historically used ``search`` on the client).
        ``page`` / ``per_page`` override ``offset`` / ``limit`` when provided.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            text = (search if search not in (None, False) else None) or query or ''
            text = (text or '').strip()

            domain = []
            if not include_inactive:
                domain.append(('active', '=', True))
            if sale_ok is not False and sale_ok is not None:
                domain.append(('sale_ok', '=', True))
            if category_id:
                try:
                    domain.append(('categ_id', '=', int(category_id)))
                except (TypeError, ValueError):
                    pass
            if text:
                if hasattr(request.env['product.product'], 'foreign_name'):
                    domain += ['|', '|', ('name', 'ilike', text), ('default_code', 'ilike', text), ('foreign_name', 'ilike', text)]
                else:
                    domain += ['|', ('name', 'ilike', text), ('default_code', 'ilike', text)]

            Product = request.env['product.product'].sudo()
            total = Product.search_count(domain)

            # When the user types something that looks like an exact item code
            # (no spaces), also include any product whose default_code matches
            # case-insensitively — even if it is archived or has sale_ok=False.
            # This ensures items like LOC00516 that are deactivated in Odoo but
            # still exist in SAP are always findable by their exact code.
            _extra_by_code_ids: set = set()
            if text and ' ' not in text:
                extra = Product.with_context(active_test=False).search([
                    ('default_code', '=ilike', text),
                ], order='name asc')
                _extra_by_code_ids = set(extra.ids)

            fetch_all_flag = bool(fetch_all) or kwargs.get('fetch_all') is True

            if page is not None or per_page is not None:
                try:
                    page_n = max(1, int(page or 1))
                except (TypeError, ValueError):
                    page_n = 1
                try:
                    per_n = int(per_page) if per_page is not None else int(limit or 80)
                except (TypeError, ValueError):
                    per_n = 80
                if fetch_all_flag or per_n <= 0:
                    products = Product.search(domain, order='name asc') if total else Product.browse()
                    offset_out = 0
                    limit_out = 0
                else:
                    per_n = max(per_n, 1)
                    offset_calc = (page_n - 1) * per_n
                    products = Product.search(domain, limit=per_n, offset=offset_calc, order='name asc')
                    offset_out = offset_calc
                    limit_out = per_n
            elif fetch_all_flag or int(limit or 0) <= 0:
                products = Product.search(domain, order='name asc') if total else Product.browse()
                offset_out = 0
                limit_out = 0
            else:
                try:
                    lim = int(limit or 80)
                except (TypeError, ValueError):
                    lim = 80
                lim = max(lim, 1)
                try:
                    off = int(offset or 0)
                except (TypeError, ValueError):
                    off = 0
                products = Product.search(domain, limit=lim, offset=off, order='name asc')
                offset_out = off
                limit_out = lim

            # Merge exact-code matches (including inactive) that weren't already
            # returned by the normal domain search.
            seen_ids = set(products.ids)
            extra_records = Product.browse()
            if _extra_by_code_ids:
                missing = _extra_by_code_ids - seen_ids
                if missing:
                    extra_records = Product.with_context(active_test=False).browse(list(missing))
                    total += len(extra_records)

            items = []
            for p in list(products) + list(extra_records):
                foreign_name = getattr(p, 'foreign_name', '') or ''
                sales_uom = _get_sales_uom(p)
                items.append({
                    'id': p.id,
                    'name': p.name,
                    'default_code': p.default_code or '',
                    'foreign_name': foreign_name,
                    'uom_id': {'id': sales_uom.id, 'name': sales_uom.name},
                    'list_price': p.list_price,
                    'qty_available': p.qty_available,
                    'active': p.active,
                })
            return {
                'success': True,
                'data': {
                    'total': total,
                    'offset': offset_out,
                    'limit': limit_out,
                    'returned': len(items),
                    'items': items,
                },
            }
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
            sales_uom = _get_sales_uom(product)
            if pricelist and pricelist.exists():
                try:
                    price_unit = pricelist._get_product_price(product, 1.0, uom=sales_uom) or product.list_price
                except Exception:
                    price_unit = product.list_price
            # All pricelist UoMs + guarantee the sales UoM is always present
            seen_uom_ids = set()
            available_uoms = []
            uom_items = request.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id if pricelist else 0),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('compute_price', '=', 'fixed'),
            ]) if pricelist and pricelist.exists() else []
            for item in uom_items:
                uom = item.product_uom_id if item.product_uom_id else sales_uom
                if not uom or uom.id in seen_uom_ids:
                    continue
                try:
                    uom_price = pricelist._get_product_price(product, 1.0, uom=uom)
                except Exception:
                    uom_price = product.list_price
                seen_uom_ids.add(uom.id)
                available_uoms.append({'id': uom.id, 'name': uom.name, 'price': uom_price})
            if sales_uom and sales_uom.id not in seen_uom_ids:
                available_uoms.insert(0, {'id': sales_uom.id, 'name': sales_uom.name, 'price': price_unit})
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
                    'product_uom_id': sales_uom.id if sales_uom else product.uom_id.id,
                    'product_uom_name': sales_uom.name if sales_uom else product.uom_id.name,
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
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('orders.create')
            if denied:
                return denied
            if not _pos_available():
                return {'success': False, 'error': 'POS Perfume module (pos_perfume_custom) is required'}
            if not partner_id:
                return {'success': False, 'error': 'partner_id is required'}
            # Use sudo() — Lugal permission tree is the authority; ORM-level group checks bypass
            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            if not partner.exists():
                return {'success': False, 'error': 'Customer not found'}
            Order = request.env['pos.perfume.order'].sudo()
            pl = None
            if pricelist_id:
                pl = request.env['product.pricelist'].sudo().browse(int(pricelist_id))
            if not pl or not pl.exists():
                pl_id = Order._get_default_pricelist()
                pl = request.env['product.pricelist'].sudo().browse(pl_id) if pl_id else None
            if not pl or not pl.exists():
                return {'success': False, 'error': 'Pricelist not found'}
            order_vals = {
                'partner_id': partner.id,
                'pricelist_id': pl.id,
                'state': 'draft',
                'invoice_type': str(invoice_type),
                'user_id': uid,
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
                call = request.env['lugal.crm.call'].sudo().browse(call_id)
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
            denied = require_permission('orders.view')
            if denied:
                return denied
            if not _pos_available():
                return {'success': False, 'error': 'POS Perfume module is required'}
            order = request.env['pos.perfume.order'].sudo().browse(order_id)
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
            denied = require_permission('orders.list')
            if denied:
                return denied
            if not _pos_available():
                return {'success': True, 'data': {'items': []}}
            domain = [('partner_id', '=', int(partner_id))]
            orders = request.env['pos.perfume.order'].sudo().search(domain, limit=limit, order='date desc')
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
