# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._error import crm_error
from ._permissions import require_permission

_logger = logging.getLogger(__name__)


def _ticket_to_dict(ticket, include_notes=False):
    """Serialize lugal.crm.ticket to dict."""
    data = {
        'id': ticket.id,
        'customer_id': ticket.customer_id.id if ticket.customer_id else None,
        'customer_name': ticket.customer_id.name if ticket.customer_id else '',
        'branch_id': ticket.branch_id.id if ticket.branch_id else None,
        'assigned_to_id': ticket.assigned_to_id.id if ticket.assigned_to_id else None,
        'assigned_to_name': ticket.assigned_to_id.name if ticket.assigned_to_id else '',
        'escalated_to_id': ticket.escalated_to_id.id if ticket.escalated_to_id else None,
        'escalated_to_name': ticket.escalated_to_id.name if ticket.escalated_to_id else '',
        'title': ticket.title or '',
        'description': ticket.description or '',
        'ticket_type': ticket.ticket_type or '',
        'channel': ticket.channel or '',
        'status': ticket.status or '',
        'priority': ticket.priority or '',
        'sla_deadline': ticket.sla_deadline.isoformat() if ticket.sla_deadline else None,
        'first_response_at': ticket.first_response_at.isoformat() if ticket.first_response_at else None,
        'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        'created_at': ticket.create_date.isoformat() if ticket.create_date else None,
        'updated_at': ticket.write_date.isoformat() if ticket.write_date else None,
    }
    if include_notes:
        notes = request.env['lugal.crm.interaction'].search([
            ('customer_id', '=', ticket.customer_id.id),
            ('channel', '=', f'ticket:{ticket.id}'),
            ('is_deleted', '=', False),
        ], order='interaction_date asc')
        data['notes'] = [{
            'id': n.id,
            'body': n.body or '',
            'author': n.user_id.name if n.user_id else '',
            'date': n.interaction_date.isoformat() if n.interaction_date else None,
        } for n in notes]
    return data


class TicketController(http.Controller):

    @http.route('/api/crm/tickets/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_tickets(self, page=1, per_page=50, customer_id=None, branch_id=None,
                     status=None, priority=None, assigned_to_id=None, **kwargs):
        """List tickets with filters."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.list')
            if denied:
                return denied
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if status:
                domain.append(('status', '=', status))
            if priority:
                domain.append(('priority', '=', priority))
            if assigned_to_id:
                domain.append(('assigned_to_id', '=', assigned_to_id))
            Ticket = request.env['lugal.crm.ticket']
            total = Ticket.search_count(domain)
            offset = (page - 1) * per_page
            tickets = Ticket.search(domain, limit=per_page, offset=offset, order='create_date desc')
            return {
                'success': True,
                'data': {
                    'items': [_ticket_to_dict(t) for t in tickets],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'list_tickets')

    @http.route('/api/crm/tickets/<int:ticket_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_ticket(self, ticket_id, include_notes=False, **kwargs):
        """Get single ticket, optionally with notes/comments."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.view')
            if denied:
                return denied
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            return {'success': True, 'data': _ticket_to_dict(ticket, include_notes=include_notes)}
        except Exception as e:
            return crm_error(e, 'get_ticket')

    @http.route('/api/crm/tickets/search', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def search_tickets(self, query, branch_id=None, limit=30, **kwargs):
        """Search tickets by title or description."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.list')
            if denied:
                return denied
            if not query or len(query.strip()) < 2:
                return {'success': True, 'data': {'items': [], 'total': 0}}
            domain = [
                ('is_deleted', '=', False),
                '|',
                ('title', 'ilike', query.strip()),
                ('description', 'ilike', query.strip()),
            ]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            tickets = request.env['lugal.crm.ticket'].search(domain, limit=limit, order='create_date desc')
            return {'success': True, 'data': {'items': [_ticket_to_dict(t) for t in tickets], 'total': len(tickets)}}
        except Exception as e:
            return crm_error(e, 'search_tickets')

    @http.route('/api/crm/tickets/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_ticket(self, customer_id, title, description=None, branch_id=None,
                      ticket_type=None, channel=None, priority='medium', sla_deadline=None, **kwargs):
        """Create a new ticket."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.create')
            if denied:
                return denied
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists():
                return {'success': False, 'error': 'Customer not found'}
            vals = {
                'customer_id': customer_id,
                'title': title,
                'description': description or '',
                'branch_id': branch_id,
                'ticket_type': ticket_type or '',
                'channel': channel or '',
                'priority': priority,
            }
            if sla_deadline:
                vals['sla_deadline'] = sla_deadline
            ticket = request.env['lugal.crm.ticket'].create(vals)
            crm_audit('ticket_created', customer_id=customer_id,
                      record_model='lugal.crm.ticket', record_id=ticket.id,
                      details={'title': title, 'priority': priority, 'ticket_type': ticket_type})
            return {'success': True, 'data': _ticket_to_dict(ticket)}
        except Exception as e:
            return crm_error(e, 'create_ticket')

    @http.route('/api/crm/tickets/<int:ticket_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_ticket(self, ticket_id, **kwargs):
        """Update ticket fields (title, description, priority, ticket_type, channel, sla_deadline)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.edit')
            if denied:
                return denied
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            allowed = {'title', 'description', 'ticket_type', 'channel', 'priority', 'sla_deadline', 'branch_id'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                ticket.write(vals)
            return {'success': True, 'data': _ticket_to_dict(ticket)}
        except Exception as e:
            return crm_error(e, 'update_ticket')

    @http.route('/api/crm/tickets/<int:ticket_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_status(self, ticket_id, status, **kwargs):
        """Update ticket status. Sets resolved_at when status = resolved."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.close' if status in ('closed', 'resolved', 'done') else 'tickets.edit')
            if denied:
                return denied
            from odoo.fields import Datetime
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            vals = {'status': status}
            if status == 'resolved' and not ticket.resolved_at:
                vals['resolved_at'] = Datetime.now()
            ticket.write(vals)
            crm_audit('ticket_status_changed',
                      customer_id=ticket.customer_id.id if ticket.customer_id else None,
                      record_model='lugal.crm.ticket', record_id=ticket_id,
                      details={'new_status': status})
            return {'success': True, 'data': _ticket_to_dict(ticket)}
        except Exception as e:
            return crm_error(e, 'update_status')

    @http.route('/api/crm/tickets/<int:ticket_id>/assign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def assign_ticket(self, ticket_id, assigned_to_id, **kwargs):
        """Assign ticket to a user; sets first_response_at on first assignment."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.assign')
            if denied:
                return denied
            from odoo.fields import Datetime
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            vals = {'assigned_to_id': assigned_to_id}
            if not ticket.first_response_at:
                vals['first_response_at'] = Datetime.now()
            ticket.write(vals)
            crm_audit('ticket_assigned',
                      customer_id=ticket.customer_id.id if ticket.customer_id else None,
                      record_model='lugal.crm.ticket', record_id=ticket_id,
                      details={'assigned_to_id': assigned_to_id})
            return {'success': True, 'data': _ticket_to_dict(ticket)}
        except Exception as e:
            return crm_error(e, 'assign_ticket')

    @http.route('/api/crm/tickets/<int:ticket_id>/escalate', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def escalate_ticket(self, ticket_id, escalated_to_id, **kwargs):
        """Escalate ticket to another user (supervisor)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.escalate')
            if denied:
                return denied
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            ticket.write({'escalated_to_id': escalated_to_id, 'assigned_to_id': escalated_to_id})
            crm_audit('ticket_escalated',
                      customer_id=ticket.customer_id.id if ticket.customer_id else None,
                      record_model='lugal.crm.ticket', record_id=ticket_id,
                      details={'escalated_to_id': escalated_to_id})
            return {'success': True, 'data': _ticket_to_dict(ticket)}
        except Exception as e:
            return crm_error(e, 'escalate_ticket')

    @http.route('/api/crm/tickets/<int:ticket_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_ticket(self, ticket_id, **kwargs):
        """Soft-delete a ticket."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.delete')
            if denied:
                return denied
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists():
                return {'success': False, 'error': 'Ticket not found'}
            ticket.write({'is_deleted': True, 'active': False})
            crm_audit('ticket_deleted',
                      customer_id=ticket.customer_id.id if ticket.customer_id else None,
                      record_model='lugal.crm.ticket', record_id=ticket_id)
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_ticket')

    @http.route('/api/crm/tickets/<int:ticket_id>/note/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def add_note(self, ticket_id, body, **kwargs):
        """Add an internal note/comment to a ticket (stored as crm.interaction)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.edit')
            if denied:
                return denied
            from odoo.fields import Datetime
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            note = request.env['lugal.crm.interaction'].create({
                'customer_id': ticket.customer_id.id,
                'interaction_type': 'note',
                'channel': f'ticket:{ticket_id}',
                'subject': f'Note on Ticket #{ticket_id}',
                'body': body,
                'interaction_date': Datetime.now(),
                'user_id': request.env.uid,
            })
            return {'success': True, 'data': {
                'id': note.id,
                'body': note.body or '',
                'author': note.user_id.name if note.user_id else '',
                'date': note.interaction_date.isoformat() if note.interaction_date else None,
            }}
        except Exception as e:
            return crm_error(e, 'add_note')

    @http.route('/api/crm/tickets/<int:ticket_id>/notes', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_notes(self, ticket_id, **kwargs):
        """Get all notes/comments for a ticket."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('tickets.view')
            if denied:
                return denied
            ticket = request.env['lugal.crm.ticket'].browse(ticket_id)
            if not ticket.exists() or ticket.is_deleted:
                return {'success': False, 'error': 'Ticket not found'}
            notes = request.env['lugal.crm.interaction'].search([
                ('customer_id', '=', ticket.customer_id.id),
                ('channel', '=', f'ticket:{ticket_id}'),
                ('is_deleted', '=', False),
            ], order='interaction_date asc')
            items = [{
                'id': n.id,
                'body': n.body or '',
                'author': n.user_id.name if n.user_id else '',
                'date': n.interaction_date.isoformat() if n.interaction_date else None,
            } for n in notes]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'get_notes')
