# -*- coding: utf-8 -*-
"""Extended supply-chain JSON-RPC routes:
  - /api/crm/supply/containers/tracking/view | update
  - /api/crm/supply/clearance_companies/*
  - /api/crm/supply/negotiations/*
  - /api/crm/supply/item_requests/*
  - /api/crm/supply/inventory/minmax (list / update / delete)
  - /api/crm/supply/notifications/*
"""

import logging
from odoo import fields, http
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from ._permissions import (
    is_supervisor_or_above,
    is_manager_or_above,
    is_general_manager,
    forbidden,
)
from .supply_chain_controller import _serialize_mail_message

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _s_clearance(c):
    return {
        'id': c.id,
        'name': c.name or '',
        'contact_name': c.contact_name or '',
        'phone': c.phone or '',
        'email': c.email or '',
        'whatsapp': c.whatsapp or '',
        'telegram': c.telegram or '',
        'country_id': c.country_id.id if c.country_id else None,
        'country_name': c.country_id.name if c.country_id else '',
        'city': c.city or '',
        'address': c.address or '',
        'license_number': c.license_number or '',
        'license_expiry': c.license_expiry.isoformat() if c.license_expiry else None,
        'notes': c.notes or '',
        'is_active': bool(c.is_active),
        'created_at': c.create_date.isoformat() if c.create_date else '',
    }


def _s_negotiation(n):
    vendor = n.supply_vendor_id
    partner = n.vendor_id
    product = n.product_id
    cur = n.currency_id
    assigned = n.assigned_user_id
    return {
        'id': n.id,
        'title': n.title or '',
        'supply_vendor_id': vendor.id if vendor else None,
        'supply_vendor_name': vendor.name if vendor else '',
        'vendor_id': partner.id if partner else None,
        'vendor_name': partner.name if partner else '',
        'product_id': product.id if product else None,
        'product_name': product.name if product else (n.product_name or ''),
        'description': n.description or '',
        'quantity': float(n.quantity or 0.0),
        'uom': n.uom or '',
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'expected_price': float(n.expected_price or 0.0),
        'agreed_price': float(n.agreed_price or 0.0),
        'status': n.status or 'open',
        'due_date': n.due_date.isoformat() if n.due_date else None,
        'notes': n.notes or '',
        'assigned_user_id': assigned.id if assigned else None,
        'assigned_user_name': assigned.name if assigned else '',
        'created_at': n.create_date.isoformat() if n.create_date else '',
        'updated_at': n.write_date.isoformat() if n.write_date else '',
    }


def _s_item_request(r):
    product = r.product_id
    req_by = r.requested_by_id
    rev_by = r.reviewed_by_id
    return {
        'id': r.id,
        'product_id': product.id if product else None,
        'product_name': product.name if product else (r.product_name or ''),
        'item_code': r.item_code or '',
        'quantity': float(r.quantity or 0.0),
        'uom': r.uom or '',
        'branch_id': int(r.branch_id or 0),
        'requested_by_id': req_by.id if req_by else None,
        'requested_by_name': req_by.name if req_by else '',
        'status': r.status or 'pending',
        'priority': r.priority or 'normal',
        'note': r.note or '',
        'reviewed_by_id': rev_by.id if rev_by else None,
        'reviewed_by_name': rev_by.name if rev_by else '',
        'reviewed_at': r.reviewed_at.isoformat() if r.reviewed_at else None,
        'created_at': r.create_date.isoformat() if r.create_date else '',
        'updated_at': r.write_date.isoformat() if r.write_date else '',
    }


def _s_minmax(m):
    product = m.product_id
    return {
        'id': m.id,
        'product_id': product.id if product else None,
        'product_name': product.name if product else '',
        'product_code': product.default_code if product else '',
        'branch_id': int(m.branch_id or 0),
        'min_qty': float(m.min_qty or 0.0),
        'max_qty': float(m.max_qty or 0.0),
    }


def _s_notification(n):
    return {
        'id': n.id,
        'user_id': n.user_id.id if n.user_id else None,
        'notif_type': n.notif_type or 'general',
        'title': n.title or '',
        'body': n.body or '',
        'related_type': n.related_type or '',
        'related_id': int(n.related_id or 0),
        'is_read': bool(n.is_read),
        'created_at': n.create_date.isoformat() if n.create_date else '',
    }


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class CrmSupplyExtendedController(http.Controller):

    # =========================================================================
    # Container Tracking
    # =========================================================================

    @http.route('/api/crm/supply/containers/tracking/view', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_container_tracking_view(self, **kwargs):
        """Return tracking info for a container (by container_id param)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            container_id = kwargs.get('container_id')
            if not container_id:
                return {'success': False, 'error': 'container_id is required'}
            c = request.env['lugal.supply.container'].sudo().browse(int(container_id)).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            return {
                'success': True,
                'data': {
                    'id': c.id,
                    'name': c.name or '',
                    'container_number': c.container_number or '',
                    'bl_number': c.bl_number or '',
                    'tracking_url': c.tracking_url or '',
                    'status': c.status or 'waiting',
                    'origin_location': c.origin_location or '',
                    'destination_port': c.destination_port or '',
                    'departure_date': c.departure_date.isoformat() if c.departure_date else None,
                    'eta': c.eta.isoformat() if c.eta else None,
                    'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
                    'division': c.division or '',
                    'total_weight_kg': float(c.total_weight_kg or 0.0),
                    'total_cbm': float(c.total_cbm or 0.0),
                    'clearance_info_delivered': bool(c.clearance_info_delivered),
                    'clearance_info_delivered_at': c.clearance_info_delivered_at.isoformat()
                    if c.clearance_info_delivered_at else None,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_tracking_view')

    @http.route('/api/crm/supply/containers/tracking/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_container_tracking_update(self, **kwargs):
        """Update tracking URL / status on a container."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Forbidden — Supervisor role required to update container tracking')
            container_id = kwargs.get('container_id')
            if not container_id:
                return {'success': False, 'error': 'container_id is required'}
            c = request.env['lugal.supply.container'].sudo().browse(int(container_id)).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            allowed = {'tracking_url', 'status', 'eta', 'departure_date', 'arrived_at'}
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                c.write(vals)
            return {
                'success': True,
                'data': {
                    'id': c.id,
                    'tracking_url': c.tracking_url or '',
                    'status': c.status or 'waiting',
                    'eta': c.eta.isoformat() if c.eta else None,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_tracking_update')

    # =========================================================================
    # Clearance Companies
    # =========================================================================

    @http.route('/api/crm/supply/clearance_companies/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 50)))
            search = (kwargs.get('search') or '').strip()
            domain = [('is_deleted', '=', False)]
            if search:
                domain += ['|', ('name', 'ilike', search), ('contact_name', 'ilike', search)]
            CC = request.env['lugal.supply.clearance.company'].sudo()
            total = CC.search_count(domain)
            rows = CC.search(domain, order='name asc, id asc', limit=per_page, offset=(page - 1) * per_page)
            return {
                'success': True,
                'data': {
                    'items': [_s_clearance(c) for c in rows],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_list')

    @http.route('/api/crm/supply/clearance_companies/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to create clearance companies')
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required'}
            vals = {
                'name': name,
                'contact_name': kwargs.get('contact_name') or False,
                'phone': kwargs.get('phone') or False,
                'email': kwargs.get('email') or False,
                'whatsapp': kwargs.get('whatsapp') or False,
                'telegram': kwargs.get('telegram') or False,
                'city': kwargs.get('city') or False,
                'address': kwargs.get('address') or False,
                'license_number': kwargs.get('license_number') or False,
                'license_expiry': kwargs.get('license_expiry') or False,
                'notes': kwargs.get('notes') or False,
            }
            if kwargs.get('country_id'):
                vals['country_id'] = int(kwargs['country_id'])
            cc = request.env['lugal.supply.clearance.company'].sudo().create(vals)
            return {'success': True, 'data': _s_clearance(cc)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_create')

    @http.route('/api/crm/supply/clearance_companies/<int:company_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_get(self, company_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(company_id).exists()
            if not cc or cc.is_deleted:
                return {'success': False, 'error': 'Company not found'}
            return {'success': True, 'data': _s_clearance(cc)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_get')

    @http.route('/api/crm/supply/clearance_companies/<int:company_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_update(self, company_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to update clearance companies')
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(company_id).exists()
            if not cc or cc.is_deleted:
                return {'success': False, 'error': 'Company not found'}
            allowed = {
                'name', 'contact_name', 'phone', 'email', 'whatsapp', 'telegram',
                'country_id', 'city', 'address', 'license_number', 'license_expiry',
                'notes', 'is_active',
            }
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                cc.write(vals)
            return {'success': True, 'data': _s_clearance(cc)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_update')

    @http.route('/api/crm/supply/clearance_companies/<int:company_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_delete(self, company_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_general_manager():
                return forbidden('Forbidden — General Manager role required to delete clearance companies')
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(company_id).exists()
            if not cc or cc.is_deleted:
                return {'success': False, 'error': 'Company not found'}
            cc.write({'is_deleted': True})
            return {'success': True, 'data': {'id': company_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_delete')

    # =========================================================================
    # Negotiations
    # =========================================================================

    @http.route('/api/crm/supply/negotiations/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 20)))
            domain = [('is_deleted', '=', False)]
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('supply_vendor_id'):
                domain.append(('supply_vendor_id', '=', int(kwargs['supply_vendor_id'])))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('title', 'ilike', search), ('product_name', 'ilike', search)]
            Neg = request.env['lugal.supply.negotiation'].sudo()
            total = Neg.search_count(domain)
            rows = Neg.search(domain, order='write_date desc, id desc', limit=per_page, offset=(page - 1) * per_page)
            return {
                'success': True,
                'data': {'items': [_s_negotiation(n) for n in rows], 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'supply_negotiations_list')

    @http.route('/api/crm/supply/negotiations/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Forbidden — Supervisor role required to create negotiations')
            title = (kwargs.get('title') or '').strip()
            if not title:
                return {'success': False, 'error': 'title is required'}
            vals = {
                'title': title,
                'supply_vendor_id': kwargs.get('supply_vendor_id') or False,
                'vendor_id': kwargs.get('vendor_id') or False,
                'product_id': kwargs.get('product_id') or False,
                'product_name': kwargs.get('product_name') or False,
                'description': kwargs.get('description') or False,
                'quantity': float(kwargs['quantity']) if kwargs.get('quantity') is not None else 0.0,
                'uom': kwargs.get('uom') or False,
                'currency_id': kwargs.get('currency_id') or False,
                'expected_price': float(kwargs['expected_price']) if kwargs.get('expected_price') is not None else 0.0,
                'agreed_price': float(kwargs['agreed_price']) if kwargs.get('agreed_price') is not None else 0.0,
                'status': kwargs.get('status') or 'open',
                'due_date': kwargs.get('due_date') or False,
                'notes': kwargs.get('notes') or False,
                'assigned_user_id': kwargs.get('assigned_user_id') or False,
            }
            n = request.env['lugal.supply.negotiation'].sudo().create(vals)
            return {'success': True, 'data': _s_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_create')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_get(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            return {'success': True, 'data': _s_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_get')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_update(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Forbidden — Supervisor role required to update negotiations')
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            allowed = {
                'title', 'supply_vendor_id', 'vendor_id', 'product_id', 'product_name',
                'description', 'quantity', 'uom', 'currency_id', 'expected_price',
                'agreed_price', 'status', 'due_date', 'notes', 'assigned_user_id',
            }
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                n.write(vals)
            return {'success': True, 'data': _s_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_update')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_delete(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_general_manager():
                return forbidden('Forbidden — General Manager role required to delete negotiations')
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            n.write({'is_deleted': True})
            return {'success': True, 'data': {'id': neg_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_delete')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/comments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_comments_list(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            page = max(1, int(kwargs.get('page') or 1))
            domain = [('model', '=', 'lugal.supply.negotiation'), ('res_id', '=', n.id),
                      ('message_type', 'in', ('comment', 'notification'))]
            Msg = request.env['mail.message'].sudo()
            total = Msg.search_count(domain)
            msgs = Msg.search(domain, order='id desc', limit=50, offset=(page - 1) * 50)
            return {'success': True, 'data': {'total': total, 'items': [_serialize_mail_message(m) for m in msgs]}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_list')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/comments/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_comments_add(self, neg_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            body = (kwargs.get('body') or '').strip()
            if not body:
                return {'success': False, 'error': 'body is required'}
            is_note = bool(kwargs.get('is_note'))
            subtype = 'mail.mt_note' if is_note else 'mail.mt_comment'
            msg = n.with_user(uid).message_post(body=body, message_type='comment', subtype_xmlid=subtype)
            return {'success': True, 'data': _serialize_mail_message(msg)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_add')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/comments/<int:message_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_comments_delete(self, neg_id, message_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Forbidden — Supervisor role required to delete negotiation comments')
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found'}
            msg = request.env['mail.message'].sudo().browse(message_id).exists()
            if not msg or msg.model != 'lugal.supply.negotiation' or msg.res_id != n.id:
                return {'success': False, 'error': 'Message not found'}
            msg.unlink()
            return {'success': True, 'data': {'id': message_id}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_delete')

    # =========================================================================
    # Item Requests
    # =========================================================================

    @http.route('/api/crm/supply/item_requests/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 20)))
            domain = [('is_deleted', '=', False)]
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('branch_id') is not None:
                domain.append(('branch_id', '=', int(kwargs['branch_id'])))
            if kwargs.get('requested_by_id'):
                domain.append(('requested_by_id', '=', int(kwargs['requested_by_id'])))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('product_name', 'ilike', search), ('item_code', 'ilike', search)]
            Req = request.env['lugal.supply.item.request'].sudo()
            total = Req.search_count(domain)
            rows = Req.search(domain, order='write_date desc, id desc', limit=per_page, offset=(page - 1) * per_page)
            return {
                'success': True,
                'data': {'items': [_s_item_request(r) for r in rows], 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'supply_item_requests_list')

    @http.route('/api/crm/supply/item_requests/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_create(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            vals = {
                'product_id': kwargs.get('product_id') or False,
                'product_name': kwargs.get('product_name') or False,
                'item_code': kwargs.get('item_code') or False,
                'quantity': float(kwargs['quantity']) if kwargs.get('quantity') is not None else 1.0,
                'uom': kwargs.get('uom') or False,
                'branch_id': int(kwargs['branch_id']) if kwargs.get('branch_id') is not None else 0,
                'requested_by_id': uid,
                'priority': kwargs.get('priority') or 'normal',
                'note': kwargs.get('note') or False,
                'status': 'pending',
            }
            if not vals['product_id'] and not vals['product_name']:
                return {'success': False, 'error': 'product_id or product_name is required'}
            r = request.env['lugal.supply.item.request'].sudo().create(vals)
            return {'success': True, 'data': _s_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_create')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_get(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Request not found'}
            return {'success': True, 'data': _s_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_get')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_update(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Request not found'}
            allowed = {'product_id', 'product_name', 'item_code', 'quantity', 'uom', 'branch_id', 'priority', 'note'}
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                r.write(vals)
            return {'success': True, 'data': _s_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_update')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_update_status(self, req_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Request not found'}
            new_status = (kwargs.get('status') or '').strip()
            valid = {'pending', 'approved', 'rejected', 'fulfilled'}
            if new_status in ('approved', 'rejected') and not is_supervisor_or_above():
                return forbidden('Forbidden — Supervisor role required to approve or reject item requests')
            if new_status == 'fulfilled' and not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to mark item requests as fulfilled')
            if new_status not in valid:
                return {'success': False, 'error': f'Invalid status. Must be one of: {", ".join(sorted(valid))}'}
            r.write({
                'status': new_status,
                'reviewed_by_id': uid,
                'reviewed_at': fields.Datetime.now(),
            })
            return {'success': True, 'data': _s_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_update_status')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_delete(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to delete item requests')
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Request not found'}
            r.write({'is_deleted': True})
            return {'success': True, 'data': {'id': req_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_delete')

    # =========================================================================
    # Inventory Min/Max
    # =========================================================================

    @http.route('/api/crm/supply/inventory/minmax', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(500, max(1, int(kwargs.get('per_page') or 100)))
            domain = []
            if kwargs.get('branch_id') is not None:
                domain.append(('branch_id', '=', int(kwargs['branch_id'])))
            if kwargs.get('product_id'):
                domain.append(('product_id', '=', int(kwargs['product_id'])))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('product_id.name', 'ilike', search), ('product_id.default_code', 'ilike', search)]
            MM = request.env['lugal.supply.minmax'].sudo()
            total = MM.search_count(domain)
            rows = MM.search(domain, order='product_id asc, branch_id asc', limit=per_page, offset=(page - 1) * per_page)
            return {
                'success': True,
                'data': {'items': [_s_minmax(m) for m in rows], 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_list')

    @http.route('/api/crm/supply/inventory/minmax/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_update(self, **kwargs):
        """Upsert min/max rule for a product+branch combination."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to set inventory min/max rules')
            product_id = kwargs.get('product_id')
            if not product_id:
                return {'success': False, 'error': 'product_id is required'}
            branch_id = int(kwargs.get('branch_id') or 0)
            min_qty = float(kwargs.get('min_qty') or 0.0)
            max_qty = float(kwargs.get('max_qty') or 0.0)
            MM = request.env['lugal.supply.minmax'].sudo()
            existing = MM.search([('product_id', '=', int(product_id)), ('branch_id', '=', branch_id)], limit=1)
            if existing:
                existing.write({'min_qty': min_qty, 'max_qty': max_qty})
                record = existing
            else:
                record = MM.create({
                    'product_id': int(product_id),
                    'branch_id': branch_id,
                    'min_qty': min_qty,
                    'max_qty': max_qty,
                })
            return {'success': True, 'data': _s_minmax(record)}
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_update')

    @http.route('/api/crm/supply/inventory/minmax/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_delete(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_manager_or_above():
                return forbidden('Forbidden — Manager role required to delete inventory min/max rules')
            product_id = kwargs.get('product_id')
            if not product_id:
                return {'success': False, 'error': 'product_id is required'}
            branch_id = int(kwargs.get('branch_id') or 0)
            MM = request.env['lugal.supply.minmax'].sudo()
            rows = MM.search([('product_id', '=', int(product_id)), ('branch_id', '=', branch_id)])
            if not rows:
                return {'success': False, 'error': 'Rule not found'}
            rows.unlink()
            return {'success': True, 'data': {'product_id': int(product_id), 'branch_id': branch_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_delete')

    # =========================================================================
    # Notifications
    # =========================================================================

    @http.route('/api/crm/supply/notifications/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_list(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(100, max(1, int(kwargs.get('per_page') or 20)))
            domain = [('user_id', '=', uid), ('is_deleted', '=', False)]
            if kwargs.get('is_read') is not None:
                domain.append(('is_read', '=', bool(kwargs['is_read'])))
            Notif = request.env['lugal.supply.notification'].sudo()
            total = Notif.search_count(domain)
            unread = Notif.search_count([('user_id', '=', uid), ('is_deleted', '=', False), ('is_read', '=', False)])
            rows = Notif.search(domain, order='create_date desc, id desc', limit=per_page, offset=(page - 1) * per_page)
            return {
                'success': True,
                'data': {
                    'items': [_s_notification(n) for n in rows],
                    'total': total,
                    'unread_count': unread,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_notifications_list')

    @http.route('/api/crm/supply/notifications/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            user_id = kwargs.get('user_id')
            title = (kwargs.get('title') or '').strip()
            if not user_id or not title:
                return {'success': False, 'error': 'user_id and title are required'}
            n = request.env['lugal.supply.notification'].sudo().create({
                'user_id': int(user_id),
                'notif_type': kwargs.get('notif_type') or 'general',
                'title': title,
                'body': kwargs.get('body') or False,
                'related_type': kwargs.get('related_type') or False,
                'related_id': int(kwargs['related_id']) if kwargs.get('related_id') else 0,
                'is_read': False,
            })
            return {'success': True, 'data': _s_notification(n)}
        except Exception as e:
            return crm_error(e, 'supply_notifications_create')

    @http.route('/api/crm/supply/notifications/<int:notif_id>/mark_read', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_mark_read(self, notif_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            n = request.env['lugal.supply.notification'].sudo().browse(notif_id).exists()
            if not n or n.is_deleted or n.user_id.id != uid:
                return {'success': False, 'error': 'Notification not found'}
            n.write({'is_read': True})
            return {'success': True, 'data': _s_notification(n)}
        except Exception as e:
            return crm_error(e, 'supply_notifications_mark_read')

    @http.route('/api/crm/supply/notifications/mark_all_read', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_mark_all_read(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            Notif = request.env['lugal.supply.notification'].sudo()
            rows = Notif.search([('user_id', '=', uid), ('is_read', '=', False), ('is_deleted', '=', False)])
            rows.write({'is_read': True})
            return {'success': True, 'data': {'marked_count': len(rows)}}
        except Exception as e:
            return crm_error(e, 'supply_notifications_mark_all_read')

    @http.route('/api/crm/supply/notifications/<int:notif_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_delete(self, notif_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            n = request.env['lugal.supply.notification'].sudo().browse(notif_id).exists()
            if not n or n.is_deleted or n.user_id.id != uid:
                return {'success': False, 'error': 'Notification not found'}
            n.write({'is_deleted': True})
            return {'success': True, 'data': {'id': notif_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_notifications_delete')
