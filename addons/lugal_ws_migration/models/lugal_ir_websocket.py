import logging
import time

from odoo import api, models
from odoo.http import SessionExpiredException
from odoo.service import security
from odoo.addons.bus.websocket import wsrequest

_logger = logging.getLogger(__name__)


class LugalIrWebsocket(models.AbstractModel):
    """
    Extends Odoo's native ir.websocket to:
      1. Override _authenticate to gracefully handle stale WS sessions
         (session_token=None) so the subscribe frame is never silently dropped.
         A TypeError from check_session now raises SessionExpiredException
         (WS close code 4001) so the frontend refreshes the session and reconnects.
      2. Detect mid-connection uid changes (login/logout of different user on the
         same browser session) and force SessionExpiredException so the WS
         reconnects with fresh channel subscriptions for the new user.
      3. Automatically subscribe each authenticated user to their supply chat,
         per-user, per-session, and stories channels when the WebSocket opens.
    """
    _name = 'ir.websocket'
    _inherit = 'ir.websocket'

    @classmethod
    def _authenticate(cls):
        """
        Override Odoo's WebSocket authentication to handle three cases:

        Case 1 — Stale session (session_token=None):
          TypeError from check_session → log + raise SessionExpiredException (4001)
          → FE calls _ensureSession() and reconnects.

        Case 2 — UID changed mid-connection (e.g. different user logged in on
          the same browser session, or logout then login):
          The session store shows a different uid than when this WS connection
          first authenticated. Raise SessionExpiredException (4001) so the WS
          closes and the FE reconnects — the new connection's _build_bus_channel_list
          subscribes to the correct channels for the new user.

        Case 3 — Logout (uid becomes None on a previously authenticated connection):
          The WS was open for uid=X. The HTTP logout endpoint set session.uid=None.
          Raise SessionExpiredException (4001) so the WS closes cleanly.
          FE's _handleClose(4001) calls _ensureSession() → gets 401 (JWT revoked)
          → shows login screen.
        """
        # ws_obj persists for the lifetime of this WebSocket connection.
        # We attach _authenticated_uid to track the uid at first authentication.
        ws_obj = getattr(wsrequest, 'ws', None)

        current_uid = wsrequest.session.uid

        if current_uid is not None:
            session_valid = False
            try:
                session_valid = security.check_session(
                    wsrequest.session, wsrequest.env, wsrequest
                )
            except TypeError:
                _logger.info(
                    '[WS] Stale session (session_token=None) for uid=%s — forcing re-auth',
                    current_uid,
                )
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()

            if not session_valid:
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()

            # ── UID-change detection ───────────────────────────────────────
            # Store the uid on first successful authentication for this WS
            # connection.  If it changes on a later frame (e.g. different user
            # logged in using the same browser session cookie) we force close.
            if ws_obj is not None:
                initial_uid = getattr(ws_obj, '_authenticated_uid', None)
                if initial_uid is None:
                    # First successful auth — record it.
                    ws_obj._authenticated_uid = current_uid
                    _logger.info(
                        '[WS] Connection authenticated: uid=%s session=%s',
                        current_uid, wsrequest.session.sid[:8],
                    )
                elif initial_uid != current_uid:
                    # UID changed (different user re-used this session cookie).
                    # Close the stale connection so the new session opens a fresh
                    # WS with correct channel subscriptions.
                    _logger.info(
                        '[WS] UID changed %s → %s on session %s — forcing reconnect '
                        '(channels would be stale)',
                        initial_uid, current_uid, wsrequest.session.sid[:8],
                    )
                    raise SessionExpiredException()

        else:
            # uid is None — either anonymous connection or a logged-out session.
            if ws_obj is not None and getattr(ws_obj, '_authenticated_uid', None) is not None:
                # This connection WAS authenticated (uid was recorded).  Now the
                # session shows uid=None → the HTTP logout endpoint was called.
                # Force close so the FE can handle the logout state.
                _logger.info(
                    '[WS] Session logged out for uid=%s — closing WS (code 4001)',
                    ws_obj._authenticated_uid,
                )
                raise SessionExpiredException()

            # Genuinely anonymous or never-authenticated connection — allow as public.
            public_user = wsrequest.env.ref('base.public_user')
            wsrequest.update_env(user=public_user.id)

    def _build_bus_channel_list(self, channels):
        result = super()._build_bus_channel_list(channels)
        uid = self.env.uid

        # Only add custom channels for real authenticated users
        try:
            public_uid = self.env.ref('base.public_user').id
        except Exception:
            public_uid = None

        if not uid or uid == public_uid:
            return result

        # All active supply chat conversations this user participates in
        try:
            Conv = self.env['lugal.supply.conversation'].sudo()
            convs = Conv.search([
                ('is_archived', '=', False),
                ('participant_ids', 'in', [uid]),
            ])
            for conv in convs:
                result.append(f'supply_chat.{conv.id}')
        except Exception as exc:
            _logger.warning(
                '_build_bus_channel_list: failed to fetch conversations for uid=%s: %s',
                uid, exc
            )

        # Per-user private channel (email notifications, delivery receipts, etc.)
        result.append(f'supply_user.{uid}')

        # Per-session channel: used for session-specific signals (force_close,
        # reconnect_required) so only THIS browser's WS receives them and not
        # every tab that the same user has open.
        try:
            session_sid = wsrequest.session.sid
            result.append(f'supply_session.{session_sid}')
        except Exception:
            pass

        # Global stories broadcast channel
        result.append('supply_stories')

        # CRM marquee / announcements broadcast — all authenticated users
        result.append('crm_broadcast')

        # CRM presence updates — all authenticated users
        result.append('crm_presence')

        _logger.debug(
            '[WS] Channel list built for uid=%s at %.3f (%d channels)',
            uid, time.time(), len(result),
        )
        return result
# TODO: remove - cherry-pick marker
