# -*- coding: utf-8 -*-
"""Chat session REST aliases over omnichannel messages (conversation_id threads)."""
import logging
from collections import OrderedDict

from odoo import http
from odoo.http import request
from odoo.fields import Datetime

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .channel_controller import _message_to_dict

_logger = logging.getLogger(__name__)


def _session_domain(page=1, per_page=50, customer_id=None, channel=None, status=None,
                    branch_id=None, assigned_to_id=None, sla_breached=None, **kwargs):
    domain = [('is_deleted', '=', False)]
    if customer_id:
        domain.append(('customer_id', '=', customer_id))
    if channel:
        domain.append(('channel', '=', channel))
    if status:
        domain.append(('status', '=', status))
    if branch_id:
        domain.append(('branch_id', '=', branch_id))
    if assigned_to_id:
        domain.append(('assigned_to_id', '=', assigned_to_id))
    if sla_breached is not None:
        domain.append(('sla_breached', '=', sla_breached))
    return domain


def _aggregate_status(thread_msgs):
    if not thread_msgs:
        return 'resolved'
    if any(m.status != 'resolved' for m in thread_msgs):
        if any(m.status == 'pending' for m in thread_msgs):
            return 'pending'
        return 'assigned'
    return 'resolved'


def _session_summary(conversation_id, thread_msgs):
    thread_msgs = sorted(thread_msgs, key=lambda m: m.sent_at or m.id)
    last = thread_msgs[-1]
    unread = sum(
        1 for m in thread_msgs
        if m.direction == 'inbound' and not m.read_at
    )
    preview = (last.content or '')[:200]
    return {
        'conversation_id': conversation_id,
        'customer_id': last.customer_id.id if last.customer_id else None,
        'customer_name': last.customer_id.name if last.customer_id else '',
        'channel': last.channel,
        'last_message_at': last.sent_at.isoformat() if last.sent_at else None,
        'last_message_preview': preview,
        'unread_count': unread,
        'status': _aggregate_status(thread_msgs),
        'assigned_to_id': last.assigned_to_id.id if last.assigned_to_id else None,
        'assigned_to_name': last.assigned_to_id.name if last.assigned_to_id else '',
        'branch_id': last.branch_id.id if last.branch_id else None,
        'sla_breached': any(m.sla_breached for m in thread_msgs),
    }


class ChatSessionController(http.Controller):
    """Documented under /api/crm/chat/sessions/* — backed by lugal.crm.omnichannel.message."""

    def _group_by_conversation(self, domain):
        Message = request.env['lugal.crm.omnichannel.message']
        domain = domain + [('conversation_id', '!=', False)]
        msgs = Message.search(domain, order='sent_at asc, id asc')
        groups = OrderedDict()
        for m in msgs:
            cid = (m.conversation_id or '').strip()
            if not cid:
                continue
            groups.setdefault(cid, []).append(m)
        return groups

    @http.route('/api/crm/chat/sessions/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def sessions_list(self, page=1, per_page=50, customer_id=None, channel=None, status=None,
                      branch_id=None, assigned_to_id=None, sla_breached=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            base = _session_domain(
                page=page, per_page=per_page, customer_id=customer_id, channel=channel,
                status=status, branch_id=branch_id, assigned_to_id=assigned_to_id,
                sla_breached=sla_breached, **kwargs,
            )
            groups = self._group_by_conversation(base)
            summaries = [
                _session_summary(cid, thread)
                for cid, thread in groups.items()
            ]
            summaries.sort(key=lambda s: s['last_message_at'] or '', reverse=True)
            total = len(summaries)
            page = max(1, int(page or 1))
            per_page = max(1, min(int(per_page or 50), 200))
            offset = (page - 1) * per_page
            page_items = summaries[offset:offset + per_page]
            return {
                'success': True,
                'data': {
                    'items': page_items,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'chat_sessions_list')

    @http.route('/api/crm/chat/sessions/unread_counts', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def sessions_unread_counts(self, branch_id=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('direction', '=', 'inbound'), ('read_at', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            groups = self._group_by_conversation(domain)
            by_channel = {}
            total = 0
            for _cid, thread in groups.items():
                if not any(m.direction == 'inbound' and not m.read_at for m in thread):
                    continue
                last = max(thread, key=lambda m: (m.sent_at or m.id,))
                ch = last.channel or 'unknown'
                by_channel[ch] = by_channel.get(ch, 0) + 1
                total += 1
            return {'success': True, 'data': {'by_channel': by_channel, 'total': total}}
        except Exception as e:
            return crm_error(e, 'chat_sessions_unread_counts')

    @http.route('/api/crm/chat/sessions/<string:session_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def session_detail(self, session_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            cid = (session_id or '').strip()
            if not cid:
                return {'success': False, 'error': 'session_id required'}
            Message = request.env['lugal.crm.omnichannel.message']
            thread = Message.search([
                ('conversation_id', '=', cid),
                ('is_deleted', '=', False),
            ], order='sent_at asc, id asc')
            if not thread:
                return {'success': False, 'error': 'Session not found'}
            now = Datetime.now()
            unread_in = thread.filtered(
                lambda m: m.direction == 'inbound' and not m.read_at
            )
            if unread_in:
                unread_in.write({'read_at': now})
            session = _session_summary(cid, list(thread))
            return {
                'success': True,
                'data': {
                    'session': session,
                    'messages': [_message_to_dict(m) for m in thread],
                },
            }
        except Exception as e:
            return crm_error(e, 'chat_session_detail')

    @http.route(
        '/api/crm/chat/sessions/<string:session_id>/resolve',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def session_resolve(self, session_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            cid = (session_id or '').strip()
            Message = request.env['lugal.crm.omnichannel.message']
            thread = Message.search([
                ('conversation_id', '=', cid),
                ('is_deleted', '=', False),
            ])
            if not thread:
                return {'success': False, 'error': 'Session not found'}
            thread.write({'status': 'resolved'})
            return {'success': True, 'data': _session_summary(cid, list(thread))}
        except Exception as e:
            return crm_error(e, 'chat_session_resolve')

    @http.route(
        '/api/crm/chat/sessions/<string:session_id>/reopen',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def session_reopen(self, session_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            cid = (session_id or '').strip()
            Message = request.env['lugal.crm.omnichannel.message']
            thread = Message.search([
                ('conversation_id', '=', cid),
                ('is_deleted', '=', False),
            ])
            if not thread:
                return {'success': False, 'error': 'Session not found'}
            thread.write({'status': 'pending'})
            return {'success': True, 'data': _session_summary(cid, list(thread))}
        except Exception as e:
            return crm_error(e, 'chat_session_reopen')
