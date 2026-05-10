# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._error import crm_error
from ._permissions import require_permission

_logger = logging.getLogger(__name__)


def _call_to_dict(call):
    """Serialize lugal.crm.call to dict."""
    return {
        'id': call.id,
        'customer_id': call.customer_id.id if call.customer_id else None,
        'customer_name': call.customer_id.name if call.customer_id else '',
        'agent_id': call.agent_id.id if call.agent_id else None,
        'agent_name': call.agent_id.name if call.agent_id else '',
        'branch_id': call.branch_id.id if call.branch_id else None,
        'call_type': call.call_type or '',
        'channel': call.channel or '',
        'caller_number': call.caller_number or '',
        'duration_seconds': call.duration_seconds,
        'started_at': call.started_at.isoformat() if call.started_at else None,
        'ended_at': call.ended_at.isoformat() if call.ended_at else None,
        'outcome': call.outcome or '',
        'notes': call.notes or '',
        'ai_summary': call.ai_summary or '',
        'qa_score': call.qa_score,
        'issues_found': call.issues_found or '',
        'balance_at_call': call.balance_at_call,
        'outstanding_at_call': call.outstanding_at_call,
        'credit_limit_at_call': call.credit_limit_at_call,
        'catalogue_sent': call.catalogue_sent,
        'catalogue_sent_via': call.catalogue_sent_via or '',
        'recording_url': call.recording_url or '',
        'pos_order_id': call.pos_order_id,
        'pos_order_name': call.pos_order_name or '',
        'pos_order_total': call.pos_order_total,
        'pos_order_state': call.pos_order_state or '',
        'created_at': call.create_date.isoformat() if call.create_date else None,
    }


class CallController(http.Controller):

    @http.route('/api/crm/calls/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_calls(self, page=1, per_page=50, customer_id=None, branch_id=None, agent_id=None,
                   date_from=None, date_to=None, outcome=None, **kwargs):
        """List call records with filters."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.list')
            if denied:
                return denied
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if agent_id:
                domain.append(('agent_id', '=', agent_id))
            if outcome:
                domain.append(('outcome', '=', outcome))
            if date_from:
                domain.append(('started_at', '>=', date_from))
            if date_to:
                domain.append(('started_at', '<=', date_to))
            Call = request.env['lugal.crm.call']
            total = Call.search_count(domain)
            offset = (page - 1) * per_page
            calls = Call.search(domain, limit=per_page, offset=offset, order='started_at desc')
            return {
                'success': True,
                'data': {
                    'items': [_call_to_dict(c) for c in calls],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'list_calls')

    @http.route('/api/crm/calls/<int:call_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_call(self, call_id, **kwargs):
        """Get single call by ID."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.view')
            if denied:
                return denied
            call = request.env['lugal.crm.call'].browse(call_id)
            if not call.exists() or call.is_deleted:
                return {'success': False, 'error': 'Call not found'}
            return {'success': True, 'data': _call_to_dict(call)}
        except Exception as e:
            return crm_error(e, 'get_call')

    @http.route('/api/crm/calls/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_call(self, customer_id, call_type='inbound', channel=None, caller_number=None, branch_id=None, **kwargs):
        """Start a new call record."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.create')
            if denied:
                return denied
            from odoo.fields import Datetime
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists():
                return {'success': False, 'error': 'Customer not found'}

            # Snapshot financial data at call time
            balance = customer.credit_debt or 0.0
            outstanding = 0.0
            credit_limit = customer.credit_limit or 0.0

            call = request.env['lugal.crm.call'].create({
                'customer_id': customer_id,
                'agent_id': request.env.uid,
                'call_type': call_type,
                'channel': channel or '',
                'caller_number': caller_number or '',
                'branch_id': branch_id,
                'started_at': Datetime.now(),
                'balance_at_call': balance,
                'outstanding_at_call': outstanding,
                'credit_limit_at_call': credit_limit,
            })
            # Update customer last_call_date
            customer.write({'last_call_date': Datetime.now()})
            crm_audit('call_created', customer_id=customer_id,
                      record_model='lugal.crm.call', record_id=call.id,
                      details={'call_type': call_type, 'channel': channel, 'caller_number': caller_number})
            return {'success': True, 'data': _call_to_dict(call)}
        except Exception as e:
            return crm_error(e, 'create_call')

    @http.route('/api/crm/calls/<int:call_id>/end', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def end_call(self, call_id, duration_seconds=None, outcome=None, notes=None,
                 catalogue_sent=None, catalogue_sent_via=None, recording_url=None, **kwargs):
        """End a call and set outcome, notes, recording URL."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.edit')
            if denied:
                return denied
            from odoo.fields import Datetime
            call = request.env['lugal.crm.call'].browse(call_id)
            if not call.exists() or call.is_deleted:
                return {'success': False, 'error': 'Call not found'}
            vals = {'ended_at': Datetime.now()}
            if duration_seconds is not None:
                vals['duration_seconds'] = duration_seconds
            if outcome is not None:
                vals['outcome'] = outcome
            if notes is not None:
                vals['notes'] = notes
            if catalogue_sent is not None:
                vals['catalogue_sent'] = catalogue_sent
            if catalogue_sent_via is not None:
                vals['catalogue_sent_via'] = catalogue_sent_via
            if recording_url is not None:
                vals['recording_url'] = recording_url
            call.write(vals)
            crm_audit('call_ended', customer_id=call.customer_id.id if call.customer_id else None,
                      record_model='lugal.crm.call', record_id=call.id,
                      details={'outcome': outcome, 'duration_seconds': duration_seconds})
            return {'success': True, 'data': _call_to_dict(call)}
        except Exception as e:
            return crm_error(e, 'end_call')

    @http.route('/api/crm/calls/<int:call_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_call(self, call_id, **kwargs):
        """Update any writable call field (QA score, notes, recording URL, etc.)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.edit')
            if denied:
                return denied
            call = request.env['lugal.crm.call'].browse(call_id)
            if not call.exists() or call.is_deleted:
                return {'success': False, 'error': 'Call not found'}
            allowed = {
                'notes', 'ai_summary', 'qa_score', 'issues_found',
                'outcome', 'recording_url', 'catalogue_sent', 'catalogue_sent_via',
                'pos_order_id', 'pos_order_name', 'pos_order_total',
                'pos_order_total_iqd', 'pos_order_state', 'pos_sale_order_name', 'pos_sap_synced',
            }
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                call.write(vals)
            return {'success': True, 'data': _call_to_dict(call)}
        except Exception as e:
            return crm_error(e, 'update_call')

    @http.route('/api/crm/calls/<int:call_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_call(self, call_id, **kwargs):
        """Soft-delete a call record."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.delete')
            if denied:
                return denied
            call = request.env['lugal.crm.call'].browse(call_id)
            if not call.exists():
                return {'success': False, 'error': 'Call not found'}
            call.write({'is_deleted': True, 'active': False})
            crm_audit('call_deleted', customer_id=call.customer_id.id if call.customer_id else None,
                      record_model='lugal.crm.call', record_id=call_id)
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_call')

    @http.route('/api/crm/calls/<int:call_id>/attach_recording', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def attach_recording(self, call_id, recording_url, **kwargs):
        """Attach recording URL to an existing call."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.edit')
            if denied:
                return denied
            call = request.env['lugal.crm.call'].browse(call_id)
            if not call.exists() or call.is_deleted:
                return {'success': False, 'error': 'Call not found'}
            call.write({'recording_url': recording_url})
            crm_audit('call_recording_attached', customer_id=call.customer_id.id if call.customer_id else None,
                      record_model='lugal.crm.call', record_id=call_id,
                      details={'recording_url': recording_url})
            return {'success': True, 'data': {'id': call.id, 'recording_url': call.recording_url}}
        except Exception as e:
            return crm_error(e, 'attach_recording')

    # ─── Queue ────────────────────────────────────────────────────────────

    @http.route('/api/crm/calls/queue/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def queue_list(self, status='waiting', **kwargs):
        """List calls in queue."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.list')
            if denied:
                return denied
            domain = [('is_deleted', '=', False), ('status', '=', status)]
            Queue = request.env['lugal.crm.call.queue']
            items = Queue.search(domain, order='queue_position asc, queued_at asc')
            data = [{
                'id': q.id,
                'customer_id': q.customer_id.id if q.customer_id else None,
                'customer_name': q.customer_id.name if q.customer_id else '',
                'channel': q.channel or '',
                'caller_number': q.caller_number or '',
                'queue_position': q.queue_position,
                'queued_at': q.queued_at.isoformat() if q.queued_at else None,
                'status': q.status or '',
            } for q in items]
            return {'success': True, 'data': {'items': data}}
        except Exception as e:
            return crm_error(e, 'queue_list')

    @http.route('/api/crm/calls/queue/<int:queue_id>/assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def queue_assign(self, queue_id, **kwargs):
        """Assign a queued call to current user."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('call_centre.create')
            if denied:
                return denied
            q = request.env['lugal.crm.call.queue'].browse(queue_id)
            if not q.exists():
                return {'success': False, 'error': 'Queue entry not found'}
            q.write({'assigned_to_id': request.env.uid, 'status': 'assigned'})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'queue_assign')

    @http.route('/api/crm/calls/queue/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def queue_add(self, customer_id=None, channel=None, caller_number=None, **kwargs):
        """Add an incoming call to the queue."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            from odoo.fields import Datetime
            # Compute next queue position
            last = request.env['lugal.crm.call.queue'].search(
                [('status', '=', 'waiting')], order='queue_position desc', limit=1)
            next_pos = (last.queue_position + 1) if last else 1
            q = request.env['lugal.crm.call.queue'].create({
                'customer_id': customer_id,
                'channel': channel or '',
                'caller_number': caller_number or '',
                'queue_position': next_pos,
                'queued_at': Datetime.now(),
                'status': 'waiting',
            })
            return {'success': True, 'data': {'id': q.id, 'queue_position': q.queue_position}}
        except Exception as e:
            return crm_error(e, 'queue_add')
