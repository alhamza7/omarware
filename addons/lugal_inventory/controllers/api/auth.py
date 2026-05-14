"""Authentication API for lugal_inventory."""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _generate_token, _parse_body, require_auth


class InventoryAuthController(http.Controller):

    @http.route('/api/inventory/v1/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        """
        Authenticate user and return JWT token.
        Body: { "username": str, "password": str, "warehouse_id": int (optional) }
        """
        try:
            body = _parse_body()
            username = body.get('username', '').strip()
            password = body.get('password', '').strip()
            warehouse_id = body.get('warehouse_id')

            if not username or not password:
                return _error('Username and password are required', status=400)

            # Authenticate against Odoo 19 (credential dict style)
            try:
                auth_info = request.env['res.users'].sudo()._login(
                    {'type': 'password', 'login': username, 'password': password},
                    {'interactive': False}
                )
                uid = auth_info.get('uid')
            except Exception:
                return _error('Invalid credentials', status=401)

            if not uid:
                return _error('Invalid credentials', status=401)

            user = request.env['res.users'].sudo().browse(uid)

            # Find inventory user record (to get role and warehouse)
            inv_user_domain = [('user_id', '=', uid)]
            if warehouse_id:
                inv_user_domain.append(('warehouse_id', '=', int(warehouse_id)))

            inv_user = request.env['lugal.inventory.user'].sudo().search(inv_user_domain, limit=1)

            role = inv_user.role if inv_user else 'user'
            assigned_warehouse_id = inv_user.warehouse_id.id if inv_user else warehouse_id or 0
            warehouse_code = inv_user.warehouse_id.code if inv_user else ''

            token = _generate_token(uid, username, role, assigned_warehouse_id)

            return _success({
                'token': token,
                'user_id': uid,
                'username': username,
                'full_name': inv_user.full_name or user.name,
                'role': role,
                'warehouse_id': assigned_warehouse_id,
                'warehouse_code': warehouse_code,
            })

        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/auth/me', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def me(self, **kwargs):
        """Return current user info from token."""
        try:
            payload = request.env.context.get('inv_token_payload') or getattr(request, '_inv_token_payload', {})
            user_id = payload.get('user_id')
            if not user_id:
                return _error('Invalid token payload', status=401)

            user = request.env['res.users'].sudo().browse(user_id)
            inv_user = request.env['lugal.inventory.user'].sudo().search([('user_id', '=', user_id)], limit=1)

            return _success({
                'user_id': user_id,
                'username': user.login,
                'full_name': inv_user.full_name or user.name,
                'role': inv_user.role if inv_user else 'user',
                'warehouse_id': payload.get('warehouse_id', 0),
            })
        except Exception as e:
            return _error(str(e), status=500)
