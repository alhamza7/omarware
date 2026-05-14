"""Warehouse API for lugal_inventory."""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, require_auth, _extract_translatable


class InventoryWarehouseController(http.Controller):

    @http.route('/api/inventory/v1/warehouses', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_warehouses(self, **kwargs):
        """Return all warehouses available in the system."""
        try:
            warehouses = request.env['stock.warehouse'].sudo().search([], order='id asc')
            data = [
                {
                    'id': wh.id,
                    'name': _extract_translatable(wh.name),
                    'code': wh.code or str(wh.id),
                    'short_name': wh.code or str(wh.id),
                }
                for wh in warehouses
            ]
            return _success(data)
        except Exception as e:
            return _error(str(e), status=500)
