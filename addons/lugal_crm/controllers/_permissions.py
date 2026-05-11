# -*- coding: utf-8 -*-
"""
Permission guard helpers for lugal_crm controllers.

Usage:
    from ._permissions import require_group, is_supervisor_or_above

    uid = ensure_jwt_user_id()
    if not uid:
        return {'success': False, 'error': 'Unauthorized'}

    if not require_group('lugal_crm.group_lugal_crm_supervisor'):
        return {'success': False, 'error': 'Forbidden — Supervisor role required'}

Group hierarchy (each level implies all levels below it):
    group_lugal_crm_agent           — Basic agent
    group_lugal_crm_supervisor      — Implies agent
    group_lugal_crm_manager         — Implies supervisor
    group_lugal_crm_general_manager — Implies manager
    group_lugal_crm_qa              — QA Auditor role (independent track)
    group_lugal_crm_qa_supervisor   — Implies group_lugal_crm_qa

Also:
    Odoo base group 'base.group_system' (Technical Admin) always has full access
    via require_group — has_group() returns True for admins regardless of explicit membership.
"""

import logging
from odoo.http import request

_logger = logging.getLogger(__name__)

# Convenience aliases — use these in controllers to avoid typos
AGENT           = 'lugal_crm.group_lugal_crm_agent'
SUPERVISOR      = 'lugal_crm.group_lugal_crm_supervisor'
MANAGER         = 'lugal_crm.group_lugal_crm_manager'
GENERAL_MANAGER = 'lugal_crm.group_lugal_crm_general_manager'
QA_AUDITOR      = 'lugal_crm.group_lugal_crm_qa'           # defined as group_lugal_crm_qa in groups.xml
QA_SUPERVISOR   = 'lugal_crm.group_lugal_crm_qa_supervisor'


def require_group(group_xml_id):
    """
    Return True if the current request user has *group_xml_id*.
    Must be called AFTER ensure_jwt_user_id() has bound the user to request.env.
    """
    try:
        return request.env.user.has_group(group_xml_id)
    except Exception as exc:
        _logger.error('_permissions.require_group error: %s', exc)
        return False


def is_agent_or_above():
    """True for Agent, Supervisor, Manager, General Manager."""
    return require_group(AGENT)


def is_supervisor_or_above():
    """True for Supervisor, Manager, General Manager."""
    return require_group(SUPERVISOR)


def is_manager_or_above():
    """True for Manager and General Manager only."""
    return require_group(MANAGER)


def is_general_manager():
    """True only for General Manager."""
    return require_group(GENERAL_MANAGER)


def is_qa_auditor_or_above():
    """True for QA Auditor and QA Supervisor."""
    return require_group(QA_AUDITOR)


def is_qa_supervisor():
    """True only for QA Supervisor."""
    return require_group(QA_SUPERVISOR)


def _is_system_admin():
    """Technical admins bypass fine-grained checks."""
    try:
        user = request.env.user
        return bool(
            user.id == 1
            or user.has_group('base.group_system')
        )
    except Exception:
        return False


def _lookup_permission(permissions, path):
    current = permissions or {}
    for part in (path or '').split('.'):
        if not isinstance(current, dict):
            return False
        current = current.get(part)
    return current is True


def has_permission(path):
    """
    Return True when the current request user has a resolved permission leaf.

    Must be called after ensure_jwt_user_id(), because that helper binds
    request.env to the authenticated user. Permission resolution is imported
    lazily to avoid a controller import cycle.
    """
    try:
        if _is_system_admin():
            return True
        from .admin_controller import _get_effective_permissions

        permissions = _get_effective_permissions(request.env.user.sudo())
        return _lookup_permission(permissions, path)
    except Exception as exc:
        _logger.error('_permissions.has_permission(%s) error: %s', path, exc, exc_info=True)
        return False


def has_any_permission(*paths):
    """Return True when the current user has at least one permission path."""
    return any(has_permission(path) for path in paths)


def require_permission(path, message=None):
    """Return None when allowed; otherwise return a standard forbidden payload."""
    if has_permission(path):
        return None
    return forbidden(
        message or f'Forbidden — permission required: {path}',
        error_code='PERMISSION_DENIED',
        permission=path,
    )


def forbidden(message='Insufficient permissions', **extra):
    """Shorthand for a standard Forbidden response dict."""
    payload = {'success': False, 'error': message, 'code': 403}
    payload.update(extra)
    return payload
