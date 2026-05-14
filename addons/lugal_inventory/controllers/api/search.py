"""
Product search and barcode scan API for lugal_inventory.

Uses REAL system data:
  - Barcodes    → product.barcode.alternative  (synced from SAP)
  - Quantities  → sap.product.warehouse.info   (synced from SAP → stock.quant)
  - Products    → product.product              (standard Odoo)

Search endpoint accepts query in THREE ways (priority order):
  1. POST body JSON  { "query": "...", "warehouse_id": 1 }   ← preferred (safe for barcodes with / // spaces)
  2. Header          X-Inventory-Query: <barcode>            ← for scanner integrations
  3. GET query param ?query=...                              ← only for plain text (no special chars)
"""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _serialize_product, _parse_body, require_auth, _extract_translatable


class InventorySearchController(http.Controller):

    @http.route('/api/inventory/v1/search', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    @require_auth
    def search_product(self, query='', warehouse_id=None, limit=15, **kwargs):
        """
        Search for a product by barcode scan or manual code/name input.

        Accepts query via (in priority order):
          1. POST JSON body:  { "query": "1001081//", "warehouse_id": 11, "limit": 15 }
          2. Request header:  X-Inventory-Query: 1001081//
          3. GET param:       ?query=...

        Returns:
          - Exact barcode/code match → 1 product (is_exact=True, matched_barcode set)
          - Text/name search         → up to `limit` products (default 15, max 50)
        """
        try:
            resolved_query, resolved_warehouse = _resolve_search_input(query, warehouse_id)

            if not resolved_query:
                return _error('query is required (send via POST body, X-Inventory-Query header, or ?query= param)', status=400)

            resolved_limit = min(int(limit) if limit else 15, 50)
            products, is_exact = _find_products_by_query(resolved_query, resolved_limit)

            if not products:
                return _success({'products': [], 'count': 0})

            matched = resolved_query if is_exact else None
            result = [_build_product_detail(p, resolved_warehouse, matched_barcode=matched) for p in products]
            return _success({'products': result, 'count': len(result)})

        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/products/<int:product_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def get_product(self, product_id, warehouse_id=None, **kwargs):
        """Return full detail of a single product including real stock and SAP barcodes."""
        try:
            product = request.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                return _error('Product not found', status=404)

            wh_id = int(warehouse_id) if warehouse_id else None
            return _success(_build_product_detail(product, wh_id))
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/products', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_products(self, page=1, per_page=50, search='', **kwargs):
        """Paginated product list with optional code/name search."""
        try:
            page = max(1, int(page))
            per_page = min(int(per_page), 200)
            offset = (page - 1) * per_page

            domain = [('active', '=', True)]
            if search:
                domain += ['|', ('default_code', 'ilike', search), ('name', 'ilike', search)]

            Product = request.env['product.product'].sudo()
            total = Product.search_count(domain)
            products = Product.search(domain, limit=per_page, offset=offset, order='default_code asc')

            return _success({
                'products': [_serialize_product(p) for p in products],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
            })
        except Exception as e:
            return _error(str(e), status=500)


# ─────────────────────────── input resolver ─────────────────────────────

def _resolve_search_input(query_param, warehouse_param):
    """
    Resolve query and warehouse_id from all supported input methods.

    Priority:
      1. POST JSON body  → { "query": str, "warehouse_id": int }
      2. Request header  → X-Inventory-Query + X-Inventory-Warehouse
      3. GET query param → ?query=... &warehouse_id=...

    Returns (query: str, warehouse_id: int|None)
    """
    # 1. Try POST body first (safest — no URL encoding issues)
    if request.httprequest.method == 'POST':
        body = _parse_body()
        q = (body.get('query') or '').strip()
        wh = body.get('warehouse_id')
        if q:
            return q, (int(wh) if wh else None)

    # 2. Try custom header (good for scanner hardware that sends raw bytes)
    header_query = request.httprequest.headers.get('X-Inventory-Query', '').strip()
    header_wh = request.httprequest.headers.get('X-Inventory-Warehouse', '').strip()
    if header_query:
        return header_query, (int(header_wh) if header_wh else None)

    # 3. Fallback to GET query param (plain text only — no slashes/spaces)
    q = (query_param or '').strip()
    wh = int(warehouse_param) if warehouse_param else None
    return q, wh

def _find_products_by_query(query, limit=15):
    """
    Resolve a search query to a list of product.product records.

    Returns (products: list, is_exact: bool).
    - Exact barcode/code match → ([product], True) — stops here, no further search
    - Text search (name/code ilike) → (products[:limit], False)

    Domain fix: active=True is an AND filter, not part of the OR chain.
    """
    env = request.env

    # 1. SAP alternative barcode exact match (highest priority)
    if 'product.barcode.alternative' in env:
        alt = env['product.barcode.alternative'].sudo().search(
            [('barcode', '=', query)], limit=1
        )
        if alt:
            return [alt.product_id], True

    # 2. Main product barcode or default_code exact match
    product = env['product.product'].sudo().search(
        ['|', ('barcode', '=', query), ('default_code', '=', query)], limit=1
    )
    if product:
        return list(product), True

    # 3. Partial ilike text search — returns multiple results
    # IMPORTANT: ('active', '=', True) is AND'd with the OR group,
    # NOT inside the OR. Previous bug had active inside OR which returned all products.
    products = env['product.product'].sudo().search(
        ['&', ('active', '=', True), '|', '|',
         ('default_code', 'ilike', query),
         ('name', 'ilike', query),
         ('foreign_name', 'ilike', query)],
        limit=limit, order='default_code asc'
    )
    return list(products), False


def _build_product_detail(product, warehouse_id=None, matched_barcode=None):
    """
    Build a rich product dict containing:
      - SAP barcodes with their UoMs  (product.barcode.alternative)
      - Real stock per warehouse       (sap.product.warehouse.info current_qty_available)
      - Fallback to stock.quant if SAP info is missing
    """
    env = request.env

    # ── SAP Barcodes from product.barcode.alternative (optional module) ──
    barcodes = []
    if 'product.barcode.alternative' in env:
        alt_barcodes = env['product.barcode.alternative'].sudo().search(
            [('product_id', '=', product.id), ('active', '=', True)],
            order='sequence asc'
        )
        barcodes = [
            {
                'id': b.id,
                'barcode': b.barcode,
                'uom': _extract_translatable(b.uom_name) if b.uom_name else _extract_translatable(b.uom_id.name) if b.uom_id else '',
                'uom_id': b.uom_id.id if b.uom_id else None,
                'sap_uom_entry': b.sap_uom_entry or 0,
                'matched': b.barcode == matched_barcode,
            }
            for b in alt_barcodes
        ]

    # Also include the main product barcode if it exists and not already listed
    main_barcode = product.barcode
    if main_barcode and main_barcode not in [b['barcode'] for b in barcodes]:
        barcodes.insert(0, {
            'id': None,
            'barcode': main_barcode,
            'uom': _extract_translatable(product.uom_id.name) if product.uom_id else '',
            'uom_id': product.uom_id.id if product.uom_id else None,
            'sap_uom_entry': 0,
            'matched': main_barcode == matched_barcode,
        })

    # ── Real Stock per Warehouse ──
    warehouses = _get_real_stock(product, warehouse_id)

    return {
        'id': product.id,
        'code': product.default_code or '',
        'name': _extract_translatable(product.name),
        'foreign_name': product.foreign_name or '',
        'uom': _extract_translatable(product.uom_id.name) if product.uom_id else '',
        'uom_id': product.uom_id.id if product.uom_id else None,
        'category': _extract_translatable(product.categ_id.name) if product.categ_id else '',
        'barcodes': barcodes,
        'matched_barcode': matched_barcode,
        'warehouses': warehouses,
        'total_qty': sum(w['qty'] for w in warehouses),
    }


def _get_real_stock(product, warehouse_id=None):
    """
    Return per-warehouse stock using sap.product.warehouse.info (current_qty_available).
    Falls back to stock.quant if sap.product.warehouse.info has no rows for this product.
    """
    env = request.env

    domain = [('product_id', '=', product.id)]
    if warehouse_id:
        domain.append(('warehouse_id', '=', warehouse_id))

    sap_infos = env['sap.product.warehouse.info'].sudo().search(domain)

    if sap_infos:
        return [
            {
                'warehouse_id': info.warehouse_id.id,
                'warehouse': info.warehouse_id.name,
                'warehouse_code': info.sap_warehouse_code or info.warehouse_id.code or '',
                'qty': info.current_qty_available,
                'qty_reserved': info.current_qty_reserved,
                'source': 'sap',
            }
            for info in sap_infos
        ]

    # ── Fallback: stock.quant ──
    wh_domain = [('id', '=', warehouse_id)] if warehouse_id else []
    warehouses = env['stock.warehouse'].sudo().search(wh_domain)

    result = []
    for wh in warehouses:
        location = wh.lot_stock_id
        if not location:
            continue
        quants = env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('location_id', 'child_of', location.id),
        ])
        qty = sum(quants.mapped('quantity'))
        qty_reserved = sum(quants.mapped('reserved_quantity'))
        if qty or not warehouse_id:
            result.append({
                'warehouse_id': wh.id,
                'warehouse': wh.name,
                'warehouse_code': wh.code or '',
                'qty': qty,
                'qty_reserved': qty_reserved,
                'source': 'stock_quant',
            })

    return result
