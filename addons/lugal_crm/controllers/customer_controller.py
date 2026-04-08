# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._error import crm_error

_logger = logging.getLogger(__name__)

# Maps incoming social handle field names to their channel key stored in channel_identity
_SOCIAL_HANDLE_CHANNEL_MAP = {
    'instagram_handle': 'instagram',
    'tiktok_handle':    'tiktok',
    'whatsapp_number':  'whatsapp',
    'snapchat_handle':  'snapchat',
    'twitter_handle':   'x',
    'telegram_handle':  'telegram',
    'pinterest_handle': 'pinterest',
    'youtube_handle':   'youtube',
}


def _parse_json_field(raw):
    """Safely parse a JSON text field; returns [] on any failure."""
    import json
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _serialize_branch(branch):
    """Return a flat dict for one lugal.crm.branch record."""
    return {
        'id':               branch.id,
        'name':             branch.name or '',
        'name_ar':          branch.name_ar or '',
        'code':             branch.code or '',
        'city':             branch.city or '',
        'branch_location':  branch.address or '',
        'branch_phone':     branch.phone or '',
        'branch_manager':   branch.manager_id.name if branch.manager_id else '',
    }


def _serialize_attachment(att):
    """Return a flat dict for one ir.attachment record, including the uploader."""
    return {
        'id':          att.id,
        'name':        att.name or '',
        'mimetype':    att.mimetype or '',
        'url':         f'/web/content/{att.id}?download=true',
        'uploaded_by': att.create_uid.name if att.create_uid else '',
    }


def _customer_to_dict(customer):
    """Serialize lugal.crm.customer to a dict for API response (full response contract)."""
    # --- Social handles ---
    social = {ci.channel: ci.handle for ci in customer.channel_identity_ids}

    # --- Branches with all sub-fields ---
    branches = [_serialize_branch(b) for b in customer.branch_ids]

    # --- Attachments with uploader ---
    attachments = [_serialize_attachment(a) for a in customer.attachment_ids]

    # --- Samples (single-record fields flattened into a 1-item list if set) ---
    samples = []
    if customer.sample_version or customer.sample_date or customer.sample_image:
        samples = [{
            'id':       f'sample_{customer.id}',
            'name':     f'Sample – {customer.name}',
            'version':  customer.sample_version or '',
            'dateSent': customer.sample_date.isoformat() if customer.sample_date else None,
            'image':    f'/web/image/lugal.crm.customer/{customer.id}/sample_image' if customer.sample_image else '',
        }]

    # --- Account manager phone (from linked res.users → res.partner) ---
    account_manager_phone = ''
    if customer.account_manager_id and customer.account_manager_id.partner_id:
        account_manager_phone = customer.account_manager_id.partner_id.phone or ''

    return {
        # ── Identity ──────────────────────────────────────────────────────
        'id':                        customer.id,
        'name':                      customer.name,
        'name_ar':                   customer.name_ar or '',
        'partner_id':                customer.partner_id.id if customer.partner_id else None,
        'phone_1':                   customer.phone_1 or '',
        'phone_2':                   customer.phone_2 or '',
        'phone_3':                   customer.phone_3 or '',
        'email':                     customer.email or '',
        # ── Address ───────────────────────────────────────────────────────
        'address':                   customer.address or '',
        'city':                      customer.city or '',
        'state':                     customer.state or '',
        'district':                  customer.district or '',
        'building':                  customer.building or '',
        'postal_code':               customer.postal_code or '',
        'country_id':                customer.country_id.id if customer.country_id else None,
        'country_name':              customer.country_id.name if customer.country_id else '',
        # ── Billing / Shipping ────────────────────────────────────────────
        'shipping_address':          customer.favorite_shipping_address or '',
        'billing_address':           customer.billing_address or '',
        'billing_method':            customer.billing_method or '',
        # ── Classification ────────────────────────────────────────────────
        'stage_id':                  customer.stage_id.id if customer.stage_id else None,
        'stage_name':                customer.stage_id.name if customer.stage_id else '',
        'stage_type':                customer.stage_id.stage_type if customer.stage_id else '',
        'tag_ids':                   customer.tag_ids.ids,
        'tag_names':                 [t.name for t in customer.tag_ids],
        'vip_status':                customer.vip_status,
        'is_enterprise':             customer.is_enterprise,
        # ── Account Manager ───────────────────────────────────────────────
        'account_manager_id':        customer.account_manager_id.id if customer.account_manager_id else None,
        'account_manager_name':      customer.account_manager_id.name if customer.account_manager_id else '',
        'account_manager_phone':     account_manager_phone,
        # ── Relations ─────────────────────────────────────────────────────
        'branch_ids':                customer.branch_ids.ids,
        'branches':                  branches,
        'referral_source':           customer.referral_source or '',
        # ── Location / Shop ───────────────────────────────────────────────
        'shop_name':                 customer.shop_name or '',
        'shop_location':             customer.shop_location or '',
        # ── Loyalty ───────────────────────────────────────────────────────
        'loyalty_points':            customer.loyalty_points,
        'preferred_contact_time':    customer.preferred_contact_time or '',
        'preferred_contact_channel': customer.preferred_contact_channel or '',
        # ── Commerce ──────────────────────────────────────────────────────
        'credit_limit':              customer.credit_limit,
        'lifetime_value':            customer.lifetime_value,
        'credit_debt':               customer.credit_debt,
        # ── Dates ─────────────────────────────────────────────────────────
        'member_since':              customer.member_since.isoformat() if customer.member_since else None,
        'last_call_date':            customer.last_call_date.isoformat() if customer.last_call_date else None,
        'last_purchase_date':        customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
        'days_since_purchase':       customer.days_since_purchase,
        # ── Status ────────────────────────────────────────────────────────
        'open_invoice_status':       customer.open_invoice_status or '',
        'delivery_status':           customer.delivery_status or '',
        # ── Timestamps ────────────────────────────────────────────────────
        'created_at':                customer.create_date.isoformat() if customer.create_date else None,
        'updated_at':                customer.write_date.isoformat() if customer.write_date else None,
        # ── Social handles (flat keys for legacy compat) ───────────────────
        'instagram_handle':          social.get('instagram', ''),
        'tiktok_handle':             social.get('tiktok', ''),
        'whatsapp_number':           social.get('whatsapp', ''),
        'snapchat_handle':           social.get('snapchat', ''),
        'twitter_handle':            social.get('x', ''),
        'telegram_handle':           social.get('telegram', ''),
        'pinterest_handle':          social.get('pinterest', ''),
        'youtube_handle':            social.get('youtube', ''),
        # ── Channel identities (full list with is_primary flag) ────────────
        'channel_identities':        [
            {
                'channel':     ci.channel,
                'handle':      ci.handle,
                'verified':    ci.is_verified,
                'is_primary':  ci.is_primary,
            }
            for ci in customer.channel_identity_ids
        ],
        # ── Extended classification ───────────────────────────────────────
        'activity_type':             customer.activity_type or '',
        'customer_strength':         customer.customer_strength or '',
        'dealing_method':            customer.dealing_method or '',
        'customer_rating':           customer.customer_rating or 0,
        'assigned_agent':            customer.assigned_agent or '',
        # ── Notes ─────────────────────────────────────────────────────────
        'notes':                     customer.notes or '',
        # ── Media (JSON arrays) ───────────────────────────────────────────
        'shop_images':               _parse_json_field(customer.shop_images),
        'customer_docs':             _parse_json_field(customer.customer_docs),
        # ── Attachments ───────────────────────────────────────────────────
        'attachments':               attachments,
        # ── Samples ───────────────────────────────────────────────────────
        'samples':                   samples,
        # ── Preferences ───────────────────────────────────────────────────
        'favorite_fragrance':        customer.favorite_fragrance or '',
        # ── Placeholders (enriched in get_customer via dedicated queries) ──
        'total_orders':              0,
        'activity_timeline':         [],
        'call_log':                  [],
        'payments':                  [],
        'tickets':                   [],
        'follow_ups':                [],
        'internal_notes':            [],
        'top_products':              [],
        # branch sub-fields at root level (backward compat shortcuts)
        'branch_location':           branches[0]['branch_location'] if branches else '',
        'branch_manager':            branches[0]['branch_manager'] if branches else '',
        'branch_phone':              branches[0]['branch_phone'] if branches else '',
        # note_author / internal_note_author are injected by get_customer
        'note_author':               '',
        'internal_note_author':      '',
    }


def _resolve_customer(customer_id):
    """
    Resolve a lugal.crm.customer record by CRM id OR res.partner id.

    The CRM table has its own auto-increment sequence separate from res.partner,
    so frontend clients that stored a partner id (e.g. from POS) can still look
    up the correct CRM record. Priority: CRM id first, then partner_id fallback.
    Returns a recordset (may be empty — caller must check .exists()).
    """
    Customer = request.env['lugal.crm.customer'].sudo()
    customer = Customer.browse(customer_id)
    if customer.exists():
        return customer
    # Fallback: the caller may be passing a res.partner id
    customer = Customer.search([('partner_id', '=', customer_id), ('is_deleted', '=', False)], limit=1)
    return customer


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

    @http.route('/api/crm/customers/setup_stages', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
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
            return crm_error(e, 'setup_stages')

    @http.route('/api/crm/customers/sync_from_odoo', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
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
            return crm_error(e, 'sync_from_odoo')

    @http.route('/api/crm/customers/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
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

            domain = [('is_deleted', '=', False), ('active', '=', True), ('partner_id.active', '=', True)]
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
            Customer = request.env['lugal.crm.customer'].sudo()
            total = Customer.search_count(domain)
            offset = (page - 1) * per_page
            customers = Customer.search(domain, limit=per_page, offset=offset, order='write_date desc')
            items = [_customer_to_dict(c) for c in customers]
            return {
                'success': True,
                'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'list_customers')

    @http.route('/api/crm/customers/<int:customer_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_customer(self, customer_id, **kwargs):
        """
        Return a single customer with all detail-modal data:
        - Full customer fields (addresses, preferences, billing, etc.)
        - account_manager_phone
        - total_orders count
        - branches with location / manager / phone per branch
        - attachments with uploaded_by
        - samples list
        - activity_timeline (calls + interactions + messages + tickets merged)
        - call_log (detailed call records)
        - tickets list
        - follow_ups (lugal.crm.task records)
        - internal_notes (interaction_type='note')
        - top_products (most purchased items)
        - payments stub (account.move lines — empty list when module absent)
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}

            data = _customer_to_dict(customer)

            # ── Channel identities (rich version with is_primary) ─────────
            data['channel_identities'] = [
                {
                    'channel':    c.channel,
                    'handle':     c.handle,
                    'is_verified': c.is_verified,
                    'is_primary': c.is_primary,
                }
                for c in request.env['lugal.crm.channel.identity'].sudo().search([
                    ('customer_id', '=', customer.id), ('is_deleted', '=', False)
                ])
            ]

            # ── Total orders ──────────────────────────────────────────────
            if customer.partner_id:
                data['total_orders'] = request.env['pos.perfume.order'].sudo().search_count([
                    ('partner_id', '=', customer.partner_id.id),
                    ('state', 'not in', ('cancel',)),
                ])
            else:
                data['total_orders'] = 0

            # ── Activity timeline (calls + interactions + messages + tickets) ──
            timeline = []

            calls = request.env['lugal.crm.call'].sudo().search([
                ('customer_id', '=', customer.id), ('is_deleted', '=', False)
            ], limit=100)
            for c in calls:
                timeline.append({
                    'type':             'call',
                    'id':               c.id,
                    'timestamp':        c.started_at.isoformat() if c.started_at else None,
                    'description':      f'{c.call_type} — {c.outcome or ""}',
                    'date':             c.started_at.date().isoformat() if c.started_at else None,
                    'user':             c.agent_id.name if c.agent_id else '',
                })

            interactions = request.env['lugal.crm.interaction'].sudo().search([
                ('customer_id', '=', customer.id),
                ('is_deleted', '=', False),
                ('interaction_type', 'not in', ('note',)),
            ], limit=100)
            for i in interactions:
                timeline.append({
                    'type':        i.interaction_type,
                    'id':          i.id,
                    'timestamp':   i.interaction_date.isoformat() if i.interaction_date else None,
                    'description': i.subject or '',
                    'date':        i.interaction_date.date().isoformat() if i.interaction_date else None,
                    'user':        i.user_id.name if i.user_id else '',
                })

            tickets_for_timeline = request.env['lugal.crm.ticket'].sudo().search([
                ('customer_id', '=', customer.id), ('is_deleted', '=', False)
            ], limit=100)
            for t in tickets_for_timeline:
                timeline.append({
                    'type':        'ticket',
                    'id':          t.id,
                    'timestamp':   t.create_date.isoformat() if t.create_date else None,
                    'description': t.title or '',
                    'date':        t.create_date.date().isoformat() if t.create_date else None,
                    'user':        t.assigned_to_id.name if t.assigned_to_id else '',
                })

            timeline.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
            data['activity_timeline'] = timeline

            # ── Call log (detailed) ───────────────────────────────────────
            call_records = request.env['lugal.crm.call'].sudo().search([
                ('customer_id', '=', customer.id), ('is_deleted', '=', False)
            ], limit=200, order='started_at desc')
            data['call_log'] = [
                {
                    'id':         c.id,
                    'date':       c.started_at.date().isoformat() if c.started_at else None,
                    'time':       c.started_at.strftime('%H:%M') if c.started_at else '',
                    'duration':   str(c.duration_seconds or 0),
                    'agent':      c.agent_id.name if c.agent_id else '',
                    'type':       c.call_type or '',
                    'notes':      c.notes or '',
                    'action':     c.outcome or '',
                    'aiSummary':  '',
                }
                for c in call_records
            ]

            # ── Tickets ───────────────────────────────────────────────────
            ticket_records = request.env['lugal.crm.ticket'].sudo().search([
                ('customer_id', '=', customer.id), ('is_deleted', '=', False)
            ], limit=100, order='create_date desc')
            data['tickets'] = [
                {
                    'id':         t.id,
                    'subject':    t.title or '',
                    'status':     t.status or '',
                    'priority':   t.priority or '',
                    'date':       t.create_date.date().isoformat() if t.create_date else None,
                    'assignedTo': t.assigned_to_id.name if t.assigned_to_id else '',
                }
                for t in ticket_records
            ]

            # ── Follow-ups (tasks) ────────────────────────────────────────
            task_records = request.env['lugal.crm.task'].sudo().search([
                ('customer_id', '=', customer.id), ('is_deleted', '=', False)
            ], limit=100, order='due_date asc')
            data['follow_ups'] = [
                {
                    'id':          t.id,
                    'title':       t.title or '',
                    'description': t.description or '',
                    'dueDate':     t.due_date.isoformat() if t.due_date else None,
                    'assignedTo':  t.assigned_to_id.name if t.assigned_to_id else '',
                    'assignedBy':  t.created_by_id.name if t.created_by_id else '',
                    'priority':    t.priority or '',
                    'status':      t.status or '',
                }
                for t in task_records
            ]

            # ── Internal notes ────────────────────────────────────────────
            note_records = request.env['lugal.crm.interaction'].sudo().search([
                ('customer_id', '=', customer.id),
                ('is_deleted', '=', False),
                ('interaction_type', '=', 'note'),
            ], limit=100, order='interaction_date desc')
            data['internal_notes'] = [
                {
                    'id':                   n.id,
                    'body':                 n.body or '',
                    'date':                 n.interaction_date.isoformat() if n.interaction_date else None,
                    'internal_note_author': n.user_id.name if n.user_id else '',
                    'note_author':          n.user_id.name if n.user_id else '',
                }
                for n in note_records
            ]
            # Convenience root-level shortcuts used by some UI components
            if note_records:
                data['note_author']          = note_records[0].user_id.name if note_records[0].user_id else ''
                data['internal_note_author'] = data['note_author']

            # ── Top products ──────────────────────────────────────────────
            if customer.partner_id:
                lines = request.env['pos.perfume.order.line'].sudo().search([
                    ('order_id.partner_id', '=', customer.partner_id.id),
                    ('order_id.state', 'not in', ('cancel',)),
                ], limit=500)
                product_stats = {}
                for line in lines:
                    pid = line.product_id.id if line.product_id else None
                    if not pid:
                        continue
                    if pid not in product_stats:
                        product_stats[pid] = {
                            'name':         line.product_id.name or '',
                            'quantity':     0.0,
                            'totalSpent':   0.0,
                            'lastPurchase': None,
                        }
                    product_stats[pid]['quantity']   += line.qty or 0
                    product_stats[pid]['totalSpent'] += (line.qty or 0) * (line.unit_price or 0)
                    order_date = line.order_id.create_date
                    if order_date:
                        date_str = order_date.date().isoformat()
                        if not product_stats[pid]['lastPurchase'] or date_str > product_stats[pid]['lastPurchase']:
                            product_stats[pid]['lastPurchase'] = date_str

                top = sorted(product_stats.values(), key=lambda x: x['totalSpent'], reverse=True)[:10]
                data['top_products'] = top
            else:
                data['top_products'] = []

            # ── Payments (account.move lines if module present) ───────────
            try:
                if customer.partner_id:
                    invoices = request.env['account.move'].sudo().search([
                        ('partner_id', '=', customer.partner_id.id),
                        ('move_type', 'in', ('out_invoice', 'out_receipt')),
                        ('state', '=', 'posted'),
                    ], limit=200, order='invoice_date desc')
                    data['payments'] = [
                        {
                            'id':        inv.id,
                            'date':      inv.invoice_date.isoformat() if inv.invoice_date else None,
                            'time':      '',
                            'amount':    inv.amount_total,
                            'method':    inv.invoice_payment_term_id.name if inv.invoice_payment_term_id else '',
                            'user':      inv.invoice_user_id.name if inv.invoice_user_id else '',
                            'source':    inv.ref or '',
                            'invoiceId': inv.name or '',
                            'status':    inv.payment_state or '',
                        }
                        for inv in invoices
                    ]
                else:
                    data['payments'] = []
            except Exception:
                data['payments'] = []

            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'get_customer')

    @http.route('/api/crm/customers/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_customer(self, **kwargs):
        """
        Create a new customer.
        Accepts all lugal.crm.customer fields plus:
        - Social handles (stored as channel_identity records):
            instagram_handle, tiktok_handle, whatsapp_number, snapchat_handle,
            twitter_handle, telegram_handle, pinterest_handle, youtube_handle
        - Extended fields: activity_type, customer_strength, dealing_method,
            customer_rating, assigned_agent, notes
        - Media arrays (serialised as JSON):
            shop_images: list[str]  — image URLs
            customer_docs: list[{type, name, url}]  — document objects
        """
        import json

        # Fields that arrive as lists/objects and need JSON serialisation before storing
        JSON_FIELDS = {'shop_images', 'customer_docs'}
        # Many2many fields that must be wrapped in ORM (6, 0, ids) replace command
        M2M_FIELDS = {'tag_ids', 'branch_ids', 'channel_identity_ids'}

        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Separate social handles from model fields
            social_handles = {
                field: kwargs[field]
                for field in _SOCIAL_HANDLE_CHANNEL_MAP
                if kwargs.get(field)
            }

            customer_fields = request.env['lugal.crm.customer'].sudo()._fields
            vals = {}
            for k, v in kwargs.items():
                if k in _SOCIAL_HANDLE_CHANNEL_MAP or v is None:
                    continue
                if k in JSON_FIELDS:
                    # Serialise list/object payloads to JSON text for storage
                    vals[k] = json.dumps(v) if not isinstance(v, str) else v
                elif k in M2M_FIELDS and isinstance(v, list):
                    # Convert plain id list → ORM replace command [(6, 0, [ids])]
                    # Filter out any ids that are not valid integers to be safe
                    clean_ids = [int(i) for i in v if str(i).isdigit() or isinstance(i, int)]
                    vals[k] = [(6, 0, clean_ids)]
                elif k in customer_fields:
                    vals[k] = v

            if not vals.get('name'):
                return {'success': False, 'error': 'name is required'}

            # Validate M2M ids exist before writing to get clear error messages
            if 'tag_ids' in vals:
                raw_tag_ids = vals['tag_ids'][0][2]
                if raw_tag_ids:
                    existing = request.env['lugal.crm.tag'].sudo().search(
                        [('id', 'in', raw_tag_ids), ('is_deleted', '=', False)]
                    )
                    if len(existing) != len(raw_tag_ids):
                        missing = set(raw_tag_ids) - set(existing.ids)
                        available = request.env['lugal.crm.tag'].sudo().search(
                            [('is_deleted', '=', False), ('active', '=', True)]
                        )
                        return {
                            'success': False,
                            'error': f'tag_ids {list(missing)} do not exist.',
                            'available_tag_ids': [{'id': t.id, 'name': t.name} for t in available],
                        }
            if 'branch_ids' in vals:
                raw_branch_ids = vals['branch_ids'][0][2]
                if raw_branch_ids:
                    existing = request.env['lugal.crm.branch'].sudo().search(
                        [('id', 'in', raw_branch_ids), ('is_deleted', '=', False)]
                    )
                    if len(existing) != len(raw_branch_ids):
                        missing = set(raw_branch_ids) - set(existing.ids)
                        available = request.env['lugal.crm.branch'].sudo().search(
                            [('is_deleted', '=', False), ('active', '=', True)]
                        )
                        return {
                            'success': False,
                            'error': f'branch_ids {list(missing)} do not exist.',
                            'available_branch_ids': [{'id': b.id, 'name': b.name, 'code': b.code} for b in available],
                        }

            customer = request.env['lugal.crm.customer'].sudo().create(vals)

            # Create channel identity records for each provided social handle
            ChannelIdentity = request.env['lugal.crm.channel.identity'].sudo()
            for handle_field, channel_key in _SOCIAL_HANDLE_CHANNEL_MAP.items():
                handle_value = social_handles.get(handle_field)
                if handle_value:
                    ChannelIdentity.create({
                        'customer_id': customer.id,
                        'channel':     channel_key,
                        'handle':      handle_value,
                    })

            crm_audit('customer_created', customer_id=customer.id,
                      record_model='lugal.crm.customer', record_id=customer.id,
                      details={'name': customer.name, 'phone': customer.phone_1})
            return {'success': True, 'data': _customer_to_dict(customer)}
        except ValueError as e:
            request.env.cr.rollback()
            return {'success': False, 'error': str(e), 'code': 'DUPLICATE_CUSTOMER'}
        except Exception as e:
            return crm_error(e, 'create_customer')

    @http.route('/api/crm/customers/<int:customer_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_customer(self, customer_id, **kwargs):
        """
        Partial-update a customer.

        Accepts the same fields as create (all optional):
        - All scalar CRM fields (name, phone_1, stage_id, credit_limit, etc.)
        - Social handles: instagram_handle, tiktok_handle, whatsapp_number,
          snapchat_handle, twitter_handle, telegram_handle, pinterest_handle, youtube_handle
          (upserts the linked channel_identity record for each handle provided)
        - JSON arrays: shop_images (list[str]), customer_docs (list[{type,name,url}])
          (can be passed as Python list or JSON string)
        """
        import json

        JSON_FIELDS = {'shop_images', 'customer_docs'}
        READONLY_FIELDS = {'id', 'create_date', 'create_uid', 'write_date', 'write_uid'}
        M2M_FIELDS = {'tag_ids', 'branch_ids', 'channel_identity_ids'}

        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}

            customer_fields = set(request.env['lugal.crm.customer'].sudo()._fields) - READONLY_FIELDS

            # Separate social handles from model fields
            social_handles = {
                field: kwargs[field]
                for field in _SOCIAL_HANDLE_CHANNEL_MAP
                if kwargs.get(field) is not None
            }

            vals = {}
            for k, v in kwargs.items():
                if k in _SOCIAL_HANDLE_CHANNEL_MAP or v is None:
                    continue
                if k in JSON_FIELDS:
                    vals[k] = json.dumps(v) if not isinstance(v, str) else v
                elif k in M2M_FIELDS and isinstance(v, list):
                    # Convert plain id list → ORM replace command [(6, 0, [ids])]
                    clean_ids = [int(i) for i in v if str(i).isdigit() or isinstance(i, int)]
                    vals[k] = [(6, 0, clean_ids)]
                elif k in customer_fields:
                    vals[k] = v

            if vals:
                # Validate M2M ids exist before writing to get clear error messages
                if 'tag_ids' in vals:
                    raw_tag_ids = vals['tag_ids'][0][2]
                    if raw_tag_ids:
                        existing = request.env['lugal.crm.tag'].sudo().search(
                            [('id', 'in', raw_tag_ids), ('is_deleted', '=', False)]
                        )
                        if len(existing) != len(raw_tag_ids):
                            missing = set(raw_tag_ids) - set(existing.ids)
                            available = request.env['lugal.crm.tag'].sudo().search(
                                [('is_deleted', '=', False), ('active', '=', True)]
                            )
                            return {
                                'success': False,
                                'error': f'tag_ids {list(missing)} do not exist.',
                                'available_tag_ids': [{'id': t.id, 'name': t.name} for t in available],
                            }
                if 'branch_ids' in vals:
                    raw_branch_ids = vals['branch_ids'][0][2]
                    if raw_branch_ids:
                        existing = request.env['lugal.crm.branch'].sudo().search(
                            [('id', 'in', raw_branch_ids), ('is_deleted', '=', False)]
                        )
                        if len(existing) != len(raw_branch_ids):
                            missing = set(raw_branch_ids) - set(existing.ids)
                            available = request.env['lugal.crm.branch'].sudo().search(
                                [('is_deleted', '=', False), ('active', '=', True)]
                            )
                            return {
                                'success': False,
                                'error': f'branch_ids {list(missing)} do not exist.',
                                'available_branch_ids': [{'id': b.id, 'name': b.name, 'code': b.code} for b in available],
                            }
                customer.write(vals)

            # Upsert channel identity records for each provided social handle
            if social_handles:
                ChannelIdentity = request.env['lugal.crm.channel.identity'].sudo()
                for handle_field, channel_key in _SOCIAL_HANDLE_CHANNEL_MAP.items():
                    handle_value = social_handles.get(handle_field)
                    if handle_value is None:
                        continue
                    existing = ChannelIdentity.search([
                        ('customer_id', '=', customer.id),
                        ('channel', '=', channel_key),
                        ('is_deleted', '=', False),
                    ], limit=1)
                    if handle_value == '':
                        # Empty string = delete the handle
                        if existing:
                            existing.write({'is_deleted': True})
                    elif existing:
                        existing.write({'handle': handle_value})
                    else:
                        ChannelIdentity.create({
                            'customer_id': customer.id,
                            'channel':     channel_key,
                            'handle':      handle_value,
                        })

            if vals or social_handles:
                crm_audit('customer_updated', customer_id=customer.id,
                          record_model='lugal.crm.customer', record_id=customer.id,
                          details={'updated_fields': list(vals.keys()) + list(social_handles.keys())})

            return {'success': True, 'data': _customer_to_dict(customer)}
        except Exception as e:
            return crm_error(e, 'update_customer')

    @http.route('/api/crm/customers/<int:customer_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_customer(self, customer_id, **kwargs):
        """Soft-delete customer (set is_deleted=True, active=False) and archive linked res.partner."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            Customer = request.env['lugal.crm.customer'].sudo().with_context(active_test=False)
            Partner  = request.env['res.partner'].sudo()

            # --- Resolve targets (non-deleted CRM records) ---
            # First: try as CRM id
            record = Customer.browse(customer_id)
            if record.exists():
                # Find all non-deleted CRM records sharing the same partner
                if record.partner_id:
                    targets = Customer.search([
                        ('partner_id', '=', record.partner_id.id),
                        ('is_deleted', '=', False),
                    ])
                else:
                    # No partner — only delete this one if it's not already deleted
                    targets = record.filtered(lambda r: not r.is_deleted)
            else:
                # Fallback: treat customer_id as a res.partner id
                targets = Customer.search([
                    ('partner_id', '=', customer_id),
                    ('is_deleted', '=', False),
                ])

            # Nothing active to delete → already clean
            if not targets.exists():
                return {'success': True, 'message': 'Already deleted'}

            customer_name = targets[0].name or ''
            deleted_ids   = targets.ids

            # Collect active partners before writing (write triggers partner sync hook)
            partner_records = targets.mapped('partner_id').filtered(lambda p: p.exists() and p.active)

            # Soft-delete the CRM records
            targets.write({'is_deleted': True, 'active': False})

            # Archive the res.partner records so they disappear from Odoo contacts too
            if partner_records:
                partner_records.with_context(_skip_crm_sync=True).write({'active': False})

            # Audit — pass customer_id=None to avoid FK violation after soft-delete
            crm_audit('customer_deleted',
                      customer_id=None,
                      record_model='lugal.crm.customer',
                      record_id=customer_id,
                      details={'name': customer_name, 'deleted_ids': deleted_ids})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_customer')

    @http.route('/api/crm/customers/<int:customer_id>/kanban_move', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def kanban_move(self, customer_id, stage_id, **kwargs):
        """Move customer to another stage (kanban drag)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            stage = request.env['lugal.crm.customer.stage'].sudo().browse(stage_id)
            if not stage.exists():
                return {'success': False, 'error': 'Stage not found'}
            customer.write({'stage_id': stage_id})
            crm_audit('customer_stage_moved', customer_id=customer.id,
                      record_model='lugal.crm.customer', record_id=customer.id,
                      details={'stage_id': stage_id, 'stage_name': stage.name})
            return {'success': True, 'data': _customer_to_dict(customer)}
        except Exception as e:
            return crm_error(e, 'kanban_move')

    @http.route('/api/crm/customers/search', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
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
            customers = request.env['lugal.crm.customer'].sudo().search(domain, limit=limit, order='write_date desc')
            return {'success': True, 'data': {'items': [_customer_to_dict(c) for c in customers], 'total': len(customers)}}
        except Exception as e:
            return crm_error(e, 'search_customers')

    # ─── 360° Activity Timeline ────────────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/activity', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_activity(self, customer_id, limit=50, offset=0, **kwargs):
        """Return merged, time-sorted activity timeline for a customer (calls + interactions + messages + tickets)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}

            timeline = []

            calls = request.env['lugal.crm.call'].sudo().search([
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

            interactions = request.env['lugal.crm.interaction'].sudo().search([
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

            messages = request.env['lugal.crm.omnichannel.message'].sudo().search([
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

            tickets = request.env['lugal.crm.ticket'].sudo().search([
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
            return crm_error(e, 'customer_activity')

    @http.route('/api/crm/customers/<int:customer_id>/calls', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_calls(self, customer_id, page=1, per_page=20, **kwargs):
        """List all calls for a specific customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('customer_id', '=', customer_id), ('is_deleted', '=', False)]
            Call = request.env['lugal.crm.call'].sudo()
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
            return crm_error(e, 'customer_calls')

    @http.route('/api/crm/customers/<int:customer_id>/tickets', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_tickets(self, customer_id, page=1, per_page=20, **kwargs):
        """List all tickets for a specific customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('customer_id', '=', customer_id), ('is_deleted', '=', False)]
            Ticket = request.env['lugal.crm.ticket'].sudo()
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
            return crm_error(e, 'customer_tickets')

    @http.route('/api/crm/customers/<int:customer_id>/note/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def add_quick_note(self, customer_id, note, **kwargs):
        """Create a quick note interaction on the customer card."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            from odoo.fields import Datetime
            interaction = request.env['lugal.crm.interaction'].sudo().create({
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
            return crm_error(e, 'add_quick_note')

    # ─── Channel Identity Management ───────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def channel_identity_add(self, customer_id, channel, handle, is_primary=False, **kwargs):
        """Add a new channel identity (social handle) to a customer."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            ci = request.env['lugal.crm.channel.identity'].sudo().create({
                'customer_id': customer_id,
                'channel': channel,
                'handle': handle,
                'is_primary': is_primary,
            })
            return {'success': True, 'data': {'id': ci.id, 'channel': ci.channel, 'handle': ci.handle, 'is_primary': ci.is_primary}}
        except Exception as e:
            return crm_error(e, 'channel_identity_add')

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/<int:ci_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def channel_identity_update(self, customer_id, ci_id, **kwargs):
        """Update a channel identity record."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            ci = request.env['lugal.crm.channel.identity'].sudo().browse(ci_id)
            if not ci.exists() or ci.is_deleted or ci.customer_id.id != customer_id:
                return {'success': False, 'error': 'Channel identity not found'}
            allowed = {'channel', 'handle', 'is_primary', 'is_verified', 'notes'}
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                ci.write(vals)
            return {'success': True, 'data': {'id': ci.id, 'channel': ci.channel, 'handle': ci.handle, 'is_primary': ci.is_primary, 'is_verified': ci.is_verified}}
        except Exception as e:
            return crm_error(e, 'channel_identity_update')

    @http.route('/api/crm/customers/<int:customer_id>/channel_identity/<int:ci_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def channel_identity_delete(self, customer_id, ci_id, **kwargs):
        """Soft-delete a channel identity."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            ci = request.env['lugal.crm.channel.identity'].sudo().browse(ci_id)
            if not ci.exists() or ci.customer_id.id != customer_id:
                return {'success': False, 'error': 'Channel identity not found'}
            ci.write({'is_deleted': True})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'channel_identity_delete')

    # ─── Interactions (Activity Log) ───────────────────────────────────────

    @http.route('/api/crm/customers/<int:customer_id>/interactions', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_interactions(self, customer_id, page=1, per_page=50,
                              interaction_type=None, **kwargs):
        """List all interaction records for a customer (full activity log)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            customer = _resolve_customer(customer_id)
            if not customer.exists() or customer.is_deleted:
                return {'success': False, 'error': 'Customer not found'}
            domain = [
                ('customer_id', '=', customer_id),
                ('is_deleted', '=', False),
                ('active', '=', True),
            ]
            if interaction_type:
                domain.append(('interaction_type', '=', interaction_type))
            Interaction = request.env['lugal.crm.interaction'].sudo()
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
            return crm_error(e, 'customer_interactions')

    @http.route('/api/crm/interactions/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
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
            interaction = request.env['lugal.crm.interaction'].sudo().create(vals)
            return {'success': True, 'data': {'id': interaction.id}}
        except Exception as e:
            return crm_error(e, 'create_interaction')
