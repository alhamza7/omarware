# -*- coding: utf-8 -*-
"""
Additional supply-chain JSON-RPC routes.

Covers:
  - Container tracking view (POST alias) + tracking update
  - Negotiations CRUD (+ offers/list, comments list/add/delete)
  - Item Requests CRUD
  - Clearance Companies CRUD
  - Inventory Min/Max (list / upsert / delete)
  - Supply Notifications (list / create / mark_read / mark_all_read / delete)
"""

from odoo import fields, http
from odoo.http import request
from odoo.tools.mail import html2plaintext

from odoo.exceptions import UserError

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .supply_chain_api_controller import _pagination, _parse_date
from .supply_controller import _serialize_attachment

_logger = __import__('logging').getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _serialize_negotiation_offer(o):
    cur = o.currency_id
    u = o.user_id
    return {
        'id': o.id,
        'sequence': o.sequence or 10,
        'price': float(o.price or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'notes': o.notes or '',
        'user_id': u.id if u else None,
        'user_name': u.name if u else '',
        'offer_date': o.offer_date.isoformat() if o.offer_date else '',
    }


def _serialize_negotiation(n, include_offers=True):
    vendor = n.vendor_id
    item_req = n.item_request_id
    agent = n.agent_id
    cur = n.currency_id
    final_cur = n.final_currency_id
    fin_by = n.finalized_by_id
    atts = [_serialize_attachment(a) for a in n.attachment_ids]
    data = {
        'id': n.id,
        'negotiation_code': n.name or '',
        'negotiation_ref': n.name or '',
        'name': n.name or '',
        'item_request_id': item_req.id if item_req else None,
        'item_request_name': item_req.name if item_req else '',
        'item_request': (
            None
            if not item_req
            else {
                'id': item_req.id,
                'name': item_req.name or '',
                'item_name': item_req.item_name or '',
                'state': item_req.state or 'draft',
            }
        ),
        'vendor_id': vendor.id if vendor else None,
        'vendor_name': vendor.name if vendor else '',
        'agent_id': agent.id if agent else None,
        'agent_name': agent.name if agent else '',
        'item_name': n.item_name or '',
        'quantity': float(n.quantity or 0.0),
        'capacity': n.capacity or '',
        'packing': float(n.packing_pcs_per_carton or 0.0),
        'packing_pcs_per_carton': float(n.packing_pcs_per_carton or 0.0),
        'offered_price': float(n.offered_price or 0.0),
        'final_agreed_price': float(n.final_agreed_price or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'final_currency_id': final_cur.id if final_cur else None,
        'final_currency_name': final_cur.name if final_cur else '',
        'terms': n.terms or '',
        'notes': n.notes or '',
        'state': n.state or 'ongoing',
        'status': n.state or 'ongoing',
        'approval_by_id': fin_by.id if fin_by else None,
        'approval_by_name': fin_by.name if fin_by else '',
        'finalized_date': n.finalized_date.isoformat() if n.finalized_date else None,
        'attachments': atts,
        'created_by_id': n.create_uid.id if n.create_uid else None,
        'created_by_name': n.create_uid.name if n.create_uid else '',
        'created_date': n.create_date.isoformat() if n.create_date else '',
        'created_at': n.create_date.isoformat() if n.create_date else '',
        'updated_at': n.write_date.isoformat() if n.write_date else '',
    }
    if 'extra_fields' in n._fields:
        data['extra_fields'] = n.get_extra_fields_dict()
    if include_offers:
        data['multiple_offers_history'] = [_serialize_negotiation_offer(o) for o in n.offer_ids]
        data['offer_ids'] = data['multiple_offers_history']
    if 'supply_po_ids' in n._fields:
        pos = n.supply_po_ids.filtered(lambda p: not getattr(p, 'is_deleted', False))
        data['order_ids'] = pos.ids
        data['linked_orders'] = []
        for po in pos:
            data['linked_orders'].append({
                'id': po.id,
                'name': po.name or '',
                'status': po.status or '',
                'total_amount': float(po.total_amount or 0.0),
                'currency_id': po.currency_id.id if po.currency_id else None,
                'currency_name': po.currency_id.name if po.currency_id else '',
            })
    else:
        data['order_ids'] = []
        data['linked_orders'] = []
    return data


def _serialize_item_request(r):
    requester = r.requested_by_id
    conf = r.requester_confirm_user_id
    imgs = [_serialize_attachment(a) for a in r.attachment_ids]
    negs = r.negotiation_ids.filtered(lambda n: not getattr(n, 'is_deleted', False))
    negotiations_payload = []
    for n in negs:
        vn = n.vendor_id
        negotiations_payload.append({
            'id': n.id,
            'name': n.name or '',
            'state': n.state or 'ongoing',
            'vendor_id': vn.id if vn else None,
            'vendor_name': vn.name if vn else '',
            'final_agreed_price': float(n.final_agreed_price or 0.0),
            'currency_id': n.currency_id.id if n.currency_id else None,
            'currency_name': n.currency_id.name if n.currency_id else '',
        })
    data = {
        'id': r.id,
        'request_id': r.name or '',
        'name': r.name or '',
        'item_name': r.item_name or '',
        'item_description': r.description or '',
        'description': r.description or '',
        'quantity': float(r.quantity or 0.0),
        'unit': r.uom or '',
        'uom': r.uom or '',
        'capacity': r.capacity or '',
        'packing': float(r.packing_pcs_per_carton or 0.0),
        'packing_pcs_per_carton': float(r.packing_pcs_per_carton or 0.0),
        'reference_images': imgs,
        'reference_files': imgs,
        'priority': r.priority or 'medium',
        'state': r.state or 'draft',
        'status': r.state or 'draft',
        'notes': r.notes or '',
        'requested_by_id': requester.id if requester else None,
        'requested_by_name': requester.name if requester else '',
        'request_date': r.request_date.isoformat() if r.request_date else None,
        'requester_confirm_user_id': conf.id if conf else None,
        'requester_confirm_date': r.requester_confirm_date.isoformat() if r.requester_confirm_date else None,
        'negotiation_count': int(r.negotiation_count or 0),
        'negotiation_ids': negs.ids,
        'negotiations': negotiations_payload,
        'created_by_id': r.create_uid.id if r.create_uid else None,
        'created_by_name': r.create_uid.name if r.create_uid else '',
        'created_at': r.create_date.isoformat() if r.create_date else '',
        'updated_at': r.write_date.isoformat() if r.write_date else '',
    }
    if 'extra_fields' in r._fields:
        data['extra_fields'] = r.get_extra_fields_dict()
    return data


def _serialize_payment(p):
    po = p.po_id
    cur = p.currency_id
    payee = p.payee_partner_id
    rcpts = [_serialize_attachment(a) for a in p.receipt_attachment_ids]
    item_request_id = None
    negotiation_id = None
    container_id = None
    item_request_name = ''
    negotiation_name = ''
    container_name = ''
    if po:
        if 'item_request_id' in po._fields and po.item_request_id:
            item_request_id = po.item_request_id.id
            item_request_name = po.item_request_id.name or ''
        if 'negotiation_id' in po._fields and po.negotiation_id:
            negotiation_id = po.negotiation_id.id
            negotiation_name = po.negotiation_id.name or ''
        if 'container_id' in po._fields and po.container_id:
            container_id = po.container_id.id
            container_name = po.container_id.name or ''
    return {
        'id': p.id,
        'payment_id': p.name or '',
        'name': p.name or '',
        'po_id': po.id if po else None,
        'linked_order_id': po.id if po else None,
        'order_name': po.name if po else '',
        'item_request_id': item_request_id,
        'item_request_name': item_request_name,
        'negotiation_id': negotiation_id,
        'negotiation_name': negotiation_name,
        'container_id': container_id,
        'container_name': container_name,
        'paid_to': p.paid_to or '',
        'payee_partner_id': payee.id if payee else None,
        'payee_name': payee.name if payee else '',
        'payment_type': p.payment_type or 'partial',
        'amount': float(p.amount or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'payment_date': p.payment_date.isoformat() if p.payment_date else None,
        'payment_method': p.payment_method or '',
        'remaining_balance': float(p.remaining_balance or 0.0),
        'payment_status': p.payment_status or 'pending',
        'notes': p.notes or '',
        'attachments': rcpts,
        'created_at': p.create_date.isoformat() if p.create_date else '',
        'updated_at': p.write_date.isoformat() if p.write_date else '',
    }


def _serialize_shipment_container(c):
    """Shipment view over `lugal.supply.container` (+ CRM linked POs)."""
    supplier = c.supplier_id
    agent = c.agent_id
    docs = [_serialize_attachment(a) for a in c.attachment_ids]
    linked_pos = []
    if 'purchase_order_ids' in c._fields:
        for po in c.purchase_order_ids:
            row = {
                'id': po.id,
                'name': po.name or '',
                'total_amount': float(po.total_amount or 0.0),
                'status': po.status or '',
                'currency_id': po.currency_id.id if po.currency_id else None,
                'currency_name': po.currency_id.name if po.currency_id else '',
            }
            if 'item_request_id' in po._fields:
                ir = po.item_request_id
                row['item_request_id'] = ir.id if ir else None
                row['item_request_name'] = ir.name if ir else ''
            if 'negotiation_id' in po._fields:
                ng = po.negotiation_id
                row['negotiation_id'] = ng.id if ng else None
                row['negotiation_name'] = ng.name if ng else ''
            linked_pos.append(row)
    return {
        'id': c.id,
        'shipment_id': c.shipment_ref or c.name or '',
        'name': c.name or '',
        'container_number': c.container_number or '',
        'supplier_id': supplier.id if supplier else None,
        'supplier_name': supplier.name if supplier else '',
        'agent_id': agent.id if agent else None,
        'agent_name': agent.name if agent else '',
        'linked_orders': linked_pos,
        'shipping_method': c.transport_mode or '',
        'origin': c.origin_location or '',
        'destination': c.destination_location or '',
        'etd': c.departure_date.isoformat() if c.departure_date else None,
        'eta': c.eta.isoformat() if c.eta else None,
        'status': c.shipment_tracking_state or 'pending',
        'shipment_tracking_state': c.shipment_tracking_state or 'pending',
        'shipping_line': c.shipping_line or '',
        'documents': docs,
        'tracking_url': c.tracking_url or '',
        'created_at': c.create_date.isoformat() if c.create_date else '',
        'updated_at': c.write_date.isoformat() if c.write_date else '',
    }


def _serialize_clearance_company(c):
    country = c.country_id
    return {
        'id': c.id,
        'name': c.name or '',
        'contact_name': c.contact_name or '',
        'phone': c.phone or '',
        'email': c.email or '',
        'whatsapp': c.whatsapp or '',
        'telegram': c.telegram or '',
        'country_id': country.id if country else None,
        'country_name': country.name if country else '',
        'city': c.city or '',
        'address': c.address or '',
        'license_number': c.license_number or '',
        'license_expiry': c.license_expiry.isoformat() if c.license_expiry else None,
        'notes': c.notes or '',
        'is_active': bool(c.is_active),
    }


def _serialize_inventory_minmax(r):
    product = r.product_id
    branch = r.branch_id
    tmpl = product.product_tmpl_id if product else None
    categ = tmpl.categ_id if tmpl else None
    uom = product.uom_id if product else None
    return {
        'id': r.id,
        'product_id': product.id if product else None,
        'product_name': product.name if product else '',
        'sku': product.default_code or '',
        'category': categ.name if categ else '',
        'uom': uom.name if uom else '',
        'current_stock': float(r.current_stock or 0.0),
        'min_qty': float(r.min_qty or 0.0),
        'max_qty': float(r.max_qty or 0.0),
        'branch_id': branch.id if branch else None,
        'branch_name': branch.name if branch else '',
        'needs_reorder': bool(r.needs_reorder),
    }


def _serialize_supply_notification(n):
    return {
        'id': n.id,
        'type': n.notif_type or '',
        'title': n.title or '',
        'body': n.body or '',
        'related_id': n.related_id or None,
        'related_type': n.related_type or '',
        'is_read': bool(n.is_read),
        'read_at': n.read_at.isoformat() if n.read_at else None,
        'created_at': n.create_date.isoformat() if n.create_date else '',
    }


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class CrmSupplyExtraApiController(http.Controller):

    # -----------------------------------------------------------------------
    # Container Tracking — POST JSON-RPC alias + update
    # -----------------------------------------------------------------------

    @http.route(
        '/api/crm/supply/containers/tracking/view',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_container_tracking_view_post(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            raw = kwargs.get('container_id')
            if raw is None:
                return {'success': False, 'error': 'container_id is required', 'data': None}
            try:
                cid = int(raw)
            except (TypeError, ValueError):
                return {'success': False, 'error': 'container_id must be a number', 'data': None}
            c = request.env['lugal.supply.container'].sudo().search(
                [('id', '=', cid), ('is_deleted', '=', False)], limit=1
            )
            if not c:
                return {'success': False, 'error': 'Container not found', 'data': None}
            assigned = c.assigned_user_id
            payload = c.tracking_data
            tracking_payload = payload if isinstance(payload, dict) else ({} if not payload else {'_raw': payload})
            return {
                'success': True,
                'data': {
                    'id': c.id,
                    'name': c.name or '',
                    'container_number': c.container_number or '',
                    'bl_number': c.bl_number or '',
                    'tracking_url': c.tracking_url or '',
                    'status': c.status or '',
                    'division': c.division or '',
                    'clearance_company': c.clearance_company or '',
                    'origin_location': c.origin_location or '',
                    'departure_date': c.departure_date.isoformat() if c.departure_date else None,
                    'eta': c.eta.isoformat() if c.eta else None,
                    'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
                    'assigned_user_id': assigned.id if assigned else None,
                    'assigned_user_name': assigned.name if assigned else '',
                    'tracking_data': tracking_payload,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_tracking_view_post')

    @http.route(
        '/api/crm/supply/containers/tracking/update',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_container_tracking_update(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            raw = kwargs.get('container_id')
            if raw is None:
                return {'success': False, 'error': 'container_id is required', 'data': None}
            try:
                cid = int(raw)
            except (TypeError, ValueError):
                return {'success': False, 'error': 'container_id must be a number', 'data': None}
            c = request.env['lugal.supply.container'].sudo().search(
                [('id', '=', cid), ('is_deleted', '=', False)], limit=1
            )
            if not c:
                return {'success': False, 'error': 'Container not found', 'data': None}
            vals = {}
            if 'tracking_url' in kwargs:
                vals['tracking_url'] = kwargs['tracking_url'] or ''
            if 'tracking_data' in kwargs:
                vals['tracking_data'] = kwargs['tracking_data'] or {}
            if vals:
                c.write(vals)
            return {
                'success': True,
                'data': {
                    'id': c.id,
                    'tracking_url': c.tracking_url or '',
                    'tracking_data': c.tracking_data if isinstance(c.tracking_data, dict) else {},
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_container_tracking_update')

    # -----------------------------------------------------------------------
    # Negotiations
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/negotiations/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('vendor_id'):
                try:
                    domain.append(('vendor_id', '=', int(kwargs['vendor_id'])))
                except (TypeError, ValueError):
                    pass
            if kwargs.get('item_request_id'):
                try:
                    domain.append(('item_request_id', '=', int(kwargs['item_request_id'])))
                except (TypeError, ValueError):
                    pass
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('item_name', 'ilike', search), ('name', 'ilike', search)]
            Neg = request.env['lugal.supply.negotiation'].sudo()
            total = Neg.search_count(domain)
            rows = Neg.search(domain, order='create_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total, 'page': page, 'per_page': per_page,
                    'items': [_serialize_negotiation(n) for n in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_negotiations_list')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_get(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            return {'success': True, 'data': _serialize_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_get')

    @http.route('/api/crm/supply/negotiations/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            item_request_id = kwargs.get('item_request_id')
            vendor_id = kwargs.get('vendor_id')
            if not item_request_id:
                return {'success': False, 'error': 'item_request_id is required', 'data': None}
            if not vendor_id:
                return {'success': False, 'error': 'vendor_id is required', 'data': None}
            vals = {'item_request_id': int(item_request_id), 'vendor_id': int(vendor_id)}
            for k in ('item_name', 'notes', 'terms', 'capacity'):
                if kwargs.get(k) is not None:
                    vals[k] = kwargs[k]
            if kwargs.get('agent_id'):
                vals['agent_id'] = int(kwargs['agent_id'])
            if kwargs.get('quantity') is not None:
                vals['quantity'] = float(kwargs['quantity'])
            if kwargs.get('packing') is not None:
                vals['packing_pcs_per_carton'] = float(kwargs['packing'])
            if kwargs.get('packing_pcs_per_carton') is not None:
                vals['packing_pcs_per_carton'] = float(kwargs['packing_pcs_per_carton'])
            if kwargs.get('currency_id'):
                vals['currency_id'] = int(kwargs['currency_id'])
            if kwargs.get('final_agreed_price') is not None:
                vals['final_agreed_price'] = float(kwargs['final_agreed_price'])
            if kwargs.get('final_currency_id'):
                vals['final_currency_id'] = int(kwargs['final_currency_id'])
            Neg = request.env['lugal.supply.negotiation'].sudo()
            if kwargs.get('extra_fields') is not None:
                vals['extra_fields'] = Neg.sanitize_extra_fields_input(kwargs['extra_fields'])
            rec = Neg.create(vals)
            Offer = request.env['lugal.supply.negotiation.offer'].sudo()
            op = kwargs.get('offered_price')
            if op is not None:
                cur_id = vals.get('currency_id') or (rec.currency_id.id if rec.currency_id else False)
                Offer.create({
                    'negotiation_id': rec.id,
                    'price': float(op),
                    'currency_id': cur_id,
                    'notes': kwargs.get('offer_notes') or '',
                })
                rec.invalidate_recordset()
            return {'success': True, 'data': _serialize_negotiation(rec)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_create')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_update(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            vals = {}
            for k in ('item_name', 'notes', 'terms', 'capacity', 'state'):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'agent_id' in kwargs:
                vals['agent_id'] = kwargs.get('agent_id') or False
            if 'quantity' in kwargs:
                vals['quantity'] = float(kwargs['quantity'] or 0.0)
            if 'packing' in kwargs:
                vals['packing_pcs_per_carton'] = float(kwargs['packing'] or 0.0)
            if 'packing_pcs_per_carton' in kwargs:
                vals['packing_pcs_per_carton'] = float(kwargs['packing_pcs_per_carton'] or 0.0)
            if 'final_agreed_price' in kwargs:
                vals['final_agreed_price'] = float(kwargs['final_agreed_price'] or 0.0)
            if 'currency_id' in kwargs:
                vals['currency_id'] = kwargs.get('currency_id') or False
            if 'final_currency_id' in kwargs:
                vals['final_currency_id'] = kwargs.get('final_currency_id') or False
            if vals:
                n.write(vals)
            if 'extra_fields' in kwargs and kwargs['extra_fields'] is not None:
                cleaned = request.env['lugal.supply.negotiation'].sudo().sanitize_extra_fields_input(
                    kwargs['extra_fields']
                )
                n.merge_extra_fields(cleaned)
            return {'success': True, 'data': _serialize_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_update')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_delete(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            n.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': neg_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_delete')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/confirm', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_confirm(self, neg_id, **kwargs):
        """Finalize negotiation (approval): sets state finalized, records approver."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            try:
                n.action_finalize()
            except UserError as ue:
                return {'success': False, 'error': str(ue), 'data': None}
            return {'success': True, 'data': _serialize_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_confirm')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/e_sign_approve', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_e_sign_approve(self, neg_id, **kwargs):
        """Same as confirm — negotiation-stage e-sign / approval (Odoo: finalize)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            try:
                n.action_finalize()
            except UserError as ue:
                return {'success': False, 'error': str(ue), 'data': None}
            return {'success': True, 'data': _serialize_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_e_sign_approve')

    @http.route('/api/crm/supply/negotiations/<int:neg_id>/offers/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_negotiations_offers_add(self, neg_id, **kwargs):
        """Append row to offer history (updates computed offered_price)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            price = kwargs.get('price')
            if price is None:
                return {'success': False, 'error': 'price is required', 'data': None}
            Offer = request.env['lugal.supply.negotiation.offer'].sudo()
            vals = {
                'negotiation_id': n.id,
                'price': float(price),
                'notes': kwargs.get('notes') or '',
            }
            if kwargs.get('currency_id'):
                vals['currency_id'] = int(kwargs['currency_id'])
            o = Offer.create(vals)
            n.invalidate_recordset()
            return {'success': True, 'data': _serialize_negotiation_offer(o)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_offers_add')

    @http.route(
        '/api/crm/supply/negotiations/<int:neg_id>/offers/list',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_negotiations_offers_list(self, neg_id, **kwargs):
        """List price-offer rows for this negotiation (same records as `offer_ids` on GET)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            Offer = request.env['lugal.supply.negotiation.offer'].sudo()
            domain = [('negotiation_id', '=', n.id)]
            total = Offer.search_count(domain)
            rows = Offer.search(domain, order='offer_date desc, id desc', limit=per_page, offset=offset)
            items = [_serialize_negotiation_offer(o) for o in rows]
            return {
                'success': True,
                'data': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'items': items,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_negotiations_offers_list')

    @http.route(
        '/api/crm/supply/negotiations/<int:neg_id>/comments/list',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_negotiations_comments_list(self, neg_id, **kwargs):
        """Chatter comments on negotiation (`mail.thread`)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            Message = request.env['mail.message'].sudo()
            domain = [
                ('model', '=', n._name),
                ('res_id', '=', n.id),
                ('message_type', '=', 'comment'),
            ]
            total = Message.search_count(domain)
            rows = Message.search(domain, order='date desc, id desc', limit=per_page, offset=offset)
            items = []
            for m in rows:
                body_plain = (html2plaintext(m.body or '') or '').strip()
                auth = m.author_id
                items.append({
                    'id': m.id,
                    'body': body_plain[:4000],
                    'author_id': auth.id if auth else None,
                    'author_name': auth.name if auth else '',
                    'date': m.date.isoformat() if m.date else '',
                })
            return {
                'success': True,
                'data': {'total': total, 'page': page, 'per_page': per_page, 'items': items},
            }
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_list')

    @http.route(
        '/api/crm/supply/negotiations/<int:neg_id>/comments/add',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_negotiations_comments_add(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            body = (kwargs.get('body') or kwargs.get('message') or '').strip()
            if not body:
                return {'success': False, 'error': 'body is required', 'data': None}
            n.message_post(body=body, message_type='comment')
            return {'success': True, 'data': {'posted': True}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_add')

    @http.route(
        '/api/crm/supply/negotiations/<int:neg_id>/comments/<int:msg_id>/delete',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_negotiations_comments_delete(self, neg_id, msg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            msg = request.env['mail.message'].sudo().browse(msg_id).exists()
            if not msg or msg.model != n._name or msg.res_id != n.id:
                return {'success': False, 'error': 'Message not found', 'data': None}
            msg.unlink()
            return {'success': True, 'data': {'id': msg_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_comments_delete')

    @http.route(
        '/api/crm/supply/negotiations/<int:neg_id>/attachments/link',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_negotiations_attachments_link(self, neg_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.negotiation'].sudo().browse(neg_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Negotiation not found', 'data': None}
            ids = kwargs.get('attachment_ids') or kwargs.get('ids') or []
            if not isinstance(ids, (list, tuple)):
                return {'success': False, 'error': 'attachment_ids must be a list', 'data': None}
            cmd = [(6, 0, [int(x) for x in ids])] if ids else [(5,)]
            n.write({'attachment_ids': cmd})
            return {'success': True, 'data': _serialize_negotiation(n)}
        except Exception as e:
            return crm_error(e, 'supply_negotiations_attachments_link')

    # -----------------------------------------------------------------------
    # Item Requests
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/item_requests/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('priority'):
                domain.append(('priority', '=', kwargs['priority']))
            if kwargs.get('requested_by_id'):
                try:
                    domain.append(('requested_by_id', '=', int(kwargs['requested_by_id'])))
                except (TypeError, ValueError):
                    pass
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('item_name', 'ilike', search), ('name', 'ilike', search)]
            IR = request.env['lugal.supply.item.request'].sudo()
            total = IR.search_count(domain)
            rows = IR.search(domain, order='request_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total, 'page': page, 'per_page': per_page,
                    'items': [_serialize_item_request(r) for r in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_item_requests_list')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_get(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            return {'success': True, 'data': _serialize_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_get')

    @http.route('/api/crm/supply/item_requests/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_create(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            item_name = (kwargs.get('item_name') or '').strip()
            if not item_name:
                return {'success': False, 'error': 'item_name is required', 'data': None}
            vals = {'item_name': item_name, 'requested_by_id': uid}
            for k in ('uom', 'description', 'notes', 'priority', 'capacity'):
                if kwargs.get(k) is not None:
                    vals[k] = kwargs[k]
            if kwargs.get('quantity') is not None:
                vals['quantity'] = float(kwargs['quantity'])
            if kwargs.get('packing') is not None:
                vals['packing_pcs_per_carton'] = float(kwargs['packing'])
            if kwargs.get('packing_pcs_per_carton') is not None:
                vals['packing_pcs_per_carton'] = float(kwargs['packing_pcs_per_carton'])
            if kwargs.get('request_date'):
                vals['request_date'] = _parse_date(kwargs['request_date'])
            ids = kwargs.get('attachment_ids') or kwargs.get('ids') or []
            if ids:
                if not isinstance(ids, (list, tuple)):
                    return {'success': False, 'error': 'attachment_ids must be a list', 'data': None}
                vals['attachment_ids'] = [(6, 0, [int(x) for x in ids])]
            IR = request.env['lugal.supply.item.request'].sudo()
            if kwargs.get('extra_fields') is not None:
                vals['extra_fields'] = IR.sanitize_extra_fields_input(kwargs['extra_fields'])
            rec = IR.create(vals)
            return {'success': True, 'data': _serialize_item_request(rec)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_create')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_update(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            vals = {}
            for k in ('item_name', 'uom', 'description', 'notes', 'priority', 'state', 'capacity'):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'quantity' in kwargs:
                vals['quantity'] = float(kwargs['quantity'] or 0.0)
            if 'packing' in kwargs:
                vals['packing_pcs_per_carton'] = float(kwargs['packing'] or 0.0)
            if 'packing_pcs_per_carton' in kwargs:
                vals['packing_pcs_per_carton'] = float(kwargs['packing_pcs_per_carton'] or 0.0)
            if vals:
                r.write(vals)
            if 'extra_fields' in kwargs and kwargs['extra_fields'] is not None:
                cleaned = request.env['lugal.supply.item.request'].sudo().sanitize_extra_fields_input(
                    kwargs['extra_fields']
                )
                r.merge_extra_fields(cleaned)
            return {'success': True, 'data': _serialize_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_update')

    @http.route(
        '/api/crm/supply/item_requests/<int:req_id>/requester_confirm',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_item_requests_requester_confirm(self, req_id, **kwargs):
        """Requester e-sign confirm (optional; negotiation has separate finalize flow)."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            r.action_requester_confirm()
            return {'success': True, 'data': _serialize_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_requester_confirm')

    @http.route(
        '/api/crm/supply/item_requests/<int:req_id>/attachments/link',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_item_requests_attachments_link(self, req_id, **kwargs):
        """Link existing `ir.attachment` ids (after multipart upload elsewhere)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            ids = kwargs.get('attachment_ids') or kwargs.get('ids') or []
            if not isinstance(ids, (list, tuple)):
                return {'success': False, 'error': 'attachment_ids must be a list', 'data': None}
            cmd = [(6, 0, [int(x) for x in ids])] if ids else [(5,)]
            r.write({'attachment_ids': cmd})
            return {'success': True, 'data': _serialize_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_attachments_link')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_update_status(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r or r.is_deleted:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            state = (kwargs.get('state') or kwargs.get('status') or '').strip()
            if not state:
                return {'success': False, 'error': 'state is required', 'data': None}
            r.write({'state': state})
            return {'success': True, 'data': _serialize_item_request(r)}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_update_status')

    @http.route('/api/crm/supply/item_requests/<int:req_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_item_requests_delete(self, req_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            r = request.env['lugal.supply.item.request'].sudo().browse(req_id).exists()
            if not r:
                return {'success': False, 'error': 'Item request not found', 'data': None}
            r.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': req_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_item_requests_delete')

    # -----------------------------------------------------------------------
    # Clearance Companies
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/clearance_companies/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False)]
            if kwargs.get('is_active') is not None:
                domain.append(('is_active', '=', bool(kwargs['is_active'])))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', '|', ('name', 'ilike', search), ('city', 'ilike', search), ('contact_name', 'ilike', search)]
            CC = request.env['lugal.supply.clearance.company'].sudo()
            total = CC.search_count(domain)
            rows = CC.search(domain, order='name asc, id asc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total, 'page': page, 'per_page': per_page,
                    'items': [_serialize_clearance_company(c) for c in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_list')

    @http.route('/api/crm/supply/clearance_companies/<int:cc_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_get(self, cc_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(cc_id).exists()
            if not cc or cc.is_deleted:
                return {'success': False, 'error': 'Clearance company not found', 'data': None}
            return {'success': True, 'data': _serialize_clearance_company(cc)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_get')

    @http.route('/api/crm/supply/clearance_companies/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required', 'data': None}
            vals = {'name': name}
            for k in ('contact_name', 'phone', 'email', 'whatsapp', 'telegram', 'city', 'address', 'license_number', 'notes'):
                if kwargs.get(k) is not None:
                    vals[k] = kwargs[k]
            if kwargs.get('country_id'):
                vals['country_id'] = int(kwargs['country_id'])
            if kwargs.get('license_expiry'):
                vals['license_expiry'] = _parse_date(kwargs['license_expiry'])
            if kwargs.get('is_active') is not None:
                vals['is_active'] = bool(kwargs['is_active'])
            rec = request.env['lugal.supply.clearance.company'].sudo().create(vals)
            return {'success': True, 'data': _serialize_clearance_company(rec)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_create')

    @http.route('/api/crm/supply/clearance_companies/<int:cc_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_update(self, cc_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(cc_id).exists()
            if not cc or cc.is_deleted:
                return {'success': False, 'error': 'Clearance company not found', 'data': None}
            vals = {}
            for k in ('name', 'contact_name', 'phone', 'email', 'whatsapp', 'telegram', 'city', 'address', 'license_number', 'notes'):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'country_id' in kwargs:
                vals['country_id'] = kwargs.get('country_id') or False
            if 'license_expiry' in kwargs:
                vals['license_expiry'] = _parse_date(kwargs['license_expiry'])
            if 'is_active' in kwargs:
                vals['is_active'] = bool(kwargs['is_active'])
            if vals:
                cc.write(vals)
            return {'success': True, 'data': _serialize_clearance_company(cc)}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_update')

    @http.route('/api/crm/supply/clearance_companies/<int:cc_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_clearance_companies_delete(self, cc_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            cc = request.env['lugal.supply.clearance.company'].sudo().browse(cc_id).exists()
            if not cc:
                return {'success': False, 'error': 'Clearance company not found', 'data': None}
            cc.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': cc_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_clearance_companies_delete')

    # -----------------------------------------------------------------------
    # Inventory Min/Max
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/inventory/minmax', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = []
            if kwargs.get('branch_id'):
                try:
                    domain.append(('branch_id', '=', int(kwargs['branch_id'])))
                except (TypeError, ValueError):
                    pass
            if kwargs.get('product_id'):
                try:
                    domain.append(('product_id', '=', int(kwargs['product_id'])))
                except (TypeError, ValueError):
                    pass
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('product_id.name', 'ilike', search), ('product_id.default_code', 'ilike', search)]
            MM = request.env['lugal.supply.inventory.minmax'].sudo()
            total = MM.search_count(domain)
            rows = MM.search(domain, order='product_id asc, id asc', limit=per_page, offset=offset)
            items = [_serialize_inventory_minmax(r) for r in rows]
            needs_reorder = kwargs.get('needs_reorder')
            if needs_reorder is True or str(needs_reorder).lower() == 'true':
                items = [i for i in items if i.get('needs_reorder')]
            return {
                'success': True,
                'data': {
                    'total': total, 'page': page, 'per_page': per_page,
                    'items': items,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_list')

    @http.route('/api/crm/supply/inventory/minmax/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_upsert(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            product_id = kwargs.get('product_id')
            min_qty = kwargs.get('min_qty')
            max_qty = kwargs.get('max_qty')
            if not product_id or min_qty is None or max_qty is None:
                return {'success': False, 'error': 'product_id, min_qty, and max_qty are required', 'data': None}
            pid = int(product_id)
            branch_id = int(kwargs['branch_id']) if kwargs.get('branch_id') else False
            MM = request.env['lugal.supply.inventory.minmax'].sudo()
            domain = [('product_id', '=', pid), ('branch_id', '=', branch_id)]
            existing = MM.search(domain, limit=1)
            vals = {'min_qty': float(min_qty), 'max_qty': float(max_qty)}
            if existing:
                existing.write(vals)
                rec = existing
            else:
                vals.update({'product_id': pid, 'branch_id': branch_id})
                rec = MM.create(vals)
            return {'success': True, 'data': _serialize_inventory_minmax(rec)}
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_upsert')

    @http.route('/api/crm/supply/inventory/minmax/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_inventory_minmax_delete(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            product_id = kwargs.get('product_id')
            if not product_id:
                return {'success': False, 'error': 'product_id is required', 'data': None}
            pid = int(product_id)
            branch_id = int(kwargs['branch_id']) if kwargs.get('branch_id') else False
            recs = request.env['lugal.supply.inventory.minmax'].sudo().search(
                [('product_id', '=', pid), ('branch_id', '=', branch_id)]
            )
            count = len(recs)
            recs.unlink()
            return {'success': True, 'data': {'deleted': count > 0, 'count': count}}
        except Exception as e:
            return crm_error(e, 'supply_inventory_minmax_delete')

    # -----------------------------------------------------------------------
    # Supply Notifications
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/notifications/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_list(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('user_id', '=', uid), ('is_deleted', '=', False)]
            is_read = kwargs.get('is_read')
            if is_read is not None and str(is_read).lower() not in ('', 'none', 'null'):
                domain.append(('is_read', '=', bool(is_read)))
            Notif = request.env['lugal.supply.notification'].sudo()
            total = Notif.search_count(domain)
            unread_count = Notif.search_count(
                [('user_id', '=', uid), ('is_deleted', '=', False), ('is_read', '=', False)]
            )
            rows = Notif.search(domain, order='create_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total,
                    'unread_count': unread_count,
                    'page': page,
                    'per_page': per_page,
                    'items': [_serialize_supply_notification(n) for n in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_notifications_list')

    @http.route('/api/crm/supply/notifications/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            user_id = kwargs.get('user_id')
            notif_type = (kwargs.get('notif_type') or '').strip()
            title = (kwargs.get('title') or '').strip()
            if not user_id or not notif_type or not title:
                return {'success': False, 'error': 'user_id, notif_type, and title are required', 'data': None}
            vals = {'user_id': int(user_id), 'notif_type': notif_type, 'title': title}
            if kwargs.get('body') is not None:
                vals['body'] = kwargs['body']
            if kwargs.get('related_id'):
                vals['related_id'] = int(kwargs['related_id'])
            if kwargs.get('related_type'):
                vals['related_type'] = kwargs['related_type']
            rec = request.env['lugal.supply.notification'].sudo().create(vals)
            return {'success': True, 'data': _serialize_supply_notification(rec)}
        except Exception as e:
            return crm_error(e, 'supply_notifications_create')

    @http.route('/api/crm/supply/notifications/<int:notif_id>/mark_read', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_mark_read(self, notif_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.notification'].sudo().browse(notif_id).exists()
            if not n or n.is_deleted:
                return {'success': False, 'error': 'Notification not found', 'data': None}
            n.write({'is_read': True, 'read_at': fields.Datetime.now()})
            return {'success': True, 'data': _serialize_supply_notification(n)}
        except Exception as e:
            return crm_error(e, 'supply_notifications_mark_read')

    @http.route('/api/crm/supply/notifications/mark_all_read', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_mark_all_read(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            Notif = request.env['lugal.supply.notification'].sudo()
            unread = Notif.search(
                [('user_id', '=', uid), ('is_read', '=', False), ('is_deleted', '=', False)]
            )
            count = len(unread)
            unread.write({'is_read': True, 'read_at': fields.Datetime.now()})
            return {'success': True, 'data': {'marked': count}}
        except Exception as e:
            return crm_error(e, 'supply_notifications_mark_all_read')

    @http.route('/api/crm/supply/notifications/<int:notif_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_notifications_delete(self, notif_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            n = request.env['lugal.supply.notification'].sudo().browse(notif_id).exists()
            if not n:
                return {'success': False, 'error': 'Notification not found', 'data': None}
            n.write({'is_deleted': True})
            return {'success': True, 'data': {'id': notif_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_notifications_delete')

    # -----------------------------------------------------------------------
    # Payments (`lugal.supply.payment` → linked PO)
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/payments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_payments_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = []
            if kwargs.get('po_id'):
                try:
                    domain.append(('po_id', '=', int(kwargs['po_id'])))
                except (TypeError, ValueError):
                    pass
            if kwargs.get('payment_status'):
                domain.append(('payment_status', '=', kwargs['payment_status']))
            if kwargs.get('payment_type'):
                domain.append(('payment_type', '=', kwargs['payment_type']))
            Pay = request.env['lugal.supply.payment'].sudo()
            total = Pay.search_count(domain)
            rows = Pay.search(domain, order='payment_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'items': [_serialize_payment(p) for p in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_payments_list')

    @http.route('/api/crm/supply/payments/<int:payment_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_payments_get(self, payment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            p = request.env['lugal.supply.payment'].sudo().browse(payment_id).exists()
            if not p:
                return {'success': False, 'error': 'Payment not found', 'data': None}
            return {'success': True, 'data': _serialize_payment(p)}
        except Exception as e:
            return crm_error(e, 'supply_payments_get')

    @http.route('/api/crm/supply/payments/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_payments_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po_id = kwargs.get('po_id') or kwargs.get('linked_order_id')
            amount = kwargs.get('amount')
            if not po_id or amount is None:
                return {'success': False, 'error': 'po_id and amount are required', 'data': None}
            vals = {
                'po_id': int(po_id),
                'amount': float(amount),
                'payment_type': kwargs.get('payment_type') or 'partial',
            }
            if kwargs.get('paid_to'):
                vals['paid_to'] = kwargs['paid_to']
            if kwargs.get('payee_partner_id'):
                vals['payee_partner_id'] = int(kwargs['payee_partner_id'])
            if kwargs.get('currency_id'):
                vals['currency_id'] = int(kwargs['currency_id'])
            if kwargs.get('payment_date'):
                vals['payment_date'] = _parse_date(kwargs['payment_date'])
            if kwargs.get('payment_method'):
                vals['payment_method'] = kwargs['payment_method']
            if kwargs.get('notes'):
                vals['notes'] = kwargs['notes']
            p = request.env['lugal.supply.payment'].sudo().create(vals)
            return {'success': True, 'data': _serialize_payment(p)}
        except Exception as e:
            return crm_error(e, 'supply_payments_create')

    @http.route('/api/crm/supply/payments/<int:payment_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_payments_update(self, payment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            p = request.env['lugal.supply.payment'].sudo().browse(payment_id).exists()
            if not p:
                return {'success': False, 'error': 'Payment not found', 'data': None}
            vals = {}
            for k in ('paid_to', 'payment_type', 'payment_method', 'notes'):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'amount' in kwargs:
                vals['amount'] = float(kwargs['amount'] or 0.0)
            if 'currency_id' in kwargs:
                vals['currency_id'] = kwargs.get('currency_id') or False
            if 'payee_partner_id' in kwargs:
                vals['payee_partner_id'] = kwargs.get('payee_partner_id') or False
            if 'payment_date' in kwargs:
                vals['payment_date'] = _parse_date(kwargs['payment_date'])
            if vals:
                p.write(vals)
            return {'success': True, 'data': _serialize_payment(p)}
        except Exception as e:
            return crm_error(e, 'supply_payments_update')

    @http.route('/api/crm/supply/payments/<int:payment_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_payments_delete(self, payment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            p = request.env['lugal.supply.payment'].sudo().browse(payment_id).exists()
            if not p:
                return {'success': False, 'error': 'Payment not found', 'data': None}
            p.unlink()
            return {'success': True, 'data': {'id': payment_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_payments_delete')

    @http.route(
        '/api/crm/supply/payments/<int:payment_id>/attachments/link',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_payments_attachments_link(self, payment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            p = request.env['lugal.supply.payment'].sudo().browse(payment_id).exists()
            if not p:
                return {'success': False, 'error': 'Payment not found', 'data': None}
            ids = kwargs.get('attachment_ids') or kwargs.get('ids') or []
            if not isinstance(ids, (list, tuple)):
                return {'success': False, 'error': 'attachment_ids must be a list', 'data': None}
            cmd = [(6, 0, [int(x) for x in ids])] if ids else [(5,)]
            p.write({'receipt_attachment_ids': cmd})
            return {'success': True, 'data': _serialize_payment(p)}
        except Exception as e:
            return crm_error(e, 'supply_payments_attachments_link')

    # -----------------------------------------------------------------------
    # Shipments — backed by `lugal.supply.container` (no duplicate table)
    # -----------------------------------------------------------------------

    @http.route('/api/crm/supply/shipments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if kwargs.get('status'):
                domain.append(('shipment_tracking_state', '=', kwargs['status']))
            if kwargs.get('supplier_id'):
                try:
                    domain.append(('supplier_id', '=', int(kwargs['supplier_id'])))
                except (TypeError, ValueError):
                    pass
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += [
                    '|', '|', '|',
                    ('name', 'ilike', search),
                    ('shipment_ref', 'ilike', search),
                    ('container_number', 'ilike', search),
                    ('bl_number', 'ilike', search),
                ]
            C = request.env['lugal.supply.container'].sudo()
            total = C.search_count(domain)
            rows = C.search(domain, order='departure_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'items': [_serialize_shipment_container(c) for c in rows],
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_shipments_list')

    @http.route('/api/crm/supply/shipments/<int:shipment_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_get(self, shipment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(shipment_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Shipment not found', 'data': None}
            return {'success': True, 'data': _serialize_shipment_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_shipments_get')

    @http.route('/api/crm/supply/shipments/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            name = (kwargs.get('name') or kwargs.get('container_number') or '').strip()
            if not name:
                return {'success': False, 'error': 'name or container_number is required', 'data': None}
            vals = {'name': name}
            if kwargs.get('container_number'):
                vals['container_number'] = kwargs['container_number']
            if kwargs.get('supplier_id'):
                vals['supplier_id'] = int(kwargs['supplier_id'])
            if kwargs.get('agent_id'):
                vals['agent_id'] = int(kwargs['agent_id'])
            if kwargs.get('shipping_method'):
                vals['transport_mode'] = kwargs['shipping_method']
            if kwargs.get('origin'):
                vals['origin_location'] = kwargs['origin']
            if kwargs.get('destination'):
                vals['destination_location'] = kwargs['destination']
            dd = _parse_date(kwargs.get('etd'))
            if dd:
                vals['departure_date'] = dd
            ed = _parse_date(kwargs.get('eta'))
            if ed:
                vals['eta'] = ed
            if kwargs.get('status'):
                vals['shipment_tracking_state'] = kwargs['status']
            if kwargs.get('shipping_line'):
                vals['shipping_line'] = kwargs['shipping_line']
            c = request.env['lugal.supply.container'].sudo().create(vals)
            return {'success': True, 'data': _serialize_shipment_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_shipments_create')

    @http.route('/api/crm/supply/shipments/<int:shipment_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_update(self, shipment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(shipment_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Shipment not found', 'data': None}
            vals = {}
            if kwargs.get('name'):
                vals['name'] = kwargs['name']
            if kwargs.get('container_number'):
                vals['container_number'] = kwargs['container_number']
            if 'supplier_id' in kwargs:
                vals['supplier_id'] = kwargs.get('supplier_id') or False
            if 'agent_id' in kwargs:
                vals['agent_id'] = kwargs.get('agent_id') or False
            if kwargs.get('shipping_method'):
                vals['transport_mode'] = kwargs['shipping_method']
            if kwargs.get('origin'):
                vals['origin_location'] = kwargs['origin']
            if kwargs.get('destination'):
                vals['destination_location'] = kwargs['destination']
            dd = _parse_date(kwargs.get('etd'))
            if dd:
                vals['departure_date'] = dd
            ed = _parse_date(kwargs.get('eta'))
            if ed:
                vals['eta'] = ed
            if kwargs.get('status'):
                vals['shipment_tracking_state'] = kwargs['status']
            if kwargs.get('shipping_line'):
                vals['shipping_line'] = kwargs['shipping_line']
            if vals:
                c.write(vals)
            return {'success': True, 'data': _serialize_shipment_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_shipments_update')

    @http.route('/api/crm/supply/shipments/<int:shipment_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_delete(self, shipment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(shipment_id).exists()
            if not c:
                return {'success': False, 'error': 'Shipment not found', 'data': None}
            c.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': shipment_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_shipments_delete')

    @http.route('/api/crm/supply/shipments/<int:shipment_id>/link_orders', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_shipments_link_orders(self, shipment_id, **kwargs):
        """Attach PO ids to shipment container (`purchase_order_ids` when field exists)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(shipment_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Shipment not found', 'data': None}
            if 'purchase_order_ids' not in c._fields:
                return {'success': False, 'error': 'Linked orders not available on container', 'data': None}
            raw = kwargs.get('order_ids') or kwargs.get('po_ids') or []
            if not isinstance(raw, (list, tuple)):
                return {'success': False, 'error': 'order_ids must be a list of PO ids', 'data': None}
            ids = [int(x) for x in raw]
            Po = request.env['lugal.crm.supply.po'].sudo()
            pos = Po.search([('id', 'in', ids)])
            c.write({'purchase_order_ids': [(6, 0, pos.ids)]})
            return {'success': True, 'data': _serialize_shipment_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_shipments_link_orders')
