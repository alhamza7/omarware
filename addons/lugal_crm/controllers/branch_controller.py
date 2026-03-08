# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._permissions import is_manager_or_above, is_supervisor_or_above, forbidden
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _branch_to_dict(branch):
    return {
        'id': branch.id,
        'name': branch.name,
        'name_ar': branch.name_ar or '',
        'code': branch.code or '',
        'city': branch.city or '',
        'address': branch.address or '',
        'phone': branch.phone or '',
        'email': branch.email or '',
        'manager_id': branch.manager_id.id if branch.manager_id else None,
        'manager_name': branch.manager_id.name if branch.manager_id else '',
        'user_ids': branch.user_ids.ids,
        'customer_count': branch.customer_count,
    }


class BranchController(http.Controller):

    @http.route('/api/crm/branches/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_branches(self, **kwargs):
        """List all active branches (non-deleted)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            branches = request.env['lugal.crm.branch'].search(domain, order='name asc')
            return {'success': True, 'data': {'items': [_branch_to_dict(b) for b in branches]}}
        except Exception as e:
            return crm_error(e, 'list_branches')

    @http.route('/api/crm/branches/<int:branch_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_branch(self, branch_id, **kwargs):
        """Get single branch."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            branch = request.env['lugal.crm.branch'].browse(branch_id)
            if not branch.exists() or branch.is_deleted:
                return {'success': False, 'error': 'Branch not found'}
            return {'success': True, 'data': _branch_to_dict(branch)}
        except Exception as e:
            return crm_error(e, 'get_branch')

    @http.route('/api/crm/branches/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_branch(self, name, name_ar=None, code=None, city=None, address=None, phone=None, email=None, manager_id=None, **kwargs):
        """Create a new branch. Requires Manager or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Branch creation requires Manager role or above')
            vals = {
                'name': name,
                'name_ar': name_ar,
                'code': code,
                'city': city,
                'address': address,
                'phone': phone,
                'email': email,
                'manager_id': manager_id,
            }
            branch = request.env['lugal.crm.branch'].create(vals)
            return {'success': True, 'data': _branch_to_dict(branch)}
        except Exception as e:
            return crm_error(e, 'create_branch')

    @http.route('/api/crm/branches/<int:branch_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_branch(self, branch_id, **kwargs):
        """Update branch. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Branch update requires Supervisor role or above')
            branch = request.env['lugal.crm.branch'].browse(branch_id)
            if not branch.exists() or branch.is_deleted:
                return {'success': False, 'error': 'Branch not found'}
            allow = set(request.env['lugal.crm.branch']._fields) - {'id', 'create_date', 'create_uid', 'write_date', 'write_uid', 'customer_count'}
            vals = {k: v for k, v in kwargs.items() if k in allow and v is not None}
            if vals:
                branch.write(vals)
            return {'success': True, 'data': _branch_to_dict(branch)}
        except Exception as e:
            return crm_error(e, 'update_branch')

    @http.route('/api/crm/branches/<int:branch_id>/user_assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def user_assign(self, branch_id, user_ids, **kwargs):
        """Set authorized users for a branch. Requires Manager or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('User assignment requires Manager role or above')
            branch = request.env['lugal.crm.branch'].browse(branch_id)
            if not branch.exists() or branch.is_deleted:
                return {'success': False, 'error': 'Branch not found'}
            branch.write({'user_ids': [(6, 0, user_ids or [])]})
            return {'success': True, 'data': _branch_to_dict(branch)}
        except Exception as e:
            return crm_error(e, 'user_assign')

    @http.route('/api/crm/branches/<int:branch_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_branch(self, branch_id, **kwargs):
        """Soft-delete a branch. Requires Manager or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Branch deletion requires Manager role or above')
            branch = request.env['lugal.crm.branch'].browse(branch_id)
            if not branch.exists():
                return {'success': False, 'error': 'Branch not found'}
            branch.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_branch')
