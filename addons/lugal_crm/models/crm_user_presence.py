# -*- coding: utf-8 -*-
"""
lugal.crm.user.presence
-----------------------
Tracks real-time online/AFK/offline status for CRM users.

Status rules (server-computed):
  online   — last_seen_at within the past 5 minutes
  afk      — last_seen_at between 5 minutes and 1 hour ago
  offline  — last_seen_at older than 1 hour OR never pinged
"""

import datetime as _dt
from datetime import timezone

from odoo import models, fields, api

# Thresholds (in minutes)
ONLINE_THRESHOLD_MIN = 5
AFK_THRESHOLD_MIN    = 60


class CrmUserPresence(models.Model):
    _name        = 'lugal.crm.user.presence'
    _description = 'CRM User Presence'
    _rec_name    = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        ondelete='cascade',
    )
    last_seen_at = fields.Datetime(
        string='Last Seen',
        default=fields.Datetime.now,
        index=True,
    )
    # Persisted status — updated by the ping endpoint.
    # Computed dynamically via _compute_status but also stored for DB queries.
    status = fields.Selection(
        [
            ('online',  'Online'),
            ('afk',     'Away (AFK)'),
            ('offline', 'Offline'),
        ],
        string='Status',
        default='offline',
        index=True,
    )
    # Optional: user-set custom status message ("In a meeting", "BRB", etc.)
    status_message = fields.Char(string='Status Message', default='')

    _sql_constraints = [
        ('user_uniq', 'UNIQUE(user_id)', 'Each user can have only one presence record'),
    ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _compute_status_from_timestamp(self, last_seen):
        """Given a last_seen datetime (UTC-naive), return the string status."""
        if not last_seen:
            return 'offline'
        now = _dt.datetime.utcnow()
        delta_min = (now - last_seen).total_seconds() / 60.0
        if delta_min <= ONLINE_THRESHOLD_MIN:
            return 'online'
        if delta_min <= AFK_THRESHOLD_MIN:
            return 'afk'
        return 'offline'

    def _to_iso(self, dt):
        """Convert naive-UTC datetime to ISO 8601 string, or None."""
        if not dt:
            return None
        if not isinstance(dt, _dt.datetime):
            return None
        return dt.replace(tzinfo=timezone.utc).isoformat(timespec='seconds')

    def _serialize(self):
        """Return a dict suitable for the API response."""
        self.ensure_one()
        u = self.user_id
        return {
            'user_id':        u.id,
            'user_name':      u.name or '',
            'user_email':     u.email or u.login or '',
            'avatar_url':     '/web/image/res.users/%d/avatar_128' % u.id,
            'status':         self.status,
            'status_message': self.status_message or '',
            'last_seen_at':   self._to_iso(self.last_seen_at),
        }

    # ------------------------------------------------------------------
    # Core ping method — called by the controller
    # ------------------------------------------------------------------

    @api.model
    def touch(self, uid, status_message=None):
        """
        Update (or create) the presence record for uid.
        Emits a bus event when the status changes.
        Returns the presence record.
        """
        now    = _dt.datetime.utcnow()
        record = self.search([('user_id', '=', uid)], limit=1)
        new_status = 'online'

        if record:
            old_status = record.status
            vals = {'last_seen_at': now, 'status': new_status}
            if status_message is not None:
                vals['status_message'] = status_message
            record.write(vals)
            status_changed = old_status != new_status
        else:
            vals = {
                'user_id':        uid,
                'last_seen_at':   now,
                'status':         new_status,
                'status_message': status_message or '',
            }
            record = self.create(vals)
            status_changed = True

        if status_changed:
            self._broadcast_status(record)

        return record

    @api.model
    def mark_stale(self):
        """
        Cron-callable: recalculate status for all records and emit bus events
        when a user transitions online→afk or afk→offline.
        """
        all_records = self.search([('status', '!=', 'offline')])
        for rec in all_records:
            new_status = self._compute_status_from_timestamp(rec.last_seen_at)
            if new_status != rec.status:
                rec.status = new_status
                self._broadcast_status(rec)

    def _broadcast_status(self, record):
        """Push a bus event so all clients know a user's status changed."""
        try:
            self.env['bus.bus'].sudo()._sendone(
                'crm_presence',
                'crm.user.presence.changed',
                record._serialize(),
            )
        except Exception:
            pass
