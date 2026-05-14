"""Users management API for lugal_inventory admin dashboard."""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _serialize_inv_user, _parse_body, require_auth


class InventoryUsersController(http.Controller):

    @http.route('/api/inventory/v1/users', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_users(self, page=1, per_page=50, search='', warehouse_id=None, **kwargs):
        """Return paginated list of inventory users."""
        try:
            page = max(1, int(page))
            per_page = min(int(per_page), 5000)
            offset = (page - 1) * per_page

            domain = []
            if warehouse_id:
                domain.append(('warehouse_id', '=', int(warehouse_id)))
            if search:
                domain += ['|', ('username', 'ilike', search), ('full_name', 'ilike', search)]

            InvUser = request.env['lugal.inventory.user'].sudo()
            total = InvUser.search_count(domain)
            users = InvUser.search(domain, limit=per_page, offset=offset, order='id desc')

            return _success({
                'users': [_serialize_inv_user(u) for u in users],
                'total': total,
                'page': page,
                'per_page': per_page,
            })
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/users', type='http', auth='public', methods=['POST'], csrf=False)
    @require_auth
    def create_user(self, **kwargs):
        """
        Create a new inventory user.

        Two modes:
        A) New user:    { "username", "full_name", "password", "role", "warehouse_id" }
        B) Import user: { "odoo_user_id", "full_name", "role", "warehouse_id" }
        """
        try:
            body = _parse_body()
            role = body.get('role', 'user')
            warehouse_id = body.get('warehouse_id')
            full_name = (body.get('full_name') or '').strip()

            if not warehouse_id:
                return _error('warehouse_id is required', status=400)

            # ── Mode B: import existing Odoo user ──────────────────────────────
            odoo_user_id = body.get('odoo_user_id')
            if odoo_user_id:
                odoo_user = request.env['res.users'].sudo().browse(int(odoo_user_id))
                if not odoo_user.exists():
                    return _error('Odoo user not found', status=404)
                # Check not already linked to this warehouse
                existing = request.env['lugal.inventory.user'].sudo().search([
                    ('user_id', '=', odoo_user.id),
                    ('warehouse_id', '=', int(warehouse_id)),
                ], limit=1)
                if existing:
                    return _error('هذا المستخدم مرتبط بهذا المخزن مسبقاً', status=400)
                inv_user = request.env['lugal.inventory.user'].sudo().create({
                    'user_id': odoo_user.id,
                    'full_name': full_name or odoo_user.name,
                    'role': role,
                    'warehouse_id': int(warehouse_id),
                })
                return _success(_serialize_inv_user(inv_user), status=201)

            # ── Mode A: create brand-new user ──────────────────────────────────
            username = (body.get('username') or '').strip()
            password = (body.get('password') or '').strip()

            if not username:
                return _error('username is required', status=400)

            existing = request.env['res.users'].sudo().search([('login', '=', username)], limit=1)
            if existing:
                odoo_user = existing
            else:
                if not password:
                    return _error('password is required for new users', status=400)
                odoo_user = request.env['res.users'].sudo().create({
                    'name': full_name or username,
                    'login': username,
                    'password': password,
                })
                # Grant internal user access (compatible with Odoo 16 & 17)
                try:
                    group_user = request.env.ref('base.group_user')
                    if group_user not in odoo_user.groups_id:
                        odoo_user.sudo().write({'groups_id': [(4, group_user.id)]})
                except Exception:
                    pass

            inv_user = request.env['lugal.inventory.user'].sudo().create({
                'user_id': odoo_user.id,
                'full_name': full_name,
                'role': role,
                'warehouse_id': int(warehouse_id),
            })

            return _success(_serialize_inv_user(inv_user), status=201)
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/users/<int:user_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    @require_auth
    def update_user(self, user_id, **kwargs):
        """Update an inventory user record."""
        try:
            inv_user = request.env['lugal.inventory.user'].sudo().browse(user_id)
            if not inv_user.exists():
                return _error('User not found', status=404)

            body = _parse_body()
            vals = {}
            if 'full_name' in body:
                vals['full_name'] = body['full_name']
            if 'role' in body:
                vals['role'] = body['role']
            if 'warehouse_id' in body:
                vals['warehouse_id'] = int(body['warehouse_id'])

            inv_user.write(vals)
            return _success(_serialize_inv_user(inv_user))
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/users/<int:user_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    @require_auth
    def delete_user(self, user_id, **kwargs):
        """Delete an inventory user record (does not delete the Odoo res.users)."""
        try:
            inv_user = request.env['lugal.inventory.user'].sudo().browse(user_id)
            if not inv_user.exists():
                return _error('User not found', status=404)
            inv_user.unlink()
            return _success({'deleted': True})
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/users/odoo-candidates', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_odoo_candidates(self, **kwargs):
        """
        Return Odoo res.users who exist but have NO lugal.inventory.user record yet.
        These are users that can be imported into the inventory system.
        Excludes system users (id <= 3) and public user.
        """
        try:
            env = request.env
            # Get all user_ids already in inventory system
            existing_ids = env['lugal.inventory.user'].sudo().search([]).mapped('user_id.id')

            # Find res.users not yet linked, excluding system/public accounts
            domain = [
                ('id', 'not in', existing_ids),
                ('id', '>', 3),
                ('active', '=', True),
                ('share', '=', False),  # exclude portal users
            ]
            odoo_users = env['res.users'].sudo().search(domain, order='name asc')

            data = [
                {
                    'id': u.id,
                    'name': u.name or '',
                    'login': u.login or '',
                }
                for u in odoo_users
            ]
            return _success(data)
        except Exception as e:
            return _error(str(e), status=500)
