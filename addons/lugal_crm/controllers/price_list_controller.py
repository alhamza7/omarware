# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _product_to_dict(product, pricelist=None, available_uoms=None):
    """
    Serialize product.product to a dict for the CRM price-list view.
    Includes pricelist price (when provided) and UoM options.
    """
    price = product.list_price
    if pricelist and pricelist.exists():
        try:
            price = pricelist._get_product_price(product, 1.0) or product.list_price
        except Exception:
            price = product.list_price

    uom_name = product.uom_id.name if product.uom_id else ''
    categ_name = product.categ_id.name if product.categ_id else ''
    foreign_name = getattr(product, 'foreign_name', '') or getattr(product.product_tmpl_id, 'foreign_name', '') or ''

    return {
        'id': product.id,
        'name': product.name or '',
        'foreign_name': foreign_name,
        'item_code': product.default_code or '',
        'category_id': product.categ_id.id if product.categ_id else None,
        'category_name': categ_name,
        'uom_id': product.uom_id.id if product.uom_id else None,
        'uom_name': uom_name,
        'price': price,
        'list_price': product.list_price,
        'currency': pricelist.currency_id.name if pricelist and pricelist.exists() else 'USD',
        'image_url': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else '',
        'available_uoms': available_uoms or [],
        'active': product.active,
    }


def _get_uoms_for_product(product, pricelist):
    """Collect all UoMs defined in pricelist items for this product, with their prices."""
    if not pricelist or not pricelist.exists():
        return []
    items = request.env['product.pricelist.item'].search([
        ('pricelist_id', '=', pricelist.id),
        ('product_id', '=', product.id),
        ('compute_price', '=', 'fixed'),
    ])
    uom_ids = items.mapped('uom_id').ids
    if not uom_ids:
        return []
    uoms = request.env['uom.uom'].browse(uom_ids)
    result = []
    for uom in uoms:
        try:
            uom_price = pricelist._get_product_price(product, 1.0, uom=uom)
        except Exception:
            uom_price = product.list_price
        result.append({'uom_id': uom.id, 'uom_name': uom.name, 'price': uom_price})
    return result


def _resolve_pricelist(pricelist_id):
    """Return a pricelist record; fallback to 'Price list 1' then first active pricelist."""
    if pricelist_id:
        pl = request.env['product.pricelist'].browse(pricelist_id)
        if pl.exists():
            return pl

    for name_hint in ['Price list 1', 'Pricelist 1', 'Standard']:
        pl = request.env['product.pricelist'].search([('name', 'ilike', name_hint), ('active', '=', True)], limit=1)
        if pl:
            return pl

    return request.env['product.pricelist'].search([('active', '=', True)], limit=1)


class PriceListController(http.Controller):

    @http.route('/api/crm/pricelist/categories', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_categories(self, **kwargs):
        """List product categories (brands) available in the pricelist — for filter dropdowns."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Categories that have active products
            products = request.env['product.product'].search([
                ('active', '=', True), ('sale_ok', '=', True),
            ])
            categ_ids = products.mapped('categ_id')
            items = [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id.id if c.parent_id else None}
                     for c in categ_ids.sorted('name')]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'list_categories')

    @http.route('/api/crm/pricelist/products', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_products(self, page=1, per_page=50, search=None, category_id=None,
                      uom_id=None, pricelist_id=None, new_releases_only=False,
                      discount_only=False, **kwargs):
        """
        List products for the CRM price-list view.
        Supports filters: category (brand), UoM, search, new releases, discount flag.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            pricelist = _resolve_pricelist(pricelist_id)

            domain = [('active', '=', True), ('sale_ok', '=', True)]
            if category_id:
                domain.append(('categ_id', '=', category_id))
            if search:
                if request.env['product.product']._fields.get('foreign_name'):
                    domain += ['|', '|',
                               ('name', 'ilike', search),
                               ('default_code', 'ilike', search),
                               ('foreign_name', 'ilike', search)]
                else:
                    domain += ['|', ('name', 'ilike', search), ('default_code', 'ilike', search)]

            Product = request.env['product.product']
            total = Product.search_count(domain)
            offset = (page - 1) * per_page
            products = Product.search(domain, limit=per_page, offset=offset, order='name asc')

            # If discount_only → filter to products appearing in a discounted pricelist
            if discount_only and pricelist:
                discounted_ids = request.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('compute_price', '=', 'percentage'),
                    ('percent_price', '>', 0),
                ]).mapped('product_id').ids
                products = products.filtered(lambda p: p.id in discounted_ids)
                total = len(products)

            items = []
            for p in products:
                uoms = _get_uoms_for_product(p, pricelist)
                items.append(_product_to_dict(p, pricelist, uoms))

            return {
                'success': True,
                'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'list_products')

    @http.route('/api/crm/pricelist/products/<int:product_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_product(self, product_id, pricelist_id=None, **kwargs):
        """Get full product detail with all UoM prices and stock info."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            product = request.env['product.product'].browse(product_id)
            if not product.exists() or not product.active:
                return {'success': False, 'error': 'Product not found'}

            pricelist = _resolve_pricelist(pricelist_id)
            uoms = _get_uoms_for_product(product, pricelist)
            data = _product_to_dict(product, pricelist, uoms)

            # Stock qty
            try:
                data['qty_on_hand'] = product.qty_available
                data['qty_reserved'] = product.virtual_available
            except Exception:
                data['qty_on_hand'] = 0
                data['qty_reserved'] = 0

            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'get_product')

    @http.route('/api/crm/pricelist/pricelists', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_pricelists(self, **kwargs):
        """List available pricelists (for dropdown in the CRM UI)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            pricelists = request.env['product.pricelist'].search([('active', '=', True)], order='name asc')
            items = [{'id': p.id, 'name': p.name, 'currency': p.currency_id.name} for p in pricelists]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'list_pricelists')

    @http.route('/api/crm/pricelist/requested_items/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_requested_item(self, customer_id, product_name, notes=None, **kwargs):
        """
        Customer requests an item not currently in the price list.
        Creates a crm.requested.item record linked to the customer.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not customer_id or not product_name:
                return {'success': False, 'error': 'customer_id and product_name are required'}
            item = request.env['lugal.crm.requested.item'].create({
                'customer_id': customer_id,
                'product_name': product_name,
                'notes': notes or '',
                'requested_by_id': request.env.uid,
            })
            return {'success': True, 'data': {'id': item.id, 'product_name': item.product_name}}
        except Exception as e:
            return crm_error(e, 'create_requested_item')

    @http.route('/api/crm/pricelist/requested_items', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_requested_items(self, page=1, per_page=50, customer_id=None, status=None, **kwargs):
        """List requested (out-of-catalog) items."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if status:
                domain.append(('status', '=', status))
            RI = request.env['lugal.crm.requested.item']
            total = RI.search_count(domain)
            items_rec = RI.search(domain, limit=per_page, offset=(page - 1) * per_page, order='create_date desc')
            items = [{
                'id': r.id,
                'customer_id': r.customer_id.id if r.customer_id else None,
                'customer_name': r.customer_id.name if r.customer_id else '',
                'product_name': r.product_name or '',
                'status': r.status,
                'notes': r.notes or '',
                'created_at': r.create_date.isoformat() if r.create_date else None,
            } for r in items_rec]
            return {'success': True, 'data': {'items': items, 'total': total}}
        except Exception as e:
            return crm_error(e, 'list_requested_items')

    @http.route('/api/crm/pricelist/requested_items/<int:item_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_requested_item_status(self, item_id, status, **kwargs):
        """Update status of a requested item: pending / notified / fulfilled / cancelled."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            item = request.env['lugal.crm.requested.item'].browse(item_id)
            if not item.exists() or item.is_deleted:
                return {'success': False, 'error': 'Requested item not found'}
            item.write({'status': status})
            return {'success': True, 'data': {'id': item.id, 'status': item.status}}
        except Exception as e:
            return crm_error(e, 'update_requested_item_status')

    @http.route('/api/crm/pricelist/requested_items/<int:item_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_requested_item(self, item_id, **kwargs):
        """Soft-delete a requested item."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            item = request.env['lugal.crm.requested.item'].browse(item_id)
            if not item.exists():
                return {'success': False, 'error': 'Requested item not found'}
            item.write({'is_deleted': True})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_requested_item')
