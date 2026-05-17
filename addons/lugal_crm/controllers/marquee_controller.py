# -*- coding: utf-8 -*-
"""
Marquee / System-wide announcement API
======================================

Endpoints
---------
POST  /api/crm/marquee/create          – Admin: create a new marquee
GET   /api/crm/marquee/active          – All users: get currently active marquees
GET   /api/crm/marquee/list            – Admin: full list (active + expired)
POST  /api/crm/marquee/<id>/update     – Admin: edit message / times / colours
POST  /api/crm/marquee/<id>/expire     – Admin: immediately expire (deactivate)
DELETE /api/crm/marquee/<id>           – Admin: hard-delete
"""

import logging
import datetime as _dt
from odoo import http, fields
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from ._permissions import require_permission

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _json_ok(data):
    return {'success': True, 'data': data}


def _json_err(msg, code=400):
    return {'success': False, 'error': msg}


def _require_admin(uid):
    """Return True when the user has at least manager-level access."""
    user = request.env['res.users'].sudo().browse(uid)
    return user.has_group('base.group_system') or user._is_admin()


def _parse_dt(value):
    """
    Parse an ISO-8601 datetime string (with or without timezone offset) into a
    naive UTC datetime suitable for Odoo Datetime fields.

    Accepts:
      "2026-05-17 18:00:00"         → treated as UTC
      "2026-05-17T18:00:00"         → treated as UTC
      "2026-05-17T21:00:00+03:00"   → converted to UTC (18:00)
      "2026-05-17T18:00:00Z"        → UTC
      datetime object (tz-aware or naive)  → normalised to naive UTC
    Returns naive datetime (UTC) or None if value is falsy.
    """
    if not value:
        return None
    if isinstance(value, _dt.datetime):
        if value.tzinfo is not None:
            return value.astimezone(_dt.timezone.utc).replace(tzinfo=None)
        return value
    # String path — try dateutil first (handles all ISO-8601 variants)
    try:
        from dateutil import parser as _dparser
        dt = _dparser.isoparse(value)
        if dt.tzinfo is not None:
            dt = dt.astimezone(_dt.timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass
    # Fallback: Odoo's own parser (handles "YYYY-MM-DD HH:MM:SS" only)
    try:
        return fields.Datetime.from_string(value)
    except Exception:
        raise ValueError(f"Cannot parse datetime: {value!r}. Use ISO-8601, e.g. 2026-05-17T18:00:00+03:00")


# ---------------------------------------------------------------------------
# controller
# ---------------------------------------------------------------------------

class MarqueeController(http.Controller):

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/create',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_create(self,
                       message='', message_ar='',
                       starts_at=None, expires_at=None,
                       bg_color='#1E3A5F', text_color='#FFFFFF',
                       speed=60, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)
            denied = require_permission('settings.general.edit')
            if denied:
                return denied

            if not message:
                return _json_err('message is required')
            if not expires_at:
                return _json_err('expires_at is required (ISO-8601 UTC)')

            Marquee = request.env['lugal.crm.marquee'].sudo()

            vals = {
                'message':    message,
                'message_ar': message_ar or '',
                'expires_at': _parse_dt(expires_at),
                'starts_at':  _parse_dt(starts_at) if starts_at else fields.Datetime.now(),
                'bg_color':   bg_color or '#1E3A5F',
                'text_color': text_color or '#FFFFFF',
                'speed':      int(speed or 60),
                'created_by': uid,
            }

            rec = Marquee.create(vals)
            return _json_ok(rec._to_dict())
        except Exception as exc:
            return crm_error(exc, 'marquee_create')

    # ------------------------------------------------------------------
    # Active announcements  (any logged-in user)
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/active',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_active(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)

            now = fields.Datetime.now()
            recs = request.env['lugal.crm.marquee'].sudo().search([
                ('starts_at',  '<=', now),
                ('expires_at', '>=', now),
            ], order='created_at desc')

            return _json_ok({
                'total': len(recs),
                'items': [r._to_dict() for r in recs],
            })
        except Exception as exc:
            return crm_error(exc, 'marquee_active')

    # ------------------------------------------------------------------
    # Full list  (admin)
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_list(self, page=1, per_page=30, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)
            denied = require_permission('settings.general.view')
            if denied:
                return denied

            offset = (int(page) - 1) * int(per_page)
            Marquee = request.env['lugal.crm.marquee'].sudo()
            total   = Marquee.search_count([])
            recs    = Marquee.search([], limit=int(per_page), offset=offset,
                                     order='created_at desc')

            return _json_ok({
                'total':    total,
                'page':     int(page),
                'per_page': int(per_page),
                'items':    [r._to_dict() for r in recs],
            })
        except Exception as exc:
            return crm_error(exc, 'marquee_list')

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/<int:marquee_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_update(self, marquee_id,
                       message=None, message_ar=None,
                       starts_at=None, expires_at=None,
                       bg_color=None, text_color=None,
                       speed=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)
            denied = require_permission('settings.general.edit')
            if denied:
                return denied

            rec = request.env['lugal.crm.marquee'].sudo().browse(marquee_id)
            if not rec.exists():
                return _json_err('Not found', 404)

            vals = {}
            if message    is not None: vals['message']    = message
            if message_ar is not None: vals['message_ar'] = message_ar
            if bg_color   is not None: vals['bg_color']   = bg_color
            if text_color is not None: vals['text_color'] = text_color
            if speed      is not None: vals['speed']      = int(speed)
            if starts_at  is not None:
                vals['starts_at'] = _parse_dt(starts_at)
            if expires_at is not None:
                vals['expires_at'] = _parse_dt(expires_at)

            if not vals:
                return _json_err('Nothing to update')

            rec.write(vals)
            return _json_ok(rec._to_dict())
        except Exception as exc:
            return crm_error(exc, 'marquee_update')

    # ------------------------------------------------------------------
    # Expire immediately  (soft-stop)
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/<int:marquee_id>/expire',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_expire(self, marquee_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)
            denied = require_permission('settings.general.edit')
            if denied:
                return denied

            rec = request.env['lugal.crm.marquee'].sudo().browse(marquee_id)
            if not rec.exists():
                return _json_err('Not found', 404)

            rec.write({'expires_at': fields.Datetime.now()})
            # Push deletion event so FE hides it immediately
            rec._push_to_all_users('crm.marquee.expired')
            return _json_ok({'id': marquee_id, 'expired': True})
        except Exception as exc:
            return crm_error(exc, 'marquee_expire')

    # ------------------------------------------------------------------
    # Hard delete
    # ------------------------------------------------------------------
    @http.route('/api/crm/marquee/<int:marquee_id>/delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def marquee_delete(self, marquee_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json_err('Unauthorized', 401)
            denied = require_permission('settings.general.edit')
            if denied:
                return denied

            rec = request.env['lugal.crm.marquee'].sudo().browse(marquee_id)
            if not rec.exists():
                return _json_err('Not found', 404)

            # Notify before delete so the FE can remove it
            try:
                rec._push_to_all_users('crm.marquee.deleted')
            except Exception:
                pass

            rec.unlink()
            return _json_ok({'id': marquee_id, 'deleted': True})
        except Exception as exc:
            return crm_error(exc, 'marquee_delete')
