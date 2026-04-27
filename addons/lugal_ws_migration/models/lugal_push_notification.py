# -*- coding: utf-8 -*-
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LugalPushSubscription(models.Model):
    _name = 'lugal.push.subscription'
    _description = 'Browser Web Push Subscription'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        ondelete='cascade',
        index=True,
    )
    endpoint = fields.Char(required=True, index=True)
    auth_key = fields.Char(string='Auth Key')
    p256dh_key = fields.Char(string='P256DH Key')
    user_agent = fields.Char()
    active = fields.Boolean(default=True)
    created_at = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('endpoint_unique', 'unique(endpoint)', 'Push endpoint must be unique.'),
    ]

    @api.model
    def send_push_to_user(self, user_id, title, body, data=None):
        """Send a Web Push notification to every active browser subscription for a user.

        Called from bus event publishers (new chat message, new email, etc.) so that
        users with a closed/backgrounded browser tab still receive a system notification.
        """
        subscriptions = self.search([
            ('user_id', '=', user_id),
            ('active', '=', True),
        ])
        if not subscriptions:
            return
        for sub in subscriptions:
            try:
                sub._do_send(title, body, data or {})
            except Exception as exc:
                _logger.warning(
                    'Push send failed uid=%s endpoint=%s: %s',
                    user_id, (sub.endpoint or '')[:60], exc,
                )

    def _do_send(self, title, body, data):
        """Low-level: send a single push notification to this subscription."""
        self.ensure_one()
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            _logger.warning(
                'pywebpush is not installed — push notifications disabled. '
                'Install it with: pip install pywebpush'
            )
            return

        ICP = self.env['ir.config_parameter'].sudo()
        private_key = ICP.get_param('lugal.push.vapid.private_key', '').strip()
        vapid_email = ICP.get_param('lugal.push.vapid.email', 'admin@example.com').strip()

        if not private_key:
            _logger.warning(
                'VAPID private key not configured. '
                'Run the "Generate VAPID Keys" server action or set '
                'lugal.push.vapid.private_key in ir.config_parameter.'
            )
            return

        payload = json.dumps({
            'title': title,
            'body': body,
            'data': data,
        })

        subscription_info = {
            'endpoint': self.endpoint,
            'keys': {
                'auth': self.auth_key or '',
                'p256dh': self.p256dh_key or '',
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={'sub': f'mailto:{vapid_email}'},
                content_encoding='aes128gcm',
            )
        except WebPushException as exc:
            response = getattr(exc, 'response', None)
            status = response.status_code if response is not None else None
            if status in (404, 410):
                # The subscription is gone (browser cleared it) — deactivate
                self.sudo().write({'active': False})
                _logger.info(
                    'Push subscription expired (HTTP %s) for uid=%s — deactivated',
                    status, self.user_id.id,
                )
            else:
                raise
