# -*- coding: utf-8 -*-
"""
Backward-compatible /web/bus/poll endpoint for Odoo 19.

Odoo 19 replaced long-polling with a WebSocket-based system (/websocket).
Custom frontends (like NBS-CRM) that still call the old /web/bus/poll endpoint
receive a proper response from this shim controller, which delegates to the
same bus.bus._poll() model method.

Old request format  (still accepted):
    POST /web/bus/poll
    Body (JSON-RPC): { "channels": [...], "last": N }

Old response format (returned):
    { "result": [{"id": N, "message": {...}}, ...] }
"""

import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BusPollCompatController(http.Controller):
    """Provides /web/bus/poll for frontends that haven't migrated to WebSocket."""

    @http.route('/web/bus/poll', type='jsonrpc', auth='public', csrf=False,
                methods=['POST'], cors='*')
    def bus_poll(self, channels=None, last=0, options=None, **kwargs):
        """
        Accept legacy long-poll requests and service them via bus.bus._poll().

        Parameters (JSON-RPC params):
            channels  – list of channel identifiers (strings, lists, or dicts)
            last      – last notification id the client received (0 = first poll)
            options   – optional dict (ignored, kept for forward compat)

        Returns a list of notification objects:
            [{"id": <int>, "message": <dict>}, ...]
        """
        try:
            if channels is None:
                channels = []

            db = request.db
            if not db:
                return []

            # Import bus utilities using Odoo's module path
            from odoo.addons.bus.models.bus import channel_with_db

            channels_with_db = [
                channel_with_db(db, c) for c in (channels or [])
            ]

            try:
                last_id = int(last or 0)
            except (ValueError, TypeError):
                last_id = 0

            notifications = request.env['bus.bus'].sudo()._poll(
                channels_with_db, last_id
            )
            return notifications

        except Exception as e:
            _logger.exception('bus_poll compat error: %s', e)
            return []
