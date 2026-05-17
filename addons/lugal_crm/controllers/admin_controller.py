# -*- coding: utf-8 -*-
"""
CRM User & Permission Management API.

Permission resolution order (later steps win)
---------------------------------------------
  1. PERMISSION_TREE          — all actions False (empty baseline).
  2. CRM role baseline        — hardcoded defaults per role.
  3. CRM-role template        — admin-set overrides for the entire role group,
                                stored as job_title='__role__<role>' in the template table.
  4. Job-title template       — per-title overrides from lugal.crm.permission.template.
  5. User-specific overrides  — highest priority.

Schema
------
  current_view_crm_tree  — all FE-rendered routes.
  future_edits_crm_tree  — backend-only internal paths not yet in FE.
  Keys starting with '_' in PERMISSION_TREE are internal-only and stripped
  from all FE responses (permissions, routes, schema).

Rules
-----
- Only General Manager or Odoo system admin can call /api/crm/admin/* routes.
- Any authenticated user can call /api/crm/me/permissions.
- apply_to_all_same_crm_role=true  → upserts the role-level template (step 3)
  for the user's current CRM role. Does NOT touch individual overrides for others.
- Every permission response includes a `routes` map for navigation visibility.
  A route is visible when at least one action leaf in its subtree is True.

Endpoints
---------
  POST /api/crm/me/permissions
  POST /api/crm/admin/permissions/schema
  POST /api/crm/admin/permissions/job_titles/list
  POST /api/crm/admin/permissions/job_titles/upsert   { job_title, crm_role, permissions, apply_to_all_users, notes }
  POST /api/crm/admin/permissions/job_titles/delete   { job_title }
  POST /api/crm/admin/users/list
  POST /api/crm/admin/users/<id>/get
  POST /api/crm/admin/users/<id>/permissions/get
  POST /api/crm/admin/users/<id>/permissions/set      { permissions, apply_to_all_same_crm_role, notes }
  POST /api/crm/admin/users/<id>/permissions/reset
  POST /api/crm/admin/users/assign_role               { email, role }
  POST /api/crm/admin/users/bulk_assign               { assignments: [{email, role}] }
  POST /api/crm/admin/users/<id>/deactivate
  POST /api/crm/admin/users/<id>/activate
"""

import copy
import json
import logging

from odoo import fields, http
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)

# ─── Canonical Permission Tree ────────────────────────────────────────────────
# Single source of truth.  All leaves are False (denied) by default.
# Keys prefixed with '_' are backend-internal (not sent to the FE).
# Sections: supply_chain | crm | qa | pos | hr | inventory | finance | analytics | settings | admin

PERMISSION_TREE = {

    # ── Flat top-level FE routes ───────────────────────────────────────────────
    "dashboard":      {"view": False, "view_team_data": False, "export": False},
    "customers":      {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "import": False, "export": False, "merge": False},
    "products":       {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "set_price": False, "set_discount": False,
                       "import": False, "export": False},
    "orders":         {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "create_invoice": False, "refund": False,
                       "export_pdf": False, "view_delivery": False, "view_branches": False,
                       "view_samples": False},
    "omni_channel":   {"view": False, "reply": False, "assign": False},
    "tickets":        {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "assign": False, "escalate": False, "close": False},
    "tasks":          {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "assign": False, "close": False,
                       "view_projects": False, "manage_projects": False},
    "employees":      {"list": False, "view": False, "create": False, "edit": False,
                       "deactivate": False, "assign_role": False, "add_task": False,
                       "message": False},
    "sales_pipeline": {"view": False},
    "forecasting":    {"view": False, "export": False},

    # ── Supply Chain (nested) ─────────────────────────────────────────────────
    "supply_chain": {
        "containers": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "assign_driver": False, "unassign_driver": False, "mark_arrived": False,
            "clearance_delivered": False, "set_reminder": False,
            "upload_attachment": False, "delete_attachment": False,
            "add_comment": False, "delete_comment": False,
            "add_penalty": False, "delete_penalty": False,
        },
        "purchase_orders": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "confirm": False, "ship": False, "receive": False,
            "cancel": False, "reopen": False,
            "add_line": False, "edit_line": False, "delete_line": False,
            "upload_attachment": False, "delete_attachment": False,
            "add_comment": False, "delete_comment": False, "export_pdf": False,
        },
        "negotiations": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "add_comment": False, "delete_comment": False,
        },
        "item_requests": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "approve": False, "reject": False, "fulfill": False,
        },
        "vendors": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
        },
    },

    # ── Conversations (nested) ────────────────────────────────────────────────
    "conversations": {
        "chat": {
            "view": False, "send": False, "delete_message": False,
            "create_group": False,
            "add_member": False, "remove_member": False, "manage_group": False,
            "pin_message": False, "broadcast": False, "forward": False, "search": False,
        },
        "email": {
            "view": False, "send": False, "reply": False, "forward": False,
            "delete": False, "manage_rules": False,
        },
        "stories":   {"view": False, "create": False, "delete": False},
        "localsend": {"view": False, "send": False},
    },

    # ── More flat FE routes ───────────────────────────────────────────────────
    "promotions":     {"list": False, "create": False, "edit": False, "delete": False},
    "analytics":      {"view": False, "export": False, "view_team_data": False},
    "knowledge_base": {"list": False, "view": False, "create": False, "edit": False, "delete": False},
    "call_centre":    {"list": False, "view": False, "create": False, "edit": False,
                       "delete": False, "listen_recording": False},
    "event_log":      {"view": False, "export": False, "delete": False},
    "admin_dashboard":{"view": False, "manage_users": False, "manage_tasks": False},

    # ── Settings (nested) ─────────────────────────────────────────────────────
    "settings": {
        "general":      {"view": False, "edit": False},
        "permissions":  {"view": False, "set_user_overrides": False, "set_job_title_defaults": False},
        "templates":    {"view": False, "create": False, "edit": False, "delete": False},
        "rules":        {"view": False, "create": False, "edit": False, "delete": False},
        "channels":     {"view": False, "edit": False},
        "sla":          {"view": False, "edit": False},
        "shifts":       {"view": False, "manage": False},
        "omni_channels":{"view": False, "edit": False},
    },

    # ── Backend-only internal paths (stripped from all FE responses) ──────────
    "_internal": {
        "branches": {"list": False, "view": False, "create": False, "edit": False, "delete": False},
    },
}

# ─── FE schema helpers ────────────────────────────────────────────────────────

def _build_fe_schema() -> dict:
    """PERMISSION_TREE without internal-only keys (those starting with '_')."""
    return {k: copy.deepcopy(v) for k, v in PERMISSION_TREE.items() if not k.startswith('_')}

def _filter_to_fe_schema(perms: dict) -> dict:
    """Filter an effective-permissions dict to only FE-visible action keys."""
    def _pick(definition, src):
        if not isinstance(definition, dict):
            return bool(src)
        if any(isinstance(v, dict) for v in definition.values()):
            return {sub: _pick(sub_def, (src or {}).get(sub) or {})
                    for sub, sub_def in definition.items()}
        return {action: bool((src or {}).get(action, False)) for action in definition}

    return {
        section: _pick(definition, perms.get(section))
        for section, definition in PERMISSION_TREE.items()
        if not section.startswith('_')
    }


def _compute_route_visibility(perms: dict, route_overrides: dict = None) -> dict:
    """
    Flat map of route paths → bool for FE navigation visibility.

    Step 1 — compute from actions: a route is accessible when at least one
             action leaf in its subtree is True.
    Step 2 — apply explicit route_overrides (from the dedicated
             route_visibility_json column in lugal.crm.user.permission):
             False always hides the route, True always shows it.

    Both section-level ('supply_chain') and subsection-level
    ('supply_chain.containers') keys are included.
    Internal keys (starting with '_') are excluded from the output.
    """
    def _any_true(node) -> bool:
        if isinstance(node, bool):
            return bool(node)
        if isinstance(node, dict):
            return any(_any_true(v) for v in node.values())
        return False

    routes: dict = {}
    for section, value in perms.items():
        if section.startswith('_') or not isinstance(value, dict):
            continue
        if any(isinstance(v, dict) for v in value.values()):
            section_accessible = False
            for sub, sub_val in value.items():
                if not isinstance(sub_val, dict):
                    continue
                sub_ok = _any_true(sub_val)
                routes[f'{section}.{sub}'] = sub_ok
                if sub_ok:
                    section_accessible = True
            routes[section] = section_accessible
        else:
            routes[section] = _any_true(value)

    # Apply explicit admin-set route overrides (highest priority, separate DB field)
    for path, visible in (route_overrides or {}).items():
        routes[path] = bool(visible)

    return routes


def _set_all_leaves(node, value: bool) -> None:
    """Set every boolean leaf in a nested permission node."""
    if not isinstance(node, dict):
        return
    for key, child in node.items():
        if isinstance(child, dict):
            _set_all_leaves(child, value)
        elif isinstance(child, bool):
            node[key] = value


def _node_for_route(perms: dict, route_path: str):
    node = perms
    for part in (route_path or '').split('.'):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _apply_route_visibility_to_permissions(perms: dict, route_overrides: dict = None) -> dict:
    """
    Apply explicit route hides to the permission tree itself.

    route_visibility=false is not only a nav/sidebar concern. If an admin hides
    a route, all permission leaves under that route must be false in API
    responses and backend permission checks. route_visibility=true only affects
    nav visibility and does not grant actions.
    """
    result = copy.deepcopy(perms)
    for route_path, visible in (route_overrides or {}).items():
        if bool(visible):
            continue
        node = _node_for_route(result, route_path)
        _set_all_leaves(node, False)
    return result


def _all_route_paths() -> list:
    """Return every settable route path (section + subsection level)."""
    paths = []
    for section, value in PERMISSION_TREE.items():
        if section.startswith('_') or not isinstance(value, dict):
            continue
        paths.append(section)
        if any(isinstance(v, dict) for v in value.values()):
            for sub, sub_val in value.items():
                if isinstance(sub_val, dict):
                    paths.append(f'{section}.{sub}')
    return paths

# ─── Role-level baseline permissions ─────────────────────────────────────────
# Aligned to the new PERMISSION_TREE structure. Higher roles are supersets.

def _base_for_role(role: str) -> dict:
    """Return baseline permission overrides for a named CRM role."""
    bases = {
        'none': {},

        # ── Agent ─────────────────────────────────────────────────────────────
        'agent': {
            "dashboard":      {"view": True},
            "customers":      {"list": True, "view": True, "create": True, "edit": True},
            "omni_channel":   {"view": True, "reply": True},
            "tickets":        {"list": True, "view": True, "create": True, "edit": True},
            "tasks":          {"list": True, "view": True, "create": True, "edit": True},
            "employees":      {"list": True, "view": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True, "upload_attachment": True, "add_comment": True},
                "purchase_orders": {"list": True, "view": True, "create": True, "edit": True,
                                    "add_line": True, "edit_line": True, "upload_attachment": True, "add_comment": True},
                "negotiations":    {"list": True, "view": True, "add_comment": True},
                "item_requests":   {"list": True, "view": True, "create": True, "edit": True},
                "vendors":         {"list": True, "view": True},
            },
            "conversations": {
                "chat":      {"view": True, "send": True, "search": True},
                "stories":   {"view": True, "create": True},
                "localsend": {"view": True, "send": True},
            },
            "analytics":      {"view": True},
            "knowledge_base": {"list": True, "view": True, "create": True, "edit": True},
            "call_centre":    {"list": True, "view": True, "create": True, "edit": True},
            "settings": {
                "general": {"view": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True},
            },
        },

        # ── Supervisor ────────────────────────────────────────────────────────
        'supervisor': {
            "dashboard":      {"view": True, "view_team_data": True},
            "customers":      {"list": True, "view": True, "create": True, "edit": True},
            "omni_channel":   {"view": True, "reply": True, "assign": True},
            "tickets":        {"list": True, "view": True, "create": True, "edit": True, "assign": True, "escalate": True},
            "tasks":          {"list": True, "view": True, "create": True, "edit": True, "assign": True, "view_projects": True},
            "employees":      {"list": True, "view": True, "assign_role": True, "message": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True, "create": True, "edit": True,
                                    "assign_driver": True, "unassign_driver": True, "mark_arrived": True,
                                    "clearance_delivered": True, "set_reminder": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True},
                "purchase_orders": {"list": True, "view": True, "create": True, "edit": True,
                                    "confirm": True, "add_line": True, "edit_line": True, "delete_line": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":    {"list": True, "view": True, "create": True, "edit": True,
                                    "add_comment": True, "delete_comment": True},
                "item_requests":   {"list": True, "view": True, "create": True, "edit": True,
                                    "approve": True, "reject": True},
                "vendors":         {"list": True, "view": True},
            },
            "conversations": {
                "chat":      {"view": True, "send": True, "delete_message": True,
                              "add_member": True, "remove_member": True,
                              "pin_message": True, "search": True},
                "stories":   {"view": True, "create": True},
                "localsend": {"view": True, "send": True},
            },
            "analytics":      {"view": True, "view_team_data": True},
            "knowledge_base": {"list": True, "view": True, "create": True, "edit": True},
            "call_centre":    {"list": True, "view": True, "create": True, "edit": True},
            "settings": {
                "general":  {"view": True},
                "channels": {"view": True},
                "sla":      {"view": True},
                "shifts":   {"view": True, "manage": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True, "edit": True},
            },
        },

        # ── Manager ───────────────────────────────────────────────────────────
        'manager': {
            "dashboard":      {"view": True, "view_team_data": True, "export": True},
            "customers":      {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "import": True, "export": True, "merge": True},
            "products":       {"list": True, "view": True, "create": True, "edit": True,
                               "set_price": True, "set_discount": True},
            "orders":         {"list": True, "view": True, "create": True, "edit": True,
                               "export_pdf": True, "view_delivery": True, "view_branches": True, "view_samples": True},
            "omni_channel":   {"view": True, "reply": True, "assign": True},
            "tickets":        {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "assign": True, "escalate": True, "close": True},
            "tasks":          {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "assign": True, "close": True, "view_projects": True},
            "employees":      {"list": True, "view": True, "create": True, "edit": True,
                               "deactivate": True, "assign_role": True, "message": True},
            "sales_pipeline": {"view": True},
            "forecasting":    {"view": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True, "create": True, "edit": True,
                                    "assign_driver": True, "unassign_driver": True, "mark_arrived": True,
                                    "clearance_delivered": True, "set_reminder": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True,
                                    "add_penalty": True, "delete_penalty": True},
                "purchase_orders": {"list": True, "view": True, "create": True, "edit": True,
                                    "confirm": True, "ship": True, "receive": True, "cancel": True, "reopen": True,
                                    "add_line": True, "edit_line": True, "delete_line": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":    {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "add_comment": True, "delete_comment": True},
                "item_requests":   {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "approve": True, "reject": True, "fulfill": True},
                "vendors":         {"list": True, "view": True, "create": True, "edit": True},
            },
            "conversations": {
                "chat":      {"view": True, "send": True, "delete_message": True,
                              "create_group": True, "add_member": True, "remove_member": True, "manage_group": True, "pin_message": True,
                              "broadcast": True, "forward": True, "search": True},
                "email":     {"view": True, "send": True, "reply": True, "forward": True, "delete": True},
                "stories":   {"view": True, "create": True, "delete": True},
                "localsend": {"view": True, "send": True},
            },
            "promotions":     {"list": True, "create": True, "edit": True},
            "analytics":      {"view": True, "export": True, "view_team_data": True},
            "knowledge_base": {"list": True, "view": True, "create": True, "edit": True, "delete": True},
            "call_centre":    {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "listen_recording": True},
            "event_log":      {"view": True},
            "admin_dashboard":{"view": True},
            "settings": {
                "general":     {"view": True, "edit": True},
                "permissions": {"view": True},
                "templates":   {"view": True, "create": True, "edit": True},
                "rules":       {"view": True, "create": True, "edit": True},
                "channels":    {"view": True, "edit": True},
                "sla":         {"view": True, "edit": True},
                "shifts":      {"view": True, "manage": True},
                "omni_channels":{"view": True, "edit": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True, "create": True, "edit": True},
            },
        },

        # ── General Manager ───────────────────────────────────────────────────
        'general_manager': {
            "dashboard":      {"view": True, "view_team_data": True, "export": True},
            "customers":      {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "import": True, "export": True, "merge": True},
            "products":       {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "set_price": True, "set_discount": True,
                               "import": True, "export": True},
            "orders":         {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "create_invoice": True, "refund": True,
                               "export_pdf": True, "view_delivery": True, "view_branches": True,
                               "view_samples": True},
            "omni_channel":   {"view": True, "reply": True, "assign": True},
            "tickets":        {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "assign": True, "escalate": True, "close": True},
            "tasks":          {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "assign": True, "close": True,
                               "view_projects": True, "manage_projects": True},
            "employees":      {"list": True, "view": True, "create": True, "edit": True,
                               "deactivate": True, "assign_role": True, "add_task": True, "message": True},
            "sales_pipeline": {"view": True},
            "forecasting":    {"view": True, "export": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "assign_driver": True, "unassign_driver": True, "mark_arrived": True,
                                    "clearance_delivered": True, "set_reminder": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True,
                                    "add_penalty": True, "delete_penalty": True},
                "purchase_orders": {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "confirm": True, "ship": True, "receive": True, "cancel": True, "reopen": True,
                                    "add_line": True, "edit_line": True, "delete_line": True,
                                    "upload_attachment": True, "delete_attachment": True,
                                    "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":    {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "add_comment": True, "delete_comment": True},
                "item_requests":   {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                    "approve": True, "reject": True, "fulfill": True},
                "vendors":         {"list": True, "view": True, "create": True, "edit": True, "delete": True},
            },
            "conversations": {
                "chat":      {"view": True, "send": True, "delete_message": True,
                              "create_group": True, "add_member": True, "remove_member": True, "manage_group": True, "pin_message": True,
                              "broadcast": True, "forward": True, "search": True},
                "email":     {"view": True, "send": True, "reply": True, "forward": True,
                              "delete": True, "manage_rules": True},
                "stories":   {"view": True, "create": True, "delete": True},
                "localsend": {"view": True, "send": True},
            },
            "promotions":     {"list": True, "create": True, "edit": True, "delete": True},
            "analytics":      {"view": True, "export": True, "view_team_data": True},
            "knowledge_base": {"list": True, "view": True, "create": True, "edit": True, "delete": True},
            "call_centre":    {"list": True, "view": True, "create": True, "edit": True,
                               "delete": True, "listen_recording": True},
            "event_log":      {"view": True, "export": True, "delete": True},
            "admin_dashboard":{"view": True, "manage_users": True, "manage_tasks": True},
            "settings": {
                "general":      {"view": True, "edit": True},
                "permissions":  {"view": True, "set_user_overrides": True, "set_job_title_defaults": True},
                "templates":    {"view": True, "create": True, "edit": True, "delete": True},
                "rules":        {"view": True, "create": True, "edit": True, "delete": True},
                "channels":     {"view": True, "edit": True},
                "sla":          {"view": True, "edit": True},
                "shifts":       {"view": True, "manage": True},
                "omni_channels":{"view": True, "edit": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True, "create": True, "edit": True, "delete": True},
            },
        },

        # ── QA Auditor ────────────────────────────────────────────────────────
        'qa_auditor': {
            "dashboard":      {"view": True},
            "customers":      {"list": True, "view": True},
            "tickets":        {"list": True, "view": True},
            "tasks":          {"list": True, "view": True},
            "employees":      {"list": True, "view": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True},
                "purchase_orders": {"list": True, "view": True, "export_pdf": True},
                "negotiations":    {"list": True, "view": True},
                "item_requests":   {"list": True, "view": True},
                "vendors":         {"list": True, "view": True},
            },
            "conversations": {
                "chat":    {"view": True, "search": True},
                "stories": {"view": True},
            },
            "analytics":      {"view": True},
            "knowledge_base": {"list": True, "view": True},
            "call_centre":    {"list": True, "view": True, "listen_recording": True},
            "settings": {
                "general": {"view": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True},
            },
        },

        # ── QA Supervisor ─────────────────────────────────────────────────────
        'qa_supervisor': {
            "dashboard":      {"view": True, "view_team_data": True},
            "customers":      {"list": True, "view": True},
            "tickets":        {"list": True, "view": True},
            "tasks":          {"list": True, "view": True},
            "employees":      {"list": True, "view": True},
            "supply_chain": {
                "containers":      {"list": True, "view": True},
                "purchase_orders": {"list": True, "view": True, "export_pdf": True},
                "negotiations":    {"list": True, "view": True},
                "item_requests":   {"list": True, "view": True},
                "vendors":         {"list": True, "view": True},
            },
            "conversations": {
                "chat":    {"view": True, "search": True},
                "stories": {"view": True},
            },
            "analytics":      {"view": True, "export": True},
            "knowledge_base": {"list": True, "view": True},
            "call_centre":    {"list": True, "view": True, "listen_recording": True},
            "event_log":      {"view": True, "export": True},
            "settings": {
                "general": {"view": True},
                "shifts":  {"view": True},
            },
            "_internal": {
                "branches": {"list": True, "view": True},
            },
        },
    }
    return bases.get(role, {})


# ─── CRM role group XML IDs ───────────────────────────────────────────────────

_ALL_CRM_GROUPS = [
    'lugal_crm.group_lugal_crm_agent',
    'lugal_crm.group_lugal_crm_supervisor',
    'lugal_crm.group_lugal_crm_manager',
    'lugal_crm.group_lugal_crm_general_manager',
    'lugal_crm.group_lugal_crm_qa',
    'lugal_crm.group_lugal_crm_qa_supervisor',
]

_ROLE_GROUP = {
    'agent':           'lugal_crm.group_lugal_crm_agent',
    'supervisor':      'lugal_crm.group_lugal_crm_supervisor',
    'manager':         'lugal_crm.group_lugal_crm_manager',
    'general_manager': 'lugal_crm.group_lugal_crm_general_manager',
    'qa_auditor':      'lugal_crm.group_lugal_crm_qa',
    'qa_supervisor':   'lugal_crm.group_lugal_crm_qa_supervisor',
    'none':            None,
}


# ─── Helper utilities ─────────────────────────────────────────────────────────

def _notify_permissions_updated(user_ids, changed_by_uid: int):
    """
    Push a lightweight 'crm.permissions.updated' event to each affected user's
    personal bus channel (supply_user.<uid>) so their FE can immediately
    re-fetch /api/crm/me/permissions without waiting for a manual refresh.

    This reuses the same personal channel the supply chat already subscribes to,
    so no new WS subscription is needed on the FE side.

    Payload fields
    --------------
    type            : 'crm.permissions.updated'  (FE switches on this)
    changed_by_uid  : uid of the admin who made the change
    timestamp       : ISO-8601 UTC string
    """
    payload = {
        'type': 'crm.permissions.updated',
        'changed_by_uid': changed_by_uid,
        'timestamp': fields.Datetime.now().isoformat(),
    }
    for uid in (user_ids or []):
        try:
            request.env['bus.bus'].sudo()._sendone(
                f'supply_user.{uid}',
                'crm.permissions.updated',
                payload,
            )
            _logger.info('permissions push → supply_user.%s (by uid=%s)', uid, changed_by_uid)
        except Exception as exc:
            _logger.warning('_notify_permissions_updated bus error uid=%s: %s', uid, exc)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge `override` into a copy of `base`. Override wins."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _resolve_role(user) -> str:
    """Return the highest CRM role the user currently holds."""
    try:
        if user.has_group('lugal_crm.group_lugal_crm_general_manager'):
            return 'general_manager'
        if user.has_group('lugal_crm.group_lugal_crm_manager'):
            return 'manager'
        if user.has_group('lugal_crm.group_lugal_crm_supervisor'):
            return 'supervisor'
        if user.has_group('lugal_crm.group_lugal_crm_agent'):
            return 'agent'
        if user.has_group('lugal_crm.group_lugal_crm_qa_supervisor'):
            return 'qa_supervisor'
        if user.has_group('lugal_crm.group_lugal_crm_qa'):
            return 'qa_auditor'
    except Exception:
        pass
    return 'none'


def _is_admin() -> bool:
    try:
        u = request.env.user
        return (u.id == 1 or
                u.has_group('base.group_system') or
                u.has_group('lugal_crm.group_lugal_crm_general_manager'))
    except Exception:
        return False


def _find_user_by_email(email: str):
    email = (email or '').strip().lower()
    if not email:
        return None
    User = request.env['res.users'].sudo()
    u = User.search([('login', '=ilike', email), ('active', 'in', [True, False])], limit=1)
    if not u:
        partner = request.env['res.partner'].sudo().search([('email', '=ilike', email)], limit=1)
        if partner:
            u = User.search([('partner_id', '=', partner.id), ('active', 'in', [True, False])], limit=1)
    return u or None


def _get_effective_permissions(user) -> dict:
    """
    Compute the full permission dict for a user (including _internal paths).
    Resolution order: PERMISSION_TREE → role baseline → role template →
                      job-title template → user override.
    """
    base = copy.deepcopy(PERMISSION_TREE)
    role = _resolve_role(user)
    base = _deep_merge(base, _base_for_role(role))
    route_overrides = {}

    Tmpl = request.env['lugal.crm.permission.template'].sudo()

    # CRM-role template (admin-customised defaults for the whole role)
    role_tmpl = Tmpl.search([('job_title', '=', f'__role__{role}'), ('is_active', '=', True)], limit=1)
    if role_tmpl:
        rtp = role_tmpl.get_permissions()
        if rtp:
            base = _deep_merge(base, rtp)
        route_overrides.update(role_tmpl.get_route_visibility())

    # Job-title template
    job_title = user.sudo().partner_id.function or ''
    if job_title:
        tmpl = Tmpl.search([('job_title', '=ilike', job_title), ('is_active', '=', True)], limit=1)
        if tmpl:
            tmpl_perms = tmpl.get_permissions()
            if tmpl_perms:
                base = _deep_merge(base, tmpl_perms)
            if tmpl.crm_role and tmpl.crm_role != role:
                base = _deep_merge(base, _base_for_role(tmpl.crm_role))
                base = _deep_merge(base, tmpl_perms)
            route_overrides.update(tmpl.get_route_visibility())

    # User-specific overrides
    Override = request.env['lugal.crm.user.permission'].sudo()
    override_rec = Override.search([('user_id', '=', user.id)], limit=1)
    if override_rec:
        eff_title = override_rec.job_title_override or job_title
        if eff_title and eff_title != job_title:
            tmpl2 = Tmpl.search([('job_title', '=ilike', eff_title), ('is_active', '=', True)], limit=1)
            if tmpl2:
                base = _deep_merge(base, tmpl2.get_permissions())
                route_overrides.update(tmpl2.get_route_visibility())
        user_overrides = override_rec.get_overrides()
        if user_overrides:
            base = _deep_merge(base, user_overrides)
        route_overrides.update(override_rec.get_route_visibility())

    if route_overrides:
        base = _apply_route_visibility_to_permissions(base, route_overrides)

    return base


def _get_effective_route_visibility(user) -> dict:
    """Return route visibility overrides merged in the same priority order as permissions."""
    route_overrides = {}
    role = _resolve_role(user)
    Tmpl = request.env['lugal.crm.permission.template'].sudo()

    role_tmpl = Tmpl.search([('job_title', '=', f'__role__{role}'), ('is_active', '=', True)], limit=1)
    if role_tmpl:
        route_overrides.update(role_tmpl.get_route_visibility())

    job_title = user.sudo().partner_id.function or ''
    if job_title:
        tmpl = Tmpl.search([('job_title', '=ilike', job_title), ('is_active', '=', True)], limit=1)
        if tmpl:
            route_overrides.update(tmpl.get_route_visibility())

    Override = request.env['lugal.crm.user.permission'].sudo()
    override_rec = Override.search([('user_id', '=', user.id)], limit=1)
    if override_rec:
        eff_title = override_rec.job_title_override or job_title
        if eff_title and eff_title != job_title:
            tmpl2 = Tmpl.search([('job_title', '=ilike', eff_title), ('is_active', '=', True)], limit=1)
            if tmpl2:
                route_overrides.update(tmpl2.get_route_visibility())
        route_overrides.update(override_rec.get_route_visibility())

    return route_overrides


def _user_to_dict(user, include_permissions: bool = True) -> dict:
    role = _resolve_role(user)
    Override = request.env['lugal.crm.user.permission'].sudo()
    override_rec = Override.search([('user_id', '=', user.id)], limit=1)
    has_override = bool(override_rec and (
        override_rec.get_overrides() or override_rec.get_route_visibility()
    ))

    d = {
        'id': user.id,
        'name': user.name or '',
        'email': user.partner_id.email or user.login or '',
        'login': user.login or '',
        'job_title': user.sudo().partner_id.function or '',
        'active': bool(user.active),
        'role': role,
        'role_label': role.replace('_', ' ').title(),
        'has_individual_overrides': has_override,
        'override_notes': override_rec.admin_notes or '' if override_rec else '',
        'avatar_url': f'/web/image/res.users/{user.id}/avatar_128',
    }
    if include_permissions:
        full_perms = _get_effective_permissions(user)
        fe_perms   = _filter_to_fe_schema(full_perms)
        route_overrides = _get_effective_route_visibility(user)
        d['permissions']      = fe_perms
        d['routes']           = _compute_route_visibility(fe_perms, route_overrides)
        d['route_visibility'] = route_overrides   # echo back the explicit overrides set
    return d


# ─── Controller ───────────────────────────────────────────────────────────────

class CrmAdminController(http.Controller):

    # =========================================================================
    # Any logged-in user
    # =========================================================================

    @http.route('/api/crm/me/permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def crm_me_permissions(self, **kwargs):
        """
        Returns the current user's full effective permission map.
        Call this on app startup and cache in the FE store.

        Response → see schema in /api/crm/admin/permissions/schema
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            user = request.env['res.users'].sudo().browse(uid)
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'crm_me_permissions')

    # =========================================================================
    # Permission schema (admin)
    # =========================================================================

    @http.route('/api/crm/admin/permissions/schema', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_permissions_schema(self, **kwargs):
        """
        Returns the permission schema split into two parts:
          current_view_crm_tree  — all FE-rendered routes (use this for the admin UI form).
          future_edits_crm_tree  — backend-only internal paths not yet rendered by the FE.

        Response:
          {
            "success": true,
            "data": {
              "current_view_crm_tree": { ...FE schema all-false... },
              "future_edits_crm_tree": { ...internal paths all-false... },
              "roles": [...],
              "role_baselines": { "<role>": { current_view_crm_tree: {...}, future_edits_crm_tree: {...} } }
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden — Admin required', 'code': 403}
            fe_schema       = _build_fe_schema()
            internal_schema = copy.deepcopy(PERMISSION_TREE.get('_internal', {}))
            roles = list(_ROLE_GROUP.keys())
            role_baselines = {}
            for r in roles:
                full = _deep_merge(copy.deepcopy(PERMISSION_TREE), _base_for_role(r))
                role_baselines[r] = {
                    'current_view_crm_tree': _filter_to_fe_schema(full),
                    'future_edits_crm_tree': copy.deepcopy(full.get('_internal', {})),
                }
            return {
                'success': True,
                'data': {
                    'current_view_crm_tree': fe_schema,
                    'future_edits_crm_tree': internal_schema,
                    'roles':                 roles,
                    'role_baselines':        role_baselines,
                    # All paths the FE can pass in `route_visibility` to
                    # explicitly show/hide a nav section or sub-section
                    'settable_route_paths':  _all_route_paths(),
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_permissions_schema')

    # =========================================================================
    # Job-title templates
    # =========================================================================

    @http.route('/api/crm/admin/permissions/job_titles/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_job_titles_list(self, **kwargs):
        """
        List all job-title permission templates.

        Optional params:
          search (str)   — filter by job title name
          active (bool)  — default true
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            search = (kwargs.get('search') or '').strip()
            active = kwargs.get('active')
            if active is None:
                active = True
            Tmpl = request.env['lugal.crm.permission.template'].sudo()
            domain = [('is_active', '=', bool(active))]
            if search:
                domain.append(('job_title', 'ilike', search))
            records = Tmpl.search(domain, order='job_title asc')
            items = []
            for t in records:
                items.append({
                    'job_title':  t.job_title,
                    'label':      t.label or t.job_title,
                    'crm_role':   t.crm_role or 'none',
                    'notes':      t.notes or '',
                    'is_active':  t.is_active,
                    'user_count': t.user_count,
                    'permissions': t.get_permissions(),
                })
            return {'success': True, 'data': {'items': items, 'total': len(items)}}
        except Exception as e:
            return crm_error(e, 'admin_job_titles_list')

    @http.route('/api/crm/admin/permissions/job_titles/upsert', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_job_titles_upsert(self, **kwargs):
        """
        Create or update a job-title permission template.

        Params:
          job_title         (str,  required) — exact job title string, e.g. "Sales Agent"
          crm_role          (str,  optional) — "agent"|"supervisor"|"manager"|"general_manager"|"qa_auditor"|"qa_supervisor"|"none"
          permissions       (obj,  required) — full or partial permission tree (missing keys keep their current value)
          apply_to_all_users (bool, optional, default false)
                              — If true, clears all INDIVIDUAL overrides for every user that has
                                this job title, giving them a clean slate against the new template.
                                If false, individual overrides are kept (they still layer on top).
          label             (str,  optional) — friendly display name
          notes             (str,  optional)

        Response: the saved template record
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            job_title = (kwargs.get('job_title') or '').strip()
            if not job_title:
                return {'success': False, 'error': 'job_title is required'}

            new_perms   = kwargs.get('permissions') or {}
            crm_role    = (kwargs.get('crm_role') or 'none').strip()
            apply_all   = bool(kwargs.get('apply_to_all_users'))
            label       = (kwargs.get('label') or '').strip() or job_title
            notes       = (kwargs.get('notes') or '').strip()

            if crm_role not in _ROLE_GROUP:
                crm_role = 'none'

            Tmpl = request.env['lugal.crm.permission.template'].sudo()
            existing = Tmpl.search([('job_title', '=ilike', job_title)], limit=1)

            # Merge new_perms with current (if exists) or empty tree
            if existing:
                current = existing.get_permissions()
                merged = _deep_merge(current, new_perms)
            else:
                merged = _deep_merge(copy.deepcopy(PERMISSION_TREE), new_perms)

            vals = {
                'job_title':        job_title,
                'label':            label,
                'crm_role':         crm_role,
                'permissions_json': json.dumps(merged, ensure_ascii=False),
                'notes':            notes or False,
                'is_active':        True,
            }
            if existing:
                existing.write(vals)
                tmpl = existing
            else:
                tmpl = Tmpl.create(vals)

            # Optionally wipe individual overrides for all users with this job title
            if apply_all:
                partners = request.env['res.partner'].sudo().search([
                    ('function', '=ilike', job_title),
                ])
                users_with_title = request.env['res.users'].sudo().search([
                    ('partner_id', 'in', partners.ids),
                    ('active', '=', True),
                ])
                Override = request.env['lugal.crm.user.permission'].sudo()
                overrides = Override.search([('user_id', 'in', users_with_title.ids)])
                overrides.unlink()
                _logger.info(
                    'admin_job_titles_upsert: cleared %d individual overrides for job_title="%s"',
                    len(overrides), job_title,
                )

            return {
                'success': True,
                'data': {
                    'job_title':   tmpl.job_title,
                    'label':       tmpl.label,
                    'crm_role':    tmpl.crm_role,
                    'permissions': tmpl.get_permissions(),
                    'user_count':  tmpl.user_count,
                    'applied_to_all_users': apply_all,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_job_titles_upsert')

    @http.route('/api/crm/admin/permissions/job_titles/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_job_titles_delete(self, **kwargs):
        """
        Delete a job-title template (soft-deletes by setting is_active=False).

        Params:
          job_title (str, required)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            job_title = (kwargs.get('job_title') or '').strip()
            if not job_title:
                return {'success': False, 'error': 'job_title is required'}
            Tmpl = request.env['lugal.crm.permission.template'].sudo()
            tmpl = Tmpl.search([('job_title', '=ilike', job_title)], limit=1)
            if not tmpl:
                return {'success': False, 'error': 'Template not found'}
            tmpl.write({'is_active': False})
            return {'success': True, 'data': {'job_title': job_title, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'admin_job_titles_delete')

    # =========================================================================
    # User management
    # =========================================================================

    @http.route('/api/crm/admin/users/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_users_list(self, **kwargs):
        """
        List CRM users with their role, job title, override flag, and
        (optionally) full permission map.

        Params:
          role         (str)   — filter by crm role
          job_title    (str)   — filter by job title (partial match)
          search       (str)   — name / email search
          active       (bool)  — default true
          with_perms   (bool)  — include full permissions in response (default false — faster)
          page, per_page
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            page      = max(1, int(kwargs.get('page') or 1))
            per_page  = min(200, max(1, int(kwargs.get('per_page') or 50)))
            active    = kwargs.get('active')
            if active is None:
                active = True
            search      = (kwargs.get('search') or '').strip()
            role_filter = (kwargs.get('role') or '').strip()
            title_filter = (kwargs.get('job_title') or '').strip()
            with_perms  = bool(kwargs.get('with_perms'))

            crm_group_refs = [
                request.env.ref(gid, raise_if_not_found=False)
                for gid in _ALL_CRM_GROUPS
            ]
            crm_groups = [g for g in crm_group_refs if g]
            user_ids = set()
            for g in crm_groups:
                user_ids.update(g.sudo().user_ids.ids)

            domain = [('id', 'in', list(user_ids)), ('active', '=', bool(active)), ('share', '=', False)]
            if search:
                domain += ['|', ('name', 'ilike', search), ('login', 'ilike', search)]
            if title_filter:
                title_partners = request.env['res.partner'].sudo().search([('function', 'ilike', title_filter)])
                domain.append(('partner_id', 'in', title_partners.ids))

            all_users = request.env['res.users'].sudo().search(domain, order='name asc')
            if role_filter and role_filter in _ROLE_GROUP:
                all_users = all_users.filtered(lambda u: _resolve_role(u) == role_filter)

            total  = len(all_users)
            sliced = all_users[(page - 1) * per_page: page * per_page]
            return {
                'success': True,
                'data': {
                    'items':    [_user_to_dict(u, include_permissions=with_perms) for u in sliced],
                    'total':    total,
                    'page':     page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_users_list')

    @http.route('/api/crm/admin/users/<int:user_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_users_get(self, user_id, **kwargs):
        """Get single user detail (includes full permissions by default)."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'admin_users_get')

    @http.route('/api/crm/admin/users/<int:user_id>/permissions/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_user_permissions_get(self, user_id, **kwargs):
        """
        Get a user's full permission detail, including:
          - effective permissions (the merged result the FE sees)
          - role-level baseline
          - job-title template snapshot
          - individual overrides
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}

            role = _resolve_role(user)
            job_title = user.sudo().partner_id.function or ''

            # Job-title template
            Tmpl = request.env['lugal.crm.permission.template'].sudo()
            tmpl = Tmpl.search([('job_title', '=ilike', job_title), ('is_active', '=', True)], limit=1) if job_title else None

            # Individual overrides
            Override = request.env['lugal.crm.user.permission'].sudo()
            override_rec = Override.search([('user_id', '=', user_id)], limit=1)

            return {
                'success': True,
                'data': {
                    'user_id':   user.id,
                    'name':      user.name,
                    'email':     user.partner_id.email or user.login,
                    'job_title': job_title,
                    'role':      role,

                    # Layer 1 — role baseline
                    'role_baseline': _deep_merge(
                        copy.deepcopy(PERMISSION_TREE), _base_for_role(role)
                    ),

                    # Layer 2 — job-title template (None if no template for this title)
                    'job_title_template': {
                        'found':      bool(tmpl),
                        'crm_role':   tmpl.crm_role if tmpl else None,
                        'permissions': tmpl.get_permissions() if tmpl else None,
                    },

                    # Layer 3 — individual overrides
                    'individual_overrides': {
                        'found':              bool(override_rec),
                        'job_title_override': override_rec.job_title_override if override_rec else None,
                        'overrides':          override_rec.get_overrides() if override_rec else {},
                        'route_visibility':   override_rec.get_route_visibility() if override_rec else {},
                        'admin_notes':        override_rec.admin_notes if override_rec else '',
                        'last_modified_by':   override_rec.last_modified_by.name if override_rec and override_rec.last_modified_by else '',
                        'last_modified_at':   override_rec.last_modified_at.isoformat() if override_rec and override_rec.last_modified_at else None,
                    },

                    # Final merged result — what the user actually experiences
                    'effective_permissions': _get_effective_permissions(user),

                    # Flat route → bool visibility map (use this for FE navigation)
                    'routes': _compute_route_visibility(
                        _filter_to_fe_schema(_get_effective_permissions(user)),
                        _get_effective_route_visibility(user),
                    ),

                    # The explicit route overrides saved for this user (all sources merged)
                    'route_visibility': _get_effective_route_visibility(user),
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_user_permissions_get')

    @http.route('/api/crm/admin/users/<int:user_id>/permissions/set', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_user_permissions_set(self, user_id, **kwargs):
        """
        Set individual permission overrides for a specific user.

        The `permissions` object you send is deep-merged on top of the user's
        job-title baseline. Only the DELTA needs to be sent — you don't have
        to send the entire tree.

        Params:
          permissions (obj, required)
              — The override map. Can be partial. Example:
                {
                  "supply_chain": {
                    "containers": { "create": true, "delete": true },
                    "po":         { "confirm": true }
                  },
                  "crm": { "analytics": { "export": true } }
                }

          route_visibility (obj, optional)
              — Explicit route-level on/off map. Takes the highest priority
                over computed route visibility from action permissions.
                Keys are route paths (section or section.subsection).
                  { "supply_chain": false, "conversations.email": false }
                false = always hide this nav route regardless of actions.
                true  = always show this nav route regardless of actions.
                Omit a key to fall back to computed (any action True → visible).

          apply_to_all_same_crm_role (bool, optional, default false)
              — If TRUE: saves these overrides as the CRM-role template for the
                user's current role (step 3 in the resolution chain). Stored
                with the reserved key  job_title='__role__<role>'.
                Does NOT clear individual overrides for other users.
                This user's own individual override is cleared so they
                inherit the role template directly.

          job_title_override (str, optional)
              — Override baseline job-title lookup for this specific user.

          notes (str, optional) — reason for the override (stored for audit trail)

        Response: user dict with updated effective permissions + routes map.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}

            new_overrides       = kwargs.get('permissions') or {}
            route_vis_input     = kwargs.get('route_visibility')
            apply_to_all        = bool(kwargs.get('apply_to_all_same_crm_role'))
            job_title_override  = (kwargs.get('job_title_override') or '').strip() or None
            notes               = (kwargs.get('notes') or '').strip()

            if not isinstance(new_overrides, dict):
                return {'success': False, 'error': '`permissions` must be an object'}

            if route_vis_input is not None and not isinstance(route_vis_input, dict):
                return {'success': False, 'error': '`route_visibility` must be an object'}

            # Validate route_visibility paths
            validated_route_vis = None
            if route_vis_input is not None:
                valid_paths = set(_all_route_paths())
                bad = [k for k in route_vis_input if k not in valid_paths]
                if bad:
                    return {'success': False,
                            'error': f'Unknown route path(s) in route_visibility: {bad}'}
                validated_route_vis = {k: bool(v) for k, v in route_vis_input.items()}

            Override = request.env['lugal.crm.user.permission'].sudo()

            if apply_to_all:
                # Upsert the role-level template (reserved key __role__<role>)
                role = _resolve_role(user.sudo())
                tmpl_key = f'__role__{role}'
                Tmpl = request.env['lugal.crm.permission.template'].sudo()
                existing_tmpl = Tmpl.search([('job_title', '=', tmpl_key)], limit=1)
                if existing_tmpl:
                    current = existing_tmpl.get_permissions()
                    merged  = _deep_merge(current, new_overrides)
                    vals = {'permissions_json': json.dumps(merged, ensure_ascii=False)}
                    if validated_route_vis is not None:
                        current_routes = existing_tmpl.get_route_visibility()
                        vals['route_visibility_json'] = json.dumps(
                            {**current_routes, **validated_route_vis},
                            ensure_ascii=False,
                        )
                    existing_tmpl.write(vals)
                else:
                    merged = _deep_merge(copy.deepcopy(PERMISSION_TREE), new_overrides)
                    Tmpl.create({
                        'job_title':        tmpl_key,
                        'label':            f'Role default: {role}',
                        'crm_role':         role,
                        'permissions_json': json.dumps(merged, ensure_ascii=False),
                        'route_visibility_json': json.dumps(validated_route_vis or {}, ensure_ascii=False),
                        'is_active':        True,
                    })
                # Clear this user's individual override so they inherit the role template
                override_rec = Override.search([('user_id', '=', user_id)], limit=1)
                if override_rec:
                    override_rec.unlink()
                _logger.info(
                    'admin_user_permissions_set: upserted role template "%s" (uid=%d, by=%d)',
                    tmpl_key, user_id, uid,
                )
            else:
                # Store only for this individual user
                Override.upsert_for_user(
                    user_id=user_id,
                    overrides=new_overrides,
                    route_visibility=validated_route_vis,
                    job_title_override=job_title_override,
                    admin_notes=notes or None,
                    modifier_id=uid,
                )

            # Flush ORM cache so _user_to_dict reads the freshly written record
            request.env['lugal.crm.user.permission'].invalidate_model()
            request.env['lugal.crm.permission.template'].invalidate_model()
            user.invalidate_recordset()

            # Push real-time update so affected users' FE can re-fetch immediately
            if apply_to_all:
                # Find every active user with the same role and notify them all
                affected_role = _resolve_role(user.sudo())
                group_xml = _ROLE_GROUP.get(affected_role)
                if group_xml:
                    try:
                        grp = request.env.ref(group_xml, raise_if_not_found=False)
                        if grp:
                            affected_uids = list(grp.sudo().user_ids.ids)
                        else:
                            affected_uids = [user_id]
                    except Exception:
                        affected_uids = [user_id]
                else:
                    affected_uids = [user_id]
                _notify_permissions_updated(affected_uids, uid)
            else:
                _notify_permissions_updated([user_id], uid)

            return {
                'success': True,
                'data': {
                    **_user_to_dict(user),
                    'applied_to_all_same_crm_role': apply_to_all,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_user_permissions_set')

    @http.route('/api/crm/admin/users/<int:user_id>/permissions/reset', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_user_permissions_reset(self, user_id, **kwargs):
        """
        Remove ALL individual overrides for a user, returning them to pure
        job-title-template defaults.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            Override = request.env['lugal.crm.user.permission'].sudo()
            rec = Override.search([('user_id', '=', user_id)], limit=1)
            if rec:
                rec.unlink()
            _notify_permissions_updated([user_id], uid)
            return {'success': True, 'data': {**_user_to_dict(user), 'reset': True}}
        except Exception as e:
            return crm_error(e, 'admin_user_permissions_reset')

    # ─── Role (system group) assignment ──────────────────────────────────────

    @http.route('/api/crm/admin/users/assign_role', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_assign_role(self, **kwargs):
        """
        Assign a CRM system role (Odoo group) to a user identified by email.

        Params:
          email  (str, required)
          role   (str, required) — agent|supervisor|manager|general_manager|qa_auditor|qa_supervisor|none

        The role assignment governs the Odoo model-level access rights (record
        rules, menu visibility etc.).  The fine-grained action permissions shown
        in /api/crm/me/permissions are controlled separately via the
        permissions/set endpoint above.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            email = (kwargs.get('email') or '').strip()
            role  = (kwargs.get('role')  or '').strip().lower()

            if not email:
                return {'success': False, 'error': 'email is required'}
            if role not in _ROLE_GROUP:
                return {'success': False, 'error': f'Invalid role. Valid: {", ".join(sorted(_ROLE_GROUP.keys()))}'}

            user = _find_user_by_email(email)
            if not user:
                return {'success': False, 'error': f'No user found for "{email}"'}

            all_groups = {gid: request.env.ref(gid, raise_if_not_found=False) for gid in _ALL_CRM_GROUPS}
            remove = [(3, g.id) for g in all_groups.values() if g and g in user.sudo().group_ids]
            add    = []
            tgid   = _ROLE_GROUP[role]
            if tgid:
                tg = request.env.ref(tgid, raise_if_not_found=False)
                if tg:
                    add = [(4, tg.id)]
            user.sudo().write({'group_ids': remove + add})
            user.sudo().invalidate_recordset()
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'admin_assign_role')

    @http.route('/api/crm/admin/users/bulk_assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_bulk_assign(self, **kwargs):
        """
        Assign roles to multiple users in one call.

        Params:
          assignments (list) — [{ email, role }, ...]
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            assignments = kwargs.get('assignments') or []
            if not isinstance(assignments, list):
                return {'success': False, 'error': 'assignments must be a list'}
            results = []
            for item in assignments:
                email = (item.get('email') or '').strip()
                role  = (item.get('role')  or '').strip().lower()
                if not email or role not in _ROLE_GROUP:
                    results.append({'email': email, 'role': role, 'success': False, 'error': 'Invalid email or role'})
                    continue
                user = _find_user_by_email(email)
                if not user:
                    results.append({'email': email, 'role': role, 'success': False, 'error': f'User not found: {email}'})
                    continue
                try:
                    all_groups = {gid: request.env.ref(gid, raise_if_not_found=False) for gid in _ALL_CRM_GROUPS}
                    remove = [(3, g.id) for g in all_groups.values() if g and g in user.sudo().group_ids]
                    add = []
                    tgid = _ROLE_GROUP[role]
                    if tgid:
                        tg = request.env.ref(tgid, raise_if_not_found=False)
                        if tg:
                            add = [(4, tg.id)]
                    user.sudo().write({'group_ids': remove + add})
                    user.sudo().invalidate_recordset()
                    results.append({'email': email, 'role': role, 'success': True, 'user': _user_to_dict(user, include_permissions=False)})
                except Exception as ex:
                    results.append({'email': email, 'role': role, 'success': False, 'error': str(ex)})
            return {'success': True, 'data': {'results': results, 'updated_count': sum(1 for r in results if r['success'])}}
        except Exception as e:
            return crm_error(e, 'admin_bulk_assign')

    @http.route('/api/crm/admin/users/<int:user_id>/deactivate', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_deactivate_user(self, user_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            if user_id in (uid, 1):
                return {'success': False, 'error': 'Cannot deactivate this account'}
            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            user.sudo().write({'active': False})
            return {'success': True, 'data': {'id': user_id, 'active': False}}
        except Exception as e:
            return crm_error(e, 'admin_deactivate_user')

    @http.route('/api/crm/admin/users/<int:user_id>/activate', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_activate_user(self, user_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            user = request.env['res.users'].sudo().browse(user_id).with_context(active_test=False).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            user.sudo().write({'active': True})
            return {'success': True, 'data': _user_to_dict(user, include_permissions=False)}
        except Exception as e:
            return crm_error(e, 'admin_activate_user')

    # ─── Convenience: get any user's permissions (admin view) ─────────────────

    @http.route('/api/crm/users/<int:user_id>/permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_user_permissions_shortcut(self, user_id, **kwargs):
        """Alias of /api/crm/admin/users/<id>/permissions/get (admin only)."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}
            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            return {'success': True, 'data': _user_to_dict(user)}
        except Exception as e:
            return crm_error(e, 'admin_user_permissions_shortcut')

    # ─── Admin: Create user ────────────────────────────────────────────────────

    @http.route('/api/crm/admin/users/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_create_user(self, **kwargs):
        """
        Create a new Odoo user and optionally assign a CRM role.

        Params (all in jsonrpc params):
          name         str  required  Display name
          email        str  required  Login / email
          job_title    str  optional  Stored in partner.function
          role         str  optional  agent|supervisor|manager|general_manager|qa_auditor|qa_supervisor
          password     str  optional  Initial password (plain); if omitted Odoo sends reset link
          lang         str  optional  e.g. "ar_001" / "en_US"
          groups_ids   list optional  Extra Odoo group XML IDs to add
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            name = (params.get('name') or '').strip()
            email = (params.get('email') or '').strip().lower()
            job_title = (params.get('job_title') or '').strip()
            role = (params.get('role') or 'none').strip()
            password = (params.get('password') or '').strip()
            lang = (params.get('lang') or 'en_US').strip()

            if not name or not email:
                return {'success': False, 'error': 'name and email are required'}

            # check uniqueness
            existing = request.env['res.users'].sudo().search(
                [('login', '=ilike', email), ('active', 'in', [True, False])], limit=1)
            if existing:
                return {'success': False, 'error': f'A user with email {email} already exists'}

            vals = {
                'name': name,
                'login': email,
                'email': email,
                'lang': lang,
                'sel_groups_1_10_11': request.env.ref('base.group_user').id,
            }

            user = request.env['res.users'].sudo().create(vals)

            # set job title on partner
            if job_title:
                user.sudo().partner_id.write({'function': job_title})

            # assign CRM role
            if role and role != 'none' and role in _ROLE_GROUP:
                group_xml = _ROLE_GROUP[role]
                if group_xml:
                    group = request.env.ref(group_xml, raise_if_not_found=False)
                    if group:
                        group.sudo().write({'users': [(4, user.id)]})

            # set password
            if password:
                user.sudo().write({'password': password})

            _logger.info('Admin %s created user %s (role=%s)', uid, email, role)
            return {'success': True, 'data': _user_to_dict(user, include_permissions=False)}
        except Exception as e:
            return crm_error(e, 'admin_create_user')

    # ─── Admin: Update user profile ────────────────────────────────────────────

    @http.route('/api/crm/admin/users/<int:user_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_update_user(self, user_id, **kwargs):
        """
        Update basic profile fields for a user.

        Updatable fields:
          name       str  Display name
          email      str  Login / email  (changing this changes login)
          job_title  str  partner.function
          lang       str  "ar_001" / "en_US"
          active     bool True/False
          phone      str  Partner phone
          mobile     str  Partner mobile
          notes      str  Internal HR notes (partner.comment)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}

            params = kwargs.get('params') or kwargs
            user_vals = {}
            partner_vals = {}

            if 'name' in params:
                user_vals['name'] = (params['name'] or '').strip()
            if 'email' in params:
                new_email = (params['email'] or '').strip().lower()
                user_vals['login'] = new_email
                user_vals['email'] = new_email
                partner_vals['email'] = new_email
            if 'lang' in params:
                user_vals['lang'] = params['lang']
            if 'active' in params:
                user_vals['active'] = bool(params['active'])
            if 'job_title' in params:
                partner_vals['function'] = (params['job_title'] or '').strip()
            if 'phone' in params:
                partner_vals['phone'] = (params['phone'] or '').strip()
            if 'mobile' in params:
                partner_vals['mobile'] = (params['mobile'] or '').strip()
            if 'notes' in params:
                partner_vals['comment'] = (params['notes'] or '').strip()

            if user_vals:
                user.sudo().write(user_vals)
            if partner_vals:
                user.sudo().partner_id.write(partner_vals)

            _logger.info('Admin %s updated user %s fields: %s', uid, user_id, list({**user_vals, **partner_vals}.keys()))
            return {'success': True, 'data': _user_to_dict(user, include_permissions=False)}
        except Exception as e:
            return crm_error(e, 'admin_update_user')

    # ─── Admin: Change user password ───────────────────────────────────────────

    @http.route('/api/crm/admin/users/<int:user_id>/change_password', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_change_password(self, user_id, **kwargs):
        """
        Force-change a user's password (admin privilege).

        Params:
          new_password  str  required
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            new_password = (params.get('new_password') or '').strip()
            if not new_password or len(new_password) < 6:
                return {'success': False, 'error': 'new_password must be at least 6 characters'}

            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}

            user.sudo().write({'password': new_password})
            _logger.info('Admin %s changed password for user %s', uid, user_id)
            return {'success': True, 'message': f'Password changed for {user.name}'}
        except Exception as e:
            return crm_error(e, 'admin_change_password')

    # ─── Admin: Delete user ────────────────────────────────────────────────────

    @http.route('/api/crm/admin/users/<int:user_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_delete_user(self, user_id, **kwargs):
        """
        Permanently delete a user account.
        CAUTION: irreversible. Prefer /deactivate for soft removal.

        Params:
          confirm  bool  Must be true to proceed (safety check)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            if not params.get('confirm'):
                return {'success': False, 'error': 'Pass confirm=true to permanently delete this user'}

            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}
            if user.id == uid:
                return {'success': False, 'error': 'You cannot delete yourself'}
            if user.id == 1:
                return {'success': False, 'error': 'Cannot delete the root admin account'}

            name = user.name
            user.sudo().unlink()
            _logger.info('Admin %s permanently deleted user %s (id=%s)', uid, name, user_id)
            return {'success': True, 'message': f'User {name} permanently deleted'}
        except Exception as e:
            return crm_error(e, 'admin_delete_user')

    # ─── Admin: Get single job-title template ──────────────────────────────────

    @http.route('/api/crm/admin/permissions/job_titles/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_job_title_get(self, **kwargs):
        """
        Retrieve a single job-title permission template with full details.

        Params:
          job_title  str   required  Exact job title string to look up
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            job_title = (params.get('job_title') or '').strip()
            if not job_title:
                return {'success': False, 'error': 'job_title is required'}

            tmpl = request.env['lugal.crm.permission.template'].sudo().search(
                [('job_title', '=', job_title)], limit=1)
            if not tmpl:
                return {'success': False, 'error': f'No template found for job_title="{job_title}"'}

            try:
                perms = json.loads(tmpl.permissions_json or '{}')
            except Exception:
                perms = {}

            # Compute effective = merge(role_baseline, template)
            effective = _deep_merge(copy.deepcopy(PERMISSION_TREE), _base_for_role(tmpl.crm_role or 'none'))
            effective = _deep_merge(effective, perms)
            for k in effective:
                for sk in effective[k]:
                    if isinstance(effective[k][sk], dict):
                        for ak in list(effective[k][sk]):
                            if ak not in PERMISSION_TREE.get(k, {}).get(sk, {}):
                                del effective[k][sk][ak]

            return {
                'success': True,
                'data': {
                    'id': tmpl.id,
                    'job_title': tmpl.job_title,
                    'label': tmpl.label or tmpl.job_title,
                    'crm_role': tmpl.crm_role or 'none',
                    'is_active': tmpl.is_active,
                    'notes': tmpl.notes or '',
                    'permissions': perms,
                    'effective_permissions': effective,
                    'user_count': tmpl.user_count,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_job_title_get')

    # ─── Admin: Bulk apply template to users ──────────────────────────────────

    @http.route('/api/crm/admin/users/bulk_permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_bulk_permissions(self, **kwargs):
        """
        Apply the same permission overrides to multiple users at once.

        Params:
          user_ids    list[int]   required  List of user IDs to update
          permissions dict        required  Permission delta to apply (same structure as /set)
          mode        str         optional  "merge" (default) | "replace" | "reset"
                                            merge:   deep-merge on top of existing overrides
                                            replace: wipe existing overrides and set new ones
                                            reset:   remove all individual overrides (permissions ignored)
          notes       str         optional  Audit note
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            user_ids = params.get('user_ids') or []
            permissions = params.get('permissions') or {}
            mode = (params.get('mode') or 'merge').strip()
            notes = (params.get('notes') or '').strip()

            if not user_ids or not isinstance(user_ids, list):
                return {'success': False, 'error': 'user_ids must be a non-empty list'}
            if mode not in ('merge', 'replace', 'reset'):
                return {'success': False, 'error': 'mode must be merge | replace | reset'}

            UserPerm = request.env['lugal.crm.user.permission'].sudo()
            users = request.env['res.users'].sudo().browse(user_ids).exists()
            results = []

            for user in users:
                try:
                    if mode == 'reset':
                        rec = UserPerm.search([('user_id', '=', user.id)], limit=1)
                        if rec:
                            rec.unlink()
                        results.append({'user_id': user.id, 'status': 'reset'})
                    elif mode == 'replace':
                        UserPerm.upsert_for_user(user.id, permissions,
                                                  notes=notes, modifier_id=uid)
                        results.append({'user_id': user.id, 'status': 'replaced'})
                    else:  # merge
                        existing_rec = UserPerm.search([('user_id', '=', user.id)], limit=1)
                        existing = {}
                        if existing_rec:
                            try:
                                existing = json.loads(existing_rec.permissions_json or '{}')
                            except Exception:
                                existing = {}
                        merged = _deep_merge(existing, permissions)
                        UserPerm.upsert_for_user(user.id, merged,
                                                  notes=notes, modifier_id=uid)
                        results.append({'user_id': user.id, 'status': 'merged'})
                except Exception as ex:
                    results.append({'user_id': user.id, 'status': 'error', 'error': str(ex)})

            _logger.info('Admin %s bulk_permissions mode=%s on %d users', uid, mode, len(user_ids))
            return {
                'success': True,
                'data': {
                    'total': len(user_ids),
                    'processed': len(results),
                    'results': results,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_bulk_permissions')

    # ─── Admin: Audit log ─────────────────────────────────────────────────────

    @http.route('/api/crm/admin/audit/permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_audit_log(self, **kwargs):
        """
        Return a chronological log of all permission changes tracked by Odoo
        chatter on lugal.crm.user.permission records.

        Params:
          user_id     int    optional  Filter by specific user ID
          limit       int    optional  Default 50, max 200
          offset      int    optional  Pagination offset
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            filter_user_id = params.get('user_id')
            limit = min(int(params.get('limit') or 50), 200)
            offset = int(params.get('offset') or 0)

            UserPerm = request.env['lugal.crm.user.permission'].sudo()

            domain = []
            if filter_user_id:
                domain.append(('user_id', '=', int(filter_user_id)))

            records = UserPerm.search(domain, order='write_date desc', limit=limit, offset=offset)
            total = UserPerm.search_count(domain)

            log = []
            for rec in records:
                try:
                    perms = json.loads(rec.permissions_json or '{}')
                except Exception:
                    perms = {}

                modifier = None
                if rec.last_modified_by:
                    mod_user = request.env['res.users'].sudo().browse(rec.last_modified_by).exists()
                    if mod_user:
                        modifier = {'id': mod_user.id, 'name': mod_user.name, 'email': mod_user.login}

                log.append({
                    'id': rec.id,
                    'user': {
                        'id': rec.user_id.id,
                        'name': rec.user_id.name,
                        'email': rec.user_id.login,
                        'job_title': rec.user_id.partner_id.function or '',
                    },
                    'job_title_override': rec.job_title_override or '',
                    'permissions_delta': perms,
                    'notes': rec.admin_notes or '',
                    'modified_by': modifier,
                    'modified_at': rec.last_modified_at.isoformat() if rec.last_modified_at else None,
                    'last_write': fields.Datetime.to_string(rec.write_date),
                })

            return {
                'success': True,
                'data': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'log': log,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_audit_log')

    # ─── Admin: Dashboard statistics ─────────────────────────────────────────

    @http.route('/api/crm/admin/stats', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_stats(self, **kwargs):
        """
        Return high-level user/permission statistics for the admin dashboard.
        No params required.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            User = request.env['res.users'].sudo()
            UserPerm = request.env['lugal.crm.user.permission'].sudo()
            Template = request.env['lugal.crm.permission.template'].sudo()

            # Active internal users only
            all_users = User.search([
                ('share', '=', False),
                ('active', '=', True),
                ('id', '!=', 1),
            ])
            inactive_users = User.search([
                ('share', '=', False),
                ('active', '=', False),
                ('id', '!=', 1),
            ])

            # Role distribution
            role_counts = {}
            for role_key in _ROLE_GROUP:
                if role_key == 'none':
                    continue
                g_xml = _ROLE_GROUP[role_key]
                if not g_xml:
                    continue
                try:
                    g = request.env.ref(g_xml, raise_if_not_found=False)
                    role_counts[role_key] = len(g.user_ids) if g else 0
                except Exception:
                    role_counts[role_key] = 0

            # users with individual overrides
            users_with_overrides = UserPerm.search_count([])

            # Job-title templates
            active_templates = Template.search_count([('is_active', '=', True)])
            total_templates = Template.search_count([])

            # users without any CRM role
            users_no_role = []
            for u in all_users:
                role = _resolve_role(u)
                if role == 'none':
                    users_no_role.append({'id': u.id, 'name': u.name, 'email': u.login})

            return {
                'success': True,
                'data': {
                    'users': {
                        'total_active': len(all_users),
                        'total_inactive': len(inactive_users),
                        'with_individual_overrides': users_with_overrides,
                        'without_crm_role': len(users_no_role),
                        'no_role_list': users_no_role[:20],
                    },
                    'roles': role_counts,
                    'templates': {
                        'active': active_templates,
                        'total': total_templates,
                    },
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_stats')

    # ─── Admin: Export permissions as JSON ───────────────────────────────────

    @http.route('/api/crm/admin/export/permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_export_permissions(self, **kwargs):
        """
        Export all users' effective permissions as a JSON snapshot.
        Useful for FE to bulk-cache or for backup/audit purposes.

        Params:
          format   str  optional  "full" (default) | "delta_only"
                                  full:        complete resolved permission map per user
                                  delta_only:  only individual overrides (lighter payload)
          role     str  optional  Filter by CRM role
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            fmt = (params.get('format') or 'full').strip()
            role_filter = (params.get('role') or '').strip()

            User = request.env['res.users'].sudo()
            domain = [('share', '=', False), ('active', '=', True), ('id', '!=', 1)]
            all_users = User.search(domain)

            result = []
            for user in all_users:
                role = _resolve_role(user)
                if role_filter and role != role_filter:
                    continue

                entry = {
                    'id': user.id,
                    'name': user.name,
                    'email': user.login,
                    'job_title': user.partner_id.function or '',
                    'role': role,
                }

                if fmt == 'delta_only':
                    rec = request.env['lugal.crm.user.permission'].sudo().search(
                        [('user_id', '=', user.id)], limit=1)
                    entry['individual_overrides'] = json.loads(rec.permissions_json or '{}') if rec else {}
                else:
                    entry['effective_permissions'] = _get_effective_permissions(user)

                result.append(entry)

            return {
                'success': True,
                'data': {
                    'exported_at': fields.Datetime.to_string(fields.Datetime.now()),
                    'format': fmt,
                    'total_users': len(result),
                    'users': result,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_export_permissions')

    # ─── Admin: Import / restore permissions ─────────────────────────────────

    @http.route('/api/crm/admin/import/permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_import_permissions(self, **kwargs):
        """
        Restore individual permission overrides from a previously exported snapshot.

        Params:
          users      list  required  Same format as export response users[]
                           Each item: { email, individual_overrides, job_title_override (opt) }
          dry_run    bool  optional  If true, simulate and return what would change (no write)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            users_data = params.get('users') or []
            dry_run = bool(params.get('dry_run', False))

            if not users_data:
                return {'success': False, 'error': 'users list is required'}

            UserPerm = request.env['lugal.crm.user.permission'].sudo()
            results = []

            for item in users_data:
                email = (item.get('email') or '').strip().lower()
                overrides = item.get('individual_overrides') or {}
                job_title_override = (item.get('job_title_override') or '').strip()

                user = _find_user_by_email(email)
                if not user:
                    results.append({'email': email, 'status': 'not_found'})
                    continue

                if dry_run:
                    results.append({
                        'email': email,
                        'user_id': user.id,
                        'name': user.name,
                        'status': 'would_update',
                        'overrides': overrides,
                    })
                    continue

                UserPerm.upsert_for_user(
                    user.id, overrides,
                    job_title_override=job_title_override or None,
                    notes=f'Imported by admin {uid}',
                    modifier_id=uid,
                )
                results.append({'email': email, 'user_id': user.id, 'status': 'updated'})

            return {
                'success': True,
                'data': {
                    'dry_run': dry_run,
                    'total': len(users_data),
                    'results': results,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_import_permissions')

    # ─── Admin: Remove a user's CRM role ─────────────────────────────────────

    @http.route('/api/crm/admin/users/<int:user_id>/remove_role', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_remove_role(self, user_id, **kwargs):
        """
        Remove all CRM roles from a user (sets them to 'none').
        Their individual overrides are preserved.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            user = request.env['res.users'].sudo().browse(user_id).exists()
            if not user:
                return {'success': False, 'error': 'User not found'}

            for g_xml in _ALL_CRM_GROUPS:
                try:
                    g = request.env.ref(g_xml, raise_if_not_found=False)
                    if g and user in g.user_ids:
                        g.sudo().write({'user_ids': [(3, user.id)]})
                except Exception:
                    pass

            _logger.info('Admin %s removed all CRM roles from user %s', uid, user_id)
            return {'success': True, 'data': _user_to_dict(user, include_permissions=False)}
        except Exception as e:
            return crm_error(e, 'admin_remove_role')

    # ─── Admin: Compare two users' permissions ────────────────────────────────

    @http.route('/api/crm/admin/users/compare_permissions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_compare_permissions(self, **kwargs):
        """
        Compare the effective permissions of two users side-by-side.
        Returns a diff showing which keys differ.

        Params:
          user_id_a  int  required
          user_id_b  int  required
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            id_a = int(params.get('user_id_a') or 0)
            id_b = int(params.get('user_id_b') or 0)
            if not id_a or not id_b:
                return {'success': False, 'error': 'user_id_a and user_id_b are required'}

            user_a = request.env['res.users'].sudo().browse(id_a).exists()
            user_b = request.env['res.users'].sudo().browse(id_b).exists()
            if not user_a or not user_b:
                return {'success': False, 'error': 'One or both users not found'}

            perms_a = _get_effective_permissions(user_a)
            perms_b = _get_effective_permissions(user_b)

            # Build diff: only keys where values differ
            diff = {}
            for mod, sections in PERMISSION_TREE.items():
                for section, actions in sections.items():
                    for action in actions:
                        val_a = perms_a.get(mod, {}).get(section, {}).get(action, False)
                        val_b = perms_b.get(mod, {}).get(section, {}).get(action, False)
                        if val_a != val_b:
                            diff.setdefault(mod, {}).setdefault(section, {})[action] = {
                                'user_a': val_a,
                                'user_b': val_b,
                            }

            return {
                'success': True,
                'data': {
                    'user_a': {'id': user_a.id, 'name': user_a.name, 'role': _resolve_role(user_a)},
                    'user_b': {'id': user_b.id, 'name': user_b.name, 'role': _resolve_role(user_b)},
                    'total_differences': sum(
                        len(s) for m in diff.values() for s in m.values()
                    ),
                    'diff': diff,
                    'permissions_a': perms_a,
                    'permissions_b': perms_b,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_compare_permissions')

    # ── Admin: Email Account Management ──────────────────────────────────────
    # Admins can view, update credentials, and test email accounts for any user.
    # This is needed when a user's IMAP password changes on the mail server and
    # they can't sync — the admin can update the password on their behalf.

    @http.route('/api/crm/admin/email/accounts', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_email_accounts_list(self, **kwargs):
        """
        List all email accounts across all users with their sync status.
        Admin use: identify accounts that need attention (auth failures, never synced).

        Returns:
          accounts: [{id, user_id, user_login, name, email, sync_status,
                      password_set, last_sync_date, sync_error, needs_setup}]
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            params = kwargs.get('params') or kwargs
            status_filter = params.get('sync_status')  # optional: 'error'|'never'|'ok'

            domain = [('is_deleted', '=', False)]
            if status_filter:
                domain.append(('sync_status', '=', status_filter))

            accounts = request.env['lugal.email.account'].sudo().search(domain, order='id')
            result = []
            for acc in accounts:
                has_pw = bool((acc.password or '').strip())
                err = acc.sync_error_msg or ''
                is_auth_fail = 'AUTHENTICATIONFAILED' in err.upper() or 'INVALID CREDENTIALS' in err.upper()
                needs_setup = not has_pw or is_auth_fail
                result.append({
                    'id':             acc.id,
                    'user_id':        acc.user_id.id,
                    'user_login':     acc.user_id.login,
                    'user_name':      acc.user_id.name,
                    'name':           acc.name,
                    'email':          acc.email_address,
                    'imap_host':      acc.imap_host,
                    'imap_port':      acc.imap_port,
                    'username':       acc.username or acc.email_address,
                    'password_set':   has_pw,
                    'sync_status':    acc.sync_status or 'never',
                    'last_sync_date': str(acc.last_sync_date) if acc.last_sync_date else None,
                    'sync_error':     err or None,
                    'needs_setup':    needs_setup,
                    'setup_reason':   'invalid_credentials' if is_auth_fail else ('no_password' if not has_pw else None),
                })
            return {
                'success': True,
                'data': {
                    'total':           len(result),
                    'needs_attention': sum(1 for a in result if a['needs_setup']),
                    'accounts':        result,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_email_accounts_list')

    @http.route('/api/crm/admin/email/accounts/<int:account_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_email_account_update(self, account_id, **kwargs):
        """
        Update email account credentials for any user (admin only).
        Use this when a user's IMAP/SMTP password changes on the mail server.

        Params (all optional):
          password      str   New IMAP/SMTP app password
          username      str   IMAP username (defaults to email address)
          imap_host     str   IMAP host
          imap_port     int   IMAP port
          imap_use_ssl  bool
          smtp_host     str
          smtp_port     int
          smtp_use_tls  bool

        Returns: updated account info + test result
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.is_deleted:
                return {'success': False, 'error': 'Email account not found'}

            params = kwargs.get('params') or kwargs
            allowed = {
                'password', 'username',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls',
            }
            vals = {k: v for k, v in params.items() if k in allowed and v is not None}
            if not vals:
                return {'success': False, 'error': 'No fields to update provided'}

            acc.write(vals)
            request.env.cr.commit()

            # Auto-test connection after updating credentials
            test_result = None
            if 'password' in vals:
                try:
                    test_result = acc.action_test_connection()
                    request.env.cr.commit()
                except Exception as te:
                    test_result = {'status': 'error', 'message': str(te)}

            has_pw = bool((acc.password or '').strip())
            err = acc.sync_error_msg or ''
            is_auth_fail = 'AUTHENTICATIONFAILED' in err.upper() or 'INVALID CREDENTIALS' in err.upper()
            return {
                'success': True,
                'data': {
                    'id':           acc.id,
                    'email':        acc.email_address,
                    'user_login':   acc.user_id.login,
                    'password_set': has_pw,
                    'sync_status':  acc.sync_status or 'never',
                    'needs_setup':  not has_pw or is_auth_fail,
                    'test_result':  test_result,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_email_account_update')

    @http.route('/api/crm/admin/email/accounts/<int:account_id>/sync',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def admin_email_account_sync(self, account_id, **kwargs):
        """
        Force IMAP sync for any user's email account (admin only).
        Returns: sync result with imported count and updated status.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden', 'code': 403}

            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.is_deleted:
                return {'success': False, 'error': 'Email account not found'}

            if not (acc.password or '').strip():
                return {'success': False, 'error': 'No app password configured on this account — use the update endpoint first'}

            result = acc.action_sync()
            request.env.cr.commit()

            unread = request.env['lugal.email.message'].sudo().search_count([
                ('account_id', '=', acc.id),
                ('folder', '=', 'inbox'),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])
            return {
                'success': True,
                'data': {
                    'id':          acc.id,
                    'email':       acc.email_address,
                    'user_login':  acc.user_id.login,
                    'sync_ok':     (result or {}).get('sync_status') == 'ok',
                    'imported':    (result or {}).get('imported', 0),
                    'unread':      unread,
                    'sync_status': acc.sync_status or 'never',
                    'sync_error':  acc.sync_error_msg or None,
                },
            }
        except Exception as e:
            return crm_error(e, 'admin_email_account_sync')
