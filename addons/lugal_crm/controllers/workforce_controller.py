# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)


# ─── Serializers ──────────────────────────────────────────────────────────────

def _shift_to_dict(s):
    return {
        'id': s.id,
        'name': s.name,
        'name_ar': s.name_ar or '',
        'branch_id': s.branch_id.id if s.branch_id else None,
        'branch_name': s.branch_id.name if s.branch_id else '',
        'shift_type': s.shift_type,
        'start_time': s.start_time,
        'end_time': s.end_time,
        'user_ids': s.user_ids.ids,
        'user_names': [u.name for u in s.user_ids],
        'is_active': s.is_active,
    }


def _attendance_to_dict(a):
    return {
        'id': a.id,
        'employee_id': a.employee_id.id if a.employee_id else None,
        'employee_name': a.employee_id.name if a.employee_id else '',
        'branch_id': a.branch_id.id if a.branch_id else None,
        'shift_id': a.shift_id.id if a.shift_id else None,
        'shift_name': a.shift_id.name if a.shift_id else '',
        'check_in': a.check_in.isoformat() if a.check_in else None,
        'check_out': a.check_out.isoformat() if a.check_out else None,
        'duration_hours': a.duration_hours,
        'work_type': a.work_type,
        'ip_address': a.ip_address or '',
        'device_type': a.device_type or '',
        'location_label': a.location_label or '',
        'location_lat': a.location_lat,
        'location_lng': a.location_lng,
        'is_late': a.is_late,
        'notes': a.notes or '',
    }


def _template_to_dict(t):
    return {
        'id': t.id,
        'name': t.name,
        'name_ar': t.name_ar or '',
        'channel': t.channel,
        'category': t.category,
        'body': t.body,
        'body_ar': t.body_ar or '',
        'branch_id': t.branch_id.id if t.branch_id else None,
        'requires_approval': t.requires_approval,
        'approval_status': t.approval_status,
        'is_active': t.is_active,
    }


class WorkforceController(http.Controller):

    # ─── Shifts ───────────────────────────────────────────────────────────

    @http.route('/api/crm/shifts/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def shift_list(self, branch_id=None, **kwargs):
        """List work shifts for a branch."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            shifts = request.env['lugal.crm.shift'].search(domain, order='branch_id asc, start_time asc')
            return {'success': True, 'data': {'items': [_shift_to_dict(s) for s in shifts]}}
        except Exception as e:
            return crm_error(e, 'shift_list')

    @http.route('/api/crm/shifts/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def shift_create(self, name, branch_id, shift_type='morning', start_time=8.0, end_time=17.0,
                     user_ids=None, name_ar=None, **kwargs):
        """Create a work shift."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {
                'name': name,
                'name_ar': name_ar or '',
                'branch_id': branch_id,
                'shift_type': shift_type,
                'start_time': start_time,
                'end_time': end_time,
            }
            if user_ids:
                vals['user_ids'] = [(6, 0, user_ids)]
            shift = request.env['lugal.crm.shift'].create(vals)
            return {'success': True, 'data': _shift_to_dict(shift)}
        except Exception as e:
            return crm_error(e, 'shift_create')

    @http.route('/api/crm/shifts/<int:shift_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def shift_update(self, shift_id, **kwargs):
        """Update a shift."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            shift = request.env['lugal.crm.shift'].browse(shift_id)
            if not shift.exists() or shift.is_deleted:
                return {'success': False, 'error': 'Shift not found'}
            allowed = {'name', 'name_ar', 'shift_type', 'start_time', 'end_time', 'is_active'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if 'user_ids' in kwargs and kwargs['user_ids'] is not None:
                vals['user_ids'] = [(6, 0, kwargs['user_ids'])]
            if vals:
                shift.write(vals)
            return {'success': True, 'data': _shift_to_dict(shift)}
        except Exception as e:
            return crm_error(e, 'shift_update')

    @http.route('/api/crm/shifts/<int:shift_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def shift_delete(self, shift_id, **kwargs):
        """Soft-delete a shift."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            shift = request.env['lugal.crm.shift'].browse(shift_id)
            if not shift.exists():
                return {'success': False, 'error': 'Shift not found'}
            shift.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'shift_delete')

    # ─── Attendance ───────────────────────────────────────────────────────

    @http.route('/api/crm/attendance/check_in', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def check_in(self, branch_id=None, shift_id=None, work_type='office',
                 ip_address=None, device_type=None, location_lat=None, location_lng=None,
                 location_label=None, **kwargs):
        """Employee check-in."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            from odoo.fields import Datetime
            uid = request.env.uid

            # Check if already checked in (no check_out yet)
            existing = request.env['lugal.crm.attendance'].search([
                ('employee_id', '=', uid),
                ('check_out', '=', False),
                ('is_deleted', '=', False),
            ], limit=1)
            if existing:
                return {'success': False, 'error': 'Already checked in — please check out first'}

            # Determine if late (compare to shift start)
            is_late = False
            if shift_id:
                shift = request.env['lugal.crm.shift'].browse(shift_id)
                if shift.exists():
                    now = Datetime.now()
                    shift_start_hour = shift.start_time
                    current_hour = now.hour + now.minute / 60.0
                    is_late = current_hour > (shift_start_hour + 0.25)  # 15 min grace

            record = request.env['lugal.crm.attendance'].create({
                'employee_id': uid,
                'branch_id': branch_id,
                'shift_id': shift_id,
                'check_in': Datetime.now(),
                'work_type': work_type,
                'ip_address': ip_address or '',
                'device_type': device_type or '',
                'location_lat': location_lat or 0.0,
                'location_lng': location_lng or 0.0,
                'location_label': location_label or '',
                'is_late': is_late,
            })
            return {'success': True, 'data': _attendance_to_dict(record)}
        except Exception as e:
            return crm_error(e, 'check_in')

    @http.route('/api/crm/attendance/check_out', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def check_out(self, notes=None, **kwargs):
        """Employee check-out — closes the open attendance record."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            from odoo.fields import Datetime
            uid = request.env.uid

            record = request.env['lugal.crm.attendance'].search([
                ('employee_id', '=', uid),
                ('check_out', '=', False),
                ('is_deleted', '=', False),
            ], limit=1)
            if not record:
                return {'success': False, 'error': 'No open check-in found'}

            now = Datetime.now()
            delta = (now - record.check_in).total_seconds() / 3600.0
            record.write({
                'check_out': now,
                'duration_hours': round(delta, 2),
                'notes': notes or '',
            })
            return {'success': True, 'data': _attendance_to_dict(record)}
        except Exception as e:
            return crm_error(e, 'check_out')

    @http.route('/api/crm/attendance/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def attendance_list(self, page=1, per_page=50, branch_id=None, employee_id=None,
                        date_from=None, date_to=None, work_type=None, **kwargs):
        """List attendance records. Supervisor/HR use."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            if date_from:
                domain.append(('check_in', '>=', date_from))
            if date_to:
                domain.append(('check_in', '<=', date_to))
            if work_type:
                domain.append(('work_type', '=', work_type))
            Att = request.env['lugal.crm.attendance']
            total = Att.search_count(domain)
            records = Att.search(domain, limit=per_page, offset=(page - 1) * per_page, order='check_in desc')
            return {
                'success': True,
                'data': {
                    'items': [_attendance_to_dict(r) for r in records],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'attendance_list')

    @http.route('/api/crm/attendance/live_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def live_status(self, branch_id=None, **kwargs):
        """Supervisor view: who is currently checked in."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('check_out', '=', False), ('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            online = request.env['lugal.crm.attendance'].search(domain, order='check_in asc')
            items = [{
                'employee_id': r.employee_id.id if r.employee_id else None,
                'employee_name': r.employee_id.name if r.employee_id else '',
                'check_in': r.check_in.isoformat() if r.check_in else None,
                'work_type': r.work_type,
                'location_label': r.location_label or '',
                'shift': r.shift_id.name if r.shift_id else '',
            } for r in online]
            return {'success': True, 'data': {'online': items, 'count': len(items)}}
        except Exception as e:
            return crm_error(e, 'live_status')

    # ─── Message Templates ────────────────────────────────────────────────

    @http.route('/api/crm/templates/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_list(self, channel=None, category=None, branch_id=None, **kwargs):
        """List message templates (for agent quick-reply)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('is_active', '=', True)]
            if channel:
                domain += ['|', ('channel', '=', channel), ('channel', '=', 'any')]
            if category:
                domain.append(('category', '=', category))
            if branch_id:
                domain += ['|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]
            templates = request.env['lugal.crm.message.template'].search(domain, order='category asc, name asc')
            return {'success': True, 'data': {'items': [_template_to_dict(t) for t in templates]}}
        except Exception as e:
            return crm_error(e, 'template_list')

    @http.route('/api/crm/templates/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_create(self, name, channel, body, category='other', body_ar=None,
                        branch_id=None, requires_approval=False, **kwargs):
        """Create a message template."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            tmpl = request.env['lugal.crm.message.template'].create({
                'name': name,
                'channel': channel,
                'body': body,
                'body_ar': body_ar or '',
                'category': category,
                'branch_id': branch_id,
                'requires_approval': requires_approval,
            })
            return {'success': True, 'data': _template_to_dict(tmpl)}
        except Exception as e:
            return crm_error(e, 'template_create')

    @http.route('/api/crm/templates/<int:template_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_update(self, template_id, **kwargs):
        """Update a message template."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            tmpl = request.env['lugal.crm.message.template'].browse(template_id)
            if not tmpl.exists() or tmpl.is_deleted:
                return {'success': False, 'error': 'Template not found'}
            allowed = {'name', 'name_ar', 'channel', 'category', 'body', 'body_ar',
                       'branch_id', 'requires_approval', 'approval_status', 'is_active'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                tmpl.write(vals)
            return {'success': True, 'data': _template_to_dict(tmpl)}
        except Exception as e:
            return crm_error(e, 'template_update')

    @http.route('/api/crm/templates/<int:template_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_delete(self, template_id, **kwargs):
        """Soft-delete a template."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            tmpl = request.env['lugal.crm.message.template'].browse(template_id)
            if not tmpl.exists():
                return {'success': False, 'error': 'Template not found'}
            tmpl.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'template_delete')

    @http.route('/api/crm/templates/<int:template_id>/render', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_render(self, template_id, customer_id=None, **kwargs):
        """
        Render a template body with substituted variables.
        Variables: {customer_name}, {agent_name}, {branch_name}.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            tmpl = request.env['lugal.crm.message.template'].browse(template_id)
            if not tmpl.exists() or tmpl.is_deleted:
                return {'success': False, 'error': 'Template not found'}

            agent = request.env.user
            customer_name = ''
            if customer_id:
                c = request.env['lugal.crm.customer'].browse(customer_id)
                if c.exists():
                    customer_name = c.name

            variables = {
                'customer_name': customer_name,
                'agent_name': agent.name or '',
                'branch_name': tmpl.branch_id.name if tmpl.branch_id else '',
            }

            rendered = tmpl.body
            rendered_ar = tmpl.body_ar or ''
            for k, v in variables.items():
                rendered = rendered.replace(f'{{{k}}}', v)
                rendered_ar = rendered_ar.replace(f'{{{k}}}', v)

            return {'success': True, 'data': {'rendered': rendered, 'rendered_ar': rendered_ar}}
        except Exception as e:
            return crm_error(e, 'template_render')

    @http.route('/api/crm/employees/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employees_list(self, **kwargs):
        """Internal active users (CRM / supply assignment pickers)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            users = request.env['res.users'].search(
                [('share', '=', False), ('active', '=', True)],
                order='name asc',
                limit=500,
            )
            items = []
            for u in users:
                items.append({
                    'id': u.id,
                    'name': u.name or '',
                    'email': u.email or '',
                    'login': u.login or '',
                    'job_position': u.partner_id.function or '',
                    'avatar': f'/web/image/res.users/{u.id}/avatar_128',
                })
            return {'success': True, 'data': {'items': items, 'total': len(items)}}
        except Exception as e:
            return crm_error(e, 'employees_list')
