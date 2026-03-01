# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Config parameter keys for rate-limit settings
_KEY_MAX_ATTEMPTS = 'lugal_auth.login_max_attempts'   # default 10
_KEY_WINDOW_MINS  = 'lugal_auth.login_window_minutes'  # default 15
_KEY_LOCKOUT_MINS = 'lugal_auth.login_lockout_minutes'  # default 30


class LugalAuthRateLimit(models.Model):
    """
    Tracks failed login attempts per username/IP.

    Prevents brute-force attacks on /lugal/auth/login.
    Config (ir.config_parameter):
        lugal_auth.login_max_attempts   — max failures before lockout  (default 10)
        lugal_auth.login_window_minutes — sliding window in minutes     (default 15)
        lugal_auth.login_lockout_minutes — lockout duration in minutes  (default 30)
    """

    _name        = 'lugal.auth.rate.limit'
    _description = 'Lugal Auth Rate Limit'
    _order       = 'last_attempt_at desc'

    identifier     = fields.Char(string='Identifier (username/IP)', required=True, index=True)
    attempt_count  = fields.Integer(string='Failed Attempts', default=0)
    locked_until   = fields.Datetime(string='Locked Until')
    last_attempt_at = fields.Datetime(string='Last Attempt At', default=fields.Datetime.now)

    _sql_constraints = [
        ('unique_identifier', 'UNIQUE(identifier)', 'Identifier must be unique'),
    ]

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _cfg(self, key, default):
        return int(self.env['ir.config_parameter'].sudo().get_param(key, default))

    def _max_attempts(self):
        return self._cfg(_KEY_MAX_ATTEMPTS, 10)

    def _window_minutes(self):
        return self._cfg(_KEY_WINDOW_MINS, 15)

    def _lockout_minutes(self):
        return self._cfg(_KEY_LOCKOUT_MINS, 30)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @api.model
    def is_locked(self, identifier):
        """Return True if the identifier is currently locked out."""
        record = self.search([('identifier', '=', identifier)], limit=1)
        if not record:
            return False
        if record.locked_until and record.locked_until > datetime.utcnow():
            return True
        # Lock expired — reset
        if record.locked_until and record.locked_until <= datetime.utcnow():
            record.write({'attempt_count': 0, 'locked_until': False})
        return False

    @api.model
    def record_failure(self, identifier):
        """
        Increment failure counter for *identifier*.
        Locks the identifier when max_attempts is reached.
        Returns True if now locked, False otherwise.
        """
        record = self.search([('identifier', '=', identifier)], limit=1)
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self._window_minutes())

        if not record:
            self.create({'identifier': identifier, 'attempt_count': 1, 'last_attempt_at': now})
            return False

        # Reset counter if last attempt was outside the window
        if record.last_attempt_at and record.last_attempt_at < window_start:
            record.write({'attempt_count': 1, 'locked_until': False, 'last_attempt_at': now})
            return False

        new_count = record.attempt_count + 1
        if new_count >= self._max_attempts():
            locked_until = now + timedelta(minutes=self._lockout_minutes())
            record.write({'attempt_count': new_count, 'locked_until': locked_until, 'last_attempt_at': now})
            _logger.warning('lugal_auth: identifier "%s" locked until %s', identifier, locked_until)
            return True

        record.write({'attempt_count': new_count, 'last_attempt_at': now})
        return False

    @api.model
    def record_success(self, identifier):
        """Clear failure counter on successful login."""
        record = self.search([('identifier', '=', identifier)], limit=1)
        if record:
            record.write({'attempt_count': 0, 'locked_until': False})

    @api.model
    def action_purge_old_entries(self):
        """Cron: remove stale rate-limit records older than 24 h."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        old = self.search([
            ('last_attempt_at', '<', cutoff),
            ('locked_until', '=', False),
        ])
        old.unlink()
        _logger.info('lugal_auth: purged %d stale rate-limit entries', len(old))
