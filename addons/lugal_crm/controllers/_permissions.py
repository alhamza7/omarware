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
    group_lugal_crm_qa_auditor      — QA role (independent)
    group_lugal_crm_qa_supervisor   — Implies qa_auditor
"""

import logging
from odoo.http import request

_logger = logging.getLogger(__name__)

# Convenience aliases — use these in controllers to avoid typos
AGENT           = 'lugal_crm.group_lugal_crm_agent'
SUPERVISOR      = 'lugal_crm.group_lugal_crm_supervisor'
MANAGER         = 'lugal_crm.group_lugal_crm_manager'
GENERAL_MANAGER = 'lugal_crm.group_lugal_crm_general_manager'
QA_AUDITOR      = 'lugal_crm.group_lugal_crm_qa_auditor'
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


def forbidden(message='Insufficient permissions'):
    """Shorthand for a standard Forbidden response dict."""
    return {'success': False, 'error': message, 'code': 403}
