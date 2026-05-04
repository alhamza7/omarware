# -*- coding: utf-8 -*-
"""
REST-like JSON-RPC routes for Supply Chain SPA (`frontends/44`).

Covers vendors, containers (CRUD + workflow helpers), and purchase orders + lines.
Chat/stories remain in other controllers; attachments lists aligned with `supply_controller`.
"""

from datetime import date, datetime

from odoo import fields, http
from odoo.http import request

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .supply_controller import _serialize_supply_po, _serialize_supply_po_line
from .upload_controller import _build_attachment_url

_logger = __import__('logging').getLogger(__name__)


def _pagination(kwargs):
    try:
        page = max(1, int(kwargs.get('page') or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(200, max(1, int(kwargs.get('per_page') or 20)))
    except (TypeError, ValueError):
        per_page = 20
    return page, per_page, (page - 1) * per_page


def _parse_date(val):
    if not val:
        return False
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    s = str(val).strip()
    if not s:
        return False
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError:
        return False


def _serialize_vendor(v):
    country = v.country_id
    cur = v.currency_id
    return {
        'id': v.id,
        'name': v.name or '',
        'name_ar': v.name_ar or '',
        'contact_type': 'vendor',
        'phone': v.phone or '',
        'email': v.email or '',
        'website': v.website or '',
        'whatsapp': v.whatsapp or '',
        'telegram': v.telegram or '',
        'wechat': v.wechat or '',
        'division': v.division or '',
        'city': v.city or '',
        'country_name': country.name if country else '',
        'address': v.address or '',
        'payment_terms': v.payment_terms or '',
        'lead_time_days': int(v.lead_time_days or 0),
        'min_order_value': float(v.min_order_value or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'contact_name': v.contact_name or '',
        'notes': v.notes or '',
        'created_at': v.create_date.isoformat() if v.create_date else '',
    }


def _serialize_container(c):
    delivered_by = c.clearance_info_delivered_by_id
    supplier = c.supplier_id
    return {
        'id': c.id,
        'name': c.name or '',
        'container_number': c.container_number or '',
        'bl_number': c.bl_number or '',
        'clearance_company_id': None,
        'clearance_company_name': c.clearance_company or '',
        'origin_location': c.origin_location or '',
        'destination_port': c.destination_location or '',
        'departure_date': c.departure_date.isoformat() if c.departure_date else None,
        'eta': c.eta.isoformat() if c.eta else None,
        'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
        'status': c.status or 'waiting',
        'division': c.division or '',
        'tracking_url': c.tracking_url or '',
        'total_weight_kg': 0.0,
        'total_cbm': 0.0,
        'driver_id': None,
        'driver_name': '',
        'driver_phone': '',
        'driver_assigned_at': None,
        'driver_assigned_by': '',
        'clearance_info_delivered': bool(c.clearance_info_delivered),
        'clearance_info_delivered_at': (
            c.clearance_info_delivered_at.isoformat() if c.clearance_info_delivered_at else None
        ),
        'clearance_info_delivered_by': delivered_by.name if delivered_by else '',
        'attachment_count': len(c.attachment_ids),
        'penalty_count': len(c.penalty_ids),
        'vendor_id': supplier.id if supplier else None,
        'vendor_name': supplier.name if supplier else '',
        'reminder_date': None,
        'reminder_note': '',
        'notes': c.notes or '',
        'created_at': c.create_date.isoformat() if c.create_date else '',
        'updated_at': c.write_date.isoformat() if c.write_date else '',
    }


def _vendor_from_partner_id(partner_id):
    """Resolve `lugal.supply.vendor` from `res.partner` id (frontend vendor_customer_id)."""
    if not partner_id:
        return None
    Vendor = request.env['lugal.supply.vendor'].sudo()
    return Vendor.search([('partner_id', '=', int(partner_id))], limit=1)


class CrmSupplyChainApiController(http.Controller):
    # -------------------------------------------------------------------------
    # Vendors
    # -------------------------------------------------------------------------
    @http.route('/api/crm/supply/vendors/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            search = (kwargs.get('search') or '').strip()
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if search:
                domain += ['|', '|', ('name', 'ilike', search), ('name_ar', 'ilike', search), ('phone', 'ilike', search)]
            Vendor = request.env['lugal.supply.vendor'].sudo()
            total = Vendor.search_count(domain)
            rows = Vendor.search(domain, order='name asc, id asc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'items': [_serialize_vendor(v) for v in rows],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_vendors_list')

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_get(self, vendor_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found', 'data': None}
            return {'success': True, 'data': _serialize_vendor(v)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_get')

    @http.route('/api/crm/supply/vendors/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required', 'data': None}
            vals = {'name': name}
            opt = (
                'name_ar', 'phone', 'email', 'website', 'whatsapp', 'telegram', 'wechat',
                'city', 'address', 'payment_terms', 'notes', 'contact_name',
            )
            for k in opt:
                if kwargs.get(k) is not None:
                    vals[k] = kwargs[k]
            if kwargs.get('division'):
                vals['division'] = kwargs['division']
            if kwargs.get('lead_time_days') is not None:
                vals['lead_time_days'] = int(kwargs['lead_time_days'] or 0)
            if kwargs.get('min_order_value') is not None:
                vals['min_order_value'] = float(kwargs['min_order_value'] or 0.0)
            if kwargs.get('currency_id'):
                vals['currency_id'] = int(kwargs['currency_id'])
            rec = request.env['lugal.supply.vendor'].sudo().create(vals)
            return {'success': True, 'data': _serialize_vendor(rec)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_create')

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_update(self, vendor_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found', 'data': None}
            vals = {}
            for k in (
                'name', 'name_ar', 'phone', 'email', 'website', 'whatsapp', 'telegram', 'wechat',
                'city', 'address', 'payment_terms', 'notes', 'contact_name', 'division',
            ):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'lead_time_days' in kwargs:
                vals['lead_time_days'] = int(kwargs['lead_time_days'] or 0)
            if 'min_order_value' in kwargs:
                vals['min_order_value'] = float(kwargs['min_order_value'] or 0.0)
            if 'currency_id' in kwargs:
                vals['currency_id'] = kwargs.get('currency_id') or False
            if vals:
                v.write(vals)
            return {'success': True, 'data': _serialize_vendor(v)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_update')

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_delete(self, vendor_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v:
                return {'success': False, 'error': 'Vendor not found', 'data': None}
            v.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': vendor_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_vendors_delete')

    # -------------------------------------------------------------------------
    # Containers
    # -------------------------------------------------------------------------
    @http.route('/api/crm/supply/containers/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('division'):
                domain.append(('division', '=', kwargs['division']))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += [
                    '|', '|', '|',
                    ('name', 'ilike', search),
                    ('container_number', 'ilike', search),
                    ('bl_number', 'ilike', search),
                    ('shipment_ref', 'ilike', search),
                ]
            C = request.env['lugal.supply.container'].sudo()
            total = C.search_count(domain)
            rows = C.search(domain, order='departure_date desc, id desc', limit=per_page, offset=offset)
            return {
                'success': True,
                'data': {
                    'items': [_serialize_container(c) for c in rows],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'supply_containers_list')

    @http.route('/api/crm/supply/containers/<int:container_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_get(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_get')

    @http.route('/api/crm/supply/containers/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required', 'data': None}
            vals = {'name': name}
            if kwargs.get('container_number'):
                vals['container_number'] = kwargs['container_number']
            if kwargs.get('bl_number'):
                vals['bl_number'] = kwargs['bl_number']
            if kwargs.get('clearance_company_id'):
                pass  # model stores clearance_company as Char
            if kwargs.get('clearance_company'):
                vals['clearance_company'] = kwargs['clearance_company']
            if kwargs.get('origin_location'):
                vals['origin_location'] = kwargs['origin_location']
            if kwargs.get('destination_port'):
                vals['destination_location'] = kwargs['destination_port']
            dd = _parse_date(kwargs.get('departure_date'))
            if dd:
                vals['departure_date'] = dd
            ed = _parse_date(kwargs.get('eta'))
            if ed:
                vals['eta'] = ed
            if kwargs.get('division'):
                vals['division'] = kwargs['division']
            if kwargs.get('tracking_url'):
                vals['tracking_url'] = kwargs['tracking_url']
            if kwargs.get('notes'):
                vals['notes'] = kwargs['notes']
            c = request.env['lugal.supply.container'].sudo().create(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_create')

    @http.route('/api/crm/supply/containers/<int:container_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_update(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            vals = {}
            string_fields = (
                'name', 'container_number', 'bl_number', 'clearance_company',
                'origin_location', 'tracking_url', 'notes', 'shipping_line',
            )
            for k in string_fields:
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'destination_port' in kwargs:
                vals['destination_location'] = kwargs['destination_port']
            if 'status' in kwargs and kwargs['status']:
                vals['status'] = kwargs['status']
            if 'division' in kwargs:
                vals['division'] = kwargs['division']
            dd = _parse_date(kwargs.get('departure_date'))
            if dd:
                vals['departure_date'] = dd
            ed = _parse_date(kwargs.get('eta'))
            if ed:
                vals['eta'] = ed
            if vals:
                c.write(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_update')

    @http.route('/api/crm/supply/containers/<int:container_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_delete(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c:
                return {'success': False, 'error': 'Container not found', 'data': None}
            c.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': container_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_containers_delete')

    @http.route('/api/crm/supply/containers/<int:container_id>/mark_arrived', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_mark_arrived(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            c.write({
                'arrived_at': fields.Datetime.now(),
                'status': 'completed',
                'received_date': fields.Date.context_today(request.env['lugal.supply.container']),
                'shipment_tracking_state': 'arrived',
            })
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_mark_arrived')

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/clearance_delivered',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_containers_clearance_delivered(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            c.action_mark_clearance_delivered()
            c.invalidate_recordset()
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_clearance_delivered')

    @http.route('/api/crm/supply/containers/<int:container_id>/assign_driver', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_assign_driver(self, container_id, **kwargs):
        """No dedicated driver fields on model — acknowledge and return container."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_assign_driver')

    @http.route('/api/crm/supply/containers/<int:container_id>/unassign_driver', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_unassign_driver(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_unassign_driver')

    @http.route('/api/crm/supply/containers/<int:container_id>/set_reminder', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_set_reminder(self, container_id, **kwargs):
        """Reminder fields not on model — no-op success for API compatibility."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found', 'data': None}
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_set_reminder')

    # -------------------------------------------------------------------------
    # Purchase orders (register specific paths before generic /<id>/get)
    # -------------------------------------------------------------------------
    @http.route('/api/crm/supply/po/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            page, per_page, offset = _pagination(kwargs)
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('division'):
                domain.append(('division', '=', kwargs['division']))
            if kwargs.get('vendor_customer_id'):
                v = _vendor_from_partner_id(kwargs['vendor_customer_id'])
                if v:
                    domain.append(('vendor_id', '=', v.id))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain.append(('name', 'ilike', search))
            Po = request.env['lugal.crm.supply.po'].sudo()
            total = Po.search_count(domain)
            rows = Po.search(domain, order='write_date desc, id desc', limit=per_page, offset=offset)
            items = [_serialize_supply_po(po) for po in rows]
            return {'success': True, 'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page}}
        except Exception as e:
            return crm_error(e, 'supply_po_list')

    @http.route('/api/crm/supply/po/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            partner_id = kwargs.get('vendor_customer_id')
            vendor = _vendor_from_partner_id(partner_id) if partner_id else None
            if not vendor:
                return {'success': False, 'error': 'vendor_customer_id must reference a vendor-linked partner', 'data': None}
            vals = {'vendor_id': vendor.id}
            if kwargs.get('name'):
                vals['name'] = (kwargs.get('name') or '').strip()
            if kwargs.get('division'):
                vals['division'] = kwargs['division']
            if kwargs.get('currency_id'):
                vals['currency_id'] = int(kwargs['currency_id'])
            if kwargs.get('container_id'):
                vals['container_id'] = int(kwargs['container_id'])
            if kwargs.get('branch_id'):
                vals['branch_id'] = int(kwargs['branch_id'])
            Po = request.env['lugal.crm.supply.po'].sudo()
            if kwargs.get('item_request_id'):
                vals['item_request_id'] = int(kwargs['item_request_id'])
            if kwargs.get('negotiation_id'):
                vals['negotiation_id'] = int(kwargs['negotiation_id'])
            if kwargs.get('agent_id'):
                vals['agent_id'] = int(kwargs['agent_id'])
            if kwargs.get('order_date'):
                vals['order_date'] = _parse_date(kwargs['order_date'])
            if kwargs.get('production_completion_date'):
                vals['production_completion_date'] = _parse_date(kwargs['production_completion_date'])
            if kwargs.get('payment_term'):
                vals['payment_term'] = kwargs['payment_term']
            if kwargs.get('shipping_method'):
                vals['shipping_method'] = kwargs['shipping_method']
            if kwargs.get('notes'):
                vals['notes'] = kwargs['notes']
            if kwargs.get('extra_fields') is not None:
                vals['extra_fields'] = Po.sanitize_extra_fields_input(kwargs['extra_fields'])
            po = Po.create(vals)
            Line = request.env['lugal.crm.supply.po.line'].sudo()
            for line in kwargs.get('lines') or []:
                lv = {
                    'po_id': po.id,
                    'product_name': line.get('product_name') or '',
                    'item_code': line.get('item_code') or '',
                    'uom': line.get('uom') or '',
                    'quantity': float(line.get('quantity') or 1.0),
                    'unit_price': float(line.get('unit_price') or 0.0),
                    'min_qty': float(line.get('min_qty') or 0.0),
                    'max_qty': float(line.get('max_qty') or 0.0),
                }
                if line.get('currency_id'):
                    lv['currency_id'] = int(line['currency_id'])
                Line.create(lv)
            po.invalidate_recordset()
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_create')

    @http.route('/api/crm/supply/po/<int:po_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_get(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_get')

    @http.route('/api/crm/supply/po/<int:po_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_update(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            vals = {}
            if 'name' in kwargs:
                vals['name'] = kwargs['name']
            if 'division' in kwargs:
                vals['division'] = kwargs['division']
            if 'currency_id' in kwargs:
                vals['currency_id'] = kwargs.get('currency_id') or False
            if 'container_id' in kwargs:
                vals['container_id'] = kwargs.get('container_id') or False
            if 'branch_id' in kwargs:
                vals['branch_id'] = kwargs.get('branch_id') or False
            if 'status' in kwargs and kwargs['status']:
                vals['status'] = kwargs['status']
            if 'is_suggested' in kwargs:
                vals['is_suggested'] = bool(kwargs['is_suggested'])
            wf_keys = (
                'item_request_id', 'negotiation_id', 'agent_id',
                'payment_term', 'shipping_method', 'notes',
            )
            for k in wf_keys:
                if k in kwargs:
                    vals[k] = kwargs[k] if kwargs[k] not in (False, None, '') else False
            if 'order_date' in kwargs:
                vals['order_date'] = _parse_date(kwargs['order_date'])
            if 'production_completion_date' in kwargs:
                vals['production_completion_date'] = _parse_date(kwargs['production_completion_date'])
            if vals:
                po.write(vals)
            if 'extra_fields' in kwargs and kwargs['extra_fields'] is not None:
                cleaned = request.env['lugal.crm.supply.po'].sudo().sanitize_extra_fields_input(
                    kwargs['extra_fields']
                )
                po.merge_extra_fields(cleaned)
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_update')

    @http.route('/api/crm/supply/po/<int:po_id>/order_e_sign', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_order_e_sign(self, po_id, **kwargs):
        """Record order-level confirmation signature on PO (CRM extend model)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            if hasattr(po, 'action_confirm_order_e_sign'):
                po.action_confirm_order_e_sign()
            else:
                return {'success': False, 'error': 'Order e-sign not available', 'data': None}
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_order_e_sign')

    @http.route('/api/crm/supply/po/<int:po_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_delete(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'is_deleted': True, 'active': False})
            return {'success': True, 'data': {'id': po_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_po_delete')

    @http.route('/api/crm/supply/po/<int:po_id>/confirm', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_confirm(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'status': 'confirmed'})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_confirm')

    @http.route('/api/crm/supply/po/<int:po_id>/ship', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_ship(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'status': 'confirmed'})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_ship')

    @http.route('/api/crm/supply/po/<int:po_id>/receive', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_receive(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'status': 'confirmed'})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_receive')

    @http.route('/api/crm/supply/po/<int:po_id>/cancel', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_cancel(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'status': 'cancelled'})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_cancel')

    @http.route('/api/crm/supply/po/<int:po_id>/reopen', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_reopen(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            po.write({'status': 'draft'})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_reopen')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_lines_add(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            Line = request.env['lugal.crm.supply.po.line'].sudo()
            lv = {
                'po_id': po.id,
                'product_name': kwargs.get('product_name') or '',
                'item_code': kwargs.get('item_code') or '',
                'uom': kwargs.get('uom') or '',
                'quantity': float(kwargs.get('quantity') or 1.0),
                'unit_price': float(kwargs.get('unit_price') or 0.0),
                'min_qty': float(kwargs.get('min_qty') or 0.0),
                'max_qty': float(kwargs.get('max_qty') or 0.0),
            }
            if kwargs.get('currency_id'):
                lv['currency_id'] = int(kwargs['currency_id'])
            line = Line.create(lv)
            po.invalidate_recordset()
            return {'success': True, 'data': _serialize_supply_po_line(line)}
        except Exception as e:
            return crm_error(e, 'supply_po_lines_add')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_lines_update(self, po_id, line_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            line = request.env['lugal.crm.supply.po.line'].sudo().browse(line_id).exists()
            if not line or line.po_id.id != po_id:
                return {'success': False, 'error': 'Line not found', 'data': None}
            vals = {}
            for k in (
                'product_name', 'item_code', 'uom', 'min_qty', 'max_qty',
                'sequence', 'size', 'capacity',
            ):
                if k in kwargs:
                    vals[k] = kwargs[k]
            if 'quantity' in kwargs:
                vals['quantity'] = float(kwargs['quantity'] or 0.0)
            if 'unit_price' in kwargs:
                vals['unit_price'] = float(kwargs['unit_price'] or 0.0)
            if 'currency_id' in kwargs:
                vals['currency_id'] = kwargs.get('currency_id') or False
            if 'last_purchase_price' in kwargs:
                vals['last_purchase_price'] = float(kwargs['last_purchase_price'] or 0.0)
            lp = _parse_date(kwargs.get('last_purchase_date'))
            if lp:
                vals['last_purchase_date'] = lp
            if vals:
                line.write(vals)
            return {'success': True, 'data': _serialize_supply_po_line(line)}
        except Exception as e:
            return crm_error(e, 'supply_po_lines_update')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_lines_delete(self, po_id, line_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            line = request.env['lugal.crm.supply.po.line'].sudo().browse(line_id).exists()
            if not line or line.po_id.id != po_id:
                return {'success': False, 'error': 'Line not found', 'data': None}
            line.unlink()
            return {'success': True, 'data': {'id': line_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_po_lines_delete')

    @http.route('/api/crm/supply/po/<int:po_id>/attachments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_attachments_list(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            attachments = []
            if 'order_attachment_ids' in po._fields:
                for att in po.order_attachment_ids.sorted('id', reverse=True):
                    attachments.append({
                        'id': att.id,
                        'name': att.name or '',
                        'mimetype': att.mimetype or 'application/octet-stream',
                        'size': int(att.file_size or 0),
                        'url': _build_attachment_url(att),
                        'file_url': _build_attachment_url(att),
                        'uploaded_by_name': att.create_uid.name if att.create_uid else '',
                        'created_at': att.create_date.isoformat() if att.create_date else '',
                    })
            return {'success': True, 'data': {'po_id': po.id, 'attachments': attachments}}
        except Exception as e:
            return crm_error(e, 'supply_po_attachments_list')

    @http.route(
        '/api/crm/supply/po/<int:po_id>/attachments/link',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_po_attachments_link(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found', 'data': None}
            if 'order_attachment_ids' not in po._fields:
                return {'success': False, 'error': 'Order attachments not available', 'data': None}
            ids = kwargs.get('attachment_ids') or kwargs.get('ids') or []
            if not isinstance(ids, (list, tuple)):
                return {'success': False, 'error': 'attachment_ids must be a list', 'data': None}
            cmd = [(6, 0, [int(x) for x in ids])] if ids else [(5,)]
            po.write({'order_attachment_ids': cmd})
            return {'success': True, 'data': _serialize_supply_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_attachments_link')

    # --- Stubs: mail-thread comments not wired in this iteration ---
    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/list',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_container_comments_list_stub(self, container_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': True, 'data': {'total': 0, 'items': []}}

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/add',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_container_comments_add_stub(self, container_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': False, 'error': 'Container comments API not enabled', 'data': None}

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/<int:msg_id>/delete',
        type='jsonrpc', auth='none', csrf=False, methods=['POST'],
    )
    def supply_container_comments_delete_stub(self, container_id, msg_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': False, 'error': 'Container comments API not enabled', 'data': None}

    @http.route('/api/crm/supply/po/<int:po_id>/comments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_list_stub(self, po_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': True, 'data': {'total': 0, 'items': []}}

    @http.route('/api/crm/supply/po/<int:po_id>/comments/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_add_stub(self, po_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': False, 'error': 'PO comments API not enabled', 'data': None}

    @http.route('/api/crm/supply/po/<int:po_id>/comments/<int:msg_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_delete_stub(self, po_id, msg_id, **kwargs):
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized', 'data': None}
        return {'success': False, 'error': 'PO comments API not enabled', 'data': None}
