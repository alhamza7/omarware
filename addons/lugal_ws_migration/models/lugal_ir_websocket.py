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
      2. Automatically subscribe each authenticated user to their supply chat,
         per-user, and stories channels when the WebSocket connection opens.
    """
    _name = 'ir.websocket'
    _inherit = 'ir.websocket'

    @classmethod
    def _authenticate(cls):
        """
        Override Odoo's WebSocket authentication to handle stale sessions.

        The original raises an uncaught TypeError when session.session_token is
        None (sessions created before the compute_session_token fix in ws_session.py).
        That TypeError is swallowed by websocket.py's except-Exception handler,
        leaving the socket open but subscribed to ZERO channels — no events ever arrive.

        This override catches the TypeError, logs it as INFO (not ERROR), clears
        the stale session, and raises SessionExpiredException so Odoo closes the
        WebSocket with code 4001.  The frontend's _handleClose(4001) branch then
        calls _ensureSession() (POST /api/crm/ws/session) to obtain a fresh session
        and reconnects.
        """
        if wsrequest.session.uid is not None:
            session_valid = False
            try:
                session_valid = security.check_session(
                    wsrequest.session, wsrequest.env, wsrequest
                )
            except TypeError:
                _logger.info(
                    '_authenticate: stale WS session (session_token=None) '
                    'for uid=%s — forcing re-auth',
                    wsrequest.session.uid,
                )
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()

            if not session_valid:
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()
        else:
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

        # Per-user private channel (delivery/read receipts, resubscribe signals)
        result.append(f'supply_user.{uid}')

        # Global stories broadcast channel
        result.append('supply_stories')

        _logger.info(
            '[WS] Channel list built for uid=%s at %.3f: %s',
            uid, time.time(), result,
        )
        return result
