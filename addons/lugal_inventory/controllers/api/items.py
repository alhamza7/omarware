"""Items (products) CRUD API for admin dashboard."""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _serialize_product, _parse_body, require_auth


class InventoryItemsController(http.Controller):

    @http.route('/api/inventory/v1/items', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_items(self, page=1, per_page=50, search='', **kwargs):
        """Return paginated list of all system products (items view in admin)."""
        try:
            page = max(1, int(page))
            per_page = min(int(per_page), 200)
            offset = (page - 1) * per_page

            domain = [('active', '=', True)]
            if search:
                domain += ['|', ('default_code', 'ilike', search), ('name', 'ilike', search)]

            Product = request.env['product.product'].sudo()
            total = Product.search_count(domain)
            products = Product.search(domain, limit=per_page, offset=offset, order='id desc')

            data = [
                {
                    'id': p.id,
                    'code': p.default_code or '',
                    'name': p.name or '',
                    'dateAdded': p.create_date.isoformat() if p.create_date else '',
                }
                for p in products
            ]
            return _success({
                'items': data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
            })
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/items/<int:item_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def get_item(self, item_id, **kwargs):
        """Return a single product item by ID."""
        try:
            product = request.env['product.product'].sudo().browse(item_id)
            if not product.exists():
                return _error('Item not found', status=404)
            return _success(_serialize_product(product))
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/items/stats', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def stats(self, warehouse_id=None, **kwargs):
        """
        Return dashboard stats matching the UI:
          - Total items, UoMs, SAP barcodes, completed audits
          - UoM distribution table (name, item count, barcode count)
          - total_audits is scoped to warehouse_id when provided.
        Uses real system data: product.barcode.alternative for barcodes.
        """
        try:
            env = request.env

            total_items = env['product.product'].sudo().search_count([('active', '=', True)])

            # Real SAP barcodes from product.barcode.alternative (optional module)
            if 'product.barcode.alternative' in env:
                total_barcodes = env['product.barcode.alternative'].sudo().search_count([('active', '=', True)])
            else:
                total_barcodes = 0

            # Audit count — scoped to a specific warehouse when warehouse_id is provided
            audit_domain = []
            resolved_wh_id = int(warehouse_id) if warehouse_id else None
            if resolved_wh_id:
                audit_domain = [('warehouse_id', '=', resolved_wh_id)]
            total_audits = env['lugal.inventory.audit'].sudo().search_count(audit_domain)

            uom_count = env['uom.uom'].sudo().search_count([('active', '=', True)])
            uom_distribution = _get_uom_distribution(env)

            return _success({
                'total_items':    total_items,
                'total_barcodes': total_barcodes,
                'total_audits':   total_audits,
                'uom_count':      uom_count,
                'uom_distribution': uom_distribution,
                'warehouse_id':   resolved_wh_id,
            })
        except Exception as e:
            return _error(str(e), status=500)


def _get_uom_distribution(env):
    """
    UoM distribution: items per UoM + barcodes per UoM.
    Uses product.barcode.alternative if available, falls back to product.product.barcode.
    """
    barcode_subquery = ""
    if 'product.barcode.alternative' in env:
        barcode_subquery = """
            (SELECT COUNT(*) FROM product_barcode_alternative pba2
             JOIN product_product pp2 ON pba2.product_id = pp2.id
             JOIN product_template pt2 ON pp2.product_tmpl_id = pt2.id
             WHERE pba2.uom_id = u.id AND pba2.active = true)
        """
    else:
        barcode_subquery = """
            (SELECT COUNT(*) FROM product_product pp2
             JOIN product_template pt2 ON pp2.product_tmpl_id = pt2.id
             WHERE pt2.uom_id = u.id AND pp2.barcode IS NOT NULL AND pp2.active = true)
        """

    env.cr.execute(f"""
        SELECT
            u.name,
            COUNT(DISTINCT pp.id)  AS items,
            {barcode_subquery}     AS barcodes
        FROM uom_uom u
        JOIN product_template pt ON pt.uom_id = u.id
        JOIN product_product pp  ON pp.product_tmpl_id = pt.id
        WHERE pt.active = true AND pp.active = true AND u.active = true
        GROUP BY u.id, u.name
        ORDER BY items DESC
        LIMIT 20
    """)
    rows = env.cr.fetchall()

    def _extract_name(raw):
        """Extract string from either a plain string or a jsonb dict like {'en_US': 'كغم'}."""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            return raw.get('en_US') or raw.get('ar_001') or next(iter(raw.values()), '')
        # psycopg2 may return it as a JSON string
        try:
            import json as _json
            parsed = _json.loads(raw)
            if isinstance(parsed, dict):
                return parsed.get('en_US') or next(iter(parsed.values()), '')
        except Exception:
            pass
        return str(raw) if raw else ''

    return [
        {
            'name': _extract_name(row[0]),
            'items': str(row[1]),
            'barcodes': str(row[2]),
        }
        for row in rows
    ]
