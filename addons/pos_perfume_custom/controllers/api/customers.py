# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Customers

Routes:
  GET  /api/pos_perfume/v1/customers              List / search customers
  POST /api/pos_perfume/v1/customers              Create a new customer
  GET  /api/pos_perfume/v1/customers/<id>         Get a single customer
  PUT  /api/pos_perfume/v1/customers/<id>         Update a customer
"""

import logging
from odoo import http
from odoo.http import request

from ._helpers import _success, _error, _get_json_body, _serialize_customer, _check_auth

_logger = logging.getLogger(__name__)


class PosPerfumeApiCustomers(http.Controller):

    @http.route('/api/pos_perfume/v1/customers', type='http', auth='none', methods=['GET'], csrf=False)
    def list_customers(self, query='', limit='50', offset='0', **kwargs):
        """Search and list customers.

        GET /api/pos_perfume/v1/customers?query=Ahmed&limit=50&offset=0
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            limit = int(limit)
            offset = int(offset)

            domain = [('customer_rank', '>', 0), ('active', '=', True)]
            if query:
                domain += ['|', '|',
                           ('name', 'ilike', query),
                           ('phone', 'ilike', query),
                           ('ref', 'ilike', query)]

            # Use sudo() so record rules (e.g. company) do not hide newly created customers
            Partner = request.env['res.partner'].sudo()
            partners = Partner.search(
                domain, limit=limit, offset=offset, order='id desc, name asc'
            )
            total = Partner.search_count(domain)

            return _success({
                'total': total,
                'offset': offset,
                'limit': limit,
                'items': [_serialize_customer(p) for p in partners],
            })
        except Exception as e:
            _logger.error('[POS API] list_customers: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/customers', type='http', auth='none', methods=['POST'], csrf=False)
    def create_customer(self, **kwargs):
        """Create a new customer.

        POST /api/pos_perfume/v1/customers
        Body: { "name": "...", "phone": "...", "mobile": "...", "email": "..." }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            body = _get_json_body()
            if not body.get('name'):
                return _error('Customer name is required')

            partner_fields = request.env['res.partner']._fields
            vals = {
                'name': body['name'],
                'customer_rank': 1,
                'phone': body.get('phone', ''),
                'email': body.get('email', ''),
                'street': body.get('street', ''),
                'city': body.get('city', ''),
                'ref': body.get('ref', ''),
            }
            # mobile field may not exist in all Odoo versions
            if 'mobile' in partner_fields and body.get('mobile'):
                vals['mobile'] = body['mobile']
            if body.get('country_id'):
                vals['country_id'] = int(body['country_id'])

            partner = request.env['res.partner'].create(vals)
            return _success(_serialize_customer(partner), message='Customer created')
        except Exception as e:
            _logger.error('[POS API] create_customer: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/customers/<int:customer_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_customer(self, customer_id, **kwargs):
        """Get a single customer by ID.

        GET /api/pos_perfume/v1/customers/42
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            partner = request.env['res.partner'].browse(customer_id)
            if not partner.exists():
                return _error('Customer not found', 404)
            return _success(_serialize_customer(partner))
        except Exception as e:
            _logger.error('[POS API] get_customer: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/customers/<int:customer_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_customer(self, customer_id, **kwargs):
        """Update a customer.

        PUT /api/pos_perfume/v1/customers/42
        Body: { "phone": "...", "mobile": "...", ... }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            partner = request.env['res.partner'].browse(customer_id)
            if not partner.exists():
                return _error('Customer not found', 404)

            body = _get_json_body()
            partner_fields = request.env['res.partner']._fields
            # only include fields that actually exist in this Odoo instance
            allowed = ['name', 'phone', 'email', 'street', 'city', 'ref', 'country_id']
            if 'mobile' in partner_fields:
                allowed.append('mobile')
            vals = {k: body[k] for k in allowed if k in body}
            if vals:
                partner.write(vals)
            return _success(_serialize_customer(partner), message='Customer updated')
        except Exception as e:
            _logger.error('[POS API] update_customer: %s', e, exc_info=True)
            return _error(str(e), 500)
