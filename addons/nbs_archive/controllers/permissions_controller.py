# -*- coding: utf-8 -*-

import logging
import json
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSPermissionsController(http.Controller):
    """
    Admin permission management (roles + department access).
    """

    def _require_admin(self):
        if not ensure_jwt_user_id():
            return False, {'success': False, 'error': 'Unauthorized'}
        if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
            return False, {'success': False, 'error': 'Access denied'}
        return True, None

    @http.route('/api/nbs/admin/users', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_users(self, **kwargs):
        try:
            ok, err = self._require_admin()
            if not ok:
                return request.make_json_response(err, status=401 if err.get('error') == 'Unauthorized' else 403)

            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except Exception:
                data = {}

            search = data.get('search')

            domain = [('active', '=', True)]
            if search:
                domain = ['|', ('name', 'ilike', search), ('login', 'ilike', search)] + domain

            users = request.env['res.users'].sudo().search(domain, order='name asc', limit=200)

            grp_admin = request.env.ref('nbs_archive.group_nbs_admin').id
            grp_manager = request.env.ref('nbs_archive.group_nbs_manager').id
            grp_user = request.env.ref('nbs_archive.group_nbs_user').id

            data = []
            for u in users:
                # role derived from group membership
                if grp_admin in u.group_ids.ids:
                    role = 'admin'
                elif grp_manager in u.group_ids.ids:
                    role = 'manager'
                elif grp_user in u.group_ids.ids:
                    role = 'employee'
                else:
                    role = 'employee'

                data.append({
                    'id': u.id,
                    'name': u.name,
                    'login': u.login,
                    'email': u.email,
                    'role': role,
                    'department_ids': getattr(u, 'nbs_department_ids', request.env['nbs.department']).ids,
                    'manager_department_ids': getattr(u, 'nbs_manager_department_ids', request.env['nbs.department']).ids,
                })

            return request.make_json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f'List users error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e), 'data': []}, status=500)

    @http.route('/api/nbs/admin/users/<int:user_id>/update', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_user(self, user_id, **kwargs):
        try:
            ok, err = self._require_admin()
            if not ok:
                return request.make_json_response(err, status=401 if err.get('error') == 'Unauthorized' else 403)

            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except Exception:
                data = {}

            role = data.get('role')
            department_ids = data.get('department_ids')
            manager_department_ids = data.get('manager_department_ids')

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return request.make_json_response({'success': False, 'error': 'User not found'}, status=404)

            grp_admin = request.env.ref('nbs_archive.group_nbs_admin').id
            grp_manager = request.env.ref('nbs_archive.group_nbs_manager').id
            grp_user = request.env.ref('nbs_archive.group_nbs_user').id

            # Set role groups (remove all then add desired)
            if role:
                role = str(role).lower()
                remove_cmds = [(3, grp_admin), (3, grp_manager), (3, grp_user)]
                add_cmds = []
                if role == 'admin':
                    add_cmds.append((4, grp_admin))
                elif role == 'manager':
                    add_cmds.append((4, grp_manager))
                else:
                    add_cmds.append((4, grp_user))
                user.write({'groups_id': remove_cmds + add_cmds})

            # Departments access
            if department_ids is not None:
                dept_ids = [int(x) for x in (department_ids or [])]
                user.write({'nbs_department_ids': [(6, 0, dept_ids)]})

            # Managed departments (subset)
            if manager_department_ids is not None:
                mgr_ids = [int(x) for x in (manager_department_ids or [])]
                user.write({'nbs_manager_department_ids': [(6, 0, mgr_ids)]})

            return request.make_json_response({'success': True})
        except Exception as e:
            _logger.error(f'Update user error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)}, status=500)


