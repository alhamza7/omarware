# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)

# Role → group xmlid map (Odoo 19: use group.user_ids not domain search)
_ROLE_GROUP_MAP = {
    'agent':      'lugal_crm.group_lugal_crm_agent',
    'supervisor': 'lugal_crm.group_lugal_crm_supervisor',
    'manager':    'lugal_crm.group_lugal_crm_manager',
}


def _build_employee_dict(user):
    """
    Canonical serializer for a CRM employee (res.users record).
    Used by list, detail, create, and update endpoints.
    Matches the CrmEmployee TypeScript interface in the frontend.
    """
    role = 'agent'
    try:
        if user._has_group('lugal_crm.group_lugal_crm_general_manager'):
            role = 'general_manager'
        elif user._has_group('lugal_crm.group_lugal_crm_manager'):
            role = 'manager'
        elif user._has_group('lugal_crm.group_lugal_crm_supervisor'):
            role = 'supervisor'
        elif user._has_group('lugal_crm.group_lugal_crm_qa_supervisor'):
            role = 'qa_supervisor'
        elif user._has_group('lugal_crm.group_lugal_crm_qa'):
            role = 'qa_auditor'
    except Exception:
        pass

    branches = request.env['lugal.crm.branch'].search(
        [('user_ids', 'in', user.id), ('is_deleted', '=', False)]
    )
    first_branch = branches[:1]

    email = user.partner_id.email or user.login or ''
    phone = user.partner_id.phone or ''
    mobile = user.partner_id.mobile or ''
    job_title = user.partner_id.function or ''

    return {
        # Core identity
        'id':          user.id,
        'name':        user.name or '',
        'login':       user.login or '',
        'email':       email,
        'phone':       phone,
        'mobile':      mobile,
        'job_title':   job_title,
        'lang':        user.lang or 'en_US',
        'tz':          user.tz or 'UTC',
        # Status
        'is_active':   user.active,
        'active':      user.active,         # backward compat alias
        # Role
        'role':        role,
        # Avatar — both field names for compatibility
        'avatar':      f'/web/image/res.users/{user.id}/avatar_128',
        'avatar_url':  f'/web/image/res.users/{user.id}/avatar_128',
        # Branch — both singular (CrmEmployee interface) and plural (legacy)
        'branch_id':   first_branch.id if first_branch else None,
        'branch_name': first_branch.name if first_branch else '',
        'branch_ids':  branches.ids,
        'branch_names': [b.name for b in branches],
    }


def _assign_crm_role(user, role):
    """Assign the appropriate CRM security group to a user (Odoo 19 compatible)."""
    for role_key, xmlid in _ROLE_GROUP_MAP.items():
        grp = request.env.ref(xmlid, raise_if_not_found=False)
        if not grp:
            continue
        if role_key == role:
            grp.sudo().write({'user_ids': [(4, user.id)]})
        else:
            grp.sudo().write({'user_ids': [(3, user.id)]})


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

    # ─── Employees (CRM system users with branch info) ────────────────────────

    @http.route('/api/crm/employees/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employees_list(self, branch_id=None, active=True, limit=100, offset=0, **kwargs):
        """
        List all active CRM employees (res.users with CRM group membership).

        Filters:
          branch_id — restrict to employees of a specific branch
          active    — default True; pass False to include deactivated accounts
          limit / offset — pagination
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Collect all users that belong to ANY CRM role group.
            # Querying only group_lugal_crm_agent misses supervisors, managers, etc.
            crm_group_xmlids = list(_ROLE_GROUP_MAP.values()) + [
                'lugal_crm.group_lugal_crm_general_manager',
                'lugal_crm.group_lugal_crm_qa',
                'lugal_crm.group_lugal_crm_qa_supervisor',
            ]
            seen_ids = set()
            user_list = request.env['res.users'].sudo().browse()  # empty recordset
            for xmlid in crm_group_xmlids:
                grp = request.env.ref(xmlid, raise_if_not_found=False)
                if grp:
                    for u in grp.sudo().user_ids:
                        if u.id not in seen_ids and u.active == active:
                            seen_ids.add(u.id)
                            user_list |= u

            # Sort by partner name ascending (same order as before)
            users = user_list.sorted(key=lambda u: (u.partner_id.name or u.login or '').lower())
            total = len(users)

            # Pagination
            off = int(offset)
            lim = int(limit)
            users = users[off: off + lim]

            # Optional branch filter
            if branch_id:
                branch = request.env['lugal.crm.branch'].browse(int(branch_id))
                if branch.exists():
                    users = users.filtered(lambda u: u in branch.user_ids)

            return {
                'success': True,
                'data': {
                    'items': [_build_employee_dict(u) for u in users],
                    'total': total,
                    'limit': int(limit),
                    'offset': int(offset),
                },
            }
        except Exception as e:
            return crm_error(e, 'employees_list')

    # ─── Single employee detail ───────────────────────────────────────────────

    @http.route('/api/crm/employees/<int:employee_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_detail(self, employee_id, **kwargs):
        """Get a single CRM employee by user ID."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(employee_id)
            if not user.exists() or not user.active:
                return {'success': False, 'error': 'Employee not found'}
            return {'success': True, 'data': _build_employee_dict(user)}
        except Exception as e:
            return crm_error(e, 'employee_detail')

    # ─── Create employee ──────────────────────────────────────────────────────

    @http.route('/api/crm/employees/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_create(self, name, email, password=None, role='agent', branch_id=None,
                        phone=None, job_title=None, lang='en_US', tz='UTC',
                        avatar_128=None, **kwargs):
        """
        Create a new CRM employee (Odoo res.users + assign to CRM group + branch).

        Required: name, email
        Optional: password, role (agent|supervisor), branch_id, phone, job_title, lang, tz
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not name or not email:
                return {'success': False, 'error': 'name and email are required'}

            # Check email uniqueness
            existing = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing:
                return {'success': False, 'error': f'A user with email {email} already exists'}

            # Build user vals — in Odoo 19 the internal user group is assigned via group_ids
            group_user = request.env.ref('base.group_user', raise_if_not_found=False)
            vals = {
                'name':   name,
                'login':  email,
                'email':  email,
                'lang':   lang or 'en_US',
                'tz':     tz   or 'UTC',
                'active': True,
            }
            if group_user:
                vals['group_ids'] = [(4, group_user.id)]
            if phone:
                vals['phone'] = phone
            if job_title:
                vals['function'] = job_title
            if password:
                vals['password'] = password

            new_user = request.env['res.users'].sudo().create(vals)

            # Save avatar if provided (base64 PNG/JPEG)
            if avatar_128:
                try:
                    new_user.sudo().write({'image_128': avatar_128})
                except Exception:
                    pass

            # Assign CRM role group
            _assign_crm_role(new_user, role)

            # Assign to branch
            if branch_id:
                branch = request.env['lugal.crm.branch'].browse(int(branch_id))
                if branch.exists():
                    branch.sudo().write({'user_ids': [(4, new_user.id)]})

            # Auto-create a default email account for the employee using
            # the company mail server defaults and the same password the admin
            # just entered — this is the only moment the plain-text password
            # is available; after create() it is stored hashed.
            if email:
                try:
                    request.env['lugal.email.account'].sudo().create({
                        'user_id':       new_user.id,
                        'name':          name,
                        'email_address': email,
                        'username':      email,
                        'password':      password or '',
                        'imap_host':     'mail.nooralnibras.com',
                        'imap_port':     993,
                        'imap_use_ssl':  True,
                        'smtp_host':     'mail.nooralnibras.com',
                        'smtp_port':     465,
                        'smtp_use_tls':  False,
                        'is_default':    True,
                        'is_active':     True,
                        'sync_status':   'never',
                    })
                except Exception:
                    _logger.warning(
                        'employee_create: failed to auto-create email account for uid=%s',
                        new_user.id, exc_info=True,
                    )

            return {'success': True, 'data': _build_employee_dict(new_user)}
        except Exception as e:
            return crm_error(e, 'employee_create')

    # ─── Update employee ──────────────────────────────────────────────────────

    @http.route('/api/crm/employees/<int:employee_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_update(self, employee_id, name=None, phone=None, job_title=None,
                        role=None, branch_id=None, lang=None, tz=None, avatar_128=None, **kwargs):
        """Update a CRM employee's profile fields."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}

            vals = {}
            if name:
                vals['name'] = name
            if phone is not None:
                vals['phone'] = phone
            if job_title is not None:
                vals['function'] = job_title
            if lang:
                vals['lang'] = lang
            if tz:
                vals['tz'] = tz
            if vals:
                user.write(vals)

            # Save avatar separately (image field)
            if avatar_128:
                try:
                    user.sudo().write({'image_128': avatar_128})
                except Exception:
                    pass

            if role:
                _assign_crm_role(user, role)

            if branch_id is not None:
                # Remove from all branches first, then assign new one
                all_branches = request.env['lugal.crm.branch'].sudo().search(
                    [('user_ids', 'in', user.id)]
                )
                for b in all_branches:
                    b.write({'user_ids': [(3, user.id)]})
                if branch_id:
                    branch = request.env['lugal.crm.branch'].browse(int(branch_id))
                    if branch.exists():
                        branch.write({'user_ids': [(4, user.id)]})

            return {'success': True, 'data': _build_employee_dict(user)}
        except Exception as e:
            return crm_error(e, 'employee_update')

    # ─── Activate / Deactivate / Delete ─────────────────────────────────────

    @http.route('/api/crm/employees/<int:employee_id>/deactivate', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_deactivate(self, employee_id, **kwargs):
        """Deactivate a CRM employee account (soft — keeps data, just disables login)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}
            user.write({'active': False})
            return {'success': True, 'data': {'id': employee_id, 'is_active': False}}
        except Exception as e:
            return crm_error(e, 'employee_deactivate')

    @http.route('/api/crm/employees/<int:employee_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_delete(self, employee_id, **kwargs):
        """
        Permanently delete a CRM employee (res.users record).

        Safety rules:
          - Cannot delete the currently authenticated user.
          - Cannot delete the admin user (id = 1 or id = 2).
          - The user is first deactivated, then unlinked — Odoo requires this order.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            if employee_id in (1, 2):
                return {'success': False, 'error': 'Cannot delete system administrator accounts'}

            if employee_id == uid:
                return {'success': False, 'error': 'Cannot delete your own account'}

            user = request.env['res.users'].sudo().with_context(active_test=False).browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}

            # Snapshot basic info for the response before deletion
            deleted_name = user.name
            deleted_id   = user.id

            # Odoo requires the user to be archived before unlink
            user.write({'active': False})
            user.unlink()

            return {
                'success': True,
                'data': {
                    'id':      deleted_id,
                    'name':    deleted_name,
                    'deleted': True,
                },
            }
        except Exception as e:
            return crm_error(e, 'employee_delete')

    @http.route('/api/crm/employees/<int:employee_id>/activate', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_activate(self, employee_id, **kwargs):
        """Reactivate a CRM employee account."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().with_context(active_test=False).browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}
            user.write({'active': True})
            return {'success': True, 'data': {'id': employee_id, 'is_active': True}}
        except Exception as e:
            return crm_error(e, 'employee_activate')

    # ─── KPI block ────────────────────────────────────────────────────────────

    @http.route('/api/crm/employees/<int:employee_id>/kpi', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_kpi(self, employee_id, days=30, **kwargs):
        """Return KPI summary for a CRM employee over the last N days."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}

            from datetime import datetime, timedelta
            since = datetime.utcnow() - timedelta(days=int(days))

            # Calls handled
            total_calls = 0
            answered_calls = 0
            try:
                Call = request.env['lugal.crm.call']
                total_calls = Call.search_count([
                    ('agent_id', '=', employee_id),
                    ('create_date', '>=', since.isoformat()),
                ])
                answered_calls = Call.search_count([
                    ('agent_id', '=', employee_id),
                    ('status', 'in', ['answered', 'completed']),
                    ('create_date', '>=', since.isoformat()),
                ])
            except Exception:
                pass

            # Messages sent
            total_messages = 0
            try:
                Msg = request.env['lugal.crm.omnichannel.message']
                total_messages = Msg.search_count([
                    ('author_id', '=', employee_id),
                    ('direction', '=', 'outbound'),
                    ('create_date', '>=', since.isoformat()),
                ])
            except Exception:
                pass

            return {
                'success': True,
                'data': {
                    'employee_id':   employee_id,
                    'days':          int(days),
                    'total_calls':   total_calls,
                    'answered_calls': answered_calls,
                    'total_messages': total_messages,
                    'avg_frt_seconds': None,
                },
            }
        except Exception as e:
            return crm_error(e, 'employee_kpi')

    # ─── Attendance ───────────────────────────────────────────────────────────

    @http.route('/api/crm/employees/<int:employee_id>/attendance', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_attendance(self, employee_id, days=30, page=1, per_page=30, **kwargs):
        """Return attendance records for a CRM employee."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(employee_id)
            if not user.exists():
                return {'success': False, 'error': 'Employee not found'}

            try:
                from datetime import datetime, timedelta
                since = datetime.utcnow() - timedelta(days=int(days))

                Att = request.env['hr.attendance']
                domain = [
                    ('employee_id.user_id', '=', employee_id),
                    ('check_in', '>=', since.isoformat()),
                ]
                total  = Att.search_count(domain)
                offset = (int(page) - 1) * int(per_page)
                recs   = Att.search(domain, limit=int(per_page), offset=offset, order='check_in desc')

                def _att(r):
                    duration = None
                    if r.check_in and r.check_out:
                        duration = round((r.check_out - r.check_in).total_seconds() / 3600, 2)
                    return {
                        'id':             r.id,
                        'date':           r.check_in.date().isoformat() if r.check_in else None,
                        'check_in':       r.check_in.isoformat() if r.check_in else None,
                        'check_out':      r.check_out.isoformat() if r.check_out else None,
                        'duration_hours': duration,
                        'status':         'present' if r.check_in else 'absent',
                    }
                return {
                    'success': True,
                    'data': {'items': [_att(r) for r in recs], 'total': total},
                }
            except Exception:
                return {
                    'success': True,
                    'data': {'items': [], 'total': 0},
                }
        except Exception as e:
            return crm_error(e, 'employee_attendance')
