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


def _folder_role(folder):
    value = (folder or 'inbox').strip().lower()
    return value if value in {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'} else 'custom'


def _build_message_preview(record):
    """
    Build a complete inbox-ready message dict from an ORM record.

    This mirrors the shape of _message_to_dict() in email_controller so the FE
    can immediately prepend the new message to the inbox list without a
    follow-up /api/lugal/email/messages call.  Attachments are omitted from
    the preview (body_fetched=False for IMAP-synced headers-only messages) and
    can be fetched lazily via message_detail when the user opens the email.
    """
    try:
        atts = record.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', record.id),
        ])
        attachments = []
        inline_attachments = []
        cid_prefix = '__inline_cid__:'
        for a in atts:
            item = {
                'id':       a.id,
                'name':     a.name or 'attachment',
                'mimetype': a.mimetype or 'application/octet-stream',
                'size':     a.file_size or 0,
                'inline':   False,
            }
            desc = a.description or ''
            if desc.startswith(cid_prefix):
                cid_value = desc[len(cid_prefix):].strip()
                item['inline'] = True
                item['cid'] = f'cid:{cid_value}'
                item['content_id'] = cid_value
                inline_attachments.append(item)
            else:
                attachments.append(item)
    except Exception:
        attachments = []
        inline_attachments = []

    return {
        'id':             record.id,
        'account_id':     record.account_id.id,
        'folder':         record.folder,
        'folder_role':    _folder_role(record.folder),
        'subject':        record.subject or '(no subject)',
        'from_name':      record.from_name or '',
        'from_address':   record.from_address or '',
        'to_addresses':   record.to_addresses or '[]',
        'cc_addresses':   record.cc_addresses or '[]',
        'date':           _to_riyadh_iso(record.date),
        'received_at':    _to_riyadh_iso(record.create_date),
        'read_at':        _to_riyadh_iso(record.read_at) if record.read_at else None,
        'is_read':        record.is_read,
        'is_starred':     record.is_starred,
        'is_flagged':     record.is_flagged,
        'is_important':   record.is_important,
        'written_in_arabic': bool(getattr(record, 'written_in_arabic', False)),
        'is_draft':       record.is_draft,
        'smtp_delivered': record.smtp_delivered,
        'smtp_error':     record.smtp_error or None,
        'smtp_status':    record.smtp_status or 'pending',
        'version':        _to_riyadh_iso(record.write_date),
        'write_date':     _to_riyadh_iso(record.write_date),
        'body_fetched':   bool(getattr(record, 'body_fetched', False)),
        'attachments':    attachments,
        'inline_attachments': inline_attachments,
        'crm_links': {
            'customer': None,
            'ticket':   None,
        },
    }


def _notification_folder_domain():
    """Unread mail that should affect email badges/notifications.

    Includes inbox and custom rule folders such as INBOX.syed_naqvi and
    INBOX.syed_naqvi.Important.  Excludes outbound/system folders that should
    not increment the "new email" bell count.
    """
    return [
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
    ]


class LugalEmailMessageWs(models.Model):
    """
    Wire new inbox email arrivals to the Odoo bus so the FE WebSocket client
    receives a real-time push with the FULL message payload.

    The payload now includes a `message_data` key with the complete inbox-row
    dict so the FE can immediately prepend the new message to the inbox list
    without a follow-up /api/lugal/email/messages call.  This eliminates the
    race condition where the inbox API was called before the DB committed the
    new message, causing the FE to show stale (old) inbox data.
    """
    _inherit = 'lugal.email.message'

    def _lugal_send_new_email_notification(self):
        """Push realtime notification after the message reaches its final folder."""
        for record in self:
            try:
                record.invalidate_recordset()
            except Exception:
                pass
            record = record.sudo().exists()
            if not record or record.is_deleted or not record.active:
                continue

            if (
                not record.is_read
                and (record.folder or '') not in ('sent', 'drafts', 'trash', 'spam')
            ):
                uid = (
                    record.account_id.user_id.id
                    if record.account_id and record.account_id.user_id
                    else None
                )
                if uid:
                    try:
                        unread_count = self.sudo().search_count([
                            ('account_id', '=', record.account_id.id),
                            ('is_read',    '=', False),
                            ('is_deleted', '=', False),
                        ] + _notification_folder_domain())
                        # Full message dict so the FE can update the inbox list
                        # immediately without calling messages_list again.
                        message_data = _build_message_preview(record)
                        payload = {
                            'message_id':   record.id,
                            'account_id':   record.account_id.id,
                            'mailbox':      record.folder or 'inbox',
                            'folder':       record.folder or 'inbox',
                            'folder_role':  _folder_role(record.folder),
                            'subject':      record.subject or '(no subject)',
                            'from_name':    record.from_name or '',
                            'from_address': record.from_address or '',
                            'from':         record.from_address or '',
                            'received_at':  _to_riyadh_iso(record.date),
                            'unread_count': unread_count,
                            'uid':          uid,
                            'version':      _to_riyadh_iso(record.write_date),
                            # Full row — FE should prepend this to the correct
                            # mailbox/folder using message_data.folder.
                            'message_data': message_data,
                        }
                        _logger.info(
                            '[EmailWS] bus._sendone uid=%s channel=supply_user.%s '
                            'message_id=%s folder=%s at %.3f',
                            uid, uid, record.id, record.folder, time.time(),
                        )
                        self.env['bus.bus'].sudo()._sendone(
                            f'supply_user.{uid}',
                            'crm.email.message.new',
                            payload,
                        )
                    except Exception as exc:
                        _logger.debug(
                            'lugal_email_ws: bus notify error uid=%s: %s', uid, exc,
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
                                'type':       'email',
                                'message_id': record.id,
                                'account_id': record.account_id.id,
                                'folder':     record.folder or 'inbox',
                                'url':        '/emails',
                            },
                        )
                    except Exception:
                        pass

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('lugal_email_defer_new_message_ws'):
            records._lugal_send_new_email_notification()
        return records
