# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._error import crm_error
from ._permissions import require_permission

_logger = logging.getLogger(__name__)


def _task_to_dict(task):
    """Serialize lugal.crm.task to dict."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description or '',
        'customer_id': task.customer_id.id if task.customer_id else None,
        'customer_name': task.customer_id.name if task.customer_id else '',
        'assigned_to_id': task.assigned_to_id.id if task.assigned_to_id else None,
        'assigned_to_name': task.assigned_to_id.name if task.assigned_to_id else '',
        'created_by_id': task.created_by_id.id if task.created_by_id else None,
        'created_by_name': task.created_by_id.name if task.created_by_id else '',
        'branch_id': task.branch_id.id if task.branch_id else None,
        'branch_name': task.branch_id.name if task.branch_id else '',
        'status': task.status,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'reminder_date': task.reminder_date.isoformat() if task.reminder_date else None,
        'created_at': task.create_date.isoformat() if task.create_date else None,
        'updated_at': task.write_date.isoformat() if task.write_date else None,
    }


class TaskController(http.Controller):

    @http.route('/api/crm/tasks/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_tasks(self, page=1, per_page=50, customer_id=None, branch_id=None,
                   assigned_to_id=None, status=None, priority=None,
                   overdue_only=False, **kwargs):
        """List tasks with filters. Supervisor sees all; agent sees their own."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.list')
            if denied:
                return denied
            from datetime import datetime
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if assigned_to_id:
                domain.append(('assigned_to_id', '=', assigned_to_id))
            if status:
                domain.append(('status', '=', status))
            if priority:
                domain.append(('priority', '=', priority))
            if overdue_only:
                domain += [
                    ('status', 'not in', ['done', 'overdue']),
                    ('due_date', '<', datetime.now()),
                ]
            Task = request.env['lugal.crm.task']
            total = Task.search_count(domain)
            offset = (page - 1) * per_page
            tasks = Task.search(domain, limit=per_page, offset=offset, order='due_date asc, priority desc')
            return {
                'success': True,
                'data': {
                    'items': [_task_to_dict(t) for t in tasks],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'list_tasks')

    @http.route('/api/crm/tasks/<int:task_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_task(self, task_id, **kwargs):
        """Get a single task by ID."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.view')
            if denied:
                return denied
            task = request.env['lugal.crm.task'].browse(task_id)
            if not task.exists() or task.is_deleted:
                return {'success': False, 'error': 'Task not found'}
            return {'success': True, 'data': _task_to_dict(task)}
        except Exception as e:
            return crm_error(e, 'get_task')

    @http.route('/api/crm/tasks/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_task(self, title, customer_id=None, assigned_to_id=None, branch_id=None,
                    description=None, priority='medium', due_date=None, reminder_date=None, **kwargs):
        """Create a new follow-up task."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.create')
            if denied:
                return denied
            if not title:
                return {'success': False, 'error': 'title is required'}
            vals = {
                'title': title,
                'description': description or '',
                'priority': priority,
                'assigned_to_id': assigned_to_id or request.env.uid,
            }
            if customer_id:
                vals['customer_id'] = customer_id
            if branch_id:
                vals['branch_id'] = branch_id
            if due_date:
                vals['due_date'] = due_date
            if reminder_date:
                vals['reminder_date'] = reminder_date
            task = request.env['lugal.crm.task'].create(vals)
            crm_audit('task_created', customer_id=customer_id,
                      record_model='lugal.crm.task', record_id=task.id,
                      details={'title': title, 'priority': priority, 'assigned_to_id': assigned_to_id})
            return {'success': True, 'data': _task_to_dict(task)}
        except Exception as e:
            return crm_error(e, 'create_task')

    @http.route('/api/crm/tasks/<int:task_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_task(self, task_id, **kwargs):
        """Update task fields."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.edit')
            if denied:
                return denied
            task = request.env['lugal.crm.task'].browse(task_id)
            if not task.exists() or task.is_deleted:
                return {'success': False, 'error': 'Task not found'}
            allowed = {'title', 'description', 'priority', 'due_date', 'reminder_date',
                       'assigned_to_id', 'branch_id', 'customer_id'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                task.write(vals)
            return {'success': True, 'data': _task_to_dict(task)}
        except Exception as e:
            return crm_error(e, 'update_task')

    @http.route('/api/crm/tasks/<int:task_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_status(self, task_id, status, **kwargs):
        """Update task status: open / in_progress / done / overdue."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.close' if status in ('done', 'closed') else 'tasks.edit')
            if denied:
                return denied
            task = request.env['lugal.crm.task'].browse(task_id)
            if not task.exists() or task.is_deleted:
                return {'success': False, 'error': 'Task not found'}
            task.write({'status': status})
            crm_audit('task_status_changed',
                      customer_id=task.customer_id.id if task.customer_id else None,
                      record_model='lugal.crm.task', record_id=task_id,
                      details={'new_status': status})
            return {'success': True, 'data': _task_to_dict(task)}
        except Exception as e:
            return crm_error(e, 'update_status')

    @http.route('/api/crm/tasks/<int:task_id>/assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def assign_task(self, task_id, assigned_to_id, **kwargs):
        """Re-assign a task to another user."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.assign')
            if denied:
                return denied
            task = request.env['lugal.crm.task'].browse(task_id)
            if not task.exists() or task.is_deleted:
                return {'success': False, 'error': 'Task not found'}
            task.write({'assigned_to_id': assigned_to_id, 'status': 'open'})
            crm_audit('task_assigned',
                      customer_id=task.customer_id.id if task.customer_id else None,
                      record_model='lugal.crm.task', record_id=task_id,
                      details={'assigned_to_id': assigned_to_id})
            return {'success': True, 'data': _task_to_dict(task)}
        except Exception as e:
            return crm_error(e, 'assign_task')

    @http.route('/api/crm/tasks/<int:task_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_task(self, task_id, **kwargs):
        """Soft-delete a task."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.delete')
            if denied:
                return denied
            task = request.env['lugal.crm.task'].browse(task_id)
            if not task.exists():
                return {'success': False, 'error': 'Task not found'}
            task.write({'is_deleted': True, 'active': False})
            crm_audit('task_deleted',
                      customer_id=task.customer_id.id if task.customer_id else None,
                      record_model='lugal.crm.task', record_id=task_id)
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_task')

    @http.route('/api/crm/tasks/my', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def my_tasks(self, page=1, per_page=30, status=None, **kwargs):
        """Get tasks assigned to the current user (agent's personal task list)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tasks.list')
            if denied:
                return denied
            domain = [
                ('is_deleted', '=', False),
                ('active', '=', True),
                ('assigned_to_id', '=', request.env.uid),
            ]
            if status:
                domain.append(('status', '=', status))
            Task = request.env['lugal.crm.task']
            total = Task.search_count(domain)
            tasks = Task.search(domain, limit=per_page, offset=(page - 1) * per_page,
                                order='due_date asc, priority desc')
            return {
                'success': True,
                'data': {
                    'items': [_task_to_dict(t) for t in tasks],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'my_tasks')
