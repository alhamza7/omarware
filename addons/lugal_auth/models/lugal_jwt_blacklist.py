# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalJwtBlacklist(models.Model):
    """
    Revocation list for JWT tokens.

    When a user logs out (or an admin force-revokes a token), the token's
    ``jti`` (JWT ID) is stored here.  verify_access_token checks this table
    before accepting a token, making logout truly effective.

    Rows are cleaned up automatically by the scheduled action
    ``action_purge_expired_entries`` once the token's natural expiry has
    passed — so this table stays small.
    """

    _name        = 'lugal.jwt.blacklist'
    _description = 'Lugal JWT Token Blacklist'
    _order       = 'revoked_at desc'
    _rec_name    = 'jti'

    jti        = fields.Char(string='Token JTI', required=True, index=True)
    user_id    = fields.Many2one('res.users', string='User', ondelete='cascade', index=True)
    revoked_at = fields.Datetime(string='Revoked At', default=fields.Datetime.now, readonly=True)
    expires_at = fields.Datetime(string='Token Expires At', help='Natural expiry of the revoked token')
    reason     = fields.Selection([
        ('logout',        'Logout'),
        ('force_revoke',  'Force Revoke (Admin)'),
        ('password_reset','Password Reset'),
    ], string='Reason', default='logout')

    _sql_constraints = [
        ('unique_jti', 'UNIQUE(jti)', 'Token JTI must be unique in blacklist'),
    ]

    @api.model
    def is_revoked(self, jti):
        """Return True if the given jti has been revoked."""
        return bool(self.search_count([('jti', '=', jti)]))

    @api.model
    def revoke(self, jti, user_id=None, expires_at=None, reason='logout'):
        """Add a jti to the blacklist. Safe to call even if already revoked."""
        if self.is_revoked(jti):
            return True
        try:
            self.create({
                'jti':        jti,
                'user_id':    user_id,
                'expires_at': expires_at,
                'reason':     reason,
            })
            return True
        except Exception as exc:
            _logger.error('lugal_auth: blacklist.revoke failed — %s', exc)
            return False

    @api.model
    def action_purge_expired_entries(self):
        """Cron: delete blacklist rows whose token has naturally expired."""
        now = datetime.utcnow()
        expired = self.search([
            ('expires_at', '!=', False),
            ('expires_at', '<', now),
        ])
        count = len(expired)
        expired.unlink()
        _logger.info('lugal_auth: purged %d expired blacklist entries', count)
