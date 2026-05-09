# -*- coding: utf-8 -*-
"""
Unified CRM Notifications API

Combines chat (supply messages) and email unread counts into a single
polling endpoint so the FE can maintain a single notification badge and
notification feed without querying two separate systems.

Routes:
  GET  /api/crm/notifications          — unified unread counts + recent items
  POST /api/crm/notifications/mark_read — mark chat/email/all as read
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from odoo import http
from odoo.http import request, Response

from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)

# Riyadh = UTC+3, no DST
_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields, so we guard for both."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _json_response(data, status=200):
    resp = Response(
        json.dumps(data),
        status=status,
        mimetype='application/json',
        headers=[('Cache-Control', 'no-store')],
    )
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Odoo-Database'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    return resp


class CrmNotificationsController(http.Controller):

    # -----------------------------------------------------------------------
    # GET /api/crm/notifications
    # -----------------------------------------------------------------------

    @http.route('/api/crm/notifications', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def notifications(self, **kwargs):
        """
        Unified notifications endpoint — chat + email in one response.

        Query params:
          since=<ISO datetime>   Optional. Return only new_messages / new_emails
                                  received/created after this timestamp.
          limit=<int>            Max items in each section (default 20, max 50).

        Response shape:
          {
            "success": true,
            "data": {
              "total_unread":  <int>,          // sum of chat + email unread
              "chat": {
                "unread":       <int>,         // total unread chat messages
                "conversations": [             // conversations with unread messages
                  {
                    "id":           <int>,
                    "name":         <str>,
                    "type":         "dm"|"group"|"team",
                    "unread_count": <int>,
                    "last_message": <str>,     // content preview
                    "last_activity":<str>      // ISO-8601
                  }
                ]
              },
              "email": {
                "unread":      <int>,          // total unread inbox emails
                "items": [                     // recent unread email summaries
                  {
                    "id":           <int>,
                    "account_id":   <int>,
                    "subject":      <str>,
                    "from_name":    <str>,
                    "from_address": <str>,
                    "date":         <str>       // ISO-8601
                  }
                ]
              },
              "checked_at": <ISO-8601 UTC>
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        uid = ensure_jwt_user_id()
        if not uid:
            return _json_response({'success': False, 'error': 'Unauthorized'}, 401)

        try:
            params    = request.httprequest.args
            since_str = params.get('since', '')
            limit     = min(int(params.get('limit', 20) or 20), 50)

            since_dt = None
            if since_str:
                try:
                    from odoo.fields import Datetime as OdooDatetime
                    since_dt = OdooDatetime.from_string(since_str.replace('T', ' ')[:19])
                except Exception:
                    pass

            # ── Chat unread ───────────────────────────────────────────────
            chat_unread   = 0
            chat_convs    = []

            if 'lugal.supply.conversation' in request.env:
                Conv = request.env['lugal.supply.conversation'].sudo()
                Msg  = request.env['lugal.supply.message'].sudo()

                # Conversations where this user is a participant and not archived
                convs = Conv.search([
                    ('is_archived', '=', False),
                    ('participant_ids', 'in', [uid]),
                ])

                for conv in convs:
                    msg_domain = [
                        ('conversation_id', '=', conv.id),
                        ('sender_id', '!=', uid),
                        ('read_user_ids', 'not in', [uid]),
                        ('is_deleted', '=', False),
                        ('hidden_user_ids', 'not in', [uid]),
                    ]
                    if since_dt:
                        msg_domain.append(('create_date', '>', since_dt))

                    count = Msg.search_count(msg_domain)
                    if count:
                        chat_unread += count
                        # Last message preview
                        last = Msg.search(
                            [('conversation_id', '=', conv.id), ('is_deleted', '=', False)],
                            order='create_date desc', limit=1,
                        )
                        preview = ''
                        if last:
                            kind = getattr(last, 'kind', 'text') or 'text'
                            if kind == 'voice':
                                preview = '🎤 Voice message'
                            elif kind == 'audio':
                                preview = '🎵 Audio'
                            elif kind == 'video':
                                preview = '🎥 Video'
                            elif kind == 'image':
                                preview = '🖼 Image'
                            elif kind == 'file':
                                preview = '📎 File'
                            else:
                                preview = (last.content or '')[:80]
                        chat_convs.append({
                            'id':            conv.id,
                            'name':          conv.name or '',
                            'type':          conv.type,
                            'unread_count':  count,
                            'last_message':  preview,
                            'last_activity': _to_riyadh_iso(conv.last_activity),
                        })

                # Sort by most unread first
                chat_convs.sort(key=lambda c: c['unread_count'], reverse=True)
                chat_convs = chat_convs[:limit]

            # ── Email unread ──────────────────────────────────────────────
            email_unread = 0
            email_items  = []

            if 'lugal.email.account' in request.env:
                Acc      = request.env['lugal.email.account'].sudo()
                EmailMsg = request.env['lugal.email.message'].sudo()

                acc_ids  = Acc.search([('user_id', '=', uid)]).ids
                if acc_ids:
                    domain = [
                        ('account_id', 'in', acc_ids),
                        ('folder', '=', 'inbox'),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ]
                    if since_dt:
                        domain.append(('date', '>', since_dt))

                    email_unread = EmailMsg.search_count(domain)
                    recent = EmailMsg.search(domain, order='date desc', limit=limit)
                    for m in recent:
                        email_items.append({
                            'id':           m.id,
                            'account_id':   m.account_id.id if m.account_id else None,
                            'subject':      m.subject or '(no subject)',
                            'from_name':    m.from_name or '',
                            'from_address': m.from_address or '',
                            'date':         _to_riyadh_iso(m.date),
                        })

            checked_at = datetime.now(tz=_RIYADH_TZ).strftime('%Y-%m-%dT%H:%M:%S+03:00')

            return _json_response({
                'success': True,
                'data': {
                    'total_unread': chat_unread + email_unread,
                    'chat': {
                        'unread':        chat_unread,
                        'conversations': chat_convs,
                    },
                    'email': {
                        'unread': email_unread,
                        'items':  email_items,
                    },
                    'checked_at': checked_at,
                },
            })

        except Exception as exc:
            _logger.exception('crm_notifications error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # -----------------------------------------------------------------------
    # POST /api/crm/notifications/mark_read
    # -----------------------------------------------------------------------

    @http.route('/api/crm/notifications/mark_read', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def mark_read(self, **kwargs):
        """
        Mark notifications as read.

        JSON body options:

          // Mark all unread messages in a chat conversation as read
          { "type": "chat", "conversation_id": 8 }

          // Mark specific email messages as read
          { "type": "email", "message_ids": [55, 56, 57] }

          // Mark everything read (all chat conversations + all inbox emails)
          { "type": "all" }

        Response:
          {
            "success": true,
            "data": {
              "chat_marked":  <int>,    // number of chat messages marked read
              "email_marked": <int>     // number of email messages marked read
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        uid = ensure_jwt_user_id()
        if not uid:
            return _json_response({'success': False, 'error': 'Unauthorized'}, 401)

        try:
            body        = json.loads(request.httprequest.data or '{}')
            mark_type   = (body.get('type') or 'all').lower()
            chat_marked = 0
            email_marked = 0

            # ── Chat mark read ────────────────────────────────────────────
            if mark_type in ('chat', 'all') and 'lugal.supply.message' in request.env:
                Msg  = request.env['lugal.supply.message'].sudo()
                Conv = request.env['lugal.supply.conversation'].sudo()

                if mark_type == 'chat' and body.get('conversation_id'):
                    conv_ids = [int(body['conversation_id'])]
                else:
                    convs = Conv.search([
                        ('is_archived', '=', False),
                        ('participant_ids', 'in', [uid]),
                    ])
                    conv_ids = convs.ids

                for conv_id in conv_ids:
                    unread = Msg.search([
                        ('conversation_id', '=', conv_id),
                        ('sender_id', '!=', uid),
                        ('read_user_ids', 'not in', [uid]),
                        ('is_deleted', '=', False),
                    ])
                    if unread:
                        unread.write({'read_user_ids': [(4, uid)]})
                        chat_marked += len(unread)
                        # Notify senders via bus
                        try:
                            senders = set(unread.mapped('sender_id.id')) - {uid}
                            for sender_uid in senders:
                                request.env['bus.bus'].sudo()._sendone(
                                    f'supply_user.{sender_uid}',
                                    'supply.chat.message.read',
                                    {
                                        'conversation_id': conv_id,
                                        'read_by_uid': uid,
                                        'message_ids': unread.ids,
                                    },
                                )
                        except Exception as bus_exc:
                            _logger.debug('bus notify error: %s', bus_exc)

            # ── Email mark read ───────────────────────────────────────────
            if mark_type in ('email', 'all') and 'lugal.email.message' in request.env:
                EmailMsg = request.env['lugal.email.message'].sudo()
                Acc      = request.env['lugal.email.account'].sudo()
                acc_ids  = Acc.search([('user_id', '=', uid)]).ids

                if mark_type == 'email' and body.get('message_ids'):
                    msgs = EmailMsg.search([
                        ('id', 'in', [int(i) for i in body['message_ids']]),
                        ('account_id', 'in', acc_ids),
                    ])
                else:
                    msgs = EmailMsg.search([
                        ('account_id', 'in', acc_ids),
                        ('folder', '=', 'inbox'),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ])

                if msgs:
                    msgs.write({'is_read': True})
                    email_marked = len(msgs)

            return _json_response({
                'success': True,
                'data': {
                    'chat_marked':  chat_marked,
                    'email_marked': email_marked,
                },
            })

        except Exception as exc:
            _logger.exception('crm_notifications_mark_read error')
            return _json_response({'success': False, 'error': str(exc)}, 500)
