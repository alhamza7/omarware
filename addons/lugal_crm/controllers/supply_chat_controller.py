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
from datetime import datetime, timedelta

from odoo import http, fields as odoo_fields
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)

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
    return {
        'id': conv.id,
        'type': conv.type,
        'name': conv.name or '',
        'participant_ids': participants.ids,
        'participants': [_serialize_participant(u) for u in participants],
        'last_activity': conv.last_activity.isoformat() if conv.last_activity else None,
        'is_archived': conv.is_archived,
        'unread_count': _unread_count_for(conv, uid),
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
        'created_at': msg.create_date.isoformat() if msg.create_date else None,
        'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
        'reply_to_id': msg.reply_to_id.id if msg.reply_to_id else None,
        'reply_to_content': reply_content,
        'reply_to_sender': reply_sender,
        'reactions': reactions,
        'is_deleted': msg.is_deleted,
        'delivery_state': _delivery_state_for(msg, uid),
        'delivered_to': msg.delivered_user_ids.ids,
        'read_by': msg.read_user_ids.ids,
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
        'last_activity': odoo_fields.Datetime.now(),
    })
    return conv, True


def _resolve_thread(uid, thread_id, recipient_ids, group_name=None):
    """
    Return (conversation, error_str | None).
    Resolves thread_id OR creates/finds dm/group via recipient_ids.
    """
    Conv = request.env['lugal.supply.conversation'].sudo()
    if thread_id:
        conv = Conv.browse(int(thread_id)).exists()
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


def _publish_new_message(msg, uid, conv):
    """Broadcast new message to all relevant bus channels."""
    payload = _serialize_message(msg, uid)
    # Conversation channel — all participants receive it
    _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.message.new', payload)
    # Per-user channels — so a user who isn't polling supply_chat.<id> still gets it
    for u in conv.participant_ids:
        if u.id != uid:
            _bus_publish(f'supply_user.{u.id}', 'supply.chat.message.new', payload)


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

            if is_typing:
                # Upsert typing state in DB
                Typing = request.env['lugal.supply.typing'].sudo()
                existing = Typing.search([
                    ('user_id', '=', uid),
                    ('conversation_id', '=', conv.id),
                ], limit=1)
                now = odoo_fields.Datetime.now()
                if existing:
                    existing.write({'last_ping_at': now})
                else:
                    Typing.create({
                        'user_id': uid,
                        'conversation_id': conv.id,
                        'last_ping_at': now,
                    })

                # Publish typing.start on the conversation channel
                _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.typing.start', payload)

                # Arm/reset the auto-stop timer
                db_name = request.env.cr.dbname

                def _auto_stop():
                    try:
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as cr:
                            from odoo.api import Environment
                            env = Environment(cr, uid, {})
                            t_rec = env['lugal.supply.typing'].sudo().search([
                                ('user_id', '=', uid),
                                ('conversation_id', '=', conv_id),
                            ], limit=1)
                            if not t_rec:
                                return
                            age = (datetime.utcnow() - t_rec.last_ping_at.replace(tzinfo=None)).total_seconds()
                            if age < (_TYPING_EXPIRE_SECS - 0.5):
                                return  # a new heartbeat reset the timer — do not stop
                            t_rec.unlink()
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
                # Remove typing state from DB
                Typing = request.env['lugal.supply.typing'].sudo()
                Typing.search([
                    ('user_id', '=', uid),
                    ('conversation_id', '=', conv.id),
                ]).unlink()

                # Cancel any pending auto-stop timer
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
            conv.write({'participant_ids': [(3, int(user_id))]})
            return {'success': True, 'data': _serialize_conversation(conv, uid)}
        except Exception as e:
            return crm_error(e, 'members_remove')

    @http.route('/api/crm/supply/conversations/<int:conv_id>/members/role',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def members_role(self, conv_id, user_id=None, role=None, **kwargs):
        """Role changes are not stored yet; returns success as a forward-compat stub."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            return {'success': True, 'data': {'note': 'role management not implemented'}}
        except Exception as e:
            return crm_error(e, 'members_role')

    # -----------------------------------------------------------------------
    # Messages — list
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/messages/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_list(self, thread_id=None, recipient_ids=None, group_name=None,
                      page=1, per_page=50, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            conv, err = _resolve_thread(uid, thread_id, recipient_ids, group_name)
            if err:
                return {'success': False, 'error': err}

            Msg = request.env['lugal.supply.message'].sudo()
            domain = [
                ('conversation_id', '=', conv.id),
                ('hidden_user_ids', 'not in', [uid]),
            ]
            total = Msg.search_count(domain)
            offset = (int(page) - 1) * int(per_page)
            msgs = Msg.search(domain, order='create_date asc, id asc',
                              limit=int(per_page), offset=offset)
            items = [_serialize_message(m, uid) for m in msgs]
            return {
                'success': True,
                'data': {
                    'items': items,
                    'total': total,
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
    def messages_create(self, content='', thread_id=None, recipient_ids=None,
                        group_name=None, attachments=None, reply_to_id=None,
                        client_message_id=None, attachment_ids=None,
                        kind=None, duration_seconds=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            conv, err = _resolve_thread(uid, thread_id, recipient_ids, group_name)
            if err:
                return {'success': False, 'error': err}

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
                            'url': f'/web/content/{att.id}?download=true',
                            'kind': att_kind,
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
            msg.write({'content': str(content), 'edited_at': odoo_fields.Datetime.now()})
            serialized = _serialize_message(msg, uid)
            _bus_publish(f'supply_chat.{msg.conversation_id.id}',
                         'supply.chat.message.updated', serialized)
            return {'success': True, 'data': serialized}
        except Exception as e:
            return crm_error(e, 'message_edit')

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
                # Notify the sender
                if msg.sender_id:
                    unread_remaining = Msg.search_count([
                        ('conversation_id', '=', msg.conversation_id.id),
                        ('sender_id', '!=', uid),
                        ('read_user_ids', 'not in', [uid]),
                        ('is_deleted', '=', False),
                    ])
                    _bus_publish(
                        f'supply_user.{msg.sender_id.id}',
                        'supply.chat.message.read',
                        {
                            'message_id': msg.id,
                            'conversation_id': msg.conversation_id.id,
                            'delivery_state': 'read',
                            'read_by': msg.read_user_ids.ids,
                        },
                    )
            unread_count = Msg.search_count([
                ('conversation_id', '=', msg.conversation_id.id),
                ('sender_id', '!=', uid),
                ('read_user_ids', 'not in', [uid]),
                ('is_deleted', '=', False),
            ])
            return {
                'success': True,
                'data': {
                    'message_id': msg.id,
                    'conversation_id': msg.conversation_id.id,
                    'delivery_state': _delivery_state_for(msg, msg.sender_id.id if msg.sender_id else uid),
                    'read_by': msg.read_user_ids.ids,
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
