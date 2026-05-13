# -*- coding: utf-8 -*-
"""
Config controller — lookup/admin data:
  - Tags            /api/crm/config/tags/*
  - Customer Stages /api/crm/config/stages/*
  - Call Scripts    /api/crm/config/scripts/*
"""

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._permissions import is_supervisor_or_above, forbidden, require_permission
from ._error import crm_error

_logger = logging.getLogger(__name__)


# ── Serialisers ───────────────────────────────────────────────────────────────

def _tag_to_dict(tag):
    """Serialize lugal.crm.tag."""
    return {
        'id': tag.id,
        'name': tag.name,
        'name_ar': tag.name_ar or '',
        'tag_type': tag.tag_type,
        'color': tag.color,
        'sequence': tag.sequence,
    }


def _stage_to_dict(stage):
    """Serialize lugal.crm.customer.stage."""
    return {
        'id': stage.id,
        'name': stage.name,
        'name_ar': stage.name_ar or '',
        'stage_type': stage.stage_type,
        'sequence': stage.sequence,
    }


def _script_to_dict(script):
    """Serialize lugal.crm.call.script."""
    return {
        'id': script.id,
        'title': script.title,
        'category': script.category,
        'question': script.question or '',
        'answer': script.answer or '',
        'branch_id': script.branch_id.id if script.branch_id else None,
        'branch_name': script.branch_id.name if script.branch_id else '',
        'sequence': script.sequence,
        'is_active': script.is_active,
    }


# ── Tags ──────────────────────────────────────────────────────────────────────

class ConfigController(http.Controller):

    @http.route('/api/crm/config/tags/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def tag_list(self, tag_type=None, **kwargs):
        """List all active tags, optionally filtered by type."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if tag_type:
                domain.append(('tag_type', '=', tag_type))
            tags = request.env['lugal.crm.tag'].search(domain, order='sequence asc, name asc')
            return {'success': True, 'data': [_tag_to_dict(t) for t in tags]}
        except Exception as e:
            return crm_error(e, 'tag_list')

    @http.route('/api/crm/config/tags/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def tag_create(self, name, name_ar=None, tag_type='custom', color=0, sequence=10, **kwargs):
        """Create a new customer tag. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            if not name:
                return {'success': False, 'error': 'name is required'}
            tag = request.env['lugal.crm.tag'].create({
                'name': name,
                'name_ar': name_ar or '',
                'tag_type': tag_type,
                'color': color,
                'sequence': sequence,
            })
            return {'success': True, 'data': _tag_to_dict(tag)}
        except Exception as e:
            return crm_error(e, 'tag_create')

    @http.route('/api/crm/config/tags/<int:tag_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def tag_update(self, tag_id, **kwargs):
        """Update an existing tag. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            tag = request.env['lugal.crm.tag'].browse(tag_id)
            if not tag.exists() or tag.is_deleted:
                return {'success': False, 'error': 'Tag not found'}
            allowed = {'name', 'name_ar', 'tag_type', 'color', 'sequence'}
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                tag.write(vals)
            return {'success': True, 'data': _tag_to_dict(tag)}
        except Exception as e:
            return crm_error(e, 'tag_update')

    @http.route('/api/crm/config/tags/<int:tag_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def tag_delete(self, tag_id, **kwargs):
        """Soft-delete a tag. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            tag = request.env['lugal.crm.tag'].browse(tag_id)
            if not tag.exists():
                return {'success': False, 'error': 'Tag not found'}
            tag.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'tag_delete')

    # ── Customer Stages ───────────────────────────────────────────────────────

    @http.route('/api/crm/config/stages/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stage_list(self, **kwargs):
        """List all customer pipeline stages in sequence order."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            stages = request.env['lugal.crm.customer.stage'].search(
                [('is_deleted', '=', False), ('active', '=', True)],
                order='sequence asc',
            )
            return {'success': True, 'data': [_stage_to_dict(s) for s in stages]}
        except Exception as e:
            return crm_error(e, 'stage_list')

    @http.route('/api/crm/config/stages/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stage_create(self, name, stage_type='lead', name_ar=None, sequence=10, **kwargs):
        """Create a new customer pipeline stage. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            if not name:
                return {'success': False, 'error': 'name is required'}
            stage = request.env['lugal.crm.customer.stage'].create({
                'name': name,
                'name_ar': name_ar or '',
                'stage_type': stage_type,
                'sequence': sequence,
            })
            return {'success': True, 'data': _stage_to_dict(stage)}
        except Exception as e:
            return crm_error(e, 'stage_create')

    @http.route('/api/crm/config/stages/<int:stage_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stage_update(self, stage_id, **kwargs):
        """Update a pipeline stage. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            stage = request.env['lugal.crm.customer.stage'].browse(stage_id)
            if not stage.exists() or stage.is_deleted:
                return {'success': False, 'error': 'Stage not found'}
            allowed = {'name', 'name_ar', 'stage_type', 'sequence'}
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                stage.write(vals)
            return {'success': True, 'data': _stage_to_dict(stage)}
        except Exception as e:
            return crm_error(e, 'stage_update')

    @http.route('/api/crm/config/stages/<int:stage_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stage_delete(self, stage_id, **kwargs):
        """Soft-delete a pipeline stage. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.general.edit')
            if denied:
                return denied
            stage = request.env['lugal.crm.customer.stage'].browse(stage_id)
            if not stage.exists():
                return {'success': False, 'error': 'Stage not found'}
            stage.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'stage_delete')

    # ── Call Scripts ──────────────────────────────────────────────────────────

    @http.route('/api/crm/config/scripts/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def script_list(self, category=None, branch_id=None, search=None, **kwargs):
        """List call scripts/FAQs for agents. Filterable by category and branch."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('is_active', '=', True)]
            if category:
                domain.append(('category', '=', category))
            if branch_id:
                domain += ['|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]
            if search:
                domain += ['|', ('title', 'ilike', search), ('question', 'ilike', search)]
            scripts = request.env['lugal.crm.call.script'].search(domain, order='sequence asc')
            return {'success': True, 'data': [_script_to_dict(s) for s in scripts]}
        except Exception as e:
            return crm_error(e, 'script_list')

    @http.route('/api/crm/config/scripts/<int:script_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def script_get(self, script_id, **kwargs):
        """Get a single call script by ID."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            script = request.env['lugal.crm.call.script'].browse(script_id)
            if not script.exists() or script.is_deleted:
                return {'success': False, 'error': 'Script not found'}
            return {'success': True, 'data': _script_to_dict(script)}
        except Exception as e:
            return crm_error(e, 'script_get')

    @http.route('/api/crm/config/scripts/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def script_create(self, title, category='faq', question=None, answer=None,
                      branch_id=None, sequence=10, **kwargs):
        """Create a call script / FAQ entry. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.templates.create')
            if denied:
                return denied
            if not title:
                return {'success': False, 'error': 'title is required'}
            vals = {'title': title, 'category': category, 'sequence': sequence}
            if question:
                vals['question'] = question
            if answer:
                vals['answer'] = answer
            if branch_id:
                vals['branch_id'] = branch_id
            script = request.env['lugal.crm.call.script'].create(vals)
            return {'success': True, 'data': _script_to_dict(script)}
        except Exception as e:
            return crm_error(e, 'script_create')

    @http.route('/api/crm/config/scripts/<int:script_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def script_update(self, script_id, **kwargs):
        """Update a call script. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.templates.edit')
            if denied:
                return denied
            script = request.env['lugal.crm.call.script'].browse(script_id)
            if not script.exists() or script.is_deleted:
                return {'success': False, 'error': 'Script not found'}
            allowed = {'title', 'category', 'question', 'answer', 'branch_id', 'sequence', 'is_active'}
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                script.write(vals)
            return {'success': True, 'data': _script_to_dict(script)}
        except Exception as e:
            return crm_error(e, 'script_update')

    @http.route('/api/crm/config/scripts/<int:script_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def script_delete(self, script_id, **kwargs):
        """Soft-delete a call script. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('settings.templates.delete')
            if denied:
                return denied
            script = request.env['lugal.crm.call.script'].browse(script_id)
            if not script.exists():
                return {'success': False, 'error': 'Script not found'}
            script.write({'is_deleted': True, 'is_active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'script_delete')
