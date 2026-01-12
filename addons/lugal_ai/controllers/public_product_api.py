# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LugalPublicProductAPIController(http.Controller):
    """
    Public (no Odoo session) product endpoints for internal apps.

    Security model:
    - auth='none' (no Odoo login required)
    - require a shared token in request header:
        X-Lugal-Token: <token>
    - token is configured server-side in ir.config_parameter:
        lugal_ai.public_api_token
    """

    def _check_token(self):
        expected = request.env['ir.config_parameter'].sudo().get_param('lugal_ai.public_api_token') or ''
        expected = (expected or '').strip()

        provided = request.httprequest.headers.get('X-Lugal-Token') or ''
        provided = (provided or '').strip()

        # If token is NOT configured, allow access (no-login/no-token mode).
        # You can secure this later by setting `lugal_ai.public_api_token`.
        if not expected:
            return True, None

        if not provided or provided != expected:
            return False, 'Unauthorized'

        return True, None

    @http.route('/lugal/public/products/search', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def public_search_products(self, query='', filters=None, limit=50, **kwargs):
        """
        Public product search (no login). Returns basic product data:
        - name, list_price, uom, qty_available, etc.
        """
        ok, err = self._check_token()
        if not ok:
            return {'success': False, 'error': err}

        try:
            domain = []

            if query:
                domain += ['|', ('name', 'ilike', query), ('default_code', 'ilike', query)]

            if filters:
                if filters.get('category_id'):
                    domain.append(('categ_id', '=', filters['category_id']))
                if filters.get('min_price'):
                    domain.append(('list_price', '>=', filters['min_price']))
                if filters.get('max_price'):
                    domain.append(('list_price', '<=', filters['max_price']))
                if filters.get('available_only'):
                    domain.append(('qty_available', '>', 0))

            Product = request.env['product.product'].sudo()
            products = Product.search(domain, limit=limit, order='name')
            total_count = Product.search_count(domain)

            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code,
                    'barcode': product.barcode,
                    'list_price': product.list_price,
                    'qty_available': product.qty_available,
                    'uom_name': product.uom_id.name,
                    'uom_id': product.uom_id.id,
                    'category': product.categ_id.name if product.categ_id else '',
                    'image_url': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else '',
                })

            return {
                'success': True,
                'products': products_data,
                'total_count': total_count,
            }
        except Exception as e:
            _logger.error(f'Public product search error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/lugal/public/products/categories', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def public_get_categories(self, **kwargs):
        ok, err = self._check_token()
        if not ok:
            return {'success': False, 'error': err}

        try:
            categories = request.env['product.category'].sudo().search([], order='name')
            return {
                'success': True,
                'categories': [{
                    'id': c.id,
                    'name': c.complete_name,
                    'parent_id': c.parent_id.id if c.parent_id else None,
                } for c in categories],
            }
        except Exception as e:
            _logger.error(f'Public categories error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}


