# -*- coding: utf-8 -*-

import logging
import json
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSWorkflowController(http.Controller):
    """
    Folder workflow API (admin-focused for configuration).
    """

    @http.route('/api/workflows', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_workflows(self, department_id=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Access denied', 'data': []}

            domain = [('active', '=', True)]
            if department_id:
                domain.append(('department_id', '=', int(department_id)))

            wfs = request.env['nbs.folder.workflow'].sudo().search(domain, order='name asc')
            return {
                'success': True,
                'data': [{
                    'id': wf.id,
                    'name': wf.name,
                    'department_id': wf.department_id.id if wf.department_id else None,
                    'department_name': wf.department_id.name if wf.department_id else None,
                } for wf in wfs]
            }
        except Exception as e:
            _logger.error(f'List workflows error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e), 'data': []}

    @http.route('/api/workflows/<int:workflow_id>/detail', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def workflow_detail(self, workflow_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Access denied'}

            wf = request.env['nbs.folder.workflow'].sudo().browse(workflow_id)
            if not wf.exists():
                return {'success': False, 'error': 'Workflow not found'}

            states = wf.state_ids.sorted(key=lambda s: (s.sequence, s.id))
            transitions = wf.transition_ids

            return {
                'success': True,
                'data': {
                    'id': wf.id,
                    'name': wf.name,
                    'department_id': wf.department_id.id if wf.department_id else None,
                    'states': [{
                        'id': s.id,
                        'name': s.name,
                        'code': s.code,
                        'sequence': s.sequence,
                        'is_initial': s.is_initial,
                        'is_final': s.is_final,
                    } for s in states],
                    'transitions': [{
                        'id': tr.id,
                        'name': tr.name,
                        'from_state_id': tr.from_state_id.id,
                        'to_state_id': tr.to_state_id.id,
                        'allow_employee': tr.allow_employee,
                        'allow_manager': tr.allow_manager,
                        'allow_admin': tr.allow_admin,
                        'requires_request': tr.requires_request,
                    } for tr in transitions],
                }
            }
        except Exception as e:
            _logger.error(f'Workflow detail error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/folders/<int:folder_id>/workflow', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def folder_workflow(self, folder_id, **kwargs):
        """
        Returns folder workflow info and allowed transitions for current user.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].sudo().browse(folder_id)
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}

            wf = folder.workflow_id
            st = folder.workflow_state_id

            allowed = []
            if wf and st:
                user = request.env.user
                is_admin = user.has_group('nbs_archive.group_nbs_admin')
                is_manager = user.has_group('nbs_archive.group_nbs_manager')
                is_employee = not (is_admin or is_manager)

                for tr in wf.transition_ids:
                    if tr.from_state_id.id != st.id:
                        continue
                    if is_admin and not tr.allow_admin:
                        continue
                    if is_manager and not tr.allow_manager:
                        continue
                    if is_employee and not tr.allow_employee:
                        continue
                    allowed.append({
                        'id': tr.id,
                        'name': tr.name,
                        'to_state_id': tr.to_state_id.id,
                        'to_state_name': tr.to_state_id.name,
                        'requires_request': tr.requires_request,
                    })

            return {
                'success': True,
                'data': {
                    'folder_id': folder.id,
                    'workflow_id': wf.id if wf else None,
                    'workflow_name': wf.name if wf else None,
                    'state_id': st.id if st else None,
                    'state_name': st.name if st else None,
                    'allowed_transitions': allowed,
                }
            }
        except Exception as e:
            _logger.error(f'Folder workflow error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/folders/<int:folder_id>/workflow/set', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def folder_workflow_set(self, folder_id, workflow_id, state_id=None, **kwargs):
        """
        Assign a workflow to a folder (Admin only). If state_id is omitted, uses workflow initial state.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Access denied'}

            folder = request.env['nbs.document.folder'].sudo().browse(folder_id)
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}

            wf = request.env['nbs.folder.workflow'].sudo().browse(int(workflow_id))
            if not wf.exists():
                return {'success': False, 'error': 'Workflow not found'}

            if state_id:
                st = request.env['nbs.folder.workflow.state'].sudo().browse(int(state_id))
                if not st.exists() or st.workflow_id.id != wf.id:
                    return {'success': False, 'error': 'Invalid state for workflow'}
            else:
                st = wf.state_ids.filtered(lambda s: s.is_initial)[:1]
                if not st:
                    return {'success': False, 'error': 'Workflow has no initial state'}

            folder.write({
                'workflow_id': wf.id,
                'workflow_state_id': st.id,
            })

            return {'success': True}
        except Exception as e:
            _logger.error(f'Set folder workflow error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/folders/<int:folder_id>/workflow/transition', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def folder_workflow_transition(self, folder_id, transition_id, message=None, **kwargs):
        """
        Apply a workflow transition for a folder, enforcing role gating.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].sudo().browse(folder_id)
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}

            if not folder.workflow_id or not folder.workflow_state_id:
                return {'success': False, 'error': 'Folder has no workflow assigned'}

            tr = request.env['nbs.folder.workflow.transition'].sudo().browse(int(transition_id))
            if not tr.exists() or tr.workflow_id.id != folder.workflow_id.id:
                return {'success': False, 'error': 'Invalid transition'}

            if tr.from_state_id.id != folder.workflow_state_id.id:
                return {'success': False, 'error': 'Transition not allowed from current state'}

            user = request.env.user
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            is_manager = user.has_group('nbs_archive.group_nbs_manager')
            is_employee = not (is_admin or is_manager)

            if is_admin and not tr.allow_admin:
                return {'success': False, 'error': 'Not allowed'}
            if is_manager and not tr.allow_manager:
                return {'success': False, 'error': 'Not allowed'}
            if is_employee and not tr.allow_employee:
                return {'success': False, 'error': 'Not allowed'}

            # For now, we only enforce request-gating at UI level; server returns requires_request.
            folder.write({'workflow_state_id': tr.to_state_id.id})

            # Store optional message about the transition in audit log (for traceability)
            try:
                details = {
                    'entity': 'folder',
                    'folder_id': folder.id,
                    'folder_name': folder.name,
                    'from_state_id': tr.from_state_id.id,
                    'from_state_name': tr.from_state_id.name,
                    'to_state_id': tr.to_state_id.id,
                    'to_state_name': tr.to_state_id.name,
                    'transition_id': tr.id,
                    'transition_name': tr.name,
                    'message': (message or '').strip() or None,
                }
                request.env['nbs.audit.log'].sudo().log_action(
                    action='approval',
                    department_id=folder.department_id.id if folder.department_id else None,
                    ip_address=request.httprequest.remote_addr,
                    user_agent=request.httprequest.headers.get('User-Agent', ''),
                    details=json.dumps(details, ensure_ascii=False),
                )
            except Exception:
                # Audit should not break workflow transition
                _logger.warning('Failed to write workflow transition audit log', exc_info=True)

            return {'success': True, 'data': {'state_id': folder.workflow_state_id.id, 'state_name': folder.workflow_state_id.name}}
        except Exception as e:
            _logger.error(f'Workflow transition error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}


