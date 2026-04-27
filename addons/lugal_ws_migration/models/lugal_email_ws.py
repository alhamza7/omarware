import logging
import time
from datetime import timedelta, timezone

from odoo import api, models

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


class LugalEmailMessageWs(models.Model):
    """
    Phase 4: Wire new inbox email arrivals to the Odoo bus so that the
    FE WebSocket client receives a real-time push notification instead
    of relying on HTTP polling.

    Additive only — zero changes to addons/lugal_email/. This model
    inherits lugal.email.message and overrides create() only.

    Field names (verified against lugal.email.message):
      - record.folder          — 'inbox' | 'sent' | 'drafts' | 'trash'
      - record.is_read         — Boolean
      - record.account_id      — lugal.email.account record
      - record.account_id.user_id.id — the res.users uid who owns the account
      - record.from_address    — sender email address string
      - record.from_name       — sender display name string
      - record.subject         — email subject string
      - record.date            — datetime of email
    """
    _inherit = 'lugal.email.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Only push notifications for unread inbox messages
            if record.folder == 'inbox' and not record.is_read:
                uid = (
                    record.account_id.user_id.id
                    if record.account_id and record.account_id.user_id
                    else None
                )
                if uid:
                    try:
                        # Count unread inbox messages for this account now that
                        # the new message is persisted — gives the FE an accurate
                        # badge count without a separate API call.
                        unread_count = self.sudo().search_count([
                            ('account_id', '=', record.account_id.id),
                            ('folder',     '=', 'inbox'),
                            ('is_read',    '=', False),
                            ('is_deleted', '=', False),
                        ])
                        payload = {
                            'message_id':   record.id,
                            'account_id':   record.account_id.id,
                            'mailbox':      'INBOX',
                            'subject':      record.subject or '(no subject)',
                            'from_name':    record.from_name or '',
                            'from_address': record.from_address or '',
                            'from':         record.from_address or '',
                            'received_at':  _to_riyadh_iso(record.date),
                            'unread_count': unread_count,
                            'uid':          uid,
                        }
                        _logger.info(
                            '[EmailWS] Calling bus._sendone for uid=%s '
                            'channel=supply_user.%s at %.3f',
                            uid, uid, time.time(),
                        )
                        self.env['bus.bus'].sudo()._sendone(
                            f'supply_user.{uid}',
                            'crm.email.message.new',
                            payload,
                        )
                        _logger.info(
                            '[EmailWS] bus._sendone returned at %.3f '
                            '(uid=%s message_id=%s)',
                            time.time(), uid, record.id,
                        )
                    except Exception as exc:
                        # Non-fatal — email is saved regardless
                        _logger.debug(
                            'lugal_email_ws: bus notify error for uid=%s: %s',
                            uid, exc
                        )
                    # Web Push — deliver even when browser tab is closed
                    try:
                        sender_label = record.from_name or record.from_address or 'New Email'
                        subject = record.subject or '(no subject)'
                        self.env['lugal.push.subscription'].sudo().send_push_to_user(
                            uid,
                            title=sender_label,
                            body=subject,
                            data={
                                'type': 'email',
                                'message_id': record.id,
                                'account_id': record.account_id.id,
                                'url': '/emails',
                            },
                        )
                    except Exception:
                        pass
        return records
