# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Products

Routes:
  GET  /api/pos_perfume/v1/products              List / search products
  GET  /api/pos_perfume/v1/categories            List all categories with product count
  GET  /api/pos_perfume/v1/sections              List all sections with product count
  POST /api/pos_perfume/v1/products/data         Full product data (UoMs, prices, stock)
  POST /api/pos_perfume/v1/products/uom_price    Price for a specific UoM
  GET  /api/pos_perfume/v1/products/<id>         Single product with full details
"""

import logging
from odoo import http
from odoo.http import request
from odoo.addons.pos_perfume_custom.controllers.pos_perfume_controller import PosPerfumeController

from ._helpers import (
    _success, _error, _get_json_body,
    _serialize_product, _check_auth, _get_warehouses_batch,
    _get_sap_extended_batch,
)

_logger = logging.getLogger(__name__)


class PosPerfumeApiProducts(http.Controller):

    @http.route('/api/pos_perfume/v1/products', type='http', auth='none', methods=['GET'], csrf=False)
    def list_products(self, query='', limit='80', offset='0', pricelist_id='',
                      brand='', category_type='', category_id='', **kwargs):
        """Search and list products.

        GET /api/pos_perfume/v1/products?query=perfume&limit=80&pricelist_id=1
            &brand=robertet               (filter by brand key)
            &category_type=fragrances     (filter by category type key)
            &category_id=9               (filter by product.category id)
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            limit  = int(limit)
            offset = int(offset)

            domain = [('sale_ok', '=', True), ('active', '=', True)]
            if query:
                domain += ['|', '|',
                           ('name', 'ilike', query),
                           ('default_code', 'ilike', query),
                           ('foreign_name', 'ilike', query)]

            # Brand filter — translate brand key to code prefix(es) / items_group_code
            if brand:
                brand_domain = _brand_key_to_domain(brand.lower().strip())
                if brand_domain:
                    domain += brand_domain

            # Category type filter — translate to items_group_code list or code prefix
            if category_type:
                cat_domain = _category_type_to_domain(category_type.lower().strip())
                if cat_domain:
                    domain += cat_domain

            # Direct category filter by product.category id
            if category_id:
                domain += [('categ_id', '=', int(category_id))]

            products = request.env['product.product'].search(
                domain, limit=limit, offset=offset, order='name asc'
            )
            total = request.env['product.product'].search_count(domain)

            # Resolve pricelist once for the whole page (used for UoM prices)
            pricelist = _resolve_pricelist(pricelist_id) if pricelist_id else None

            ctrl = PosPerfumeController()

            # Fetch all warehouse stock in one batch query then attach per-product
            warehouse_map = _get_warehouses_batch([p.id for p in products])

            # Fetch all sap.product.extended in one batch query
            sap_ext_map = _get_sap_extended_batch([p.id for p in products])

            items = []
            for p in products:
                # UoMs with prices — full SAP breakdown when pricelist given,
                # otherwise fall back to base UoM + list_price so the field is
                # always present.
                uoms = ctrl._get_uoms_from_pricelist(p, pricelist)
                items.append(_serialize_product(
                    p,
                    warehouse_map.get(p.id, []),
                    uoms,
                    sap_ext=sap_ext_map.get(p.id, False),
                ))

            return _success({
                'total': total,
                'offset': offset,
                'limit': limit,
                'items': items,
            })
        except Exception as e:
            _logger.error('[POS API] list_products: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/categories', type='http', auth='none', methods=['GET'], csrf=False)
    def list_categories(self, **kwargs):
        """List all product categories that have at least one active product.

        GET /api/pos_perfume/v1/categories
        Returns: [{ id, name, product_count }]
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            categories = _get_active_categories()
            return _success({'categories': categories})
        except Exception as e:
            _logger.error('[POS API] list_categories: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/sections', type='http', auth='none', methods=['GET'], csrf=False)
    def list_sections(self, **kwargs):
        """List all product sections with their product count.

        GET /api/pos_perfume/v1/sections

        Returns a fixed list of business sections, each with:
          - key         : stable identifier used for filtering (e.g. "fragrances")
          - label       : human-readable English name
          - product_count: number of active, sale_ok products in that section
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            sections = _get_sections_with_counts()
            return _success({'sections': sections})
        except Exception as e:
            _logger.error('[POS API] list_sections: %s', e, exc_info=True)
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

            # Fetch SAP extended info for items_group fields
            sap_ext_map = _get_sap_extended_batch([product.id])
            sap_ext = sap_ext_map.get(product.id, False)
            items_group_code = (sap_ext.items_group_code or 0) if sap_ext else 0
            items_group_name = (sap_ext.items_group_name or '') if sap_ext else ''

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
                'items_group_code': items_group_code,
                'items_group_name': items_group_name,
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

            ctrl = PosPerfumeController()

            pricelist = None
            if pricelist_id:
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None

            available_uoms = ctrl._get_uoms_from_pricelist(product, pricelist)
            warehouses = ctrl._get_warehouses_simple(product.id)

            sap_ext_map = _get_sap_extended_batch([product.id])
            sap_ext = sap_ext_map.get(product.id, False)

            data = _serialize_product(product, warehouses, available_uoms, sap_ext=sap_ext)
            return _success(data)
        except Exception as e:
            _logger.error('[POS API] get_product: %s', e, exc_info=True)
            return _error(str(e), 500)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _resolve_pricelist(pricelist_id):
    """Return a product.pricelist record or None."""
    if not pricelist_id:
        return None
    pid = pricelist_id[0] if isinstance(pricelist_id, list) else int(pricelist_id)
    pricelist = request.env['product.pricelist'].browse(pid)
    return pricelist if pricelist.exists() else None


# Brand key → default_code prefix list (used when SAP ext not available)
_BRAND_CODE_PREFIXES = {
    'adf':           ['ADF'],
    'amour_de_fleurs': ['ADF'],
    'robertet':      ['R00', 'R01', 'R02'],
    'givaudan':      ['G00', 'G01', 'G02'],
    'european':      ['N10', 'N11', 'EU0'],
    'euro':          ['N10', 'N11', 'EU0'],
    'florchem':      ['FL0', 'FL1'],
    'firmenic':      ['FF0', 'FF1'],
    'premium':       ['PRM'],
    'maison':        ['MA0', 'MA1'],
    'local':         ['LOC'],
    'mix':           ['MIX'],
    'samples':       ['S00', 'S01'],
    'crystal_glass': ['CS0', 'CS1'],
    'pack':          ['PK0', 'PK1'],
    'packaging':     ['B00', 'B01'],
    'alcohol':       ['ALC'],
}

# Brand key → SAP items_group_codes
_BRAND_ITEMS_GROUPS = {
    'adf':             [108],
    'amour_de_fleurs': [108],
    'robertet':        [109],
    'givaudan':        [107],
    'european':        [110, 112],
    'euro':            [110, 112],
    'florchem':        [111],
    'firmenic':        [123],
    'premium':         [106],
    'maison':          [131],
    'local':           [132],
    'mix':             [116],
    'samples':         [118],
    'crystal_glass':   [117],
    'pack':            [120],
    'alcohol':         [119],
}

# Category type key → SAP items_group_codes
_CATEGORY_ITEMS_GROUPS = {
    'fragrances': [106, 107, 108, 109, 110, 111, 112, 113, 116, 123, 124, 131, 132],
    'glass':      [117],
    'samples':    [118],
    'pack':       [120],
    'packaging':  [125],
    'alcohol':    [119],
    'accessories': [122, 134, 135, 137],
    'devices':    [],
    'incense':    [],
}

# Category type key → default_code prefixes (fallback)
_CATEGORY_CODE_PREFIXES = {
    'fragrances': ['ADF', 'FF', 'FL', 'N1', 'R', 'G', 'PRM', 'MA', 'LOC', 'MIX', 'EXP'],
    'glass':      ['CS'],
    'samples':    ['S00', 'S01'],
    'pack':       ['PK'],
    'packaging':  ['B00', 'B01'],
    'alcohol':    ['ALC'],
    'accessories': ['CM', 'DY', 'P00'],
    'devices':    ['DV'],
    'incense':    ['INC', 'BKH'],
}


def _brand_key_to_domain(brand_key):
    """Convert a brand key string to an Odoo ORM domain fragment."""
    groups = _BRAND_ITEMS_GROUPS.get(brand_key)
    if groups:
        # Filter via sap_product_extended join using sub-search
        product_ids = request.env['sap.product.extended'].sudo().search(
            [('items_group_code', 'in', groups)]
        ).mapped('product_id.id')
        if product_ids:
            return [('id', 'in', product_ids)]

    # Fallback: default_code prefix
    prefixes = _BRAND_CODE_PREFIXES.get(brand_key, [])
    if not prefixes:
        return []
    or_domain = []
    for pfx in prefixes:
        or_domain += [('default_code', '=like', f'{pfx}%'), ]
    if len(prefixes) == 1:
        return [('default_code', '=like', f'{prefixes[0]}%')]
    # Build OR chain for multiple prefixes
    result = ['|'] * (len(prefixes) - 1)
    for pfx in prefixes:
        result.append(('default_code', '=like', f'{pfx}%'))
    return result


def _category_type_to_domain(cat_key):
    """Convert a category_type key string to an Odoo ORM domain fragment."""
    groups = _CATEGORY_ITEMS_GROUPS.get(cat_key)
    if groups:
        product_ids = request.env['sap.product.extended'].sudo().search(
            [('items_group_code', 'in', groups)]
        ).mapped('product_id.id')
        if product_ids:
            return [('id', 'in', product_ids)]

    # Fallback: code prefix
    prefixes = _CATEGORY_CODE_PREFIXES.get(cat_key, [])
    if not prefixes:
        return []
    if len(prefixes) == 1:
        return [('default_code', '=like', f'{prefixes[0]}%')]
    result = ['|'] * (len(prefixes) - 1)
    for pfx in prefixes:
        result.append(('default_code', '=like', f'{pfx}%'))
    return result


def _get_active_categories():
    """
    Return all product categories that have at least one active, sale_ok product.
    Each entry has: id, name, product_count.
    """
    try:
        request.env.cr.execute('''
            SELECT
                pc.id,
                pc.name,
                COUNT(pp.id) AS product_count
            FROM product_category pc
            JOIN product_template pt ON pt.categ_id = pc.id
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            WHERE pt.active = true
              AND pt.sale_ok = true
              AND pp.active = true
            GROUP BY pc.id, pc.name
            HAVING COUNT(pp.id) > 0
            ORDER BY pc.name ASC
        ''')
        rows = request.env.cr.fetchall()
        return [{'id': row[0], 'name': row[1], 'product_count': row[2]} for row in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Section definitions
# Each section maps to SAP items_group_codes (primary) and default_code
# prefixes (fallback for products without a sap.product.extended row).
# ---------------------------------------------------------------------------
_SECTIONS = [
    {
        'key':           'fragrances',
        'label':         'Fragrances',
        'group_codes':   [106, 107, 108, 109, 110, 111, 112, 113, 116, 123, 124, 131, 132],
        'code_prefixes': ['ADF', 'FF', 'FL', 'N1', 'R0', 'G0', 'PRM', 'MA', 'LOC', 'MIX', 'EXP'],
    },
    {
        'key':           'glass',
        'label':         'Glass',
        'group_codes':   [117],
        'code_prefixes': ['CS'],
    },
    {
        'key':           'samples',
        'label':         'Samples',
        'group_codes':   [118],
        'code_prefixes': ['S00', 'S01'],
    },
    {
        'key':           'pack',
        'label':         'Pack',
        'group_codes':   [120],
        'code_prefixes': ['PK'],
    },
    {
        'key':           'packaging',
        'label':         'Box Packaging',
        'group_codes':   [125],
        'code_prefixes': ['B0'],
    },
    {
        'key':           'alcohol',
        'label':         'Alcohol',
        'group_codes':   [119],
        'code_prefixes': ['ALC'],
    },
    {
        'key':           'accessories',
        'label':         'Accessories',
        'group_codes':   [122, 134, 135, 137],
        'code_prefixes': ['CM', 'P00'],
    },
    {
        'key':           'dye',
        'label':         'Dye & Colour',
        'group_codes':   [],
        'code_prefixes': ['DY'],
    },
    {
        'key':           'incense',
        'label':         'Incense',
        'group_codes':   [],
        'code_prefixes': ['INC', 'BKH'],
    },
    {
        'key':           'devices',
        'label':         'Devices',
        'group_codes':   [],
        'code_prefixes': ['DV'],
    },
]


def _get_sections_with_counts():
    """
    Return all business sections each with a product_count.

    Uses two SQL queries:
      1. Count products per items_group_code via sap.product.extended (primary).
      2. Count products by default_code prefix for those WITHOUT a SAP ext row (fallback).
    Then merges both per section definition.
    """
    try:
        # Primary: products linked to sap_product_extended
        request.env.cr.execute('''
            SELECT
                spe.items_group_code,
                COUNT(DISTINCT pp.id) AS cnt
            FROM sap_product_extended spe
            JOIN product_product pp ON pp.id = spe.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.active = true
              AND pt.sale_ok = true
              AND pp.active = true
              AND spe.items_group_code IS NOT NULL
            GROUP BY spe.items_group_code
        ''')
        group_counts = {row[0]: row[1] for row in request.env.cr.fetchall()}

        # Fallback: products with NO sap_product_extended entry — count by code
        request.env.cr.execute('''
            SELECT
                pt.default_code,
                COUNT(DISTINCT pp.id) AS cnt
            FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            LEFT JOIN sap_product_extended spe ON spe.product_id = pp.id
            WHERE pt.active = true
              AND pt.sale_ok = true
              AND pp.active = true
              AND spe.id IS NULL
              AND pt.default_code IS NOT NULL
            GROUP BY pt.default_code
        ''')
        fallback_codes = {row[0]: row[1] for row in request.env.cr.fetchall()}

        result = []
        for section in _SECTIONS:
            primary = sum(group_counts.get(gc, 0) for gc in section['group_codes'])

            fallback = sum(
                cnt
                for code, cnt in fallback_codes.items()
                if any(code.upper().startswith(pfx.upper()) for pfx in section['code_prefixes'])
            )

            result.append({
                'key':           section['key'],
                'label':         section['label'],
                'product_count': primary + fallback,
            })

        return result
    except Exception as e:
        _logger.error('[POS API] _get_sections_with_counts: %s', e, exc_info=True)
        return []
