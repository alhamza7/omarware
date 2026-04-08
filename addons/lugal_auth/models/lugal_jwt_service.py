# -*- coding: utf-8 -*-

import jwt
import uuid
import logging
from datetime import datetime, timedelta
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_KEY_ACCESS_SECRET  = 'lugal_auth.jwt_secret_key'
_KEY_REFRESH_SECRET = 'lugal_auth.jwt_refresh_secret_key'
_KEY_ACCESS_EXP     = 'lugal_auth.jwt_access_token_expire_minutes'
_KEY_REFRESH_EXP    = 'lugal_auth.jwt_refresh_token_expire_days'

# Legacy key names from nbs_archive — checked as fallback during migration
_LEGACY_ACCESS_SECRET  = 'nbs_archive.jwt_secret_key'
_LEGACY_REFRESH_SECRET = 'nbs_archive.jwt_refresh_secret_key'


class LugalJwtService(models.AbstractModel):
    """
    Centralized JWT service for the Lugal suite.

    Features:
    - jti (JWT ID) in every token for revocation support
    - Blacklist check on verify (logout is truly effective)
    - Legacy nbs_archive key fallback for zero-downtime migration
    - Zero business logic — depends only on base
    """

    _name        = 'lugal.jwt.service'
    _description = 'Lugal Centralized JWT Authentication Service'

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _get_secret_key(self):
        """Return access-token signing secret (lugal_auth config param)."""
        return self.env['ir.config_parameter'].sudo().get_param(
            _KEY_ACCESS_SECRET, 'lugal-secret-change-in-production'
        )

    def _get_refresh_secret_key(self):
        """Return refresh-token signing secret."""
        return self.env['ir.config_parameter'].sudo().get_param(
            _KEY_REFRESH_SECRET, 'lugal-refresh-secret-change-in-production'
        )

    def _get_legacy_secret_key(self):
        """Return old nbs_archive secret key for migration fallback (read-only)."""
        return self.env['ir.config_parameter'].sudo().get_param(
            _LEGACY_ACCESS_SECRET, None
        )

    def _get_access_token_expire_minutes(self):
        """Return access-token lifetime in minutes (default 8 h)."""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            _KEY_ACCESS_EXP, '480'
        ))

    def _get_refresh_token_expire_days(self):
        """Return refresh-token lifetime in days (default 7 d)."""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            _KEY_REFRESH_EXP, '7'
        ))

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    @api.model
    def generate_access_token(self, user_id):
        """Sign and return a new JWT access token for *user_id*."""
        user = self.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            raise ValidationError('User not found')

        expire = datetime.utcnow() + timedelta(
            minutes=self._get_access_token_expire_minutes()
        )
        payload = {
            'jti':      str(uuid.uuid4()),   # unique ID — enables revocation
            'user_id':  user.id,
            'username': user.login,
            'exp':      expire,
            'iat':      datetime.utcnow(),
            'type':     'access',
        }
        return jwt.encode(payload, self._get_secret_key(), algorithm='HS256')

    @api.model
    def generate_refresh_token(self, user_id):
        """Sign and return a new JWT refresh token for *user_id*."""
        user = self.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            raise ValidationError('User not found')

        expire = datetime.utcnow() + timedelta(
            days=self._get_refresh_token_expire_days()
        )
        payload = {
            'jti':      str(uuid.uuid4()),
            'user_id':  user.id,
            'username': user.login,
            'exp':      expire,
            'iat':      datetime.utcnow(),
            'type':     'refresh',
        }
        return jwt.encode(
            payload, self._get_refresh_secret_key(), algorithm='HS256'
        )

    # ------------------------------------------------------------------
    # Token verification
    # ------------------------------------------------------------------

    @api.model
    def verify_access_token(self, token):
        """
        Decode and validate an access token.

        Steps:
        1. Try lugal_auth secret key
        2. If that fails AND a legacy nbs_archive key exists → try it (migration)
        3. Check blacklist (revoked tokens are rejected)
        4. Confirm user still exists in the DB

        Returns dict with user_id / username / jti on success, or None.
        """
        payload = self._decode_token(token, token_type='access')

        # --- migration fallback: try legacy nbs_archive key ---
        if payload is None:
            legacy_key = self._get_legacy_secret_key()
            if legacy_key:
                payload = self._decode_token(
                    token, token_type='access', secret_override=legacy_key
                )
                if payload:
                    _logger.info(
                        'lugal_auth: token accepted via legacy nbs_archive key '
                        '(user %s) — re-issue token with lugal_auth key',
                        payload.get('user_id'),
                    )

        if not payload:
            return None

        # --- blacklist check ---
        jti = payload.get('jti')
        if jti and self.env['lugal.jwt.blacklist'].sudo().is_revoked(jti):
            _logger.warning('lugal_auth: token jti=%s is revoked', jti)
            return None

        user = self.env['res.users'].sudo().browse(payload['user_id'])
        if not user.exists():
            _logger.warning('lugal_auth: user %s not found', payload['user_id'])
            return None

        return {
            'user_id':  user.id,
            'username': user.login,
            'jti':      jti,
            'exp':      payload.get('exp'),
        }

    @api.model
    def verify_refresh_token(self, token):
        """
        Decode and validate a refresh token.

        Returns {'user_id', 'username', 'jti'} on success or None.
        """
        payload = self._decode_token(token, token_type='refresh',
                                     secret_override=self._get_refresh_secret_key())
        if not payload:
            return None

        jti = payload.get('jti')
        if jti and self.env['lugal.jwt.blacklist'].sudo().is_revoked(jti):
            _logger.warning('lugal_auth: refresh token jti=%s is revoked', jti)
            return None

        user = self.env['res.users'].sudo().browse(payload['user_id'])
        if not user.exists():
            return None

        return {'user_id': user.id, 'username': user.login, 'jti': jti}

    # ------------------------------------------------------------------
    # Login / refresh / logout
    # ------------------------------------------------------------------

    @api.model
    def authenticate_user(self, username, password):
        """
        Validate credentials and return tokens + basic user info.

        Returns a response dict on success or None on failure.
        """
        try:
            credential = {
                'type':     'password',
                'login':    username,
                'password': password,
            }
            auth_info = self.env['res.users'].sudo().authenticate(
                credential, user_agent_env={}
            )
            uid = auth_info.get('uid') if auth_info else None
            if not uid:
                return None

            user = self.env['res.users'].sudo().browse(uid)
            access_token  = self.generate_access_token(uid)
            refresh_token = self.generate_refresh_token(uid)

            return {
                'access_token':  access_token,
                'refresh_token': refresh_token,
                'token_type':    'bearer',
                'user': {
                    'id':       user.id,
                    'name':     user.name,
                    'username': user.login,
                    'email':    user.email,
                },
            }
        except Exception as exc:
            _logger.error('lugal_auth: authentication failed — %s', exc)
            return None

    @api.model
    def refresh_access_token(self, refresh_token):
        """Issue a new access token from a valid refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        return {
            'access_token': self.generate_access_token(payload['user_id']),
            'token_type':   'bearer',
        }

    @api.model
    def revoke_token(self, token, reason='logout'):
        """
        Revoke an access OR refresh token immediately by blacklisting its jti.

        Decodes WITHOUT blacklist check first so we can extract the jti even if
        the token is about to be revoked.  Returns True on success.
        """
        # Try access key first, then refresh key
        payload = self._decode_raw(token, self._get_secret_key())
        if not payload:
            payload = self._decode_raw(token, self._get_refresh_secret_key())
        if not payload:
            return False

        jti = payload.get('jti')
        if not jti:
            _logger.warning('lugal_auth: token has no jti — cannot revoke')
            return False

        exp = payload.get('exp')
        expires_at = datetime.utcfromtimestamp(exp) if exp else None
        user_id    = payload.get('user_id')

        return self.env['lugal.jwt.blacklist'].sudo().revoke(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # Internal decode helpers
    # ------------------------------------------------------------------

    def _decode_token(self, token, token_type, secret_override=None):
        """
        Decode *token*, verify signature and type claim.
        Returns payload dict or None.  Does NOT check blacklist here.
        """
        secret = secret_override or self._get_secret_key()
        payload = self._decode_raw(token, secret)
        if not payload:
            return None
        if payload.get('type') != token_type:
            _logger.warning(
                'lugal_auth: wrong token type (got %s, expected %s)',
                payload.get('type'), token_type,
            )
            return None
        return payload

    @staticmethod
    def _decode_raw(token, secret):
        """
        Low-level JWT decode. Returns payload dict or None.
        Never raises — all exceptions are caught and logged.
        """
        try:
            return jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            _logger.warning('lugal_auth: token expired')
            return None
        except jwt.InvalidTokenError as exc:
            _logger.debug('lugal_auth: invalid token — %s', exc)
            return None
