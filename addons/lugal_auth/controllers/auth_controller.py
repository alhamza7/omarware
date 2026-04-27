# -*- coding: utf-8 -*-

import logging
import secrets
import time
from odoo import http
from odoo.http import request, root
from odoo.service.security import compute_session_token

_logger = logging.getLogger(__name__)

_RESET_TOKEN_TTL = 3600          # 1 hour before the link expires
_RESET_PARAM_PREFIX = 'lugal.pwd.reset.'

_WS_SESSION_MAX_AGE = 86400  # 24 h — matches ws_session.py


def _attach_ws_session(uid):
    """Create an Odoo session for *uid* and inject a Set-Cookie into the response.

    Called from login and refresh so the browser receives the session_id cookie
    in the same HTTP response that returns the JWT tokens.  The WebSocket can
    then be opened immediately — no separate POST /api/crm/ws/session call needed.

    Returns the session SID string on success, or None if session setup fails
    (tokens are still valid; the FE can fall back to /api/crm/ws/session).
    """
    try:
        session = request.session
        session.uid   = uid
        session.db    = request.db or request.httprequest.headers.get('X-Odoo-Database')
        session.login = request.env['res.users'].sudo().browse(uid).login
        session.session_token = compute_session_token(session, request.env)
        session.can_save = True
        session.touch()
        root.session_store.save(session)
        return session.sid
    except Exception as exc:
        _logger.warning('_attach_ws_session failed for uid=%s: %s', uid, exc)
        return None


class LugalAuthController(http.Controller):
    """
    Centralized login, refresh, and logout endpoints for the Lugal suite.

    POST /lugal/auth/login    — obtain tokens + WS session cookie (rate-limited per username+IP)
    POST /lugal/auth/refresh  — renew access token + WS session cookie
    POST /lugal/auth/logout   — revoke current token immediately
    """

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/login', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        """
        Authenticate with username + password and return JWT tokens.

        Params: username (str), password (str), remember_me (bool, optional)
        Response: access_token, refresh_token, token_type, user, ws_session_id

        The response also carries a Set-Cookie: session_id=... header so the
        browser has the Odoo session cookie ready for the WebSocket upgrade
        immediately — no separate POST /api/crm/ws/session call is required.

        When remember_me is True a long-lived refresh token (30 days) is issued
        instead of the default 7-day one.  The access-token lifetime is unchanged.
        """
        try:
            username   = (kwargs.get('username') or '').strip()
            password   = kwargs.get('password') or ''
            remember_me = bool(kwargs.get('remember_me', False))

            if not username or not password:
                return {'success': False, 'error': 'username and password are required'}

            dbname = getattr(request, 'db', None) or \
                     request.httprequest.headers.get('X-Odoo-Database')
            if not dbname:
                return {'success': False, 'error': 'Database not specified'}

            rate_limiter = request.env['lugal.auth.rate.limit'].sudo()

            client_ip  = request.httprequest.remote_addr or 'unknown'
            identifier = f'{username}:{client_ip}'

            if rate_limiter.is_locked(identifier):
                _logger.warning('lugal_auth: login blocked for %s (rate limit)', identifier)
                return {
                    'success': False,
                    'error':   'Too many failed attempts. Please try again later.',
                }

            result = request.env['lugal.jwt.service'].sudo().authenticate_user(
                username, password, remember_me=remember_me
            )

            if not result:
                locked = rate_limiter.record_failure(identifier)
                msg = ('Too many failed attempts. Please try again later.'
                       if locked else 'Invalid credentials')
                return {'success': False, 'error': msg}

            rate_limiter.record_success(identifier)

            # Create WS session — browser receives Set-Cookie in this same response
            uid = result['user']['id']
            ws_sid = _attach_ws_session(uid)
            if ws_sid:
                result['ws_session_id'] = ws_sid

            # Wake the IMAP IDLE supervisor immediately so the user's inbox
            # watcher starts without waiting for the 5-second watchdog cycle.
            # Non-fatal: tokens are already valid if this fails.
            try:
                request.env['lugal.email.idle.watcher'].sudo().start_all()
            except Exception as exc_imap:
                _logger.warning('login: start_all() failed: %s', exc_imap)

            return {'success': True, 'data': result}

        except Exception as exc:
            _logger.error('lugal_auth login error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Authentication error'}

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/refresh', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def refresh(self, **kwargs):
        """
        Exchange a refresh token for a new access token.

        Params: refresh_token (str)
        Response: access_token, token_type, ws_session_id

        Also sets a fresh Set-Cookie: session_id so the WS session stays alive
        after a token refresh (e.g. app wakes from background / tab reload).
        """
        try:
            refresh_token = kwargs.get('refresh_token') or ''
            if not refresh_token:
                return {'success': False, 'error': 'refresh_token is required'}

            result = request.env['lugal.jwt.service'].sudo().refresh_access_token(
                refresh_token
            )
            if not result:
                return {'success': False, 'error': 'Invalid or expired refresh token'}

            # Re-attach WS session for the refreshed user
            uid = result.get('user_id')
            if uid:
                ws_sid = _attach_ws_session(uid)
                if ws_sid:
                    result['ws_session_id'] = ws_sid

            return {'success': True, 'data': result}

        except Exception as exc:
            _logger.error('lugal_auth refresh error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Token refresh error'}

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/logout', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def logout(self, **kwargs):
        """
        Revoke the current access token immediately.

        The token is extracted from the Authorization: Bearer header.
        After logout the token is blacklisted — further requests with it
        will receive 401 Unauthorized.

        Params: (none — token is read from header)
        Response: { success: true }
        """
        try:
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {'success': False, 'error': 'No Bearer token in Authorization header'}

            token = auth_header.split(' ', 1)[1]
            request.env['lugal.jwt.service'].sudo().revoke_token(token, reason='logout')
            return {'success': True, 'data': {'message': 'Logged out successfully'}}

        except Exception as exc:
            _logger.error('lugal_auth logout error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Logout error'}

    # ------------------------------------------------------------------
    # Forgot password — request a reset link
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/forgot-password', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def forgot_password(self, **kwargs):
        """
        Request a password-reset e-mail.

        Params:
          email_or_username (str, required) — registered e-mail address or system login
          fe_url            (str, optional) — base URL of the frontend app
                            e.g. "http://192.168.1.10:5173"
                            When supplied it is persisted as lugal.frontend.base.url so all
                            future reset links use the same origin automatically.

        Response: { success: true, data: { message: "..." } }

        Always returns success=true even when the account is not found so that
        callers cannot enumerate valid e-mail addresses.
        """
        try:
            email_or_username = (kwargs.get('email_or_username') or '').strip()
            fe_url            = (kwargs.get('fe_url')            or '').strip().rstrip('/')

            if not email_or_username:
                return {'success': False, 'error': 'email_or_username is required'}

            ICP   = request.env['ir.config_parameter'].sudo()
            Users = request.env['res.users'].sudo()
            user  = None

            # Persist the supplied fe_url so future resets pick it up automatically
            if fe_url:
                ICP.set_param('lugal.frontend.base.url', fe_url)

            # Try matching against e-mail first, then system login
            if '@' in email_or_username:
                user = Users.search([('email', '=ilike', email_or_username), ('active', '=', True)], limit=1)
            if not user:
                user = Users.search([('login', '=', email_or_username), ('active', '=', True)], limit=1)
            if not user:
                user = Users.search([('email', '=ilike', email_or_username), ('active', '=', True)], limit=1)

            # Always respond the same way — do not leak whether the account exists
            generic_msg = 'If that account exists, a password-reset link has been sent to the registered e-mail.'

            if not user or not user.email:
                return {'success': True, 'data': {'message': generic_msg}}

            # Generate a cryptographically secure token and store it with expiry
            token     = secrets.token_urlsafe(40)
            param_key = _RESET_PARAM_PREFIX + token
            expires   = int(time.time()) + _RESET_TOKEN_TTL
            ICP.set_param(param_key, f'{user.id}:{expires}')

            # Build the reset URL:
            # Priority: fe_url (this request) > lugal.frontend.base.url (saved) > web.base.url (fallback)
            base = (
                fe_url
                or ICP.get_param('lugal.frontend.base.url')
                or ICP.get_param('web.base.url')
                or ''
            ).rstrip('/')
            reset_url = f'{base}/reset-password?token={token}'

            # Send via the user's own email account (if they have one),
            # otherwise fall back to any active account in the system.
            LugalAcc = request.env['lugal.email.account'].sudo()
            sender_acc = (
                LugalAcc.search([
                    ('user_id', '=', user.id),
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ], order='is_default desc', limit=1)
                or LugalAcc.search([
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ], order='is_default desc', limit=1)
            )

            if not sender_acc:
                _logger.warning('forgot_password: no email account available for sending — uid=%s', user.id)
                return {'success': True, 'data': {'message': generic_msg}}

            subject   = 'Password Reset Request'
            body_html = f"""<p>Hello {user.name},</p>
<p>We received a request to reset your password. Click the link below to set a new password:</p>
<p style="margin:16px 0"><a href="{reset_url}" style="background:#1a56db;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">Reset Password</a></p>
<p>Or copy this link into your browser:<br/><a href="{reset_url}">{reset_url}</a></p>
<p>This link expires in <strong>1 hour</strong>.</p>
<p>If you did not request this, you can safely ignore this e-mail.</p>"""
            body_text = (
                f"Hello {user.name},\n\n"
                f"Reset your password using this link:\n{reset_url}\n\n"
                f"This link expires in 1 hour.\n"
                f"If you did not request this, ignore this email."
            )

            # Import the working SMTP helper from the email controller
            from odoo.addons.lugal_email.controllers.email_controller import _send_via_smtp

            delivered, smtp_err, _ = _send_via_smtp(
                sender_acc, [user.email], subject, body_html, body_text
            )

            if not delivered:
                # Primary account failed — try every other active account until one works
                _logger.warning(
                    'forgot_password: primary SMTP failed for uid=%s (%s), trying fallback accounts',
                    user.id, smtp_err,
                )
                for fallback in LugalAcc.search([
                    ('id', '!=', sender_acc.id),
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ], order='is_default desc', limit=10):
                    delivered, smtp_err, _ = _send_via_smtp(
                        fallback, [user.email], subject, body_html, body_text
                    )
                    if delivered:
                        sender_acc = fallback
                        break

            if delivered:
                _logger.info('forgot_password: reset link sent to uid=%s email=%s via acc=%s',
                             user.id, user.email, sender_acc.email_address)
            else:
                _logger.error('forgot_password: all SMTP accounts failed for uid=%s: %s',
                              user.id, smtp_err)

            return {'success': True, 'data': {'message': generic_msg}}

        except Exception as exc:
            _logger.error('lugal_auth forgot_password error: %s', exc, exc_info=True)
            # Still return success to avoid leaking info
            return {'success': True, 'data': {'message': 'If that account exists, a password-reset link has been sent to the registered e-mail.'}}

    # ------------------------------------------------------------------
    # Reset password — validate token and set new password
    # ------------------------------------------------------------------

    @http.route('/lugal/auth/reset-password', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def reset_password(self, **kwargs):
        """
        Set a new password using a valid reset token.

        Params:
          token            (str) — from the e-mail link query-string
          new_password     (str) — desired new password
          confirm_password (str) — must match new_password

        Response: { success: true, data: { message: "Password updated." } }
        """
        try:
            token            = (kwargs.get('token')            or '').strip()
            new_password     = (kwargs.get('new_password')     or '').strip()
            confirm_password = (kwargs.get('confirm_password') or '').strip()

            if not token:
                return {'success': False, 'error': 'Reset token is required'}
            if not new_password:
                return {'success': False, 'error': 'new_password is required'}
            if new_password != confirm_password:
                return {'success': False, 'error': 'Passwords do not match'}
            if len(new_password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}

            ICP       = request.env['ir.config_parameter'].sudo()
            param_key = _RESET_PARAM_PREFIX + token
            stored    = ICP.get_param(param_key) or ''

            if not stored:
                return {'success': False, 'error': 'Invalid or expired reset link'}

            parts = stored.split(':')
            if len(parts) != 2:
                return {'success': False, 'error': 'Invalid reset token format'}

            uid_str, expires_str = parts
            try:
                uid     = int(uid_str)
                expires = int(expires_str)
            except ValueError:
                return {'success': False, 'error': 'Invalid reset token'}

            if int(time.time()) > expires:
                ICP.set_param(param_key, '')  # clean up
                return {'success': False, 'error': 'Reset link has expired. Please request a new one.'}

            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return {'success': False, 'error': 'Account not found'}

            # Update password and invalidate the token
            user.write({'password': new_password})
            ICP.set_param(param_key, '')   # one-time use — delete after use

            # Blacklist all existing tokens for this user so old sessions are forced to re-login
            try:
                request.env['lugal.jwt.blacklist'].sudo().search(
                    [('user_id', '=', uid), ('revoked', '=', False)]
                ).write({'revoked': True, 'reason': 'password_reset'})
            except Exception:
                pass

            _logger.info('reset_password: password updated for uid=%s', uid)
            return {'success': True, 'data': {'message': 'Password updated successfully. You can now log in with your new password.'}}

        except Exception as exc:
            _logger.error('lugal_auth reset_password error: %s', exc, exc_info=True)
            return {'success': False, 'error': 'Password reset failed'}
