import logging

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request, SessionExpiredException
from odoo.service import security
import werkzeug.exceptions

_logger = logging.getLogger(__name__)


class LugalIrHttp(models.AbstractModel):
    """
    Override ir.http._authenticate_explicit to handle stale WS session cookies
    that were created before the session_token fix in ws_session.py.

    The old WS session bridge set session.uid but forgot session.session_token,
    leaving it as None.  Odoo's check_session calls consteq(expected_str, None)
    which raises TypeError.  Without this patch, that TypeError bubbles up as
    AccessDenied → HTTP 403 for every HTTP-type route (notifications, ws/config,
    WebSocket) until the browser clears its cookies.

    With this patch we catch the TypeError and treat it like a failed session
    check: log out the stale session and continue — the JWT Bearer token in the
    Authorization header will still authenticate the request normally.
    """
    _name = 'ir.http'
    _inherit = 'ir.http'

    @classmethod
    def _authenticate_explicit(cls, auth):
        try:
            if request.session.uid is not None:
                session_valid = False
                try:
                    session_valid = security.check_session(
                        request.session, request.env, request
                    )
                except TypeError:
                    # session_token is None — stale session from old WS bridge.
                    # Treat as failed check: clear session and fall through to
                    # JWT Bearer auth below.
                    _logger.info(
                        'lugal_ws_migration: stale session (session_token=None) '
                        'for uid=%s — clearing and continuing',
                        request.session.uid,
                    )

                if not session_valid:
                    request.session.logout(keep_db=True)
                    request.env = api.Environment(
                        request.env.cr, None, request.session.context
                    )

            getattr(cls, f'_auth_method_{auth}')()

        except (AccessDenied, SessionExpiredException, werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info(
                'lugal_ws_migration: exception during authentication',
                exc_info=True,
            )
            raise AccessDenied()
# TODO: remove - cherry-pick marker
