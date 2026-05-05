# -*- coding: utf-8 -*-
"""
CRM User & Permission Management API.

Architecture
------------
Effective permissions for any user are computed as:

  1. Start with the full empty permission tree (all actions = false).
  2. Apply the JOB-TITLE TEMPLATE that matches user.job_title  →  baseline.
  3. Deep-merge the USER-SPECIFIC OVERRIDES on top              →  final.

Rules
-----
- Only General Manager or Odoo system admin can call /api/crm/admin/* routes.
- Any authenticated user can call /api/crm/me/permissions.
- apply_to_all_same_job_title=true  → saves the overrides AS a new job-title
  template (or updates existing one) so all future users with that title inherit them.
  It does NOT wipe existing individual overrides for other users.

Endpoints
---------
  # Current user
  POST /api/crm/me/permissions

  # Permission schema (for FE to build the form)
  POST /api/crm/admin/permissions/schema

  # Job-title templates
  POST /api/crm/admin/permissions/job_titles/list
  POST /api/crm/admin/permissions/job_titles/upsert        { job_title, crm_role, permissions, apply_to_all_users, notes }
  POST /api/crm/admin/permissions/job_titles/delete        { job_title }

  # User management
  POST /api/crm/admin/users/list
  POST /api/crm/admin/users/<id>/get
  POST /api/crm/admin/users/<id>/permissions/get
  POST /api/crm/admin/users/<id>/permissions/set           { permissions, apply_to_all_same_job_title, notes }
  POST /api/crm/admin/users/<id>/permissions/reset
  POST /api/crm/admin/users/assign_role                    { email, role }
  POST /api/crm/admin/users/bulk_assign                    { assignments: [{email, role}] }
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
# Single source of truth — covers every module in the system.
# All leaves are False (denied) by default.
# Sections: supply_chain | crm | qa | pos | hr | inventory | finance | analytics | settings | admin

PERMISSION_TREE = {

    # ── Supply Chain ──────────────────────────────────────────────────────────
    "supply_chain": {
        "containers": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "assign_driver": False, "mark_arrived": False, "clearance_delivered": False,
            "set_reminder": False, "upload_attachment": False, "delete_attachment": False,
            "add_comment": False, "delete_comment": False,
            "add_penalty": False, "delete_penalty": False,
        },
        "vendors": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
        },
        "po": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "submit": False, "confirm": False, "ship": False, "receive": False,
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
        "clearance_companies": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
        },
        "tracking":     {"view": False, "update": False},
        "minmax":       {"list": False, "edit": False, "delete": False},
        "penalties":    {"list": False, "add": False, "delete": False},
        "notifications":{"list": False, "mark_read": False, "delete": False},
        "chat":         {"view": False, "send": False, "delete_message": False},
        "stories":      {"list": False, "view": False, "create": False, "delete": False},
    },

    # ── CRM ───────────────────────────────────────────────────────────────────
    "crm": {
        "customers": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "export": False, "import": False, "merge": False,
        },
        "calls": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "listen_recording": False,
        },
        "tickets": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "assign": False, "escalate": False, "close": False,
        },
        "tasks": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "assign": False, "close": False,
        },
        "analytics": {
            "view": False, "export": False, "view_team_data": False,
        },
        "config": {"view": False, "edit": False},
        "branches": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
        },
        "knowledge": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
        },
        "omnichannel": {
            "view": False, "reply": False, "assign": False,
        },
        "shifts": {
            "view": False, "manage": False,
        },
    },

    # ── QA ────────────────────────────────────────────────────────────────────
    "qa": {
        "reviews": {
            "list": False, "view": False, "create": False, "score": False, "delete": False,
            "export": False,
        },
        "management": {
            "view": False, "manage": False, "assign_reviewer": False,
        },
        "reports": {
            "view": False, "export": False,
        },
    },

    # ── Point of Sale (POS) ───────────────────────────────────────────────────
    "pos": {
        "sessions": {
            "list": False, "view": False, "open": False, "close": False,
        },
        "orders": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "refund": False, "export_pdf": False,
        },
        "products": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "set_price": False, "set_discount": False,
        },
        "customers": {
            "list": False, "view": False, "create": False, "edit": False,
        },
        "payments": {
            "view": False, "process": False, "refund": False,
        },
        "reports": {
            "view": False, "export": False, "z_report": False,
        },
        "config": {
            "view": False, "edit": False,
        },
    },

    # ── HR / Human Resources ──────────────────────────────────────────────────
    "hr": {
        "employees": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "view_salary": False, "view_private": False, "export": False,
        },
        "attendance": {
            "view_own": False, "view_all": False, "edit": False, "export": False,
        },
        "leaves": {
            "view_own": False, "view_all": False,
            "request": False, "approve": False, "refuse": False,
            "manage_allocation": False,
        },
        "payroll": {
            "view_own": False, "view_all": False,
            "compute": False, "validate": False, "export": False,
        },
        "recruitment": {
            "view": False, "create": False, "manage": False, "delete": False,
        },
        "kpi": {
            "view_own": False, "view_all": False, "set": False, "export": False,
        },
        "shifts": {
            "view_own": False, "view_all": False, "manage": False,
        },
        "org_chart": {
            "view": False,
        },
        "config": {
            "view": False, "edit": False,
        },
    },

    # ── Inventory / Stock ─────────────────────────────────────────────────────
    "inventory": {
        "products": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "set_price": False, "import": False, "export": False,
        },
        "stock": {
            "view": False, "adjust": False, "transfer": False, "scrap": False,
            "view_valuation": False,
        },
        "transfers": {
            "list": False, "view": False, "create": False, "validate": False,
            "cancel": False, "delete": False,
        },
        "warehouses": {
            "view": False, "create": False, "edit": False, "delete": False,
        },
        "locations": {
            "view": False, "create": False, "edit": False, "delete": False,
        },
        "lots_serials": {
            "view": False, "create": False, "edit": False,
        },
        "reports": {
            "view": False, "export": False,
        },
        "config": {
            "view": False, "edit": False,
        },
    },

    # ── Finance / Accounting ──────────────────────────────────────────────────
    "finance": {
        "invoices": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "confirm": False, "cancel": False, "register_payment": False,
            "export_pdf": False,
        },
        "bills": {
            "list": False, "view": False, "create": False, "edit": False, "delete": False,
            "confirm": False, "cancel": False, "register_payment": False,
        },
        "payments": {
            "list": False, "view": False, "create": False, "validate": False, "cancel": False,
        },
        "journals": {
            "view": False, "create": False, "edit": False, "delete": False,
        },
        "accounts": {
            "view": False, "create": False, "edit": False,
        },
        "reports": {
            "profit_loss": False, "balance_sheet": False, "cash_flow": False,
            "tax_report": False, "export": False,
        },
        "bank_statements": {
            "view": False, "import": False, "reconcile": False,
        },
        "config": {
            "view": False, "edit": False,
        },
    },

    # ── Analytics / Dashboards ─────────────────────────────────────────────────
    "analytics": {
        "dashboards": {
            "view": False, "create": False, "edit": False, "delete": False,
            "share": False,
        },
        "reports": {
            "view": False, "create": False, "export": False,
        },
        "kpi": {
            "view": False, "manage": False,
        },
        "spreadsheets": {
            "view": False, "create": False, "edit": False, "delete": False,
        },
    },

    # ── System Settings ───────────────────────────────────────────────────────
    "settings": {
        "general": {
            "view": False, "edit": False,
        },
        "users_companies": {
            "view": False, "manage": False,
        },
        "integrations": {
            "view": False, "manage": False,
        },
        "email": {
            "view": False, "configure": False,
        },
        "sap_integration": {
            "view": False, "sync": False, "configure": False,
        },
    },

    # ── Admin Panel ───────────────────────────────────────────────────────────
    "admin": {
        "users": {
            "list": False, "view": False, "create": False,
            "assign_role": False, "deactivate": False, "activate": False,
        },
        "permissions": {
            "view": False,
            "set_job_title_defaults": False,
            "set_user_overrides": False,
        },
        "audit_logs": {
            "view": False, "export": False, "delete": False,
        },
        "modules": {
            "view": False, "install": False, "upgrade": False,
        },
    },
}

# ─── Role-level baseline permissions ─────────────────────────────────────────
# Covers every module section. Higher roles are supersets of lower ones.

def _base_for_role(role: str) -> dict:
    """Return baseline permission overrides for a named CRM role."""
    bases = {
        'none': {},

        # ── Agent: basic CRM + supply view/create only ────────────────────────
        'agent': {
            "supply_chain": {
                "containers":    {"list": True, "view": True, "upload_attachment": True, "add_comment": True},
                "vendors":       {"list": True, "view": True},
                "po":            {"list": True, "view": True, "create": True, "edit": True, "submit": True,
                                  "add_line": True, "edit_line": True, "upload_attachment": True, "add_comment": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True, "add_comment": True},
                "item_requests": {"list": True, "view": True, "create": True, "edit": True},
                "clearance_companies": {"list": True, "view": True},
                "tracking":      {"view": True},
                "minmax":        {"list": True},
                "penalties":     {"list": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":          {"view": True, "send": True},
                "stories":       {"list": True, "view": True, "create": True},
            },
            "crm": {
                "customers":  {"list": True, "view": True, "create": True, "edit": True},
                "calls":      {"list": True, "view": True, "create": True, "edit": True},
                "tickets":    {"list": True, "view": True, "create": True, "edit": True},
                "tasks":      {"list": True, "view": True, "create": True, "edit": True},
                "branches":   {"list": True, "view": True},
                "knowledge":  {"list": True, "view": True, "create": True, "edit": True},
                "omnichannel":{"view": True, "reply": True},
            },
            "hr": {
                "attendance": {"view_own": True},
                "leaves":     {"view_own": True, "request": True},
                "payroll":    {"view_own": True},
                "kpi":        {"view_own": True},
                "shifts":     {"view_own": True},
            },
            "pos": {
                "sessions":  {"list": True, "view": True, "open": True, "close": True},
                "orders":    {"list": True, "view": True, "create": True, "export_pdf": True},
                "products":  {"list": True, "view": True},
                "customers": {"list": True, "view": True, "create": True},
                "payments":  {"view": True, "process": True},
            },
            "inventory": {
                "products":  {"list": True, "view": True},
                "stock":     {"view": True},
                "transfers": {"list": True, "view": True},
            },
            "analytics": {
                "dashboards": {"view": True},
            },
        },

        # ── Supervisor: manage containers, approve POs/requests + team view ──
        'supervisor': {
            "supply_chain": {
                "containers":    {"list": True, "view": True, "create": True, "edit": True,
                                  "assign_driver": True, "mark_arrived": True, "clearance_delivered": True,
                                  "set_reminder": True, "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True},
                "vendors":       {"list": True, "view": True},
                "po":            {"list": True, "view": True, "create": True, "edit": True, "submit": True,
                                  "confirm": True, "add_line": True, "edit_line": True, "delete_line": True,
                                  "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True, "create": True, "edit": True,
                                  "add_comment": True, "delete_comment": True},
                "item_requests": {"list": True, "view": True, "create": True, "edit": True,
                                  "approve": True, "reject": True},
                "clearance_companies": {"list": True, "view": True},
                "tracking":      {"view": True, "update": True},
                "minmax":        {"list": True},
                "penalties":     {"list": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":          {"view": True, "send": True, "delete_message": True},
                "stories":       {"list": True, "view": True, "create": True, "delete": True},
            },
            "crm": {
                "customers":   {"list": True, "view": True, "create": True, "edit": True},
                "calls":       {"list": True, "view": True, "create": True, "edit": True},
                "tickets":     {"list": True, "view": True, "create": True, "edit": True, "assign": True, "escalate": True},
                "tasks":       {"list": True, "view": True, "create": True, "edit": True, "assign": True},
                "analytics":   {"view": True, "view_team_data": True},
                "branches":    {"list": True, "view": True, "edit": True},
                "knowledge":   {"list": True, "view": True, "create": True, "edit": True},
                "omnichannel": {"view": True, "reply": True, "assign": True},
                "shifts":      {"view": True, "manage": True},
            },
            "hr": {
                "attendance": {"view_own": True, "view_all": True},
                "leaves":     {"view_own": True, "view_all": True, "request": True, "approve": True, "refuse": True},
                "payroll":    {"view_own": True},
                "kpi":        {"view_own": True, "view_all": True},
                "shifts":     {"view_own": True, "view_all": True, "manage": True},
                "org_chart":  {"view": True},
            },
            "pos": {
                "sessions":  {"list": True, "view": True, "open": True, "close": True},
                "orders":    {"list": True, "view": True, "create": True, "export_pdf": True},
                "products":  {"list": True, "view": True},
                "customers": {"list": True, "view": True, "create": True, "edit": True},
                "payments":  {"view": True, "process": True, "refund": True},
                "reports":   {"view": True},
            },
            "inventory": {
                "products":  {"list": True, "view": True},
                "stock":     {"view": True},
                "transfers": {"list": True, "view": True, "create": True, "validate": True},
            },
            "analytics": {
                "dashboards": {"view": True},
                "reports":    {"view": True},
            },
        },

        # ── Manager: full ops except delete core records + finance view ───────
        'manager': {
            "supply_chain": {
                "containers":    {"list": True, "view": True, "create": True, "edit": True,
                                  "assign_driver": True, "mark_arrived": True, "clearance_delivered": True,
                                  "set_reminder": True, "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True,
                                  "add_penalty": True, "delete_penalty": True},
                "vendors":       {"list": True, "view": True, "create": True, "edit": True},
                "po":            {"list": True, "view": True, "create": True, "edit": True, "submit": True,
                                  "confirm": True, "ship": True, "receive": True, "cancel": True, "reopen": True,
                                  "add_line": True, "edit_line": True, "delete_line": True,
                                  "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "add_comment": True, "delete_comment": True},
                "item_requests": {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "approve": True, "reject": True, "fulfill": True},
                "clearance_companies": {"list": True, "view": True, "create": True, "edit": True},
                "tracking":      {"view": True, "update": True},
                "minmax":        {"list": True, "edit": True, "delete": True},
                "penalties":     {"list": True, "add": True, "delete": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":          {"view": True, "send": True, "delete_message": True},
                "stories":       {"list": True, "view": True, "create": True, "delete": True},
            },
            "crm": {
                "customers":   {"list": True, "view": True, "create": True, "edit": True, "export": True, "import": True},
                "calls":       {"list": True, "view": True, "create": True, "edit": True, "delete": True, "listen_recording": True},
                "tickets":     {"list": True, "view": True, "create": True, "edit": True, "assign": True, "escalate": True, "close": True},
                "tasks":       {"list": True, "view": True, "create": True, "edit": True, "assign": True, "close": True},
                "analytics":   {"view": True, "export": True, "view_team_data": True},
                "config":      {"view": True},
                "branches":    {"list": True, "view": True, "create": True, "edit": True},
                "knowledge":   {"list": True, "view": True, "create": True, "edit": True, "delete": True},
                "omnichannel": {"view": True, "reply": True, "assign": True},
                "shifts":      {"view": True, "manage": True},
            },
            "hr": {
                "employees":  {"list": True, "view": True, "create": True, "edit": True, "export": True},
                "attendance": {"view_own": True, "view_all": True, "edit": True, "export": True},
                "leaves":     {"view_own": True, "view_all": True, "request": True, "approve": True, "refuse": True, "manage_allocation": True},
                "payroll":    {"view_own": True, "view_all": True},
                "recruitment":{"view": True, "create": True, "manage": True},
                "kpi":        {"view_own": True, "view_all": True, "set": True, "export": True},
                "shifts":     {"view_own": True, "view_all": True, "manage": True},
                "org_chart":  {"view": True},
            },
            "pos": {
                "sessions":  {"list": True, "view": True, "open": True, "close": True},
                "orders":    {"list": True, "view": True, "create": True, "edit": True, "export_pdf": True},
                "products":  {"list": True, "view": True, "create": True, "edit": True, "set_price": True, "set_discount": True},
                "customers": {"list": True, "view": True, "create": True, "edit": True},
                "payments":  {"view": True, "process": True, "refund": True},
                "reports":   {"view": True, "export": True, "z_report": True},
                "config":    {"view": True},
            },
            "inventory": {
                "products":   {"list": True, "view": True, "create": True, "edit": True, "export": True},
                "stock":      {"view": True, "adjust": True, "transfer": True},
                "transfers":  {"list": True, "view": True, "create": True, "validate": True, "cancel": True},
                "warehouses": {"view": True},
                "locations":  {"view": True},
                "lots_serials":{"view": True, "create": True},
                "reports":    {"view": True, "export": True},
            },
            "finance": {
                "invoices":    {"list": True, "view": True, "create": True, "confirm": True, "export_pdf": True},
                "bills":       {"list": True, "view": True},
                "payments":    {"list": True, "view": True},
                "reports":     {"profit_loss": True, "export": True},
            },
            "analytics": {
                "dashboards": {"view": True, "create": True, "edit": True},
                "reports":    {"view": True, "create": True, "export": True},
                "kpi":        {"view": True},
                "spreadsheets":{"view": True, "create": True, "edit": True},
            },
        },

        # ── General Manager: FULL access to everything ────────────────────────
        'general_manager': {
            "supply_chain": {
                "containers":    {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "assign_driver": True, "mark_arrived": True, "clearance_delivered": True,
                                  "set_reminder": True, "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True,
                                  "add_penalty": True, "delete_penalty": True},
                "vendors":       {"list": True, "view": True, "create": True, "edit": True, "delete": True},
                "po":            {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "submit": True, "confirm": True, "ship": True, "receive": True,
                                  "cancel": True, "reopen": True,
                                  "add_line": True, "edit_line": True, "delete_line": True,
                                  "upload_attachment": True, "delete_attachment": True,
                                  "add_comment": True, "delete_comment": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "add_comment": True, "delete_comment": True},
                "item_requests": {"list": True, "view": True, "create": True, "edit": True, "delete": True,
                                  "approve": True, "reject": True, "fulfill": True},
                "clearance_companies": {"list": True, "view": True, "create": True, "edit": True, "delete": True},
                "tracking":      {"view": True, "update": True},
                "minmax":        {"list": True, "edit": True, "delete": True},
                "penalties":     {"list": True, "add": True, "delete": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":          {"view": True, "send": True, "delete_message": True},
                "stories":       {"list": True, "view": True, "create": True, "delete": True},
            },
            "crm": {
                "customers":   {"list": True, "view": True, "create": True, "edit": True, "delete": True, "export": True, "import": True, "merge": True},
                "calls":       {"list": True, "view": True, "create": True, "edit": True, "delete": True, "listen_recording": True},
                "tickets":     {"list": True, "view": True, "create": True, "edit": True, "delete": True, "assign": True, "escalate": True, "close": True},
                "tasks":       {"list": True, "view": True, "create": True, "edit": True, "delete": True, "assign": True, "close": True},
                "analytics":   {"view": True, "export": True, "view_team_data": True},
                "config":      {"view": True, "edit": True},
                "branches":    {"list": True, "view": True, "create": True, "edit": True, "delete": True},
                "knowledge":   {"list": True, "view": True, "create": True, "edit": True, "delete": True},
                "omnichannel": {"view": True, "reply": True, "assign": True},
                "shifts":      {"view": True, "manage": True},
            },
            "qa": {
                "reviews":    {"list": True, "view": True, "create": True, "score": True, "delete": True, "export": True},
                "management": {"view": True, "manage": True, "assign_reviewer": True},
                "reports":    {"view": True, "export": True},
            },
            "hr": {
                "employees":   {"list": True, "view": True, "create": True, "edit": True, "delete": True, "view_salary": True, "view_private": True, "export": True},
                "attendance":  {"view_own": True, "view_all": True, "edit": True, "export": True},
                "leaves":      {"view_own": True, "view_all": True, "request": True, "approve": True, "refuse": True, "manage_allocation": True},
                "payroll":     {"view_own": True, "view_all": True, "compute": True, "validate": True, "export": True},
                "recruitment": {"view": True, "create": True, "manage": True, "delete": True},
                "kpi":         {"view_own": True, "view_all": True, "set": True, "export": True},
                "shifts":      {"view_own": True, "view_all": True, "manage": True},
                "org_chart":   {"view": True},
                "config":      {"view": True, "edit": True},
            },
            "pos": {
                "sessions":  {"list": True, "view": True, "open": True, "close": True},
                "orders":    {"list": True, "view": True, "create": True, "edit": True, "delete": True, "refund": True, "export_pdf": True},
                "products":  {"list": True, "view": True, "create": True, "edit": True, "delete": True, "set_price": True, "set_discount": True},
                "customers": {"list": True, "view": True, "create": True, "edit": True},
                "payments":  {"view": True, "process": True, "refund": True},
                "reports":   {"view": True, "export": True, "z_report": True},
                "config":    {"view": True, "edit": True},
            },
            "inventory": {
                "products":    {"list": True, "view": True, "create": True, "edit": True, "delete": True, "set_price": True, "import": True, "export": True},
                "stock":       {"view": True, "adjust": True, "transfer": True, "scrap": True, "view_valuation": True},
                "transfers":   {"list": True, "view": True, "create": True, "validate": True, "cancel": True, "delete": True},
                "warehouses":  {"view": True, "create": True, "edit": True, "delete": True},
                "locations":   {"view": True, "create": True, "edit": True, "delete": True},
                "lots_serials":{"view": True, "create": True, "edit": True},
                "reports":     {"view": True, "export": True},
                "config":      {"view": True, "edit": True},
            },
            "finance": {
                "invoices":       {"list": True, "view": True, "create": True, "edit": True, "delete": True, "confirm": True, "cancel": True, "register_payment": True, "export_pdf": True},
                "bills":          {"list": True, "view": True, "create": True, "edit": True, "delete": True, "confirm": True, "cancel": True, "register_payment": True},
                "payments":       {"list": True, "view": True, "create": True, "validate": True, "cancel": True},
                "journals":       {"view": True, "create": True, "edit": True, "delete": True},
                "accounts":       {"view": True, "create": True, "edit": True},
                "reports":        {"profit_loss": True, "balance_sheet": True, "cash_flow": True, "tax_report": True, "export": True},
                "bank_statements":{"view": True, "import": True, "reconcile": True},
                "config":         {"view": True, "edit": True},
            },
            "analytics": {
                "dashboards":  {"view": True, "create": True, "edit": True, "delete": True, "share": True},
                "reports":     {"view": True, "create": True, "export": True},
                "kpi":         {"view": True, "manage": True},
                "spreadsheets":{"view": True, "create": True, "edit": True, "delete": True},
            },
            "settings": {
                "general":        {"view": True, "edit": True},
                "users_companies":{"view": True, "manage": True},
                "integrations":   {"view": True, "manage": True},
                "email":          {"view": True, "configure": True},
                "sap_integration":{"view": True, "sync": True, "configure": True},
            },
            "admin": {
                "users":       {"list": True, "view": True, "create": True, "assign_role": True, "deactivate": True, "activate": True},
                "permissions": {"view": True, "set_job_title_defaults": True, "set_user_overrides": True},
                "audit_logs":  {"view": True, "export": True, "delete": True},
                "modules":     {"view": True, "install": True, "upgrade": True},
            },
        },

        # ── QA Auditor: read-only across all + can score reviews ──────────────
        'qa_auditor': {
            "supply_chain": {
                "containers":    {"list": True, "view": True},
                "vendors":       {"list": True, "view": True},
                "po":            {"list": True, "view": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True},
                "item_requests": {"list": True, "view": True},
                "clearance_companies": {"list": True, "view": True},
                "tracking":      {"view": True},
                "minmax":        {"list": True},
                "penalties":     {"list": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":          {"view": True},
                "stories":       {"list": True, "view": True},
            },
            "crm": {
                "customers": {"list": True, "view": True},
                "calls":     {"list": True, "view": True, "listen_recording": True},
                "tickets":   {"list": True, "view": True},
                "tasks":     {"list": True, "view": True},
                "analytics": {"view": True},
                "branches":  {"list": True, "view": True},
                "knowledge": {"list": True, "view": True},
            },
            "qa": {
                "reviews":    {"list": True, "view": True, "create": True, "score": True},
                "management": {"view": True},
                "reports":    {"view": True},
            },
            "hr": {
                "attendance": {"view_own": True},
                "leaves":     {"view_own": True},
                "kpi":        {"view_own": True},
            },
            "analytics": {
                "dashboards": {"view": True},
                "reports":    {"view": True},
            },
        },

        # ── QA Supervisor: QA auditor + manage team + export ─────────────────
        'qa_supervisor': {
            "supply_chain": {
                "containers":    {"list": True, "view": True},
                "vendors":       {"list": True, "view": True},
                "po":            {"list": True, "view": True, "export_pdf": True},
                "negotiations":  {"list": True, "view": True},
                "item_requests": {"list": True, "view": True},
                "clearance_companies": {"list": True, "view": True},
                "tracking":      {"view": True},
                "minmax":        {"list": True},
                "penalties":     {"list": True},
                "notifications": {"list": True, "mark_read": True, "delete": True},
                "chat":       {"view": True},
                "stories":    {"list": True, "view": True},
            },
            "crm": {
                "customers": {"list": True, "view": True},
                "calls":     {"list": True, "view": True},
                "tickets":   {"list": True, "view": True},
                "tasks":     {"list": True, "view": True},
                "analytics": {"view": True},
                "branches":  {"list": True, "view": True},
                "knowledge": {"list": True, "view": True},
            },
            "crm": {
                "customers": {"list": True, "view": True},
                "calls":     {"list": True, "view": True, "listen_recording": True},
                "tickets":   {"list": True, "view": True},
                "tasks":     {"list": True, "view": True},
                "analytics": {"view": True},
                "branches":  {"list": True, "view": True},
                "knowledge": {"list": True, "view": True},
            },
            "qa": {
                "reviews":    {"list": True, "view": True, "create": True, "score": True, "delete": True, "export": True},
                "management": {"view": True, "manage": True, "assign_reviewer": True},
                "reports":    {"view": True, "export": True},
            },
            "hr": {
                "attendance": {"view_own": True, "view_all": True},
                "leaves":     {"view_own": True, "view_all": True},
                "kpi":        {"view_own": True, "view_all": True},
                "org_chart":  {"view": True},
            },
            "analytics": {
                "dashboards": {"view": True},
                "reports":    {"view": True, "export": True},
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
    Compute the final permission dict for a user.

    Steps
    -----
    1. Build an empty tree from PERMISSION_TREE.
    2. Apply the CRM role-level baseline (fast-path when no template).
    3. Apply the job-title template (if one exists for user.job_title).
    4. Apply the user-specific overrides on top.
    """
    # Step 1 — empty baseline
    base = copy.deepcopy(PERMISSION_TREE)

    # Step 2 — CRM role baseline (lowest priority)
    role = _resolve_role(user)
    role_overrides = _base_for_role(role)
    base = _deep_merge(base, role_overrides)

    # Step 3 — job-title template (overrides role baseline)
    job_title = user.sudo().partner_id.function or ''
    if job_title:
        Tmpl = request.env['lugal.crm.permission.template'].sudo()
        tmpl = Tmpl.search([('job_title', '=ilike', job_title), ('is_active', '=', True)], limit=1)
        if tmpl:
            tmpl_perms = tmpl.get_permissions()
            if tmpl_perms:
                base = _deep_merge(base, tmpl_perms)
            # Also apply the template's crm_role baseline (template role may differ)
            if tmpl.crm_role and tmpl.crm_role != role:
                base = _deep_merge(base, _base_for_role(tmpl.crm_role))
                base = _deep_merge(base, tmpl_perms)   # template perms win again

    # Step 4 — user-specific overrides (highest priority)
    Override = request.env['lugal.crm.user.permission'].sudo()
    override_rec = Override.search([('user_id', '=', user.id)], limit=1)
    if override_rec:
        # If user has a job_title_override, re-apply that template first
        eff_title = override_rec.job_title_override or job_title
        if eff_title and eff_title != job_title:
            Tmpl = request.env['lugal.crm.permission.template'].sudo()
            tmpl2 = Tmpl.search([('job_title', '=ilike', eff_title), ('is_active', '=', True)], limit=1)
            if tmpl2:
                base = _deep_merge(base, tmpl2.get_permissions())
        user_overrides = override_rec.get_overrides()
        if user_overrides:
            base = _deep_merge(base, user_overrides)

    return base


def _user_to_dict(user, include_permissions: bool = True) -> dict:
    role = _resolve_role(user)
    Override = request.env['lugal.crm.user.permission'].sudo()
    override_rec = Override.search([('user_id', '=', user.id)], limit=1)
    has_override = bool(override_rec and override_rec.get_overrides())

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
        d['permissions'] = _get_effective_permissions(user)
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
        Returns the FULL permission tree with every section/subsection/action.
        The FE uses this to render checkboxes dynamically.

        Response:
          {
            "success": true,
            "data": {
              "tree": { ...PERMISSION_TREE with all false... },
              "roles": ["none","agent","supervisor","manager","general_manager","qa_auditor","qa_supervisor"],
              "role_baselines": {
                "agent": { ...permissions when role=agent... },
                ...
              }
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not _is_admin():
                return {'success': False, 'error': 'Forbidden — Admin required', 'code': 403}
            roles = list(_ROLE_GROUP.keys())
            role_baselines = {}
            for r in roles:
                empty = copy.deepcopy(PERMISSION_TREE)
                role_baselines[r] = _deep_merge(empty, _base_for_role(r))
            return {
                'success': True,
                'data': {
                    'tree': copy.deepcopy(PERMISSION_TREE),
                    'roles': roles,
                    'role_baselines': role_baselines,
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
                user_ids.update(g.sudo().users.ids)

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
                        'found':             bool(override_rec),
                        'job_title_override': override_rec.job_title_override if override_rec else None,
                        'overrides':         override_rec.get_overrides() if override_rec else {},
                        'admin_notes':       override_rec.admin_notes if override_rec else '',
                        'last_modified_by':  override_rec.last_modified_by.name if override_rec and override_rec.last_modified_by else '',
                        'last_modified_at':  override_rec.last_modified_at.isoformat() if override_rec and override_rec.last_modified_at else None,
                    },

                    # Final merged result
                    'effective_permissions': _get_effective_permissions(user),
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

          apply_to_all_same_job_title (bool, optional, default false)
              — If TRUE: saves these overrides as the NEW job-title template
                for this user's job title (upserts it). Does NOT clear existing
                individual overrides for other users.
                The user's own individual override is then cleared (they get
                the template directly).

          job_title_override (str, optional)
              — If set, this user's baseline will be looked up using this
                job title instead of their actual user.job_title.
                Useful to grant one employee the same rights as a different title.

          notes (str, optional) — reason for the override (stored for audit trail)

        Response: user dict with updated effective_permissions
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
            apply_to_all        = bool(kwargs.get('apply_to_all_same_job_title'))
            job_title_override  = (kwargs.get('job_title_override') or '').strip() or None
            notes               = (kwargs.get('notes') or '').strip()

            if not isinstance(new_overrides, dict):
                return {'success': False, 'error': '`permissions` must be an object'}

            Override = request.env['lugal.crm.user.permission'].sudo()

            if apply_to_all:
                # Save overrides as the job-title template
                eff_title = job_title_override or user.sudo().partner_id.function or ''
                if not eff_title:
                    return {'success': False, 'error': 'apply_to_all_same_job_title requires the user to have a job_title (or pass job_title_override)'}
                Tmpl = request.env['lugal.crm.permission.template'].sudo()
                existing_tmpl = Tmpl.search([('job_title', '=ilike', eff_title)], limit=1)
                if existing_tmpl:
                    current = existing_tmpl.get_permissions()
                    merged  = _deep_merge(current, new_overrides)
                    existing_tmpl.write({'permissions_json': json.dumps(merged, ensure_ascii=False)})
                else:
                    merged = _deep_merge(copy.deepcopy(PERMISSION_TREE), new_overrides)
                    Tmpl.create({
                        'job_title':        eff_title,
                        'label':            eff_title,
                        'permissions_json': json.dumps(merged, ensure_ascii=False),
                        'is_active':        True,
                    })
                # Clear this user's individual override (they now inherit the template)
                override_rec = Override.search([('user_id', '=', user_id)], limit=1)
                if override_rec:
                    override_rec.unlink()
                _logger.info(
                    'admin_user_permissions_set: applied overrides as job_title template "%s" (uid=%d, by=%d)',
                    eff_title, user_id, uid,
                )
            else:
                # Store only for this individual user
                Override.upsert_for_user(
                    user_id=user_id,
                    overrides=new_overrides,
                    job_title_override=job_title_override,
                    admin_notes=notes or None,
                    modifier_id=uid,
                )

            user.invalidate_recordset()
            return {
                'success': True,
                'data': {
                    **_user_to_dict(user),
                    'applied_to_all_same_job_title': apply_to_all,
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
            remove = [(3, g.id) for g in all_groups.values() if g and g in user.sudo().groups_id]
            add    = []
            tgid   = _ROLE_GROUP[role]
            if tgid:
                tg = request.env.ref(tgid, raise_if_not_found=False)
                if tg:
                    add = [(4, tg.id)]
            user.sudo().write({'groups_id': remove + add})
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
                    remove = [(3, g.id) for g in all_groups.values() if g and g in user.sudo().groups_id]
                    add = []
                    tgid = _ROLE_GROUP[role]
                    if tgid:
                        tg = request.env.ref(tgid, raise_if_not_found=False)
                        if tg:
                            add = [(4, tg.id)]
                    user.sudo().write({'groups_id': remove + add})
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
                    role_counts[role_key] = len(g.users) if g else 0
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
                    if g and user in g.users:
                        g.sudo().write({'users': [(3, user.id)]})
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
