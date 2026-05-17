# -*- coding: utf-8 -*-
"""
CRM User Presence API
---------------------

Routes
------
  POST /api/crm/presence/ping        — heartbeat; marks caller as online
  POST /api/crm/presence/users       — list all CRM users with their current status
  POST /api/crm/presence/me          — get the caller's own presence record
  POST /api/crm/presence/set_status  — manually set status message (or go "afk")

All routes use JSON-RPC 2.0 envelope with JWT Bearer auth.

Status Rules
------------
  online   — pinged within the last  5 minutes
  afk      — pinged between 5 minutes and 1 hour ago  (or explicitly set)
  offline  — not pinged for more than 1 hour  (or never)

FE Contract
-----------
  • Call  POST /presence/ping  every 30 seconds while the app is open.
  • If the user has been inactive for ≥1 hour the server auto-downgrades to "afk".
  • Subscribe to bus channel  "crm_presence"  for live status-change events.
"""

import logging

from odoo import http, fields
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

# ─── thresholds (must match the model) ───────────────────────────────────────
ONLINE_THRESHOLD_MIN = 5
AFK_THRESHOLD_MIN    = 60


class PresenceController(http.Controller):

    # -------------------------------------------------------------------------
    # POST /api/crm/presence/ping
    # -------------------------------------------------------------------------

    @http.route('/api/crm/presence/ping',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_ping(self, status_message=None, **kwargs):
        """
        Heartbeat — call every 30 s while the app is open.

        Optional params:
          status_message (str) — short custom message shown to others, e.g. "In a meeting"

        Response:
          {
            "success": true,
            "data": {
              "user_id":        <int>,
              "user_name":      <str>,
              "status":         "online",
              "status_message": <str>,
              "last_seen_at":   "<iso8601>"
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Presence = request.env['lugal.crm.user.presence'].sudo()
            rec = Presence.touch(uid, status_message=status_message)
            return {'success': True, 'data': rec._serialize()}
        except Exception as exc:
            _logger.exception('presence_ping')
            return {'success': False, 'error': str(exc)}

    # -------------------------------------------------------------------------
    # POST /api/crm/presence/me
    # -------------------------------------------------------------------------

    @http.route('/api/crm/presence/me',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_me(self, **kwargs):
        """
        Return the caller's own presence record (without updating it).

        Response:
          { "success": true, "data": <presence_object> }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Presence = request.env['lugal.crm.user.presence'].sudo()
            rec = Presence.search([('user_id', '=', uid)], limit=1)
            if not rec:
                # Never pinged → offline
                user = request.env['res.users'].sudo().browse(uid)
                return {
                    'success': True,
                    'data': {
                        'user_id':        uid,
                        'user_name':      user.name or '',
                        'user_email':     user.email or user.login or '',
                        'avatar_url':     '/web/image/res.users/%d/avatar_128' % uid,
                        'status':         'offline',
                        'status_message': '',
                        'last_seen_at':   None,
                    },
                }

            # Recompute status dynamically (without writing, just for response)
            computed = Presence._compute_status_from_timestamp(rec.last_seen_at)
            if computed != rec.status:
                rec.status = computed
                Presence._broadcast_status(rec)

            return {'success': True, 'data': rec._serialize()}
        except Exception as exc:
            _logger.exception('presence_me')
            return {'success': False, 'error': str(exc)}

    # -------------------------------------------------------------------------
    # POST /api/crm/presence/set_status
    # -------------------------------------------------------------------------

    @http.route('/api/crm/presence/set_status',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_set_status(self, status=None, status_message=None, **kwargs):
        """
        Manually set your own status and/or status message.

        Params:
          status         (str)  — "online" | "afk"  (cannot force "offline" this way)
          status_message (str)  — short message, e.g. "In a meeting"

        Response:
          { "success": true, "data": <presence_object> }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            ALLOWED = {'online', 'afk'}
            if status and status not in ALLOWED:
                return {'success': False, 'error': 'status must be "online" or "afk"'}

            Presence = request.env['lugal.crm.user.presence'].sudo()
            rec = Presence.search([('user_id', '=', uid)], limit=1)

            vals = {}
            if status:
                vals['status'] = status
            if status_message is not None:
                vals['status_message'] = status_message

            if rec:
                old_status = rec.status
                if vals:
                    rec.write(vals)
                status_changed = status and old_status != rec.status
            else:
                rec = Presence.create({
                    'user_id':        uid,
                    'last_seen_at':   fields.Datetime.now(),
                    'status':         status or 'online',
                    'status_message': status_message or '',
                })
                status_changed = True

            if status_changed:
                Presence._broadcast_status(rec)

            return {'success': True, 'data': rec._serialize()}
        except Exception as exc:
            _logger.exception('presence_set_status')
            return {'success': False, 'error': str(exc)}

    # -------------------------------------------------------------------------
    # POST /api/crm/presence/users
    # -------------------------------------------------------------------------

    @http.route('/api/crm/presence/users',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_users(self, status=None, include_offline=True, limit=200,
                       offset=0, **kwargs):
        """
        Return presence status for all CRM users.

        Optional params:
          status          (str)   — filter: "online" | "afk" | "offline"
          include_offline (bool)  — include users who have never pinged (default true)
          limit           (int)   — max records (default 200)
          offset          (int)   — pagination offset

        Response:
          {
            "success": true,
            "data": {
              "items": [
                {
                  "user_id":        <int>,
                  "user_name":      <str>,
                  "user_email":     <str>,
                  "avatar_url":     <str>,
                  "status":         "online" | "afk" | "offline",
                  "status_message": <str>,
                  "last_seen_at":   "<iso8601>" | null
                },
                ...
              ],
              "online_count":  <int>,
              "afk_count":     <int>,
              "offline_count": <int>,
              "total":         <int>
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            # Collect all active CRM users
            _CRM_GROUPS = [
                'lugal_crm.group_lugal_crm_agent',
                'lugal_crm.group_lugal_crm_supervisor',
                'lugal_crm.group_lugal_crm_manager',
                'lugal_crm.group_lugal_crm_general_manager',
                'lugal_crm.group_lugal_crm_qa',
                'lugal_crm.group_lugal_crm_qa_supervisor',
            ]
            crm_user_ids = set()
            for gref in _CRM_GROUPS:
                grp = request.env.ref(gref, raise_if_not_found=False)
                if grp:
                    crm_user_ids.update(grp.sudo().user_ids.filtered(
                        lambda u: u.active and not u.share
                    ).ids)

            if not crm_user_ids:
                return {'success': True, 'data': {
                    'items': [], 'online_count': 0, 'afk_count': 0,
                    'offline_count': 0, 'total': 0,
                }}

            # Refresh stale statuses without writing to DB (in-memory recompute)
            Presence = request.env['lugal.crm.user.presence'].sudo()
            presence_map = {}  # user_id → presence record
            for rec in Presence.search([('user_id', 'in', list(crm_user_ids))]):
                computed = Presence._compute_status_from_timestamp(rec.last_seen_at)
                if computed != rec.status:
                    rec.status = computed
                    Presence._broadcast_status(rec)
                presence_map[rec.user_id.id] = rec

            # Build result list — include users with no presence record as "offline"
            all_users = request.env['res.users'].sudo().browse(list(crm_user_ids))
            items = []
            for u in all_users:
                rec = presence_map.get(u.id)
                if rec:
                    item = rec._serialize()
                else:
                    item = {
                        'user_id':        u.id,
                        'user_name':      u.name or '',
                        'user_email':     u.email or u.login or '',
                        'avatar_url':     '/web/image/res.users/%d/avatar_128' % u.id,
                        'status':         'offline',
                        'status_message': '',
                        'last_seen_at':   None,
                    }
                items.append(item)

            # Filter by requested status
            if status in ('online', 'afk', 'offline'):
                items = [i for i in items if i['status'] == status]
            elif not include_offline:
                items = [i for i in items if i['status'] != 'offline']

            # Sort: online first, then afk, then offline; within each group by name
            _order = {'online': 0, 'afk': 1, 'offline': 2}
            items.sort(key=lambda i: (_order.get(i['status'], 3), i['user_name'].lower()))

            # Counts (before pagination)
            online_count  = sum(1 for i in items if i['status'] == 'online')
            afk_count     = sum(1 for i in items if i['status'] == 'afk')
            offline_count = sum(1 for i in items if i['status'] == 'offline')
            total         = len(items)

            # Pagination
            try:
                limit  = max(1, min(int(limit or 200), 500))
                offset = max(0, int(offset or 0))
            except (TypeError, ValueError):
                limit, offset = 200, 0
            items = items[offset: offset + limit]

            return {
                'success': True,
                'data': {
                    'items':         items,
                    'online_count':  online_count,
                    'afk_count':     afk_count,
                    'offline_count': offline_count,
                    'total':         total,
                },
            }
        except Exception as exc:
            _logger.exception('presence_users')
            return {'success': False, 'error': str(exc)}
