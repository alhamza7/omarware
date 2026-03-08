# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _channel_config_to_dict(config):
    """Serialize channel config including SLA and work hours fields."""
    return {
        'id': config.id,
        'channel': config.channel,
        'display_name': config.display_name or '',
        'color_hex': config.color_hex or '',
        'icon': config.icon or '',
        'branch_id': config.branch_id.id if config.branch_id else None,
        'branch_name': config.branch_id.name if config.branch_id else '',
        'assigned_user_ids': config.assigned_user_ids.ids,
        'assigned_user_names': [u.name for u in config.assigned_user_ids],
        'is_free_for_all': config.is_free_for_all,
        'is_active': config.is_active,
        'sla_threshold_seconds': config.sla_threshold_seconds,
        'work_hours_start': config.work_hours_start,
        'work_hours_end': config.work_hours_end,
    }


def _message_to_dict(m):
    """Serialize omnichannel message to dict."""
    return {
        'id': m.id,
        'customer_id': m.customer_id.id if m.customer_id else None,
        'customer_name': m.customer_id.name if m.customer_id else '',
        'channel': m.channel,
        'direction': m.direction,
        'channel_identity_id': m.channel_identity_id.id if m.channel_identity_id else None,
        'content': m.content or '',
        'media_url': m.media_url or '',
        'sent_at': m.sent_at.isoformat() if m.sent_at else None,
        'read_at': m.read_at.isoformat() if m.read_at else None,
        'replied_by_agent_at': m.replied_by_agent_at.isoformat() if m.replied_by_agent_at else None,
        'assigned_to_id': m.assigned_to_id.id if m.assigned_to_id else None,
        'assigned_to_name': m.assigned_to_id.name if m.assigned_to_id else '',
        'owner_id': m.owner_id.id if m.owner_id else None,
        'owner_name': m.owner_id.name if m.owner_id else '',
        'conversation_id': m.conversation_id or '',
        'status': m.status,
        'sla_breached': m.sla_breached,
        'waiting_customer_response': m.waiting_customer_response,
        'branch_id': m.branch_id.id if m.branch_id else None,
    }


class ChannelController(http.Controller):

    # ─── Channel Config ────────────────────────────────────────────────────

    @http.route('/api/crm/channels/config_list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def config_list(self, branch_id=None, **kwargs):
        """List channel configs, optionally filtered by branch."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            configs = request.env['lugal.crm.channel.config'].search(domain, order='channel asc')
            return {'success': True, 'data': {'items': [_channel_config_to_dict(c) for c in configs]}}
        except Exception as e:
            return crm_error(e, 'config_list')

    @http.route('/api/crm/channels/config/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def config_create(self, channel, branch_id=None, display_name=None, color_hex=None,
                      is_free_for_all=True, sla_threshold_seconds=300,
                      work_hours_start=8.0, work_hours_end=18.0, **kwargs):
        """Create a new channel configuration."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            config = request.env['lugal.crm.channel.config'].create({
                'channel': channel,
                'branch_id': branch_id,
                'display_name': display_name or '',
                'color_hex': color_hex or '',
                'is_free_for_all': is_free_for_all,
                'sla_threshold_seconds': sla_threshold_seconds,
                'work_hours_start': work_hours_start,
                'work_hours_end': work_hours_end,
            })
            return {'success': True, 'data': _channel_config_to_dict(config)}
        except Exception as e:
            return crm_error(e, 'config_create')

    @http.route('/api/crm/channels/config/<int:config_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def config_update(self, config_id, **kwargs):
        """Update channel config (including SLA, work hours, assignments)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            config = request.env['lugal.crm.channel.config'].browse(config_id)
            if not config.exists() or config.is_deleted:
                return {'success': False, 'error': 'Config not found'}
            allowed = {
                'display_name', 'color_hex', 'icon', 'branch_id', 'is_free_for_all',
                'is_active', 'sla_threshold_seconds', 'work_hours_start', 'work_hours_end',
            }
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            # Handle assigned_user_ids separately (list replacement)
            if 'assigned_user_ids' in kwargs and kwargs['assigned_user_ids'] is not None:
                vals['assigned_user_ids'] = [(6, 0, kwargs['assigned_user_ids'])]
            if vals:
                config.write(vals)
            return {'success': True, 'data': _channel_config_to_dict(config)}
        except Exception as e:
            return crm_error(e, 'config_update')

    @http.route('/api/crm/channels/config/<int:config_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def config_delete(self, config_id, **kwargs):
        """Soft-delete a channel configuration."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            config = request.env['lugal.crm.channel.config'].browse(config_id)
            if not config.exists():
                return {'success': False, 'error': 'Config not found'}
            config.write({'is_deleted': True, 'active': False, 'is_active': False})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'config_delete')

    # ─── Messages ─────────────────────────────────────────────────────────

    @http.route('/api/crm/channels/messages/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_list(self, page=1, per_page=50, customer_id=None, channel=None, status=None,
                     branch_id=None, assigned_to_id=None, sla_breached=None, **kwargs):
        """List omnichannel inbox messages with filters."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
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
            Message = request.env['lugal.crm.omnichannel.message']
            total = Message.search_count(domain)
            offset = (page - 1) * per_page
            messages = Message.search(domain, limit=per_page, offset=offset, order='sent_at desc')
            return {
                'success': True,
                'data': {
                    'items': [_message_to_dict(m) for m in messages],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'message_list')

    @http.route('/api/crm/channels/messages/conversation', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def conversation(self, conversation_id, **kwargs):
        """Get full conversation thread by conversation_id."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not conversation_id:
                return {'success': False, 'error': 'conversation_id required'}
            messages = request.env['lugal.crm.omnichannel.message'].search([
                ('conversation_id', '=', conversation_id),
                ('is_deleted', '=', False),
            ], order='sent_at asc')
            return {'success': True, 'data': {'items': [_message_to_dict(m) for m in messages]}}
        except Exception as e:
            return crm_error(e, 'conversation')

    @http.route('/api/crm/channels/messages/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_create(self, customer_id, channel, content, direction='inbound',
                       conversation_id=None, branch_id=None, media_url=None, **kwargs):
        """
        Create a new inbound or outbound message.
        For outbound: sets replied_by_agent_at, waiting_customer_response, owner_id.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            from odoo.fields import Datetime
            vals = {
                'customer_id': customer_id,
                'channel': channel,
                'direction': direction,
                'content': content,
                'sent_at': Datetime.now(),
                'conversation_id': conversation_id,
                'branch_id': branch_id,
                'media_url': media_url,
                'status': 'pending' if direction == 'inbound' else 'assigned',
            }
            if direction == 'outbound':
                uid = request.env.uid
                vals['assigned_to_id'] = uid
                vals['replied_by_agent_at'] = Datetime.now()
                vals['owner_id'] = uid
                vals['waiting_customer_response'] = True
            msg = request.env['lugal.crm.omnichannel.message'].create(
                {k: v for k, v in vals.items() if v is not None})
            crm_audit('message_created', customer_id=customer_id,
                      record_model='lugal.crm.omnichannel.message', record_id=msg.id,
                      details={'channel': channel, 'direction': direction})
            return {'success': True, 'data': _message_to_dict(msg)}
        except Exception as e:
            return crm_error(e, 'message_create')

    @http.route('/api/crm/channels/messages/<int:message_id>/assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_assign(self, message_id, assigned_to_id=None, **kwargs):
        """Assign a conversation to a user (or current user)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            msg = request.env['lugal.crm.omnichannel.message'].browse(message_id)
            if not msg.exists() or msg.is_deleted:
                return {'success': False, 'error': 'Message not found'}
            uid = assigned_to_id or request.env.uid
            msg.write({'assigned_to_id': uid, 'status': 'assigned'})
            return {'success': True, 'data': _message_to_dict(msg)}
        except Exception as e:
            return crm_error(e, 'message_assign')

    @http.route('/api/crm/channels/messages/<int:message_id>/reply', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_reply(self, message_id, content, media_url=None, **kwargs):
        """
        Send an outbound reply to a message.
        Creates a new outbound message, sets ownership, FRT, and waiting_customer_response.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            from odoo.fields import Datetime
            original = request.env['lugal.crm.omnichannel.message'].browse(message_id)
            if not original.exists() or original.is_deleted:
                return {'success': False, 'error': 'Message not found'}

            uid = request.env.uid
            now = Datetime.now()

            # Mark original as owned if not already
            if not original.owner_id:
                original.write({'owner_id': uid})

            # Create outbound reply
            reply = request.env['lugal.crm.omnichannel.message'].create({
                'customer_id': original.customer_id.id,
                'channel': original.channel,
                'direction': 'outbound',
                'content': content,
                'sent_at': now,
                'conversation_id': original.conversation_id,
                'branch_id': original.branch_id.id if original.branch_id else False,
                'assigned_to_id': uid,
                'owner_id': uid,
                'replied_by_agent_at': now,
                'waiting_customer_response': True,
                'status': 'assigned',
                'media_url': media_url,
            })

            # Mark original as replied
            original.write({
                'status': 'assigned',
                'replied_by_agent_at': original.replied_by_agent_at or now,
                'waiting_customer_response': True,
            })

            crm_audit('message_replied',
                      customer_id=original.customer_id.id if original.customer_id else None,
                      record_model='lugal.crm.omnichannel.message', record_id=reply.id,
                      details={'channel': original.channel, 'conversation_id': original.conversation_id})
            return {'success': True, 'data': _message_to_dict(reply)}
        except Exception as e:
            return crm_error(e, 'message_reply')

    @http.route('/api/crm/channels/messages/<int:message_id>/resolve', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_resolve(self, message_id, **kwargs):
        """Mark a conversation as resolved."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            msg = request.env['lugal.crm.omnichannel.message'].browse(message_id)
            if not msg.exists() or msg.is_deleted:
                return {'success': False, 'error': 'Message not found'}
            msg.write({'status': 'resolved', 'waiting_customer_response': False})
            # Resolve all messages in same conversation
            if msg.conversation_id:
                request.env['lugal.crm.omnichannel.message'].search([
                    ('conversation_id', '=', msg.conversation_id),
                    ('status', '!=', 'resolved'),
                    ('is_deleted', '=', False),
                ]).write({'status': 'resolved'})
            crm_audit('message_resolved',
                      customer_id=msg.customer_id.id if msg.customer_id else None,
                      record_model='lugal.crm.omnichannel.message', record_id=message_id,
                      details={'conversation_id': msg.conversation_id})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'message_resolve')

    @http.route('/api/crm/channels/messages/<int:message_id>/transfer', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_transfer(self, message_id, new_owner_id, **kwargs):
        """Transfer conversation ownership to another agent."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            msg = request.env['lugal.crm.omnichannel.message'].browse(message_id)
            if not msg.exists() or msg.is_deleted:
                return {'success': False, 'error': 'Message not found'}
            # Transfer all messages in conversation
            if msg.conversation_id:
                request.env['lugal.crm.omnichannel.message'].search([
                    ('conversation_id', '=', msg.conversation_id),
                    ('is_deleted', '=', False),
                ]).write({'owner_id': new_owner_id, 'assigned_to_id': new_owner_id})
            else:
                msg.write({'owner_id': new_owner_id, 'assigned_to_id': new_owner_id})
            crm_audit('message_transferred',
                      customer_id=msg.customer_id.id if msg.customer_id else None,
                      record_model='lugal.crm.omnichannel.message', record_id=message_id,
                      details={'new_owner_id': new_owner_id, 'conversation_id': msg.conversation_id})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'message_transfer')
