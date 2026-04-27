# -*- coding: utf-8 -*-
"""
Supply Chat API — all conversation, message, typing and bus_channels endpoints.

Routes (all JSON-RPC POST):
  /api/crm/supply/conversations/list
  /api/crm/supply/conversations/create
  /api/crm/supply/conversations/<id>/get
  /api/crm/supply/conversations/<id>/rename
  /api/crm/supply/conversations/<id>/archive
  /api/crm/supply/conversations/<id>/leave
  /api/crm/supply/conversations/<id>/update
  /api/crm/supply/conversations/<id>/mark_read
  /api/crm/supply/conversations/<id>/typing
  /api/crm/supply/conversations/<id>/members/list
  /api/crm/supply/conversations/<id>/members/add
  /api/crm/supply/conversations/<id>/members/remove
  /api/crm/supply/conversations/<id>/members/role    (stub — no role field yet)
  /api/crm/supply/messages/list
  /api/crm/supply/messages/create
  /api/crm/supply/messages/forward
  /api/crm/supply/messages/search
  /api/crm/supply/messages/<id>/edit
  /api/crm/supply/messages/<id>/react
  /api/crm/supply/messages/<id>/delivered
  /api/crm/supply/messages/<id>/read
  /api/crm/supply/chat/bus_channels
"""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone

from odoo import http, fields as odoo_fields
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .upload_controller import _build_attachment_url

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timezone helper — all API timestamps in Asia/Riyadh (UTC+3, no DST)
# ---------------------------------------------------------------------------
_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields, so we guard for both."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


# ---------------------------------------------------------------------------
# Per-process typing timers: (uid, conv_id) → threading.Timer
# ---------------------------------------------------------------------------
_typing_timers: dict = {}
_typing_lock = threading.Lock()
_TYPING_EXPIRE_SECS = 8


# ===========================================================================
# Helpers
# ===========================================================================

def _bus_publish(channel: str, event_type: str, payload: dict):
    """Publish one bus notification; swallows exceptions so it never crashes a handler."""
    try:
        request.env['bus.bus'].sudo()._sendone(channel, event_type, payload)
    except Exception as exc:
        _logger.warning('bus_publish failed (%s %s): %s', channel, event_type, exc)


def _user_avatar_url(user):
    if not user or not user.id:
        return None
    return f'/web/image/res.users/{user.id}/avatar_128'


def _serialize_participant(user):
    return {
        'id': user.id,
        'name': user.name or '',
        'avatar': _user_avatar_url(user),
    }


def _unread_count_for(conv, uid):
    """Messages in conv sent by others that the caller has not read."""
    Msg = request.env['lugal.supply.message'].sudo()
    return Msg.search_count([
        ('conversation_id', '=', conv.id),
        ('sender_id', '!=', uid),
        ('read_user_ids', 'not in', [uid]),
        ('is_deleted', '=', False),
        ('hidden_user_ids', 'not in', [uid]),
    ])


def _serialize_conversation(conv, uid):
    participants = conv.participant_ids
    # Determine the current user's role in the group
    creator_id = conv.created_by_id.id if conv.created_by_id else None
    admin_ids = []
    supervisor_ids = []
    if conv.type == 'group':
        admin_ids = conv.group_admin_ids.ids if hasattr(conv, 'group_admin_ids') else []
        supervisor_ids = conv.group_supervisor_ids.ids if hasattr(conv, 'group_supervisor_ids') else []

    is_creator = (uid == creator_id)
    is_admin = is_creator or (uid in admin_ids)
    is_supervisor = (uid in supervisor_ids)

    role = 'admin' if is_admin else ('supervisor' if is_supervisor else 'member')

    return {
        'id': conv.id,
        'type': conv.type,
        'name': conv.name or '',
        'participant_ids': participants.ids,
        'participants': [_serialize_participant(u) for u in participants],
        'last_activity': _to_riyadh_iso(conv.last_activity),
        'is_archived': conv.is_archived,
        'unread_count': _unread_count_for(conv, uid),
        'created_by_id': creator_id,
        # Group role fields (empty for dm/team)
        'group_admin_ids': admin_ids,
        'group_supervisor_ids': supervisor_ids,
        'only_admins_can_send': getattr(conv, 'only_admins_can_send', False),
        'group_description': getattr(conv, 'group_description', '') or '',
        'my_role': role,
        'is_admin': is_admin,
        'is_supervisor': is_supervisor,
    }


def _delivery_state_for(msg, uid):
    """
    Compute delivery_state string for a message as seen by `uid`.
    - If uid is NOT the sender: always 'received' (they can see it).
    - If uid IS the sender:
        'read'       if any other participant has read it
        'delivered'  if any other participant has it delivered (but not read)
        'sent'       otherwise
    """
    if msg.sender_id.id != uid:
        return 'received'
    other_read = [u for u in msg.read_user_ids if u.id != uid]
    if other_read:
        return 'read'
    other_delivered = [u for u in msg.delivered_user_ids if u.id != uid]
    if other_delivered:
        return 'delivered'
    return 'sent'


def _serialize_message(msg, uid):
    try:
        attachments = json.loads(msg.attachments_json or '[]')
    except Exception:
        attachments = []
    try:
        reactions = json.loads(msg.reactions_json or '{}')
    except Exception:
        reactions = {}

    reply_content = None
    reply_sender = None
    if msg.reply_to_id:
        reply_content = (msg.reply_to_id.content or '')[:200]
        reply_sender = msg.reply_to_id.sender_id.name if msg.reply_to_id.sender_id else None

    # Build read_receipts: list of {user_id, user_name, read_at}
    try:
        receipts_map = json.loads(msg.read_receipts_json or '{}')
    except Exception:
        receipts_map = {}
    # Include all users in read_user_ids, merging with timestamps where available
    read_receipts = []
    for ru in msg.read_user_ids:
        read_at = receipts_map.get(str(ru.id))
        read_receipts.append({
            'user_id': ru.id,
            'user_name': ru.name or f'User #{ru.id}',
            'read_at': read_at,  # ISO string or None
        })

    conv = msg.conversation_id
    return {
        'id': msg.id,
        'thread_id': conv.id if conv else None,
        'conversation_type': conv.type if conv else None,
        'sender_id': msg.sender_id.id if msg.sender_id else None,
        'sender_name': msg.sender_id.name if msg.sender_id else '',
        'sender_avatar': _user_avatar_url(msg.sender_id) if msg.sender_id else None,
        'participant_ids': conv.participant_ids.ids if conv else [],
        'content': msg.content or '',
        'kind': msg.kind or 'text',
        'duration_seconds': float(msg.duration_seconds or 0),
        'attachments': attachments,
        'created_at': _to_riyadh_iso(msg.create_date),
        'edited_at': _to_riyadh_iso(msg.edited_at),
        'reply_to_id': msg.reply_to_id.id if msg.reply_to_id else None,
        'reply_to_content': reply_content,
        'reply_to_sender': reply_sender,
        'reactions': reactions,
        'is_deleted': msg.is_deleted,
        'is_pinned': msg.is_pinned,
        'pinned_at': _to_riyadh_iso(msg.pinned_at),
        'pinned_by_id': msg.pinned_by_id.id if msg.pinned_by_id else None,
        'delivery_state': _delivery_state_for(msg, uid),
        'delivered_to': msg.delivered_user_ids.ids,
        'read_by': msg.read_user_ids.ids,
        'read_receipts': read_receipts,
        'client_message_id': msg.client_message_id or None,
    }


def _find_or_create_dm(uid, other_uid):
    """Return (conversation, created_bool) for a DM between uid and other_uid."""
    Conv = request.env['lugal.supply.conversation'].sudo()
    existing = Conv.search([
        ('type', '=', 'dm'),
        ('participant_ids', 'in', [uid]),
        ('participant_ids', 'in', [other_uid]),
    ], limit=10)
    for c in existing:
        ids = set(c.participant_ids.ids)
        if ids == {uid, other_uid}:
            return c, False
    # Create
    users = request.env['res.users'].sudo().browse([uid, other_uid])
    names = [u.name for u in users if u.exists()]
    conv = Conv.create({
        'name': ' & '.join(names),
        'type': 'dm',
        'participant_ids': [(6, 0, [uid, other_uid])],
        'last_activity': odoo_fields.Datetime.now(),
    })
    # Tell BOTH participants to resubscribe so the new supply_chat.<id>
    # channel is added to their live WebSocket connection immediately.
    _notify_participants_resubscribe(conv, [uid, other_uid])
    return conv, True


def _find_or_create_group(uid, recipient_ids, group_name=None):
    """Find or create a group conversation for uid + recipient_ids."""
    all_ids = sorted(set([uid] + list(recipient_ids)))
    Conv = request.env['lugal.supply.conversation'].sudo()
    # Try to match an existing group with exact participants
    existing = Conv.search([
        ('type', '=', 'group'),
        ('participant_ids', 'in', [uid]),
    ], limit=50)
    for c in existing:
        if set(c.participant_ids.ids) == set(all_ids):
            return c, False
    users = request.env['res.users'].sudo().browse(all_ids)
    name = group_name or ', '.join(u.name for u in users if u.exists())
    conv = Conv.create({
        'name': name,
        'type': 'group',
        'participant_ids': [(6, 0, all_ids)],
        'created_by_id': uid,
        'last_activity': odoo_fields.Datetime.now(),
    })
    # Creator is automatically a group admin
    if hasattr(conv, 'group_admin_ids'):
        conv.write({'group_admin_ids': [(4, uid)]})
    # Tell ALL participants to resubscribe so the new supply_chat.<id>
    # channel is included in their live WebSocket connection immediately.
    _notify_participants_resubscribe(conv, all_ids)
    return conv, True


def _resolve_thread(uid, thread_id, recipient_ids, group_name=None):
    """
    Return (conversation, error_str | None).
    Resolves thread_id (or conversation_id alias) OR creates/finds dm/group via recipient_ids.
    """
    Conv = request.env['lugal.supply.conversation'].sudo()
    if thread_id:
        try:
            conv = Conv.browse(int(thread_id)).exists()
        except (ValueError, TypeError):
            return None, 'Invalid conversation id'
        if not conv:
            return None, 'Conversation not found'
        if conv.type != 'team' and uid not in conv.participant_ids.ids:
            return None, 'Forbidden'
        return conv, None

    if recipient_ids:
        ids = [int(r) for r in recipient_ids]
        if len(ids) == 1:
            conv, _ = _find_or_create_dm(uid, ids[0])
        else:
            conv, _ = _find_or_create_group(uid, ids, group_name)
        return conv, None

    return None, 'Provide thread_id or recipient_ids'


def _notify_participants_resubscribe(conv, participant_ids):
    """
    After a NEW conversation is created, tell every participant's frontend to
    call busClient.resubscribe() so Odoo adds supply_chat.<conv_id> to their
    active WebSocket subscription.

    Without this, the recipient(s) never subscribe to the new channel and miss
    all messages until they manually reload the browser.

    Publishes to supply_user.<uid> — the per-user personal channel that every
    user is already subscribed to from their initial connect.
    """
    payload = {
        'conversation_id': conv.id,
        'conversation_type': conv.type,
        'name': conv.name or '',
    }
    for uid in participant_ids:
        try:
            request.env['bus.bus'].sudo()._sendone(
                f'supply_user.{uid}',
                'supply.chat.resubscribe',
                payload,
            )
        except Exception as exc:
            _logger.debug('_notify_participants_resubscribe bus error uid=%s: %s', uid, exc)


def _publish_new_message(msg, uid, conv):
    """Broadcast a new message to all participants via two paths:

    Path 1 — conversation channel (supply_chat.<conv_id>):
      Reaches every user who is already subscribed to this conversation.
      Covers all normal cases (existing conversations, reconnected users).

    Path 2 — personal channel (supply_user.<recipient_uid>):
      Reaches every non-sender participant via their always-subscribed personal
      channel.  This is the fallback that eliminates the race condition for
      brand-new conversations: the resubscribe event and the first message are
      published at the same instant, so the recipient may not have added
      supply_chat.<conv_id> to their active subscription yet.  Publishing to
      supply_user.<uid> guarantees immediate delivery regardless of subscription
      state.

    FE deduplication: both copies carry identical message_id.  The frontend
    MUST deduplicate incoming CHAT_MESSAGE_NEW events by message_id so the
    user never sees a double notification or duplicate message bubble.
    """
    payload = _serialize_message(msg, uid)
    # Path 1 — conversation channel (no extra flag; this is the primary copy)
    _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.message.new', payload)
    # Path 2 — personal channel for every non-sender participant (fallback delivery)
    # We add _via_personal_channel=True so the FE can deduplicate: if the
    # same message_id already arrived via the conversation channel, ignore this copy.
    personal_payload = dict(payload, _via_personal_channel=True)
    sender_id = msg.sender_id.id if msg.sender_id else uid
    sender_name = msg.sender_id.name if msg.sender_id else 'New message'
    msg_preview = (msg.content or '').strip()[:80] or '📎 Attachment'

    for participant in conv.participant_ids:
        if participant.id != sender_id:
            try:
                request.env['bus.bus'].sudo()._sendone(
                    f'supply_user.{participant.id}',
                    'supply.chat.message.new',
                    personal_payload,
                )
            except Exception as exc:
                _logger.debug(
                    '_publish_new_message personal fallback error uid=%s: %s',
                    participant.id, exc,
                )
            # Web Push — reaches the user even when the browser tab is closed
            try:
                PushSub = request.env['lugal.push.subscription'].sudo()
                PushSub.send_push_to_user(
                    participant.id,
                    title=sender_name,
                    body=msg_preview,
                    data={
                        'type': 'chat',
                        'conversation_id': conv.id,
                        'message_id': msg.id,
                        'url': f'/conversations?conversation={conv.id}',
                    },
                )
            except Exception:
                pass  # push is best-effort — never crash the message send


# ===========================================================================
# Controller
# ===========================================================================

class SupplyChatController(http.Controller):

    # -----------------------------------------------------------------------
    # Conversations
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/conversations/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversations_list(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Conv = request.env['lugal.supply.conversation'].sudo()
            convs = Conv.search([
                ('is_archived', '=', False),
                ('participant_ids', 'in', [uid]),
            ], order='last_activity desc, id desc')
            items = [_serialize_conversation(c, uid) for c in convs]
            return {'success': True, 'data': {'items': items, 'total': len(items)}}
        except Exception as e:
            return crm_error(e, 'conversations_list')

    @http.route('/api/crm/supply/conversations/create',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversations_create(self, recipient_ids=None, group_name=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not recipient_ids:
                return {'success': False, 'error': 'recipient_ids is required'}
            ids = [int(r) for r in recipient_ids]
            if len(ids) == 1:
                conv, _ = _find_or_create_dm(uid, ids[0])
            else:
                conv, _ = _find_or_create_group(uid, ids, group_name)
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'conversations_create')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/get',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_get(self, conv_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'conversation_get')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/rename',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_rename(self, conv_id, name=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not name or not str(name).strip():
                return {'success': False, 'error': 'name is required'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type in ('dm', 'team'):
                return {'success': False, 'error': 'Cannot rename dm or team conversations'}
            if uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            conv.write({'name': str(name).strip()})
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'conversation_rename')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/archive',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_archive(self, conv_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type == 'team':
                return {'success': False, 'error': 'Cannot archive team channels'}
            if uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            conv.write({'is_archived': True})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'conversation_archive')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/leave',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_leave(self, conv_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type == 'team':
                return {'success': False, 'error': 'Cannot leave team channels'}
            if uid in conv.participant_ids.ids:
                conv.write({'participant_ids': [(3, uid)]})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'conversation_leave')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_update(self, conv_id, **kwargs):
        """Generic update (mute, pin, name, etc.). Only supported fields are applied."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            vals = {}
            if 'name' in kwargs and conv.type == 'group':
                vals['name'] = str(kwargs['name']).strip()
            if vals:
                conv.write(vals)
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'conversation_update')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/mark_read',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_mark_read(self, conv_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            Msg = request.env['lugal.supply.message'].sudo()
            unread = Msg.search([
                ('conversation_id', '=', conv.id),
                ('sender_id', '!=', uid),
                ('read_user_ids', 'not in', [uid]),
                ('is_deleted', '=', False),
            ])
            if unread:
                unread.write({'read_user_ids': [(4, uid)]})
                # Record the read timestamp in read_receipts_json (Riyadh time)
                now_iso = datetime.now(tz=_RIYADH_TZ).isoformat(timespec='seconds')
                for m in unread:
                    try:
                        receipts = json.loads(m.read_receipts_json or '{}')
                    except Exception:
                        receipts = {}
                    receipts[str(uid)] = now_iso
                    m.write({'read_receipts_json': json.dumps(receipts)})
                # Notify senders about the read (for delivery ticks)
                senders = set(unread.mapped('sender_id.id')) - {uid}
                for sender_uid in senders:
                    _bus_publish(
                        f'supply_user.{sender_uid}',
                        'supply.chat.message.read',
                        {
                            'conversation_id': conv.id,
                            'read_by_uid': uid,
                            'message_ids': unread.ids,
                        },
                    )
            return {'success': True, 'data': {'conversation_id': conv.id, 'unread_count': 0}}
        except Exception as e:
            return crm_error(e, 'conversation_mark_read')

    # -----------------------------------------------------------------------
    # Typing
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/conversations/<int:conv_id>/typing',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation_typing(self, conv_id, is_typing=False, **kwargs):
        """Broadcast a typing indicator to all participants of a conversation.

        Typing state is intentionally kept ONLY in the in-process timer dict
        (_typing_timers) — no DB writes are performed.  The previous
        lugal.supply.typing ORM upsert caused psycopg2 SerializationFailure
        errors under concurrent worker load (9 workers racing on the same row)
        which surfaced as HTTP 500 on the FE.  The bus event alone is
        sufficient: recipients see typing.start / typing.stop immediately via
        WebSocket and the auto-stop timer fires if the heartbeat stops.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}

            user = request.env['res.users'].sudo().browse(uid)
            payload = {
                'conversation_id': conv.id,
                'user_id': uid,
                'user_name': user.name or '',
                'is_typing': bool(is_typing),
            }

            timer_key = (uid, conv_id)
            db_name   = request.env.cr.dbname

            if is_typing:
                _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.typing.start', payload)

                # Arm/reset a pure in-memory auto-stop timer — no DB needed.
                def _auto_stop():
                    try:
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as cr:
                            from odoo.api import Environment
                            env = Environment(cr, uid, {})
                            env['bus.bus'].sudo()._sendone(
                                f'supply_chat.{conv_id}',
                                'supply.chat.typing.stop',
                                {
                                    'conversation_id': conv_id,
                                    'user_id': uid,
                                    'user_name': '',
                                    'is_typing': False,
                                },
                            )
                    except Exception as exc:
                        _logger.debug('typing auto-stop error: %s', exc)

                with _typing_lock:
                    old_timer = _typing_timers.get(timer_key)
                    if old_timer:
                        old_timer.cancel()
                    t = threading.Timer(_TYPING_EXPIRE_SECS, _auto_stop)
                    t.daemon = True
                    t.start()
                    _typing_timers[timer_key] = t

            else:
                # Cancel any pending auto-stop timer and emit stop immediately.
                with _typing_lock:
                    old = _typing_timers.pop(timer_key, None)
                    if old:
                        old.cancel()

                _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.typing.stop', payload)

            return {'success': True, 'data': payload}
        except Exception as e:
            return crm_error(e, 'conversation_typing')

    # -----------------------------------------------------------------------
    # Group members
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/conversations/<int:conv_id>/members/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def members_list(self, conv_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            members = [_serialize_participant(u) for u in conv.participant_ids]
            return {'success': True, 'data': {'members': members, 'total': len(members)}}
        except Exception as e:
            return crm_error(e, 'members_list')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/members/add',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def members_add(self, conv_id, user_ids=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not user_ids:
                return {'success': False, 'error': 'user_ids required'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'group':
                return {'success': False, 'error': 'Can only add members to group conversations'}
            if uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            # Only admins and supervisors can add members
            creator_id = conv.created_by_id.id if conv.created_by_id else None
            admin_ids = conv.group_admin_ids.ids if hasattr(conv, 'group_admin_ids') else []
            supervisor_ids = conv.group_supervisor_ids.ids if hasattr(conv, 'group_supervisor_ids') else []
            can_add = (uid == creator_id) or (uid in admin_ids) or (uid in supervisor_ids)
            if not can_add:
                return {'success': False, 'error': 'Only admins and supervisors can add members'}
            conv.write({'participant_ids': [(4, int(u)) for u in user_ids]})
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'members_add')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/members/remove',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def members_remove(self, conv_id, user_id=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not user_id:
                return {'success': False, 'error': 'user_id required'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'group':
                return {'success': False, 'error': 'Can only remove members from group conversations'}
            if uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            # Only admins (and creator) can remove members
            creator_id = conv.created_by_id.id if conv.created_by_id else None
            admin_ids = conv.group_admin_ids.ids if hasattr(conv, 'group_admin_ids') else []
            is_admin = (uid == creator_id) or (uid in admin_ids)
            # A member can always remove themselves (leave)
            target_uid = int(user_id)
            if target_uid != uid and not is_admin:
                return {'success': False, 'error': 'Only admins can remove other members'}
            if target_uid == creator_id and uid != creator_id:
                return {'success': False, 'error': 'Cannot remove the group creator'}
            conv.write({'participant_ids': [(3, target_uid)]})
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'members_remove')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/members/role',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def members_role(self, conv_id, user_id=None, role=None, **kwargs):
        """
        Assign or remove a group role for a member.

        Params:
          user_id  (int)   — target user
          role     (str)   — 'admin' | 'supervisor' | 'member' (demotes)

        Only the group creator or existing admins can call this.
        Extra group settings:
          only_admins_can_send (bool)  — toggle admin-only messaging
          group_description (str)     — update group description
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Conversation not found'}
            if conv.type != 'group':
                return {'success': False, 'error': 'Only group conversations support roles'}
            if uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}

            # Only admins (and creator) can change roles
            creator_id = conv.created_by_id.id if conv.created_by_id else None
            admin_ids = conv.group_admin_ids.ids if hasattr(conv, 'group_admin_ids') else []
            is_admin = (uid == creator_id) or (uid in admin_ids)

            # Handle group settings updates (no user_id required)
            if 'only_admins_can_send' in kwargs:
                if not is_admin:
                    return {'success': False, 'error': 'Only admins can change group settings'}
                conv.write({'only_admins_can_send': bool(kwargs['only_admins_can_send'])})
            if 'group_description' in kwargs:
                if not is_admin:
                    return {'success': False, 'error': 'Only admins can change group description'}
                conv.write({'group_description': kwargs['group_description'] or ''})

            if user_id and role:
                if not is_admin:
                    return {'success': False, 'error': 'Only admins can assign roles'}
                target_uid = int(user_id)
                if target_uid == creator_id:
                    return {'success': False, 'error': 'Cannot change the primary creator role'}
                if target_uid not in conv.participant_ids.ids:
                    return {'success': False, 'error': 'User is not a group member'}

                role = (role or '').strip().lower()
                if role == 'admin':
                    conv.write({
                        'group_admin_ids': [(4, target_uid)],
                        'group_supervisor_ids': [(3, target_uid)],
                    })
                elif role == 'supervisor':
                    conv.write({
                        'group_supervisor_ids': [(4, target_uid)],
                        'group_admin_ids': [(3, target_uid)],
                    })
                elif role == 'member':
                    conv.write({
                        'group_admin_ids': [(3, target_uid)],
                        'group_supervisor_ids': [(3, target_uid)],
                    })
                else:
                    return {'success': False, 'error': f'Invalid role: {role}'}

            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'members_role')

    # -----------------------------------------------------------------------
    # Messages — list
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_list(self, thread_id=None, conversation_id=None, recipient_ids=None,
                      group_name=None,
                      page=1, per_page=20, before_id=None, limit=None, direction=None,
                      **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            effective_thread_id = thread_id or conversation_id
            conv, err = _resolve_thread(uid, effective_thread_id, recipient_ids, group_name)
            if err:
                return {'success': False, 'error': err}

            Msg = request.env['lugal.supply.message'].sudo()
            domain = [
                ('conversation_id', '=', conv.id),
                # Include is_deleted=True messages so the frontend can render
                # "This message was deleted" (WhatsApp-style). Only filter out
                # messages hidden for this specific user ("delete for me").
                ('hidden_user_ids', 'not in', [uid]),
            ]

            # Cursor-based pagination: before_id loads messages older than the given id.
            # This replaces the old page/offset approach which returned stale old messages.
            per_page_n = int(limit or per_page)
            if before_id:
                domain = domain + [('id', '<', int(before_id))]

            total = Msg.search_count(domain)

            # Fetch newest-first so page 1 always returns the most recent messages.
            # Fetch one extra to detect whether more older messages exist.
            rows = Msg.search(domain, order='create_date desc, id desc',
                              limit=per_page_n + 1)
            has_more_older = len(rows) > per_page_n
            msgs = rows[:per_page_n]

            # Oldest id in the result set — FE uses this as before_id to load even older messages.
            anchor_before_id = msgs[-1].id if msgs else None

            items = [_serialize_message(m, uid) for m in msgs]
            return {
                'success': True,
                'data': {
                    'items': items,
                    'total': total,
                    'has_more_older': has_more_older,
                    'anchor_before_id': anchor_before_id,
                    'thread_id': conv.id,
                    'conversation_type': conv.type,
                },
            }
        except Exception as e:
            return crm_error(e, 'messages_list')

    # -----------------------------------------------------------------------
    # Messages — create
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/create',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_create(self, content='', thread_id=None, conversation_id=None,
                        recipient_ids=None,
                        group_name=None, attachments=None, reply_to_id=None,
                        client_message_id=None, attachment_ids=None,
                        kind=None, duration_seconds=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            # Accept both thread_id and conversation_id as aliases for the conversation
            effective_thread_id = thread_id or conversation_id
            conv, err = _resolve_thread(uid, effective_thread_id, recipient_ids, group_name)
            if err:
                return {'success': False, 'error': err}

            # Enforce only-admins-can-send restriction
            if (conv.type == 'group' and
                    getattr(conv, 'only_admins_can_send', False)):
                creator_id = conv.created_by_id.id if conv.created_by_id else None
                admin_ids = conv.group_admin_ids.ids if hasattr(conv, 'group_admin_ids') else []
                is_admin = (uid == creator_id) or (uid in admin_ids)
                if not is_admin:
                    return {'success': False, 'error': 'Only admins can send messages in this group'}

            # Resolve ir.attachment ids into {name, url, kind, ...} objects if provided
            att_list = list(attachments or [])
            inferred_kind = kind or 'text'

            if attachment_ids:
                IrAtt = request.env['ir.attachment'].sudo()
                for att_id in attachment_ids:
                    att = IrAtt.browse(int(att_id)).exists()
                    if att:
                        mime = att.mimetype or ''
                        if mime.startswith('audio/'):
                            att_kind = 'voice' if 'voice' in (att.name or '').lower() else 'audio'
                        elif mime.startswith('video/'):
                            att_kind = 'video'
                        elif mime.startswith('image/'):
                            att_kind = 'image'
                        else:
                            att_kind = 'file'
                        att_list.append({
                            'id': att.id,
                            'name': att.name or '',
                            'mimetype': mime,
                            'size': int(att.file_size or 0),
                            'url': _build_attachment_url(att),
                            'file_url': _build_attachment_url(att),
                            'kind': att_kind,
                            'file_type': att_kind,
                            'duration_seconds': 0,
                        })
                        # Infer message kind from first media attachment
                        if inferred_kind == 'text' and att_kind in ('audio', 'voice', 'video', 'image'):
                            inferred_kind = att_kind

            # Explicit kind param overrides inference
            final_kind = kind if kind in ('text', 'image', 'video', 'audio', 'voice', 'file') else inferred_kind

            try:
                final_duration = float(duration_seconds or 0)
            except (ValueError, TypeError):
                final_duration = 0.0

            Msg = request.env['lugal.supply.message'].sudo()
            vals = {
                'conversation_id': conv.id,
                'sender_id': uid,
                'content': str(content or ''),
                'kind': final_kind,
                'duration_seconds': final_duration,
                'attachments_json': json.dumps(att_list),
            }
            if reply_to_id:
                r = Msg.browse(int(reply_to_id)).exists()
                if r and r.conversation_id.id == conv.id:
                    vals['reply_to_id'] = r.id
            if client_message_id:
                vals['client_message_id'] = str(client_message_id)

            msg = Msg.create(vals)

            # Touch conversation activity timestamp
            conv.write({'last_activity': odoo_fields.Datetime.now()})

            serialized = _serialize_message(msg, uid)
            _publish_new_message(msg, uid, conv)

            return {'success': True, 'data': serialized}
        except Exception as e:
            return crm_error(e, 'messages_create')

    # -----------------------------------------------------------------------
    # Messages — edit
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/<int:message_id>/edit',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_edit(self, message_id, content=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if content is None:
                return {'success': False, 'error': 'content is required'}
            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}
            if msg.sender_id.id != uid:
                return {'success': False, 'error': 'Only the sender can edit this message'}
            if msg.is_deleted:
                return {'success': False, 'error': 'Cannot edit a deleted message'}
            # Enforce 5-minute edit window
            # Both odoo_fields.Datetime.now() and msg.create_date use the same
            # clock reference (server local time stored as TIMESTAMP WITHOUT TIMEZONE),
            # so their difference is always correct regardless of server timezone.
            if msg.create_date:
                age = (odoo_fields.Datetime.now() - msg.create_date).total_seconds()
                if age > 300:
                    return {
                        'success': False,
                        'error': 'Messages can only be edited within 5 minutes of sending',
                        'code': 'EDIT_WINDOW_EXPIRED',
                    }
            msg.write({'content': str(content), 'edited_at': odoo_fields.Datetime.now()})
            serialized = _serialize_message(msg, uid)
            _bus_publish(f'supply_chat.{msg.conversation_id.id}',
                         'supply.chat.message.updated', serialized)
            return {'success': True, 'data': serialized}
        except Exception as e:
            return crm_error(e, 'message_edit')

    # -----------------------------------------------------------------------
    # Messages — pin / unpin
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/<int:message_id>/pin',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_pin(self, message_id, **kwargs):
        """
        Pin or unpin a message in its conversation.
        Any conversation participant can pin/unpin.

        Body params (optional):
          pin  bool  default True — pass false to unpin
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            pin = kwargs.get('pin', True)
            if isinstance(pin, str):
                pin = pin.lower() not in ('false', '0', 'no')

            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}

            conv = msg.conversation_id
            if not conv:
                return {'success': False, 'error': 'Conversation not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            if msg.is_deleted:
                return {'success': False, 'error': 'Cannot pin a deleted message'}

            if pin:
                msg.write({
                    'is_pinned': True,
                    'pinned_at': odoo_fields.Datetime.now(),
                    'pinned_by_id': uid,
                })
            else:
                msg.write({
                    'is_pinned': False,
                    'pinned_at': False,
                    'pinned_by_id': False,
                })

            serialized = _serialize_message(msg, uid)
            _bus_publish(
                f'supply_chat.{conv.id}',
                'supply.chat.message.pinned',
                {
                    'message_id': msg.id,
                    'conversation_id': conv.id,
                    'is_pinned': msg.is_pinned,
                    'pinned_by_id': uid,
                    'pinned_at': _to_riyadh_iso(msg.pinned_at),
                    'message': serialized,
                },
            )
            return {'success': True, 'data': serialized}
        except Exception as e:
            return crm_error(e, 'message_pin')

    # -----------------------------------------------------------------------
    # Messages — react
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/<int:message_id>/react',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_react(self, message_id, emoji=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not emoji:
                return {'success': False, 'error': 'emoji is required'}
            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}
            conv = msg.conversation_id
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            try:
                reactions = json.loads(msg.reactions_json or '{}')
            except Exception:
                reactions = {}
            users = reactions.get(emoji, [])
            if uid in users:
                users.remove(uid)
            else:
                users.append(uid)
            if users:
                reactions[emoji] = users
            else:
                reactions.pop(emoji, None)
            msg.write({'reactions_json': json.dumps(reactions)})
            payload = {'message_id': msg.id, 'conversation_id': conv.id, 'reactions': reactions}
            _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.message.reaction.changed', payload)
            # Also notify the message author on their personal channel so the
            # notification bell registers the reaction (like WhatsApp).
            # Skip if the reactor IS the message author (reacting to your own msg still
            # sends a notification per user request, unless removed).
            author_id = msg.sender_id.id if msg.sender_id else None
            if author_id and uid in users:  # uid in users means emoji was just ADDED
                try:
                    reactor_name = request.env['res.users'].sudo().browse(uid).name or 'Someone'
                    _bus_publish(
                        f'supply_user.{author_id}',
                        'supply.chat.message.reaction.notify',
                        {
                            'message_id': msg.id,
                            'conversation_id': conv.id,
                            'emoji': emoji,
                            'reactor_id': uid,
                            'reactor_name': reactor_name,
                        },
                    )
                except Exception:
                    pass
            return {'success': True, 'data': {'reactions': reactions}}
        except Exception as e:
            return crm_error(e, 'message_react')

    # -----------------------------------------------------------------------
    # Messages — delivered
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/<int:message_id>/delivered',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_delivered(self, message_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}
            # Only mark delivered if the caller is NOT the sender
            if msg.sender_id.id != uid and uid not in msg.delivered_user_ids.ids:
                msg.write({'delivered_user_ids': [(4, uid)]})
                # Notify the sender
                if msg.sender_id:
                    _bus_publish(
                        f'supply_user.{msg.sender_id.id}',
                        'supply.chat.message.delivered',
                        {
                            'message_id': msg.id,
                            'conversation_id': msg.conversation_id.id,
                            'delivery_state': 'delivered',
                            'delivered_to': msg.delivered_user_ids.ids,
                        },
                    )
            return {
                'success': True,
                'data': {
                    'message_id': msg.id,
                    'conversation_id': msg.conversation_id.id,
                    'delivery_state': _delivery_state_for(msg, msg.sender_id.id if msg.sender_id else uid),
                    'delivered_to': msg.delivered_user_ids.ids,
                    'delivered_count': len(msg.delivered_user_ids),
                },
            }
        except Exception as e:
            return crm_error(e, 'message_delivered')

    # -----------------------------------------------------------------------
    # Messages — read (single message)
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/<int:message_id>/read',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_read(self, message_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Msg = request.env['lugal.supply.message'].sudo()
            msg = Msg.browse(message_id).exists()
            if not msg:
                return {'success': False, 'error': 'Message not found'}
            if msg.sender_id.id != uid and uid not in msg.read_user_ids.ids:
                msg.write({'read_user_ids': [(4, uid)]})
                # Also auto-mark delivered if not already
                if uid not in msg.delivered_user_ids.ids:
                    msg.write({'delivered_user_ids': [(4, uid)]})
                # Record the read timestamp in read_receipts_json (Riyadh time)
                read_at_iso = datetime.now(tz=_RIYADH_TZ).isoformat(timespec='seconds')
                try:
                    receipts = json.loads(msg.read_receipts_json or '{}')
                except Exception:
                    receipts = {}
                receipts[str(uid)] = read_at_iso
                msg.write({'read_receipts_json': json.dumps(receipts)})
                # Notify the sender
                if msg.sender_id:
                    unread_remaining = Msg.search_count([
                        ('conversation_id', '=', msg.conversation_id.id),
                        ('sender_id', '!=', uid),
                        ('read_user_ids', 'not in', [uid]),
                        ('is_deleted', '=', False),
                    ])
                    # Build read_receipts for the WS payload
                    try:
                        receipts_pub = json.loads(msg.read_receipts_json or '{}')
                    except Exception:
                        receipts_pub = {}
                    read_receipts_payload = [
                        {
                            'user_id': ru.id,
                            'user_name': ru.name or f'User #{ru.id}',
                            'read_at': receipts_pub.get(str(ru.id)),
                        }
                        for ru in msg.read_user_ids
                    ]
                    _bus_publish(
                        f'supply_user.{msg.sender_id.id}',
                        'supply.chat.message.read',
                        {
                            'message_id': msg.id,
                            'conversation_id': msg.conversation_id.id,
                            'delivery_state': 'read',
                            'read_by': msg.read_user_ids.ids,
                            'read_receipts': read_receipts_payload,
                        },
                    )
            unread_count = Msg.search_count([
                ('conversation_id', '=', msg.conversation_id.id),
                ('sender_id', '!=', uid),
                ('read_user_ids', 'not in', [uid]),
                ('is_deleted', '=', False),
            ])
            # Build read_receipts for the HTTP response
            try:
                receipts_map = json.loads(msg.read_receipts_json or '{}')
            except Exception:
                receipts_map = {}
            read_receipts = [
                {
                    'user_id': ru.id,
                    'user_name': ru.name or f'User #{ru.id}',
                    'read_at': receipts_map.get(str(ru.id)),
                }
                for ru in msg.read_user_ids
            ]
            return {
                'success': True,
                'data': {
                    'message_id': msg.id,
                    'conversation_id': msg.conversation_id.id,
                    'delivery_state': _delivery_state_for(msg, msg.sender_id.id if msg.sender_id else uid),
                    'read_by': msg.read_user_ids.ids,
                    'read_receipts': read_receipts,
                    'unread_count': unread_count,
                },
            }
        except Exception as e:
            return crm_error(e, 'message_read')

    # -----------------------------------------------------------------------
    # Messages — forward
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/forward',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_forward(self, message_id=None, thread_id=None, recipient_ids=None,
                         group_name=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_id:
                return {'success': False, 'error': 'message_id required'}
            Msg = request.env['lugal.supply.message'].sudo()
            src = Msg.browse(int(message_id)).exists()
            if not src:
                return {'success': False, 'error': 'Source message not found'}
            conv, err = _resolve_thread(uid, thread_id, recipient_ids, group_name)
            if err:
                return {'success': False, 'error': err}
            fwd = Msg.create({
                'conversation_id': conv.id,
                'sender_id': uid,
                'content': src.content or '',
                'attachments_json': src.attachments_json or '[]',
            })
            conv.write({'last_activity': odoo_fields.Datetime.now()})
            serialized = _serialize_message(fwd, uid)
            _publish_new_message(fwd, uid, conv)
            return {'success': True, 'data': serialized}
        except Exception as e:
            return crm_error(e, 'messages_forward')

    # -----------------------------------------------------------------------
    # Messages — search
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/conversations/<int:conv_id>/pinned',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_pinned(self, conv_id, **kwargs):
        """Return all currently-pinned messages in a conversation, newest pin first."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            conv = request.env['lugal.supply.conversation'].sudo().browse(conv_id).exists()
            if not conv:
                return {'success': False, 'error': 'Not found'}
            if conv.type != 'team' and uid not in conv.participant_ids.ids:
                return {'success': False, 'error': 'Forbidden'}
            Msg = request.env['lugal.supply.message'].sudo()
            msgs = Msg.search([
                ('conversation_id', '=', conv.id),
                ('is_pinned', '=', True),
                ('is_deleted', '=', False),
            ], order='pinned_at desc')
            return {
                'success': True,
                'data': {'items': [_serialize_message(m, uid) for m in msgs]},
            }
        except Exception as e:
            return crm_error(e, 'messages_pinned')

    # -----------------------------------------------------------------------
    # Messages — search
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/search',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_search(self, query='', thread_id=None, page=1, per_page=20, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Msg = request.env['lugal.supply.message'].sudo()
            domain = [
                ('hidden_user_ids', 'not in', [uid]),
                ('is_deleted', '=', False),
                ('content', 'ilike', str(query or '')),
            ]
            if thread_id:
                conv = request.env['lugal.supply.conversation'].sudo().browse(int(thread_id)).exists()
                if conv and (conv.type == 'team' or uid in conv.participant_ids.ids):
                    domain.append(('conversation_id', '=', conv.id))
                else:
                    domain.append(('conversation_id.participant_ids', 'in', [uid]))
            else:
                domain.append(('conversation_id.participant_ids', 'in', [uid]))
            total = Msg.search_count(domain)
            offset = (int(page) - 1) * int(per_page)
            msgs = Msg.search(domain, order='create_date desc', limit=int(per_page), offset=offset)
            return {
                'success': True,
                'data': {
                    'items': [_serialize_message(m, uid) for m in msgs],
                    'total': total,
                },
            }
        except Exception as e:
            return crm_error(e, 'messages_search')

    # -----------------------------------------------------------------------
    # Bus channel discovery
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/chat/bus_channels',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bus_channels(self, **kwargs):
        """
        Returns the list of bus channel names this user should subscribe to in /web/bus/poll.

        Channels:
          supply_chat.<conv_id>   — conversation-level events (new msg, typing, reactions)
          supply_user.<uid>       — user-level events (delivered/read receipts, DM notifications)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Conv = request.env['lugal.supply.conversation'].sudo()
            convs = Conv.search([
                ('is_archived', '=', False),
                ('participant_ids', 'in', [uid]),
            ])
            channels = [f'supply_chat.{c.id}' for c in convs]
            channels.append(f'supply_user.{uid}')
            return {
                'success': True,
                'data': {
                    'channels': channels,
                    'uid': uid,
                },
            }
        except Exception as e:
            return crm_error(e, 'bus_channels')
