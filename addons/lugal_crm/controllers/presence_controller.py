# -*- coding: utf-8 -*-
"""
CRM User Presence API — WebSocket-first design
-----------------------------------------------

The FE never polls.  Complete flow:

  1. App loads   →  POST /presence/subscribe
                    • Marks caller as online
                    • Returns FULL snapshot of all users
                    • Server broadcasts new status to all via bus

  2. Bus open    →  subscribe to channel "crm_presence"
                    • Event: crm.user.presence.changed
                    • Update local state — NO further API calls needed

  3. Keep-alive  →  POST /presence/ping  every  30 s
                    • Keeps "online" window alive
                    • Server cron (every 2 min) auto-broadcasts stale transitions

  4. Idle detect →  FE: no activity for 3 min → POST /presence/set_status {status:"afk"}
                    FE: activity resumes      → POST /presence/ping (back to online)

  5. Tab hidden  →  visibilitychange + idle timer → set_status afk

  6. Tab close   →  POST /presence/disconnect  (beforeunload via sendBeacon)
                    • Marks offline immediately, broadcasts to all

Thresholds (server-enforced, cron-broadcast)
--------------------------------------------
  online   — pinged within the last 2 minutes
  afk      — pinged between 2 and 5 minutes ago (or explicit set_status)
  offline  — no ping for more than 5 minutes   (or explicit disconnect)

Routes
------
  POST /api/crm/presence/subscribe    — connect & get full snapshot
  POST /api/crm/presence/ping         — keepalive every 30 s
  POST /api/crm/presence/disconnect   — mark offline on tab close
  POST /api/crm/presence/set_status   — set afk / status message
  POST /api/crm/presence/users        — on-demand snapshot (fallback)
  POST /api/crm/presence/me           — own record only
"""

import logging
import datetime as _dt

from odoo import http, fields
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

_CRM_GROUPS = [
    'lugal_crm.group_lugal_crm_agent',
    'lugal_crm.group_lugal_crm_supervisor',
    'lugal_crm.group_lugal_crm_manager',
    'lugal_crm.group_lugal_crm_general_manager',
    'lugal_crm.group_lugal_crm_qa',
    'lugal_crm.group_lugal_crm_qa_supervisor',
]


def _get_crm_user_ids(env):
    """Return set of active CRM user IDs across all 6 roles."""
    ids = set()
    for gref in _CRM_GROUPS:
        grp = env.ref(gref, raise_if_not_found=False)
        if grp:
            ids.update(grp.sudo().user_ids.filtered(
                lambda u: u.active and not u.share
            ).ids)
    return ids


def _build_snapshot(env, crm_user_ids):
    """
    Build the full presence snapshot for all CRM users.
    Refreshes stale statuses and broadcasts changes.
    Returns (items, online_count, afk_count, offline_count).
    """
    Presence = env['lugal.crm.user.presence'].sudo()

    # Recompute stale statuses
    presence_map = {}
    for rec in Presence.search([('user_id', 'in', list(crm_user_ids))]):
        computed = Presence._compute_status_from_timestamp(rec.last_seen_at)
        if computed != rec.status:
            rec.status = computed
            Presence._broadcast_status(rec)
        presence_map[rec.user_id.id] = rec

    all_users = env['res.users'].sudo().browse(list(crm_user_ids))
    items = []
    for u in all_users:
        rec = presence_map.get(u.id)
        if rec:
            items.append(rec._serialize())
        else:
            items.append({
                'user_id':        u.id,
                'user_name':      u.name or '',
                'user_email':     u.email or u.login or '',
                'avatar_url':     '/web/image/res.users/%d/avatar_128' % u.id,
                'status':         'offline',
                'status_message': '',
                'last_seen_at':   None,
            })

    _order = {'online': 0, 'afk': 1, 'offline': 2}
    items.sort(key=lambda i: (_order.get(i['status'], 3), i['user_name'].lower()))

    online_count  = sum(1 for i in items if i['status'] == 'online')
    afk_count     = sum(1 for i in items if i['status'] == 'afk')
    offline_count = sum(1 for i in items if i['status'] == 'offline')

    return items, online_count, afk_count, offline_count


class PresenceController(http.Controller):

    # ─────────────────────────────────────────────────────────────────────────
    # 1. SUBSCRIBE  — call once on app load
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/subscribe',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_subscribe(self, status_message=None, **kwargs):
        """
        Connect to presence system.

        Call ONCE when the app loads (or WebSocket reconnects).

        • Marks the caller as "online"
        • Broadcasts the caller's new status to all connected users via bus
        • Returns full snapshot of ALL users' current presence status

        After this call, subscribe to bus channel "crm_presence" to receive
        live  crm.user.presence.changed  events — no further API calls needed
        to keep the user list up to date.

        Response:
          {
            "success": true,
            "data": {
              "me": <presence_object>,          // caller's own record
              "users": {
                "items":         [...],          // all CRM users, online first
                "online_count":  <int>,
                "afk_count":     <int>,
                "offline_count": <int>,
                "total":         <int>
              },
              "bus_channel": "crm_presence",    // subscribe to this channel
              "bus_event":   "crm.user.presence.changed"
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Presence = request.env['lugal.crm.user.presence'].sudo()

            # Mark caller as online (broadcasts to all via bus)
            me = Presence.touch(uid, status_message=status_message)

            # Build full snapshot
            crm_user_ids = _get_crm_user_ids(request.env)
            if uid not in crm_user_ids:
                crm_user_ids.add(uid)   # include caller even if not in a CRM group

            items, online_count, afk_count, offline_count = _build_snapshot(
                request.env, crm_user_ids
            )

            return {
                'success': True,
                'data': {
                    'me': me._serialize(),
                    'users': {
                        'items':         items,
                        'online_count':  online_count,
                        'afk_count':     afk_count,
                        'offline_count': offline_count,
                        'total':         len(items),
                    },
                    'bus_channel': 'crm_presence',
                    'bus_event':   'crm.user.presence.changed',
                },
            }
        except Exception as exc:
            _logger.exception('presence_subscribe')
            return {'success': False, 'error': str(exc)}

    # ─────────────────────────────────────────────────────────────────────────
    # 2. PING  — keepalive every 2 minutes
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/ping',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_ping(self, status_message=None, **kwargs):
        """
        Keepalive — call every 30 seconds while the app is open and user is active.

        Only updates last_seen_at and broadcasts if the status changed.
        Returns only the caller's own record (no full user list).

        Response:
          { "success": true, "data": <presence_object> }
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

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DISCONNECT  — call from window.beforeunload
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/disconnect',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_disconnect(self, **kwargs):
        """
        Mark the caller as offline immediately.

        Call from  window.addEventListener('beforeunload', ...)  so other users
        see the status change right away instead of waiting for the AFK/offline
        timeout.

        Uses  navigator.sendBeacon  for reliability on page close.

        Response:
          { "success": true }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Presence = request.env['lugal.crm.user.presence'].sudo()
            rec = Presence.search([('user_id', '=', uid)], limit=1)
            if rec and rec.status != 'offline':
                # Push last_seen_at back 2 h so stale recompute also agrees it's offline
                stale_time = _dt.datetime.utcnow() - _dt.timedelta(hours=2)
                rec.write({'status': 'offline', 'last_seen_at': stale_time})
                Presence._broadcast_status(rec)

            return {'success': True}
        except Exception as exc:
            _logger.exception('presence_disconnect')
            return {'success': False, 'error': str(exc)}

    # ─────────────────────────────────────────────────────────────────────────
    # 4. USERS  — on-demand snapshot (FE normally uses bus, not this)
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/users',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_users(self, status=None, include_offline=True, limit=200,
                       offset=0, **kwargs):
        """
        On-demand full snapshot.  Prefer bus events over polling this.

        Optional params:
          status          — filter by "online" | "afk" | "offline"
          include_offline — default true
          limit / offset  — pagination

        Response:
          { "success": true, "data": { items, online_count, afk_count, offline_count, total } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            crm_user_ids = _get_crm_user_ids(request.env)
            if not crm_user_ids:
                return {'success': True, 'data': {
                    'items': [], 'online_count': 0, 'afk_count': 0,
                    'offline_count': 0, 'total': 0,
                }}

            items, online_count, afk_count, offline_count = _build_snapshot(
                request.env, crm_user_ids
            )

            # Optional status filter
            if status in ('online', 'afk', 'offline'):
                items = [i for i in items if i['status'] == status]
            elif not include_offline:
                items = [i for i in items if i['status'] != 'offline']

            # Recalculate counts after filter
            o = sum(1 for i in items if i['status'] == 'online')
            a = sum(1 for i in items if i['status'] == 'afk')
            f = sum(1 for i in items if i['status'] == 'offline')
            total = len(items)

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
                    'online_count':  o,
                    'afk_count':     a,
                    'offline_count': f,
                    'total':         total,
                },
            }
        except Exception as exc:
            _logger.exception('presence_users')
            return {'success': False, 'error': str(exc)}

    # ─────────────────────────────────────────────────────────────────────────
    # 5. ME  — own record (no update)
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/me',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_me(self, **kwargs):
        """Return own presence record without updating it."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Presence = request.env['lugal.crm.user.presence'].sudo()
            rec = Presence.search([('user_id', '=', uid)], limit=1)
            if not rec:
                user = request.env['res.users'].sudo().browse(uid)
                return {'success': True, 'data': {
                    'user_id':        uid,
                    'user_name':      user.name or '',
                    'user_email':     user.email or user.login or '',
                    'avatar_url':     '/web/image/res.users/%d/avatar_128' % uid,
                    'status':         'offline',
                    'status_message': '',
                    'last_seen_at':   None,
                }}

            computed = Presence._compute_status_from_timestamp(rec.last_seen_at)
            if computed != rec.status:
                rec.status = computed
                Presence._broadcast_status(rec)

            return {'success': True, 'data': rec._serialize()}
        except Exception as exc:
            _logger.exception('presence_me')
            return {'success': False, 'error': str(exc)}

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SET_STATUS  — manual override
    # ─────────────────────────────────────────────────────────────────────────

    @http.route('/api/crm/presence/set_status',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def presence_set_status(self, status=None, status_message=None, **kwargs):
        """
        Manually set status and/or status message.

        Params:
          status         — "online" | "afk"
          status_message — e.g. "In a meeting"
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            if status and status not in ('online', 'afk'):
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
                if status and old_status != rec.status:
                    Presence._broadcast_status(rec)
            else:
                rec = Presence.create({
                    'user_id':        uid,
                    'last_seen_at':   fields.Datetime.now(),
                    'status':         status or 'online',
                    'status_message': status_message or '',
                })
                Presence._broadcast_status(rec)

            return {'success': True, 'data': rec._serialize()}
        except Exception as exc:
            _logger.exception('presence_set_status')
            return {'success': False, 'error': str(exc)}
