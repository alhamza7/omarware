# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit

_logger = logging.getLogger(__name__)


def _customer_to_dict(customer):
    """Serialize lugal.crm.customer to a dict for API response."""
    return {
        'id': customer.id,
        'name': customer.name,
        'name_ar': customer.name_ar or '',
        'partner_id': customer.partner_id.id if customer.partner_id else None,
        'phone_1': customer.phone_1 or '',
        'phone_2': customer.phone_2 or '',
        'phone_3': customer.phone_3 or '',
        'email': customer.email or '',
        'address': customer.address or '',
        'city': customer.city or '',
        'country_id': customer.country_id.id if customer.country_id else None,
        'country_name': customer.country_id.name if customer.country_id else '',
        'stage_id': customer.stage_id.id if customer.stage_id else None,
        'stage_name': customer.stage_id.name if customer.stage_id else '',
        'stage_type': customer.stage_id.stage_type if customer.stage_id else '',
        'tag_ids': customer.tag_ids.ids,
        'tag_names': [t.name for t in customer.tag_ids],
        'vip_status': customer.vip_status,
        'is_enterprise': customer.is_enterprise,
        'lifetime_value': customer.lifetime_value,
        'credit_debt': customer.credit_debt,
        'credit_limit': customer.credit_limit,
        'member_since': customer.member_since.isoformat() if customer.member_since else None,
        'last_call_date': customer.last_call_date.isoformat() if customer.last_call_date else None,
        'last_purchase_date': customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
        'days_since_purchase': customer.days_since_purchase,
        'open_invoice_status': customer.open_invoice_status or '',
        'delivery_status': customer.delivery_status or '',
        'branch_ids': customer.branch_ids.ids,
        'account_manager_id': customer.account_manager_id.id if customer.account_manager_id else None,
        'account_manager_name': customer.account_manager_id.name if customer.account_manager_id else '',
        'referral_source': customer.referral_source or '',
        'loyalty_points': customer.loyalty_points,
        'preferred_contact_time': customer.preferred_contact_time or '',
        'preferred_contact_channel': customer.preferred_contact_channel or '',
        'created_at': customer.create_date.isoformat() if customer.create_date else None,
        'updated_at': customer.write_date.isoformat() if customer.write_date else None,
    }


def _ensure_default_stages(env):
    """
    Create the five canonical CRM stages if they do not yet exist.
    Returns a dict mapping stage_type → stage record.
    """
    Stage = env['lugal.crm.customer.stage'].sudo()
    defaults = [
        {'name': 'Lead',       'name_ar': 'عميل محتمل', 'stage_type': 'lead',       'sequence': 10},
        {'name': 'Interested', 'name_ar': 'مهتم',        'stage_type': 'interested', 'sequence': 20},
        {'name': 'Active',     'name_ar': 'عميل نشط',    'stage_type': 'active',     'sequence': 30},
        {'name': 'VIP',        'name_ar': 'VIP',          'stage_type': 'vip',        'sequence': 40},
        {'name': 'Dormant',    'name_ar': 'راكد',         'stage_type': 'dormant',    'sequence': 50},
    ]
    stage_map = {}
    for d in defaults:
        existing = Stage.search([('stage_type', '=', d['stage_type']),
                                 ('is_deleted', '=', False)], limit=1)
        if existing:
            stage_map[d['stage_type']] = existing
        else:
            stage_map[d['stage_type']] = Stage.create(d)
    return stage_map


def _sync_partners_to_crm(env, limit=500):
    """
    Import res.partner records (customer_rank > 0) that have no linked
    lugal.crm.customer yet. Uses the model's own _ensure_crm_customers so
    the partner extension's create logic is respected.
    Returns the count of newly created CRM records.
    """
    Customer = env['lugal.crm.customer'].sudo()
    Partner  = env['res.partner'].sudo()

    existing_partner_ids = Customer.search(
        [('partner_id', '!=', False)]
    ).mapped('partner_id').ids

    partners = Partner.search(
        [('customer_rank', '>', 0),
         ('id', 'not in', existing_partner_ids),
         ('active', '=', True),
         ('type', '=', 'contact')],
        limit=limit,
        order='id asc',
    )

    before = Customer.search_count([('is_deleted', '=', False)])
    partners._ensure_crm_customers()
    after  = Customer.search_count([('is_deleted', '=', False)])
    return after - before


class CustomerController(http.Controller):

    @http.route('/api/crm/customers/setup_stages', type='json', auth='none', csrf=False, methods=['POST'])
    def setup_stages(self, **kwargs):
        """
        Create the five default CRM stages if missing, then assign the 'active'
        stage to every CRM customer that currently has no stage (imported from
        res.partner contacts).
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            stage_map = _ensure_default_stages(request.env)
            active_stage = stage_map.get('active')

            # Assign 'active' stage to customers without a stage
            no_stage = request.env['lugal.crm.customer'].sudo().search(
                [('stage_id', '=', False), ('is_deleted', '=', False)]
            )
            if no_stage and active_stage:
                no_stage.write({'stage_id': active_stage.id})

            return {
                'success': True,
                'data': {
                    'stages_created': len(stage_map),
                    'customers_updated': len(no_stage),
                },
            }
        except Exception as e:
            _logger.exception('setup_stages error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/sync_from_odoo', type='json', auth='none', csrf=False, methods=['POST'])
    def sync_from_odoo(self, **kwargs):
        """
        Import all res.partner contacts (customer_rank > 0) that don't yet
        have a matching lugal.crm.customer record.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            created = _sync_partners_to_crm(request.env)
            total = request.env['lugal.crm.customer'].sudo().search_count(
                [('is_deleted', '=', False)]
            )
            return {'success': True, 'data': {'imported': created, 'total': total}}
        except Exception as e:
            _logger.exception('sync_from_odoo error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/list', type='json', auth='none', csrf=False, methods=['POST'])
    def list_customers(self, page=1, per_page=50, search=None, stage_id=None, branch_id=None, vip_only=False, **kwargs):
        """
        List customers with optional filters and pagination.
        Auto-imports Odoo partners on the first call if the CRM table is empty.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            Customer = request.env['lugal.crm.customer'].sudo()

            # Auto-sync from res.partner if CRM table is empty
            if Customer.search_count([]) == 0:
                _sync_partners_to_crm(request.env)

            # Ensure default stages exist; assign 'active' to un-staged customers
            stage_map = _ensure_default_stages(request.env)
            active_stage = stage_map.get('active')
            no_stage = Customer.search([('stage_id', '=', False), ('is_deleted', '=', False)])
            if no_stage and active_stage:
                no_stage.write({'stage_id': active_stage.id})

            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if stage_id:
                domain.append(('stage_id', '=', stage_id))
            if branch_id:
                domain.append(('branch_ids', 'in', [branch_id]))
            if vip_only:
                domain.append(('vip_status', '=', True))
            if search:
                domain.append('|')
                domain.append(('name', 'ilike', search))
                domain.append(('email', 'ilike', search))
            Customer = request.env['lugal.crm.customer']
            total = Customer.search_count(domain)
            offset = (page - 1) * per_page
            customers = Customer.search(domain, limit=per_page, offset=offset, order='write_date desc')
            items = [_customer_to_dict(c) for c in customers]
            return {
                'success': True,
                'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            _logger.exception('list_customers error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>', type='json', auth='none', csrf=False, methods=['POST'])
    def get_customer(self, customer_id, **kwargs):
        """Get a single customer by ID."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            data = _customer_to_dict(customer)
            # Add channel identities
            data['channel_identities'] = [
                {'channel': c.channel, 'handle': c.handle, 'is_verified': c.is_verified, 'is_primary': c.is_primary}
                for c in customer.env['lugal.crm.channel.identity'].search([
                    ('customer_id', '=', customer.id), ('is_deleted', '=', False)
                ])
            ]
            return {'success': True, 'data': data}
        except Exception as e:
            _logger.exception('get_customer error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/create', type='json', auth='none', csrf=False, methods=['POST'])
    def create_customer(self, **kwargs):
        """Create a new customer. Pass fields as keyword args from JSON body."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {k: v for k, v in kwargs.items() if k in request.env['lugal.crm.customer']._fields and v is not None}
            if not vals.get('name'):
                return {'success': False, 'error': 'name is required'}
            customer = request.env['lugal.crm.customer'].create(vals)
            crm_audit('customer_created', customer_id=customer.id,
                      record_model='lugal.crm.customer', record_id=customer.id,
                      details={'name': customer.name, 'phone': customer.phone_1})
            return {'success': True, 'data': _customer_to_dict(customer)}
        except Exception as e:
            _logger.exception('create_customer error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/update', type='json', auth='none', csrf=False, methods=['POST'])
    def update_customer(self, customer_id, **kwargs):
        """Update customer. Pass only fields to update."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            fields_allow = set(request.env['lugal.crm.customer']._fields) - {'id', 'create_date', 'create_uid', 'write_date', 'write_uid'}
            vals = {k: v for k, v in kwargs.items() if k in fields_allow and v is not None}
            if vals:
                customer.write(vals)
                crm_audit('customer_updated', customer_id=customer.id,
                          record_model='lugal.crm.customer', record_id=customer.id,
                          details={'updated_fields': list(vals.keys())})
            return {'success': True, 'data': _customer_to_dict(customer)}
        except Exception as e:
            _logger.exception('update_customer error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/delete', type='json', auth='none', csrf=False, methods=['POST'])
    def delete_customer(self, customer_id, **kwargs):
        """Soft-delete customer (set is_deleted=True)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists():
                return {'success': False, 'error': 'Customer not found'}
            customer.write({'is_deleted': True, 'active': False})
            crm_audit('customer_deleted', customer_id=customer_id,
                      record_model='lugal.crm.customer', record_id=customer_id,
                      details={'name': customer.name})
            return {'success': True}
        except Exception as e:
            _logger.exception('delete_customer error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/kanban_move', type='json', auth='none', csrf=False, methods=['POST'])
    def kanban_move(self, customer_id, stage_id, **kwargs):
        """Move customer to another stage (kanban drag)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            stage = request.env['lugal.crm.customer.stage'].browse(stage_id)
            if not stage.exists():
                return {'success': False, 'error': 'Stage not found'}
            customer.write({'stage_id': stage_id})
            crm_audit('customer_stage_moved', customer_id=customer.id,
                      record_model='lugal.crm.customer', record_id=customer.id,
                      details={'stage_id': stage_id, 'stage_name': stage.name})
            return {'success': True, 'data': _customer_to_dict(customer)}
        except Exception as e:
            _logger.exception('kanban_move error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/search', type='json', auth='none', csrf=False, methods=['POST'])
    def search_customers(self, query, limit=50, **kwargs):
        """Quick search by name, email, or phone."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not query or len(query.strip()) < 2:
                return {'success': True, 'data': {'items': [], 'total': 0}}
            domain = [
                ('is_deleted', '=', False),
                ('active', '=', True),
                '|', '|',
                ('name', 'ilike', query.strip()),
                ('email', 'ilike', query.strip()),
                ('phone_1', 'ilike', query.strip()),
            ]
            customers = request.env['lugal.crm.customer'].search(domain, limit=limit, order='write_date desc')
            return {'success': True, 'data': {'items': [_customer_to_dict(c) for c in customers], 'total': len(customers)}}
        except Exception as e:
            _logger.exception('search_customers error')
            return {'success': False, 'error': str(e)}

    # ─── 360° Activity Timeline ────────────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/activity', type='json', auth='none', csrf=False, methods=['POST'])
    def customer_activity(self, customer_id, limit=50, offset=0, **kwargs):
        """Return merged, time-sorted activity timeline for a customer (calls + interactions + messages + tickets)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}

            timeline = []

            calls = request.env['lugal.crm.call'].search([
                ('customer_id', '=', customer_id), ('is_deleted', '=', False)
            ], limit=limit)
            for c in calls:
                timeline.append({
                    'type': 'call',
                    'id': c.id,
                    'timestamp': c.started_at.isoformat() if c.started_at else None,
                    'summary': f'{c.call_type} — {c.outcome or "in progress"}',
                    'agent': c.agent_id.name if c.agent_id else '',
                    'duration_seconds': c.duration_seconds,
                    'notes': c.notes or '',
                    'recording_url': c.recording_url or '',
                })

            interactions = request.env['lugal.crm.interaction'].search([
                ('customer_id', '=', customer_id), ('is_deleted', '=', False)
            ], limit=limit)
            for i in interactions:
                timeline.append({
                    'type': 'interaction',
                    'id': i.id,
                    'timestamp': i.interaction_date.isoformat() if i.interaction_date else None,
                    'summary': i.subject or '',
                    'channel': i.channel or '',
                    'agent': i.user_id.name if i.user_id else '',
                    'notes': i.body or '',
                })

            messages = request.env['lugal.crm.omnichannel.message'].search([
                ('customer_id', '=', customer_id), ('is_deleted', '=', False)
            ], limit=limit)
            for m in messages:
                timeline.append({
                    'type': 'message',
                    'id': m.id,
                    'timestamp': m.sent_at.isoformat() if m.sent_at else None,
                    'summary': (m.content or '')[:120],
                    'channel': m.channel or '',
                    'direction': m.direction or '',
                    'agent': m.assigned_to_id.name if m.assigned_to_id else '',
                })

            tickets = request.env['lugal.crm.ticket'].search([
                ('customer_id', '=', customer_id), ('is_deleted', '=', False)
            ], limit=limit)
            for t in tickets:
                timeline.append({
                    'type': 'ticket',
                    'id': t.id,
                    'timestamp': t.create_date.isoformat() if t.create_date else None,
                    'summary': t.subject or '',
                    'status': t.status or '',
                    'priority': t.priority or '',
                    'agent': t.assigned_to_id.name if t.assigned_to_id else '',
                })

            # Sort descending by timestamp
            timeline.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
            paginated = timeline[offset: offset + limit]

            return {'success': True, 'data': {'items': paginated, 'total': len(timeline)}}
        except Exception as e:
            _logger.exception('customer_activity error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/calls', type='json', auth='none', csrf=False, methods=['POST'])
    def customer_calls(self, customer_id, page=1, per_page=20, **kwargs):
        """List all calls for a specific customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('customer_id', '=', customer_id), ('is_deleted', '=', False)]
            Call = request.env['lugal.crm.call']
            total = Call.search_count(domain)
            calls = Call.search(domain, limit=per_page, offset=(page - 1) * per_page, order='started_at desc')
            items = []
            for c in calls:
                items.append({
                    'id': c.id,
                    'call_type': c.call_type,
                    'caller_number': c.caller_number or '',
                    'started_at': c.started_at.isoformat() if c.started_at else None,
                    'ended_at': c.ended_at.isoformat() if c.ended_at else None,
                    'duration_seconds': c.duration_seconds,
                    'outcome': c.outcome or '',
                    'notes': c.notes or '',
                    'recording_url': c.recording_url or '',
                    'agent': c.agent_id.name if c.agent_id else '',
                    'qa_score': c.qa_score,
                    'pos_order_name': c.pos_order_name or '',
                })
            return {'success': True, 'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page}}
        except Exception as e:
            _logger.exception('customer_calls error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/tickets', type='json', auth='none', csrf=False, methods=['POST'])
    def customer_tickets(self, customer_id, page=1, per_page=20, **kwargs):
        """List all tickets for a specific customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('customer_id', '=', customer_id), ('is_deleted', '=', False)]
            Ticket = request.env['lugal.crm.ticket']
            total = Ticket.search_count(domain)
            tickets = Ticket.search(domain, limit=per_page, offset=(page - 1) * per_page, order='create_date desc')
            items = []
            for t in tickets:
                items.append({
                    'id': t.id,
                    'title': t.title or '',
                    'status': t.status or '',
                    'priority': t.priority or '',
                    'ticket_type': t.ticket_type or '',
                    'channel': t.channel or '',
                    'assigned_to': t.assigned_to_id.name if t.assigned_to_id else '',
                    'created_at': t.create_date.isoformat() if t.create_date else None,
                    'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None,
                    'sla_deadline': t.sla_deadline.isoformat() if t.sla_deadline else None,
                })
            return {'success': True, 'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page}}
        except Exception as e:
            _logger.exception('customer_tickets error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/note/add', type='json', auth='none', csrf=False, methods=['POST'])
    def add_quick_note(self, customer_id, note, **kwargs):
        """Create a quick note interaction on the customer card."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            from odoo.fields import Datetime
            interaction = request.env['lugal.crm.interaction'].create({
                'customer_id': customer_id,
                'interaction_date': Datetime.now(),
                'interaction_type': 'note',
                'channel': 'note',
                'subject': 'Quick Note',
                'body': note,
                'user_id': request.env.uid,
            })
            return {'success': True, 'data': {'interaction_id': interaction.id}}
        except Exception as e:
            _logger.exception('add_quick_note error')
            return {'success': False, 'error': str(e)}

    # ─── Channel Identity Management ───────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/add', type='json', auth='none', csrf=False, methods=['POST'])
    def channel_identity_add(self, customer_id, channel, handle, is_primary=False, **kwargs):
        """Add a new channel identity (social handle) to a customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            ci = request.env['lugal.crm.channel.identity'].create({
                'customer_id': customer_id,
                'channel': channel,
                'handle': handle,
                'is_primary': is_primary,
            })
            return {'success': True, 'data': {'id': ci.id, 'channel': ci.channel, 'handle': ci.handle, 'is_primary': ci.is_primary}}
        except Exception as e:
            _logger.exception('channel_identity_add error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/<int:ci_id>/update', type='json', auth='none', csrf=False, methods=['POST'])
    def channel_identity_update(self, customer_id, ci_id, **kwargs):
        """Update a channel identity record."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            ci = request.env['lugal.crm.channel.identity'].browse(ci_id)
            if not ci.exists() or ci.is_deleted or ci.customer_id.id != customer_id:
                return {'success': False, 'error': 'Channel identity not found'}
            allowed = {'channel', 'handle', 'is_primary', 'is_verified', 'notes'}
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                ci.write(vals)
            return {'success': True, 'data': {'id': ci.id, 'channel': ci.channel, 'handle': ci.handle, 'is_primary': ci.is_primary, 'is_verified': ci.is_verified}}
        except Exception as e:
            _logger.exception('channel_identity_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/<int:ci_id>/delete', type='json', auth='none', csrf=False, methods=['POST'])
    def channel_identity_delete(self, customer_id, ci_id, **kwargs):
        """Soft-delete a channel identity."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            ci = request.env['lugal.crm.channel.identity'].browse(ci_id)
            if not ci.exists() or ci.customer_id.id != customer_id:
                return {'success': False, 'error': 'Channel identity not found'}
            ci.write({'is_deleted': True})
            return {'success': True}
        except Exception as e:
            _logger.exception('channel_identity_delete error')
            return {'success': False, 'error': str(e)}

    # ─── Interactions (Activity Log) ───────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/interactions', type='json', auth='none', csrf=False, methods=['POST'])
    def customer_interactions(self, customer_id, page=1, per_page=50,
                              interaction_type=None, **kwargs):
        """List all interaction records for a customer (full activity log)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = request.env['lugal.crm.customer'].browse(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            domain = [
                ('customer_id', '=', customer_id),
                ('is_deleted', '=', False),
                ('active', '=', True),
            ]
            if interaction_type:
                domain.append(('interaction_type', '=', interaction_type))
            Interaction = request.env['lugal.crm.interaction']
            total = Interaction.search_count(domain)
            records = Interaction.search(
                domain, limit=per_page, offset=(page - 1) * per_page,
                order='interaction_date desc',
            )
            items = [{
                'id': r.id,
                'interaction_type': r.interaction_type,
                'channel': r.channel or '',
                'subject': r.subject or '',
                'body': r.body or '',
                'outcome': r.outcome or '',
                'duration_seconds': r.duration_seconds,
                'user_id': r.user_id.id if r.user_id else None,
                'user_name': r.user_id.name if r.user_id else '',
                'interaction_date': r.interaction_date.isoformat() if r.interaction_date else None,
            } for r in records]
            return {
                'success': True,
                'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            _logger.exception('customer_interactions error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/interactions/create', type='json', auth='none', csrf=False, methods=['POST'])
    def create_interaction(self, customer_id, interaction_type, subject=None, body=None,
                           channel=None, outcome=None, duration_seconds=0,
                           interaction_date=None, **kwargs):
        """Create a standalone interaction record for a customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not customer_id or not interaction_type:
                return {'success': False, 'error': 'customer_id and interaction_type are required'}
            from odoo.fields import Datetime
            vals = {
                'customer_id': customer_id,
                'interaction_type': interaction_type,
                'subject': subject or '',
                'body': body or '',
                'channel': channel or interaction_type,
                'outcome': outcome or '',
                'duration_seconds': duration_seconds or 0,
                'interaction_date': interaction_date or Datetime.now(),
                'user_id': request.env.uid,
            }
            interaction = request.env['lugal.crm.interaction'].create(vals)
            return {'success': True, 'data': {'id': interaction.id}}
        except Exception as e:
            _logger.exception('create_interaction error')
            return {'success': False, 'error': str(e)}
