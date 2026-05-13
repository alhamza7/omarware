# -*- coding: utf-8 -*-
"""REST JSON-RPC for supply vendors, containers, PO — routes expected by frontends/44 `supplyApi.ts`.

Models: `lugal.supply.vendor`, `lugal.supply.container`, `lugal.crm.supply.po`, `lugal.crm.supply.po.line`.
"""

import base64
import json
import logging
import mimetypes
import uuid

from odoo import fields, http
from odoo.http import request, Response

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from ._permissions import require_permission
from .supply_controller import _serialize_penalty
from .upload_controller import (
    ALLOWED_DOC_MIMES,
    _build_attachment_url,
    _create_attachment,
    is_allowed_crm_image_mime,
)

_logger = logging.getLogger(__name__)

PO_STATUS_LABEL = {
    'draft': 'Draft',
    'confirmed': 'Confirmed',
    'shipped': 'Shipped',
    'received': 'Received',
    'cancelled': 'Cancelled',
}


def _json_http(payload, status=200):
    resp = Response(
        json.dumps(payload, ensure_ascii=False, default=str),
        status=status,
        headers=[('Content-Type', 'application/json; charset=utf-8')],
    )
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Odoo-Database'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    return resp


def _allowed_upload_mime(mime):
    if not mime:
        return False
    if mime in ALLOWED_DOC_MIMES:
        return True
    return is_allowed_crm_image_mime(mime)


def _serialize_ir_attachment(att):
    return {
        'id': att.id,
        'name': att.name or '',
        'mimetype': att.mimetype or 'application/octet-stream',
        'size': int(att.file_size or 0),
        'url': _build_attachment_url(att),
        'uploaded_by_name': att.create_uid.name if att.create_uid else '',
        'created_at': att.create_date.isoformat() if att.create_date else '',
    }


def _serialize_vendor(v):
    country_name = v.country_id.name if getattr(v, 'country_id', None) else ''
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
        'country_name': country_name or '',
        'address': v.address or '',
        'payment_terms': v.payment_terms or '',
        'lead_time_days': int(v.lead_time_days or 0),
        'min_order_value': float(v.min_order_value or 0.0),
        'contact_name': v.contact_name or '',
        'notes': v.notes or '',
        'created_at': v.create_date.isoformat() if v.create_date else '',
    }


def _serialize_container(c):
    clr_by = c.clearance_info_delivered_by_id
    assign = c.assigned_user_id
    return {
        'id': c.id,
        'name': c.name or '',
        'container_number': c.container_number or '',
        'bl_number': c.bl_number or '',
        'clearance_company_id': c.clearance_company_id.id if c.clearance_company_id else None,
        'clearance_company_name': c.clearance_company_id.name if c.clearance_company_id else (c.clearance_company or ''),
        'origin_location': c.origin_location or '',
        'destination_port': c.destination_port or '',
        'departure_date': c.departure_date.isoformat() if c.departure_date else None,
        'eta': c.eta.isoformat() if c.eta else None,
        'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
        'status': c.status or 'waiting',
        'division': c.division or '',
        'tracking_url': c.tracking_url or '',
        'total_weight_kg': float(c.total_weight_kg or 0.0),
        'total_cbm': float(c.total_cbm or 0.0),
        'driver_id': assign.id if assign else None,
        'driver_name': c.driver_name or (assign.name if assign else '') or '',
        'driver_phone': c.driver_phone or '',
        'driver_assigned_at': c.driver_assigned_at.isoformat() if c.driver_assigned_at else None,
        'driver_assigned_by': '',
        'clearance_info_delivered': bool(c.clearance_info_delivered),
        'clearance_info_delivered_at': c.clearance_info_delivered_at.isoformat()
        if c.clearance_info_delivered_at
        else None,
        'clearance_info_delivered_by': clr_by.name if clr_by else '',
        'attachment_count': len(c.attachment_ids),
        'penalty_count': len(c.penalty_ids),
        'vendor_id': None,
        'vendor_name': '',
        'reminder_date': c.reminder_date.isoformat() if c.reminder_date else None,
        'reminder_note': c.reminder_note or '',
        'notes': c.notes or '',
        'created_at': c.create_date.isoformat() if c.create_date else '',
        'updated_at': c.write_date.isoformat() if c.write_date else '',
    }


def _serialize_po_line(line, po_currency):
    cur = line.currency_id or po_currency
    return {
        'id': line.id,
        'sequence': int(line.sequence or 10),
        'product_name': line.product_name or '',
        'item_code': line.item_code or '',
        'uom': line.uom or '',
        'quantity': float(line.quantity or 0.0),
        'unit_price': float(line.unit_price or 0.0),
        'total_price': float(line.total_price or 0.0),
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'last_purchase_price': float(line.last_purchase_price or 0.0),
        'last_purchase_date': line.last_purchase_date.isoformat() if line.last_purchase_date else None,
        'min_qty': float(line.min_qty or 0.0),
        'max_qty': float(line.max_qty or 0.0),
    }


def _serialize_po(po):
    vend = po.vendor_id
    cur = po.currency_id
    cont = po.container_id
    br = po.branch_id
    author = po.create_uid
    lines = [_serialize_po_line(ln, cur) for ln in po.line_ids]
    return {
        'id': po.id,
        'name': po.name or '',
        'vendor_customer_id': vend.id if vend else None,
        'vendor_customer_name': vend.name if vend else '',
        'vendor_customer_phone': vend.phone if vend else '',
        'vendor_id': vend.id if vend else None,
        'vendor_name': vend.name if vend else '',
        'division': po.division or '',
        'currency_id': cur.id if cur else None,
        'currency_name': cur.name if cur else '',
        'container_id': cont.id if cont else None,
        'container_name': cont.name if cont else '',
        'branch_id': br.id if br else None,
        'branch_name': br.name if br else '',
        'status': po.status or 'draft',
        'status_label': PO_STATUS_LABEL.get(po.status, po.status or ''),
        'is_suggested': bool(po.is_suggested),
        'line_count': len(po.line_ids),
        'total_amount': float(po.total_amount or 0.0),
        'created_by_id': author.id if author else None,
        'created_by_name': author.name if author else '',
        'created_at': po.create_date.isoformat() if po.create_date else '',
        'updated_at': po.write_date.isoformat() if po.write_date else '',
        'lines': lines,
    }


def _comment_body_plain(body):
    if not body:
        return ''
    # strip simple HTML for plain body
    import re

    s = re.sub(r'<[^>]+>', '', body or '')
    return s.strip()


def _serialize_mail_message(msg):
    subtype_xml = msg.subtype_id.xml_id if msg.subtype_id else ''
    is_note = 'note' in (subtype_xml or '').lower() or (msg.subtype_id and 'note' in (msg.subtype_id.name or '').lower())
    author = msg.author_id
    return {
        'id': msg.id,
        'body': _comment_body_plain(msg.body),
        'body_html': msg.body or '',
        'is_note': bool(is_note),
        'author_id': author.id if author else None,
        'author_name': author.name if author else '',
        'author_avatar': None,
        'message_type': msg.message_type or 'comment',
        'subtype': subtype_xml,
        'created_at': msg.date.isoformat() if msg.date else '',
    }


class CrmSupplyChainController(http.Controller):
    # -------------------------------------------------------------------------
    # Vendors
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/vendors/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.vendors.list')
            if denied:
                return denied
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 50)))
            search = (kwargs.get('search') or '').strip()
            domain = [('is_deleted', '=', False)]
            if search:
                domain += ['|', ('name', 'ilike', search), ('name_ar', 'ilike', search)]
            Vendor = request.env['lugal.supply.vendor'].sudo()
            total = Vendor.search_count(domain)
            rows = Vendor.search(domain, order='name asc, id asc', limit=per_page, offset=(page - 1) * per_page)
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
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.vendors.view')
            if denied:
                return denied
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            return {'success': True, 'data': _serialize_vendor(v)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_get')

    @http.route('/api/crm/supply/vendors/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.vendors.create')
            if denied:
                return denied
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required'}
            vals = {
                'name': name,
                'name_ar': kwargs.get('name_ar') or False,
                'division': kwargs.get('division') or False,
                'contact_name': kwargs.get('contact_name') or False,
                'phone': kwargs.get('phone') or False,
                'email': kwargs.get('email') or False,
                'website': kwargs.get('website') or False,
                'whatsapp': kwargs.get('whatsapp') or False,
                'telegram': kwargs.get('telegram') or False,
                'wechat': kwargs.get('wechat') or False,
                'city': kwargs.get('city') or False,
                'address': kwargs.get('address') or False,
                'payment_terms': kwargs.get('payment_terms') or False,
                'lead_time_days': int(kwargs['lead_time_days']) if kwargs.get('lead_time_days') is not None else 0,
                'min_order_value': float(kwargs['min_order_value']) if kwargs.get('min_order_value') is not None else 0.0,
                'notes': kwargs.get('notes') or False,
            }
            v = request.env['lugal.supply.vendor'].sudo().create(vals)
            return {'success': True, 'data': _serialize_vendor(v)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_create')

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_update(self, vendor_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.vendors.edit')
            if denied:
                return denied
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            allowed = {
                'name', 'name_ar', 'division', 'contact_name', 'phone', 'email', 'website',
                'whatsapp', 'telegram', 'wechat', 'city', 'address', 'payment_terms',
                'lead_time_days', 'min_order_value', 'notes',
            }
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                v.write(vals)
            return {'success': True, 'data': _serialize_vendor(v)}
        except Exception as e:
            return crm_error(e, 'supply_vendors_update')

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_vendors_delete(self, vendor_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.vendors.delete')
            if denied:
                return denied
            v = request.env['lugal.supply.vendor'].sudo().browse(vendor_id).exists()
            if not v or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            v.write({'is_deleted': True})
            return {'success': True, 'data': {'id': v.id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_vendors_delete')

    # -------------------------------------------------------------------------
    # Containers (CRUD + workflow)
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/containers/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.list')
            if denied:
                return denied
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 20)))
            status = kwargs.get('status')
            division = kwargs.get('division')
            search = (kwargs.get('search') or '').strip()
            domain = [('is_deleted', '=', False)]
            if status:
                domain.append(('status', '=', status))
            if division:
                domain.append(('division', '=', division))
            if search:
                domain += [
                    '|', '|', '|',
                    ('name', 'ilike', search),
                    ('container_number', 'ilike', search),
                    ('bl_number', 'ilike', search),
                    ('origin_location', 'ilike', search),
                ]
            Container = request.env['lugal.supply.container'].sudo()
            total = Container.search_count(domain)
            rows = Container.search(domain, order='departure_date desc, id desc', limit=per_page, offset=(page - 1) * per_page)
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
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.view')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_get')

    @http.route('/api/crm/supply/containers/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.create')
            if denied:
                return denied
            name = (kwargs.get('name') or '').strip()
            if not name:
                return {'success': False, 'error': 'name is required'}
            vals = {
                'name': name,
                'container_number': kwargs.get('container_number') or False,
                'bl_number': kwargs.get('bl_number') or False,
                'clearance_company_id': kwargs.get('clearance_company_id') or False,
                'origin_location': kwargs.get('origin_location') or False,
                'destination_port': kwargs.get('destination_port') or False,
                'departure_date': kwargs.get('departure_date') or False,
                'eta': kwargs.get('eta') or False,
                'division': kwargs.get('division') or False,
                'tracking_url': kwargs.get('tracking_url') or False,
                'total_weight_kg': float(kwargs['total_weight_kg']) if kwargs.get('total_weight_kg') is not None else 0.0,
                'total_cbm': float(kwargs['total_cbm']) if kwargs.get('total_cbm') is not None else 0.0,
                'notes': kwargs.get('notes') or False,
            }
            c = request.env['lugal.supply.container'].sudo().create(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_create')

    @http.route('/api/crm/supply/containers/<int:container_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_update(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.edit')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            allowed = {
                'name', 'container_number', 'bl_number', 'clearance_company', 'clearance_company_id',
                'origin_location', 'destination_port', 'departure_date', 'eta', 'status', 'division',
                'tracking_url', 'total_weight_kg', 'total_cbm', 'notes',
            }
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                c.write(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_update')

    @http.route('/api/crm/supply/containers/<int:container_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_delete(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.delete')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            c.write({'is_deleted': True})
            return {'success': True, 'data': {'id': c.id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_containers_delete')

    @http.route('/api/crm/supply/containers/<int:container_id>/mark_arrived', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_mark_arrived(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.mark_arrived')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            c.write({
                'arrived_at': fields.Datetime.now(),
                'status': 'at_port',
            })
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_mark_arrived')

    @http.route('/api/crm/supply/containers/<int:container_id>/clearance_delivered', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_clearance_delivered(self, container_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.clearance_delivered')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            c.write({
                'clearance_info_delivered': True,
                'clearance_info_delivered_at': fields.Datetime.now(),
                'clearance_info_delivered_by_id': uid,
            })
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_clearance_delivered')

    @http.route('/api/crm/supply/containers/<int:container_id>/assign_driver', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_assign_driver(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.assign_driver')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            vals = {'driver_assigned_at': fields.Datetime.now()}
            if kwargs.get('driver_id'):
                vals['assigned_user_id'] = int(kwargs['driver_id'])
            if kwargs.get('driver_name') is not None:
                vals['driver_name'] = kwargs.get('driver_name') or ''
            if kwargs.get('driver_phone') is not None:
                vals['driver_phone'] = kwargs.get('driver_phone') or ''
            c.write(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_assign_driver')

    @http.route('/api/crm/supply/containers/<int:container_id>/unassign_driver', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_unassign_driver(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.unassign_driver')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            c.write({
                'assigned_user_id': False,
                'driver_name': '',
                'driver_phone': '',
                'driver_assigned_at': False,
            })
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_unassign_driver')

    @http.route('/api/crm/supply/containers/<int:container_id>/set_reminder', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_containers_set_reminder(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.set_reminder')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            if kwargs.get('clear_reminder'):
                c.write({'reminder_date': False, 'reminder_note': False})
            else:
                vals = {}
                if 'reminder_date' in kwargs:
                    vals['reminder_date'] = kwargs.get('reminder_date') or False
                if 'reminder_note' in kwargs:
                    vals['reminder_note'] = kwargs.get('reminder_note') or ''
                if vals:
                    c.write(vals)
            return {'success': True, 'data': _serialize_container(c)}
        except Exception as e:
            return crm_error(e, 'supply_containers_set_reminder')

    # --- Container attachments (upload/delete — list lives in supply_controller) ---

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/attachments/upload',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
        max_content_length=104857600,
    )
    def supply_container_attach_upload(self, container_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])
        try:
            if not ensure_jwt_user_id():
                return _json_http({'success': False, 'error': 'Unauthorized'}, 401)
            denied = require_permission('supply_chain.containers.upload_attachment')
            if denied:
                return _json_http(denied, 403)
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return _json_http({'success': False, 'error': 'Container not found'}, 404)
            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json_http({'success': False, 'error': 'No file'}, 400)
            ir_rows = []
            for f in files:
                data = f.read()
                mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''
                if not _allowed_upload_mime(mime):
                    return _json_http({'success': False, 'error': f'Unsupported type: {mime}'}, 400)
                att = _create_attachment(
                    f.filename or 'file',
                    mime,
                    data,
                    res_model='lugal.supply.container',
                    res_id=c.id,
                )
                c.write({'attachment_ids': [(4, att.id)]})
                ir_rows.append(_serialize_ir_attachment(att))
            return _json_http({
                'success': True,
                'data': {
                    'attachments': [{'name': r['name'], 'url': r['url']} for r in ir_rows],
                    'uploaded_count': len(ir_rows),
                    'total_attachments': len(ir_rows),
                },
            })
        except Exception as e:
            _logger.exception('supply_container_attach_upload')
            return _json_http({'success': False, 'error': str(e)}, 500)

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/attachments/<int:attachment_id>/delete',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_attach_delete(self, container_id, attachment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.delete_attachment')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            att = request.env['ir.attachment'].sudo().browse(attachment_id).exists()
            if not att:
                return {'success': False, 'error': 'Attachment not found'}
            c.write({'attachment_ids': [(3, att.id)]})
            att.unlink()
            return {'success': True, 'data': {'deleted_id': attachment_id}}
        except Exception as e:
            return crm_error(e, 'supply_container_attach_delete')

    # --- Container comments (mail.thread) ---

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/list',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_comments_list(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.list')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            page = max(1, int(kwargs.get('page') or 1))
            limit = 50
            Msg = request.env['mail.message'].sudo()
            domain = [
                ('model', '=', 'lugal.supply.container'),
                ('res_id', '=', c.id),
                ('message_type', 'in', ('comment', 'notification')),
            ]
            total = Msg.search_count(domain)
            msgs = Msg.search(domain, order='id desc', limit=limit, offset=(page - 1) * limit)
            return {
                'success': True,
                'data': {'total': total, 'items': [_serialize_mail_message(m) for m in msgs]},
            }
        except Exception as e:
            return crm_error(e, 'supply_container_comments_list')

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/add',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_comments_add(self, container_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.add_comment')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            body = (kwargs.get('body') or '').strip()
            if not body:
                return {'success': False, 'error': 'body is required'}
            is_note = bool(kwargs.get('is_note'))
            subtype = 'mail.mt_note' if is_note else 'mail.mt_comment'
            msg = c.with_user(uid).message_post(
                body=body, message_type='comment', subtype_xmlid=subtype
            )
            return {'success': True, 'data': _serialize_mail_message(msg)}
        except Exception as e:
            return crm_error(e, 'supply_container_comments_add')

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/comments/<int:message_id>/delete',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_comments_delete(self, container_id, message_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.delete_comment')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            msg = request.env['mail.message'].sudo().browse(message_id).exists()
            if not msg or msg.model != 'lugal.supply.container' or msg.res_id != c.id:
                return {'success': False, 'error': 'Message not found'}
            msg.unlink()
            return {'success': True, 'data': {'id': message_id}}
        except Exception as e:
            return crm_error(e, 'supply_container_comments_delete')

    # --- Penalty add/delete ---

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/add_penalty',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_add_penalty(self, container_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.add_penalty')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            Penalty = request.env['lugal.supply.container.penalty'].sudo()
            p = Penalty.create({
                'container_id': c.id,
                'penalty_type': kwargs.get('penalty_type') or 'other',
                'amount': float(kwargs.get('amount') or 0.0),
                'currency_id': kwargs.get('currency_id') or False,
                'reason': kwargs.get('reason') or '',
                'penalty_date': kwargs.get('penalty_date') or False,
            })
            return {'success': True, 'data': _serialize_penalty(p, c)}
        except Exception as e:
            return crm_error(e, 'supply_container_add_penalty')

    @http.route(
        '/api/crm/supply/containers/<int:container_id>/penalties/<int:penalty_id>/delete',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_container_penalty_delete(self, container_id, penalty_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.containers.delete_penalty')
            if denied:
                return denied
            c = request.env['lugal.supply.container'].sudo().browse(container_id).exists()
            if not c or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            p = request.env['lugal.supply.container.penalty'].sudo().browse(penalty_id).exists()
            if not p or p.container_id.id != c.id:
                return {'success': False, 'error': 'Penalty not found'}
            p.unlink()
            return {'success': True, 'data': {'deleted_id': penalty_id, 'container_id': c.id}}
        except Exception as e:
            return crm_error(e, 'supply_container_penalty_delete')

    # -------------------------------------------------------------------------
    # Purchase orders
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/po/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_list(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.list')
            if denied:
                return denied
            page = max(1, int(kwargs.get('page') or 1))
            per_page = min(200, max(1, int(kwargs.get('per_page') or 20)))
            domain = [('is_deleted', '=', False)]
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('division'):
                domain.append(('division', '=', kwargs['division']))
            if kwargs.get('vendor_customer_id'):
                domain.append(('vendor_id', '=', int(kwargs['vendor_customer_id'])))
            if kwargs.get('container_id'):
                domain.append(('container_id', '=', int(kwargs['container_id'])))
            if kwargs.get('branch_id'):
                domain.append(('branch_id', '=', int(kwargs['branch_id'])))
            search = (kwargs.get('search') or '').strip()
            if search:
                domain += ['|', ('name', 'ilike', search), ('vendor_id.name', 'ilike', search)]
            Po = request.env['lugal.crm.supply.po'].sudo()
            total = Po.search_count(domain)
            rows = Po.search(domain, order='write_date desc, id desc', limit=per_page, offset=(page - 1) * per_page)
            items = []
            for po in rows:
                d = _serialize_po(po)
                d['lines'] = []
                items.append(d)
            return {
                'success': True,
                'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            return crm_error(e, 'supply_po_list')

    @http.route('/api/crm/supply/po/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_create(self, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.create')
            if denied:
                return denied
            name = (kwargs.get('name') or '').strip()
            vid = kwargs.get('vendor_customer_id')
            if not name:
                return {'success': False, 'error': 'name is required'}
            if not vid:
                return {'success': False, 'error': 'vendor_customer_id is required'}
            vendor = request.env['lugal.supply.vendor'].sudo().browse(int(vid)).exists()
            if not vendor or vendor.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            po_vals = {
                'name': name,
                'vendor_id': vendor.id,
                'division': kwargs.get('division') or False,
                'currency_id': kwargs.get('currency_id') or False,
                'container_id': kwargs.get('container_id') or False,
                'branch_id': kwargs.get('branch_id') or False,
                'status': 'draft',
            }
            Po = request.env['lugal.crm.supply.po'].sudo()
            po = Po.create(po_vals)
            lines_in = kwargs.get('lines') or []
            Line = request.env['lugal.crm.supply.po.line'].sudo()
            seq = 10
            for ln in lines_in:
                Line.create({
                    'po_id': po.id,
                    'sequence': seq,
                    'product_name': ln.get('product_name') or '',
                    'item_code': ln.get('item_code') or False,
                    'uom': ln.get('uom') or False,
                    'quantity': float(ln.get('quantity') or 0),
                    'unit_price': float(ln.get('unit_price') or 0),
                    'currency_id': ln.get('currency_id') or po.currency_id.id or False,
                    'min_qty': float(ln.get('min_qty') or 0),
                    'max_qty': float(ln.get('max_qty') or 0),
                })
                seq += 10
            po.invalidate_recordset()
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_create')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_line_add(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.add_line')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status in ('received', 'cancelled'):
                return {'success': False, 'error': 'Cannot edit lines in this status'}
            Line = request.env['lugal.crm.supply.po.line'].sudo()
            max_seq = max([ln.sequence for ln in po.line_ids] or [0])
            line = Line.create({
                'po_id': po.id,
                'sequence': max_seq + 10,
                'product_name': kwargs.get('product_name') or '',
                'item_code': kwargs.get('item_code') or False,
                'uom': kwargs.get('uom') or False,
                'quantity': float(kwargs.get('quantity') or 0),
                'unit_price': float(kwargs.get('unit_price') or 0),
                'currency_id': kwargs.get('currency_id') or po.currency_id.id or False,
                'min_qty': float(kwargs.get('min_qty') or 0),
                'max_qty': float(kwargs.get('max_qty') or 0),
            })
            po.invalidate_recordset()
            return {'success': True, 'data': _serialize_po_line(line, po.currency_id)}
        except Exception as e:
            return crm_error(e, 'supply_po_line_add')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_line_update(self, po_id, line_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.edit_line')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status in ('received', 'cancelled'):
                return {'success': False, 'error': 'Cannot edit lines in this status'}
            line = request.env['lugal.crm.supply.po.line'].sudo().browse(line_id).exists()
            if not line or line.po_id.id != po.id:
                return {'success': False, 'error': 'Line not found'}
            allowed = {
                'product_name', 'item_code', 'uom', 'quantity', 'unit_price',
                'currency_id', 'min_qty', 'max_qty', 'sequence',
            }
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                line.write(vals)
            return {'success': True, 'data': _serialize_po_line(line, po.currency_id)}
        except Exception as e:
            return crm_error(e, 'supply_po_line_update')

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_line_delete(self, po_id, line_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.delete_line')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status in ('received', 'cancelled'):
                return {'success': False, 'error': 'Cannot edit lines in this status'}
            line = request.env['lugal.crm.supply.po.line'].sudo().browse(line_id).exists()
            if not line or line.po_id.id != po.id:
                return {'success': False, 'error': 'Line not found'}
            line.unlink()
            return {'success': True, 'data': {'id': line_id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_po_line_delete')

    @http.route('/api/crm/supply/po/<int:po_id>/confirm', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_confirm(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.confirm')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status != 'draft':
                return {'success': False, 'error': 'Invalid status transition'}
            po.write({'status': 'confirmed'})
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_confirm')

    @http.route('/api/crm/supply/po/<int:po_id>/ship', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_ship(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.ship')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status != 'confirmed':
                return {'success': False, 'error': 'Invalid status transition'}
            po.write({'status': 'shipped'})
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_ship')

    @http.route('/api/crm/supply/po/<int:po_id>/receive', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_receive(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.receive')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status != 'shipped':
                return {'success': False, 'error': 'Invalid status transition'}
            po.write({'status': 'received'})
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_receive')

    @http.route('/api/crm/supply/po/<int:po_id>/cancel', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_cancel(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.cancel')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status in ('received', 'cancelled'):
                return {'success': False, 'error': 'Invalid status transition'}
            po.write({'status': 'cancelled'})
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_cancel')

    @http.route('/api/crm/supply/po/<int:po_id>/reopen', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_reopen(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.reopen')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            if po.status != 'cancelled':
                return {'success': False, 'error': 'Invalid status transition'}
            po.write({'status': 'draft'})
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_reopen')

    @http.route('/api/crm/supply/po/<int:po_id>/attachments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_attach_list(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.view')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            atts = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'lugal.crm.supply.po'),
                ('res_id', '=', po.id),
            ])
            return {
                'success': True,
                'data': {'po_id': po.id, 'attachments': [_serialize_ir_attachment(a) for a in atts]},
            }
        except Exception as e:
            return crm_error(e, 'supply_po_attach_list')

    @http.route(
        '/api/crm/supply/po/<int:po_id>/attachments/upload',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        save_session=False,
        cors='*',
        max_content_length=104857600,
    )
    def supply_po_attach_upload(self, po_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])
        try:
            if not ensure_jwt_user_id():
                return _json_http({'success': False, 'error': 'Unauthorized'}, 401)
            denied = require_permission('supply_chain.purchase_orders.upload_attachment')
            if denied:
                return _json_http(denied, 403)
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return _json_http({'success': False, 'error': 'PO not found'}, 404)
            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json_http({'success': False, 'error': 'No file'}, 400)
            ir_rows = []
            for f in files:
                data = f.read()
                mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''
                if not _allowed_upload_mime(mime):
                    return _json_http({'success': False, 'error': f'Unsupported type: {mime}'}, 400)
                att = _create_attachment(
                    f.filename or 'file',
                    mime,
                    data,
                    res_model='lugal.crm.supply.po',
                    res_id=po.id,
                )
                ir_rows.append(_serialize_ir_attachment(att))
            return _json_http({
                'success': True,
                'data': {
                    'attachments': [{'name': r['name'], 'url': r['url']} for r in ir_rows],
                    'uploaded_count': len(ir_rows),
                    'total_attachments': len(ir_rows),
                },
            })
        except Exception as e:
            _logger.exception('supply_po_attach_upload')
            return _json_http({'success': False, 'error': str(e)}, 500)

    @http.route(
        '/api/crm/supply/po/<int:po_id>/attachments/<int:attachment_id>/delete',
        type='jsonrpc',
        auth='none',
        csrf=False,
        methods=['POST'],
    )
    def supply_po_attach_delete(self, po_id, attachment_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.delete_attachment')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            att = request.env['ir.attachment'].sudo().browse(attachment_id).exists()
            if not att or att.res_model != 'lugal.crm.supply.po' or att.res_id != po.id:
                return {'success': False, 'error': 'Attachment not found'}
            att.unlink()
            return {'success': True, 'data': {'deleted_id': attachment_id}}
        except Exception as e:
            return crm_error(e, 'supply_po_attach_delete')

    @http.route('/api/crm/supply/po/<int:po_id>/comments/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_list(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.view')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            page = max(1, int(kwargs.get('page') or 1))
            limit = 50
            Msg = request.env['mail.message'].sudo()
            domain = [
                ('model', '=', 'lugal.crm.supply.po'),
                ('res_id', '=', po.id),
                ('message_type', 'in', ('comment', 'notification')),
            ]
            total = Msg.search_count(domain)
            msgs = Msg.search(domain, order='id desc', limit=limit, offset=(page - 1) * limit)
            return {
                'success': True,
                'data': {'total': total, 'items': [_serialize_mail_message(m) for m in msgs]},
            }
        except Exception as e:
            return crm_error(e, 'supply_po_comments_list')

    @http.route('/api/crm/supply/po/<int:po_id>/comments/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_add(self, po_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.add_comment')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            body = (kwargs.get('body') or '').strip()
            if not body:
                return {'success': False, 'error': 'body is required'}
            is_note = bool(kwargs.get('is_note'))
            subtype = 'mail.mt_note' if is_note else 'mail.mt_comment'
            msg = po.with_user(uid).message_post(
                body=body, message_type='comment', subtype_xmlid=subtype
            )
            return {'success': True, 'data': _serialize_mail_message(msg)}
        except Exception as e:
            return crm_error(e, 'supply_po_comments_add')

    @http.route('/api/crm/supply/po/<int:po_id>/comments/<int:message_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_comments_delete(self, po_id, message_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.delete_comment')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            msg = request.env['mail.message'].sudo().browse(message_id).exists()
            if not msg or msg.model != 'lugal.crm.supply.po' or msg.res_id != po.id:
                return {'success': False, 'error': 'Message not found'}
            msg.unlink()
            return {'success': True, 'data': {'id': message_id}}
        except Exception as e:
            return crm_error(e, 'supply_po_comments_delete')

    @http.route('/api/crm/supply/po/<int:po_id>/get', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_get(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.view')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_get')

    @http.route('/api/crm/supply/po/<int:po_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_update(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.edit')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            allowed = {'name', 'division', 'container_id', 'branch_id', 'currency_id', 'is_suggested'}
            vals = {k: kwargs[k] for k in allowed if k in kwargs and kwargs[k] is not None}
            if vals:
                po.write(vals)
            return {'success': True, 'data': _serialize_po(po)}
        except Exception as e:
            return crm_error(e, 'supply_po_update')

    @http.route('/api/crm/supply/po/<int:po_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_po_delete(self, po_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            denied = require_permission('supply_chain.purchase_orders.delete')
            if denied:
                return denied
            po = request.env['lugal.crm.supply.po'].sudo().browse(po_id).exists()
            if not po or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            po.write({'is_deleted': True})
            return {'success': True, 'data': {'id': po.id, 'deleted': True}}
        except Exception as e:
            return crm_error(e, 'supply_po_delete')
