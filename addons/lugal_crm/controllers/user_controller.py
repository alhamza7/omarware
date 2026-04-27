# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._permissions import (
    is_manager_or_above, is_supervisor_or_above, forbidden,
    AGENT, SUPERVISOR, MANAGER,
)
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _user_to_dict(user, include_branch=True):
    """Serialize a res.users record to a CRM-safe dict."""
    # Resolve CRM role from group membership (Odoo 19: use _has_group for sudo context)
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

    data = {
        'id': user.id,
        'name': user.name,
        'login': user.login,
        'email': user.partner_id.email or '',
        'phone': user.partner_id.phone or '',
        'mobile': user.partner_id.mobile or '',
        'lang': user.lang or 'en_US',
        'tz': user.tz or 'UTC',
        'active': user.active,
        'role': role,
        'avatar_url': f'/web/image/res.users/{user.id}/avatar_128',
    }

    if include_branch:
        branches = request.env['lugal.crm.branch'].search(
            [('user_ids', 'in', user.id), ('is_deleted', '=', False)]
        )
        data['branch_ids'] = branches.ids
        data['branch_names'] = [b.name for b in branches]

    return data


def _preferences_to_dict(user):
    """Serialize user notification/display preferences."""
    return {
        'id': user.id,
        'lang': user.lang or 'en_US',
        'tz': user.tz or 'UTC',
        'notify_email': user.notification_type or 'email',
        'signature': user.signature or '',
        'share': user.share,
    }


class UserController(http.Controller):

    # ─── List all CRM users ───────────────────────────────────────────────────

    @http.route('/api/crm/users/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_users(self, branch_id=None, role=None, active=True, limit=100, offset=0, **kwargs):
        """
        List CRM system users.

        Optional filters:
          branch_id — filter to users assigned to a specific branch
          role      — filter by CRM role: agent | supervisor | manager | general_manager | qa_auditor | qa_supervisor
          active    — default True; pass False to include deactivated accounts
          limit / offset — pagination
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Get CRM users via group.user_ids (Odoo 19: groups_id domain search is not allowed)
            crm_group = request.env.ref('lugal_crm.group_lugal_crm_agent', raise_if_not_found=False)
            if crm_group:
                base_users = crm_group.sudo().user_ids.filtered(lambda u: u.active == active)
            else:
                base_users = request.env['res.users'].sudo().search(
                    [('active', '=', active), ('share', '=', False)]
                )

            # Role filter via group membership
            role_group_map = {
                'agent':           'lugal_crm.group_lugal_crm_agent',
                'supervisor':      'lugal_crm.group_lugal_crm_supervisor',
                'manager':         'lugal_crm.group_lugal_crm_manager',
                'general_manager': 'lugal_crm.group_lugal_crm_general_manager',
                'qa_auditor':      'lugal_crm.group_lugal_crm_qa',
                'qa_supervisor':   'lugal_crm.group_lugal_crm_qa_supervisor',
            }
            if role and role in role_group_map:
                grp = request.env.ref(role_group_map[role], raise_if_not_found=False)
                if grp:
                    base_users = base_users.filtered(lambda u: u in grp.user_ids)

            total = len(base_users)
            # Pagination
            offset_val = int(offset)
            limit_val  = int(limit)
            users = base_users.sorted('name')[offset_val: offset_val + limit_val]
            if branch_id:
                branch = request.env['lugal.crm.branch'].browse(int(branch_id))
                if branch.exists():
                    users = users.filtered(lambda u: u in branch.user_ids)

            return {
                'success': True,
                'data': {
                    'items': [_user_to_dict(u) for u in users],
                    'total': total,
                    'limit': int(limit),
                    'offset': int(offset),
                },
            }
        except Exception as e:
            return crm_error(e, 'list_users')

    # ─── Current user ─────────────────────────────────────────────────────────

    @http.route('/api/crm/users/me', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def me(self, **kwargs):
        """Return the currently authenticated user's full profile."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return {'success': False, 'error': 'User not found'}
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'me')

    # ─── Preferences ──────────────────────────────────────────────────────────

    @http.route('/api/crm/users/me/preferences', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_preferences(self, **kwargs):
        """Return the current user's display and notification preferences."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return {'success': False, 'error': 'User not found'}
            return {'success': True, 'data': _preferences_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'get_preferences')

    @http.route('/api/crm/users/me/preferences/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_preferences(self, lang=None, tz=None, notify_email=None, signature=None, **kwargs):
        """Update the current user's preferences (lang, timezone, notifications)."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return {'success': False, 'error': 'User not found'}
            vals = {}
            if lang:
                vals['lang'] = lang
            if tz:
                vals['tz'] = tz
            if notify_email:
                vals['notification_type'] = notify_email
            if signature is not None:
                vals['signature'] = signature
            if vals:
                user.write(vals)
            return {'success': True, 'data': _preferences_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'update_preferences')

    # ─── Update own profile ───────────────────────────────────────────────────

    @http.route('/api/crm/users/me/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_me(self, name=None, phone=None, mobile=None, email=None,
                  lang=None, tz=None, signature=None, avatar_128=None, **kwargs):
        """
        Update the currently authenticated user's own profile.

        Accepted fields (all optional — only supplied fields are changed):
          name        — display name
          phone       — work phone
          mobile      — mobile number
          email       — email address
          lang        — language code  e.g. 'en_US', 'ar_001'
          tz          — timezone       e.g. 'Asia/Riyadh'
          signature   — email signature HTML
          avatar_128  — base64-encoded profile picture
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return {'success': False, 'error': 'User not found'}

            user_vals    = {}
            partner_vals = {}

            if name is not None:
                user_vals['name'] = name.strip()
            if lang is not None:
                user_vals['lang'] = lang
            if tz is not None:
                user_vals['tz'] = tz
            if signature is not None:
                user_vals['signature'] = signature
            if avatar_128 is not None:
                try:
                    import base64 as _b64
                    raw = avatar_128
                    # Strip data-URL prefix if present: "data:image/jpeg;base64,<data>"
                    if isinstance(raw, str) and ',' in raw:
                        raw = raw.split(',', 1)[1]
                    # Odoo image fields expect a plain base64 string (not bytes)
                    if isinstance(raw, bytes):
                        raw = raw.decode('ascii')
                    # Validate it is actually base64
                    _b64.b64decode(raw, validate=True)
                    # image_128 is the real stored field; avatar_128 is computed/read-only
                    user_vals['image_128'] = raw
                except Exception:
                    return {'success': False, 'error': 'Invalid avatar_128 — must be a base64 or data-URL encoded image'}

            if phone is not None:
                partner_vals['phone'] = phone
            if mobile is not None:
                partner_vals['mobile'] = mobile
            if email is not None:
                partner_vals['email'] = email.strip().lower()

            if user_vals:
                user.write(user_vals)
            if partner_vals:
                user.partner_id.write(partner_vals)

            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'update_me')

    # ─── Single user detail ───────────────────────────────────────────────────

    @http.route('/api/crm/users/<int:user_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_user(self, user_id, **kwargs):
        """Get a single CRM user by ID. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Requires Supervisor role or above')
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return {'success': False, 'error': 'User not found'}
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'get_user')
