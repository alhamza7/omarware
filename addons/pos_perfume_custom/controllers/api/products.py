# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Products

Routes:
  GET  /api/pos_perfume/v1/products              List / search products
  POST /api/pos_perfume/v1/products/data         Full product data (UoMs, prices, stock)
  POST /api/pos_perfume/v1/products/uom_price    Price for a specific UoM
  GET  /api/pos_perfume/v1/products/<id>         Single product with full details
"""

import logging
from odoo import http
from odoo.http import request

from ._helpers import _success, _error, _get_json_body, _serialize_product, _check_auth

_logger = logging.getLogger(__name__)


class PosPerfumeApiProducts(http.Controller):

    @http.route('/api/pos_perfume/v1/products', type='http', auth='none', methods=['GET'], csrf=False)
    def list_products(self, query='', limit='80', offset='0', pricelist_id='', **kwargs):
        """Search and list products.

        GET /api/pos_perfume/v1/products?query=perfume&limit=80&pricelist_id=1
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            limit = int(limit)
            offset = int(offset)

            domain = [('sale_ok', '=', True), ('active', '=', True)]
            if query:
                domain += ['|', '|',
                           ('name', 'ilike', query),
                           ('default_code', 'ilike', query),
                           ('foreign_name', 'ilike', query)]

            products = request.env['product.product'].search(
                domain, limit=limit, offset=offset, order='name asc'
            )
            total = request.env['product.product'].search_count(domain)

            return _success({
                'total': total,
                'offset': offset,
                'limit': limit,
                'items': [_serialize_product(p) for p in products],
            })
        except Exception as e:
            _logger.error('[POS API] list_products: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/products/data', type='http', auth='none', methods=['POST'], csrf=False)
    def get_product_data(self, **kwargs):
        """Get full product data: UoMs, prices, warehouses, stock.

        POST /api/pos_perfume/v1/products/data
        Body: { "product_id": 12, "pricelist_id": 1, "uom_id": null, "warehouse_id": null }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            body = _get_json_body()
            product_id = body.get('product_id')
            pricelist_id = body.get('pricelist_id')
            uom_id = body.get('uom_id')

            if not product_id:
                return _error('product_id is required')

            from odoo.addons.pos_perfume_custom.controllers.pos_perfume_controller import PosPerfumeController
            ctrl = PosPerfumeController()

            product = request.env['product.product'].browse(int(product_id))
            if not product.exists():
                return _error('Product not found', 404)

            pricelist = _resolve_pricelist(pricelist_id)
            available_uoms = ctrl._get_uoms_from_pricelist(product, pricelist)
            default_uom = uom_id or product.uom_id.id
            default_price = ctrl._get_price_for_uom(product, pricelist, default_uom)
            warehouses = ctrl._get_warehouses_simple(product.id)

            priority, color_class, badge_text = product._get_product_priority_and_color(product.default_code)
            foreign_name = getattr(product, 'foreign_name', '') or ''

            return _success({
                'product_id': product.id,
                'product_name': product.name,
                'product_uom_id': product.uom_id.id,
                'product_uom_name': product.uom_id.name,
                'price_unit': default_price,
                'available_qty': product.qty_available,
                'available_uoms': available_uoms,
                'warehouses': warehouses,
                'default_code': product.default_code or '',
                'foreign_name': foreign_name,
                'color_class': color_class,
                'badge_text': badge_text,
            })
        except Exception as e:
            _logger.error('[POS API] get_product_data: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/products/uom_price', type='http', auth='none', methods=['POST'], csrf=False)
    def get_uom_price(self, **kwargs):
        """Get price for a specific UoM.

        POST /api/pos_perfume/v1/products/uom_price
        Body: { "product_id": 12, "pricelist_id": 1, "uom_id": 5 }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            body = _get_json_body()
            product_id = body.get('product_id')
            pricelist_id = body.get('pricelist_id')
            uom_id = body.get('uom_id')

            if not all([product_id, uom_id]):
                return _error('product_id and uom_id are required')

            from odoo.addons.pos_perfume_custom.controllers.pos_perfume_controller import PosPerfumeController
            ctrl = PosPerfumeController()

            product = request.env['product.product'].browse(int(product_id))
            if not product.exists():
                return _error('Product not found', 404)

            pricelist = _resolve_pricelist(pricelist_id)
            price = ctrl._get_price_for_uom(product, pricelist, int(uom_id))
            return _success({'price_unit': price})
        except Exception as e:
            _logger.error('[POS API] get_uom_price: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/products/<int:product_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_product(self, product_id, pricelist_id='', **kwargs):
        """Get a single product by ID with full details (UoMs + warehouses).

        GET /api/pos_perfume/v1/products/42?pricelist_id=1
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            product = request.env['product.product'].browse(product_id)
            if not product.exists():
                return _error('Product not found', 404)

            from odoo.addons.pos_perfume_custom.controllers.pos_perfume_controller import PosPerfumeController
            ctrl = PosPerfumeController()

            pricelist = None
            if pricelist_id:
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None

            available_uoms = ctrl._get_uoms_from_pricelist(product, pricelist)
            warehouses = ctrl._get_warehouses_simple(product.id)

            data = _serialize_product(product)
            data.update({'available_uoms': available_uoms, 'warehouses': warehouses})
            return _success(data)
        except Exception as e:
            _logger.error('[POS API] get_product: %s', e, exc_info=True)
            return _error(str(e), 500)


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _resolve_pricelist(pricelist_id):
    """Return a product.pricelist record or None."""
    if not pricelist_id:
        return None
    pid = pricelist_id[0] if isinstance(pricelist_id, list) else int(pricelist_id)
    pricelist = request.env['product.pricelist'].browse(pid)
    return pricelist if pricelist.exists() else None
