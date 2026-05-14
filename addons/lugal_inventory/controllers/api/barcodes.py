"""
Barcodes API for lugal_inventory admin dashboard.

Uses product.barcode.alternative — the real SAP-synced barcode table.
These barcodes are created/updated automatically by the SAP integration,
but admins can also add/edit them manually here.
"""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _parse_body, require_auth


class InventoryBarcodesController(http.Controller):

    @http.route('/api/inventory/v1/barcodes', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_barcodes(self, page=1, per_page=50, search='', product_id=None, **kwargs):
        """Return paginated list of SAP barcodes (product.barcode.alternative)."""
        try:
            if 'product.barcode.alternative' not in request.env:
                return _success({'barcodes': [], 'total': 0, 'page': 1, 'per_page': 50})
            page = max(1, int(page))
            per_page = min(int(per_page), 200)
            offset = (page - 1) * per_page

            domain = [('active', '=', True)]
            if product_id:
                domain.append(('product_id', '=', int(product_id)))
            if search:
                domain += ['|', '|',
                           ('barcode', 'ilike', search),
                           ('product_id.default_code', 'ilike', search),
                           ('product_id.name', 'ilike', search)]

            Barcode = request.env['product.barcode.alternative'].sudo()
            total = Barcode.search_count(domain)
            barcodes = Barcode.search(domain, limit=per_page, offset=offset, order='product_id asc, sequence asc')

            return _success({
                'barcodes': [_serialize(b) for b in barcodes],
                'total': total,
                'page': page,
                'per_page': per_page,
            })
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/barcodes', type='http', auth='public', methods=['POST'], csrf=False)
    @require_auth
    def create_barcode(self, **kwargs):
        """
        Create a new barcode mapping.
        Body: { "product_id": int, "barcode": str, "uom_id": int, "uom_name": str (opt) }
        """
        try:
            body = _parse_body()
            product_id = body.get('product_id')
            barcode = (body.get('barcode') or '').strip()
            uom_id = body.get('uom_id')

            if not product_id or not barcode or not uom_id:
                return _error('product_id, barcode and uom_id are required', status=400)

            product = request.env['product.product'].sudo().browse(int(product_id))
            if not product.exists():
                return _error('Product not found', status=404)

            rec = request.env['product.barcode.alternative'].sudo().create({
                'product_id': int(product_id),
                'barcode': barcode,
                'uom_id': int(uom_id),
                'uom_name': body.get('uom_name') or '',
            })
            return _success(_serialize(rec), status=201)
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/barcodes/<int:barcode_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    @require_auth
    def update_barcode(self, barcode_id, **kwargs):
        """Update an existing barcode mapping."""
        try:
            rec = request.env['product.barcode.alternative'].sudo().browse(barcode_id)
            if not rec.exists():
                return _error('Barcode not found', status=404)

            body = _parse_body()
            vals = {}
            if 'barcode' in body:
                vals['barcode'] = body['barcode']
            if 'uom_id' in body:
                vals['uom_id'] = int(body['uom_id'])
            if 'uom_name' in body:
                vals['uom_name'] = body['uom_name']

            rec.write(vals)
            return _success(_serialize(rec))
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/barcodes/<int:barcode_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    @require_auth
    def delete_barcode(self, barcode_id, **kwargs):
        """Delete a barcode mapping (manual barcodes only; SAP ones re-sync automatically)."""
        try:
            rec = request.env['product.barcode.alternative'].sudo().browse(barcode_id)
            if not rec.exists():
                return _error('Barcode not found', status=404)
            rec.unlink()
            return _success({'deleted': True})
        except Exception as e:
            return _error(str(e), status=500)


def _serialize(b):
    """Serialize a product.barcode.alternative record to API dict."""
    return {
        'id': b.id,
        'product_id': b.product_id.id,
        'code': b.product_id.default_code or '',
        'name': b.product_id.name or '',
        'barcode': b.barcode or '',
        'unit': b.uom_name or (b.uom_id.name if b.uom_id else ''),
        'uom_id': b.uom_id.id if b.uom_id else None,
        'sap_uom_entry': b.sap_uom_entry or 0,
        'last_sync': b.last_sync.isoformat() if b.last_sync else None,
    }
