# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit

_logger = logging.getLogger(__name__)


def _container_to_dict(c):
    return {
        'id': c.id,
        'name': c.name,
        'container_number': c.container_number or '',
        'bl_number': c.bl_number or '',
        'clearance_company': c.clearance_company or '',
        'origin_location': c.origin_location or '',
        'departure_date': c.departure_date.isoformat() if c.departure_date else None,
        'eta': c.eta.isoformat() if c.eta else None,
        'arrived_at': c.arrived_at.isoformat() if c.arrived_at else None,
        'status': c.status or '',
        'division': c.division or '',
        'tracking_url': c.tracking_url or '',
        'assigned_user_id': c.assigned_user_id.id if c.assigned_user_id else None,
        'assigned_user_name': c.assigned_user_id.name if c.assigned_user_id else '',
        'po_uploaded_by_id': c.po_uploaded_by_id.id if c.po_uploaded_by_id else None,
        'po_uploaded_by_name': c.po_uploaded_by_id.name if c.po_uploaded_by_id else '',
        # Clearance delivery flag (highlighted in UI)
        'clearance_info_delivered': c.clearance_info_delivered,
        'clearance_info_delivered_at': c.clearance_info_delivered_at.isoformat() if c.clearance_info_delivered_at else None,
        'clearance_info_delivered_by': c.clearance_info_delivered_by_id.name if c.clearance_info_delivered_by_id else '',
        'attachment_count': len(c.attachment_ids),
        'notes': c.notes or '',
    }


def _po_to_dict(po, include_lines=False):
    """Serialize a PO; optionally embed line items."""
    data = {
        'id': po.id,
        'name': po.name,
        'vendor_id': po.vendor_id.id if po.vendor_id else None,
        'vendor_name': po.vendor_id.name if po.vendor_id else '',
        'division': po.division or '',
        'currency_id': po.currency_id.id if po.currency_id else None,
        'currency_name': po.currency_id.name if po.currency_id else '',
        'container_id': po.container_id.id if po.container_id else None,
        'container_name': po.container_id.name if po.container_id else '',
        'branch_id': po.branch_id.id if po.branch_id else None,
        'branch_name': po.branch_id.name if po.branch_id else '',
        'status': po.status or '',
        'is_suggested': po.is_suggested,
        'line_count': len(po.line_ids),
        'total_amount': po.total_amount,
        'updated_at': po.write_date.isoformat() if po.write_date else None,
    }
    if include_lines:
        data['lines'] = [_line_to_dict(ln) for ln in po.line_ids]
    return data


def _line_to_dict(ln):
    """Serialize a PO line."""
    return {
        'id': ln.id,
        'sequence': ln.sequence,
        'product_name': ln.product_name or '',
        'item_code': ln.item_code or '',
        'uom': ln.uom or '',
        'quantity': ln.quantity,
        'unit_price': ln.unit_price,
        'total_price': ln.total_price,
        'currency_id': ln.currency_id.id if ln.currency_id else None,
        'currency_name': ln.currency_id.name if ln.currency_id else '',
        'last_purchase_price': ln.last_purchase_price,
        'last_purchase_date': ln.last_purchase_date.isoformat() if ln.last_purchase_date else None,
        'min_qty': ln.min_qty,
        'max_qty': ln.max_qty,
    }


def _vendor_to_dict(v):
    """Serialize lugal.supply.vendor to dict."""
    return {
        'id': v.id,
        'name': v.name,
        'name_ar': v.name_ar or '',
        'division': v.division or '',
        'contact_name': v.contact_name or '',
        'phone': v.phone or '',
        'email': v.email or '',
        'website': v.website or '',
        'whatsapp': v.whatsapp or '',
        'wechat': v.wechat or '',
        'telegram': v.telegram or '',
        'country_id': v.country_id.id if v.country_id else None,
        'country_name': v.country_id.name if v.country_id else '',
        'city': v.city or '',
        'payment_terms': v.payment_terms or '',
        'currency_id': v.currency_id.id if v.currency_id else None,
        'currency_name': v.currency_id.name if v.currency_id else '',
        'lead_time_days': v.lead_time_days,
        'min_order_value': v.min_order_value,
        'partner_id': v.partner_id.id if v.partner_id else None,
        'notes': v.notes or '',
    }


class SupplyController(http.Controller):

    @http.route('/api/crm/supply/containers/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_list(self, page=1, per_page=50, status=None, division=None, **kwargs):
        """List supply containers."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if status:
                domain.append(('status', '=', status))
            if division:
                domain.append(('division', '=', division))
            Container = request.env['lugal.supply.container']
            total = Container.search_count(domain)
            offset = (page - 1) * per_page
            containers = Container.search(domain, limit=per_page, offset=offset, order='departure_date desc')
            return {
                'success': True,
                'data': {'items': [_container_to_dict(c) for c in containers], 'total': total, 'page': page, 'per_page': per_page},
            }
        except Exception as e:
            _logger.exception('container_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/containers/<int:container_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_get(self, container_id, **kwargs):
        """Get single container."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            c = request.env['lugal.supply.container'].browse(container_id)
            if not c.exists() or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            return {'success': True, 'data': _container_to_dict(c)}
        except Exception as e:
            _logger.exception('container_get error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/containers/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_create(self, name, container_number=None, bl_number=None, status='waiting', division=None, **kwargs):
        """Create a container."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {'name': name, 'container_number': container_number, 'bl_number': bl_number, 'status': status, 'division': division}
            c = request.env['lugal.supply.container'].create(vals)
            crm_audit('container_created', record_model='lugal.supply.container', record_id=c.id,
                      details={'name': name, 'container_number': container_number})
            return {'success': True, 'data': _container_to_dict(c)}
        except Exception as e:
            _logger.exception('container_create error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_list(self, page=1, per_page=50, status=None, vendor_id=None, **kwargs):
        """List purchase orders."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if status:
                domain.append(('status', '=', status))
            if vendor_id:
                domain.append(('vendor_id', '=', vendor_id))
            PO = request.env['lugal.crm.supply.po']
            total = PO.search_count(domain)
            offset = (page - 1) * per_page
            pos = PO.search(domain, limit=per_page, offset=offset, order='write_date desc')
            return {'success': True, 'data': {'items': [_po_to_dict(p) for p in pos], 'total': total, 'page': page, 'per_page': per_page}}
        except Exception as e:
            _logger.exception('po_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_get(self, po_id, **kwargs):
        """Get a single PO with its lines."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            po = request.env['lugal.crm.supply.po'].browse(po_id)
            if not po.exists() or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            return {'success': True, 'data': _po_to_dict(po, include_lines=True)}
        except Exception as e:
            _logger.exception('po_get error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_create(self, name, vendor_id, division=None, container_id=None, branch_id=None, currency_id=None, **kwargs):
        """Create a purchase order."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {
                'name': name,
                'vendor_id': vendor_id,
                'division': division,
                'container_id': container_id,
                'branch_id': branch_id,
                'currency_id': currency_id,
            }
            po = request.env['lugal.crm.supply.po'].create({k: v for k, v in vals.items() if v is not None})
            crm_audit('po_created', record_model='lugal.crm.supply.po', record_id=po.id,
                      details={'name': name, 'vendor_id': vendor_id, 'division': division})
            return {'success': True, 'data': _po_to_dict(po, include_lines=True)}
        except Exception as e:
            _logger.exception('po_create error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_update(self, po_id, **kwargs):
        """Update PO header fields."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            po = request.env['lugal.crm.supply.po'].browse(po_id)
            if not po.exists() or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            allowed = {'name', 'vendor_id', 'division', 'currency_id', 'container_id', 'branch_id', 'status', 'is_suggested'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                po.write(vals)
            return {'success': True, 'data': _po_to_dict(po, include_lines=True)}
        except Exception as e:
            _logger.exception('po_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_delete(self, po_id, **kwargs):
        """Soft-delete a PO."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            po = request.env['lugal.crm.supply.po'].browse(po_id)
            if not po.exists():
                return {'success': False, 'error': 'PO not found'}
            po.write({'is_deleted': True, 'active': False})
            crm_audit('po_deleted', record_model='lugal.crm.supply.po', record_id=po_id,
                      details={'name': po.name})
            return {'success': True}
        except Exception as e:
            _logger.exception('po_delete error')
            return {'success': False, 'error': str(e)}

    # ─── PO Lines CRUD ────────────────────────────────────────────────────

    @http.route('/api/crm/supply/po/<int:po_id>/lines', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_lines_list(self, po_id, **kwargs):
        """List all lines for a PO."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            po = request.env['lugal.crm.supply.po'].browse(po_id)
            if not po.exists() or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            return {'success': True, 'data': {'items': [_line_to_dict(ln) for ln in po.line_ids]}}
        except Exception as e:
            _logger.exception('po_lines_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>/lines/add', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_line_add(self, po_id, product_name=None, item_code=None, uom=None, quantity=1.0, unit_price=0.0, currency_id=None, min_qty=0.0, max_qty=0.0, **kwargs):
        """Add a line to an existing PO."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            po = request.env['lugal.crm.supply.po'].browse(po_id)
            if not po.exists() or po.is_deleted:
                return {'success': False, 'error': 'PO not found'}
            vals = {
                'po_id': po_id,
                'product_name': product_name,
                'item_code': item_code,
                'uom': uom,
                'quantity': quantity,
                'unit_price': unit_price,
                'min_qty': min_qty,
                'max_qty': max_qty,
            }
            if currency_id:
                vals['currency_id'] = currency_id
            line = request.env['lugal.crm.supply.po.line'].create({k: v for k, v in vals.items() if v is not None})
            return {'success': True, 'data': _line_to_dict(line)}
        except Exception as e:
            _logger.exception('po_line_add error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_line_update(self, po_id, line_id, **kwargs):
        """Update a PO line."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            line = request.env['lugal.crm.supply.po.line'].browse(line_id)
            if not line.exists() or line.po_id.id != po_id:
                return {'success': False, 'error': 'Line not found'}
            allowed = {'product_name', 'item_code', 'uom', 'quantity', 'unit_price', 'currency_id',
                       'last_purchase_price', 'last_purchase_date', 'min_qty', 'max_qty', 'sequence'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals:
                line.write(vals)
            return {'success': True, 'data': _line_to_dict(line)}
        except Exception as e:
            _logger.exception('po_line_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/<int:po_id>/lines/<int:line_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def po_line_delete(self, po_id, line_id, **kwargs):
        """Delete a PO line (hard delete — lines are expendable)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            line = request.env['lugal.crm.supply.po.line'].browse(line_id)
            if not line.exists() or line.po_id.id != po_id:
                return {'success': False, 'error': 'Line not found'}
            line.unlink()
            return {'success': True}
        except Exception as e:
            _logger.exception('po_line_delete error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/po/suggested', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def suggested_po(self, **kwargs):
        """List suggested POs (placeholder)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('is_suggested', '=', True)]
            pos = request.env['lugal.crm.supply.po'].search(domain, limit=50)
            return {'success': True, 'data': {'items': [_po_to_dict(p) for p in pos]}}
        except Exception as e:
            _logger.exception('suggested_po error')
            return {'success': False, 'error': str(e)}

    # ─── Vendor CRUD ─────────────────────────────────────────────────────

    @http.route('/api/crm/supply/vendors/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def vendor_list(self, page=1, per_page=50, search=None, division=None, **kwargs):
        """List supply vendors from lugal.supply.vendor. موردين."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if search:
                domain += ['|', '|', ('name', 'ilike', search), ('contact_name', 'ilike', search), ('phone', 'ilike', search)]
            if division:
                domain.append(('division', '=', division))
            Vendor = request.env['lugal.supply.vendor']
            total = Vendor.search_count(domain)
            vendors = Vendor.search(domain, limit=per_page, offset=(page - 1) * per_page, order='name asc')
            return {'success': True, 'data': {'items': [_vendor_to_dict(v) for v in vendors], 'total': total, 'page': page, 'per_page': per_page}}
        except Exception as e:
            _logger.exception('vendor_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/vendors/<int:vendor_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def vendor_get(self, vendor_id, **kwargs):
        """Get a single vendor card."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            v = request.env['lugal.supply.vendor'].browse(vendor_id)
            if not v.exists() or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            return {'success': True, 'data': _vendor_to_dict(v)}
        except Exception as e:
            _logger.exception('vendor_get error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/vendors/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def vendor_create(self, name, division=None, contact_name=None, phone=None, email=None,
                      whatsapp=None, wechat=None, telegram=None, country_id=None,
                      payment_terms=None, currency_id=None, lead_time_days=None, notes=None, **kwargs):
        """Create a new vendor."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {
                'name': name,
                'division': division,
                'contact_name': contact_name,
                'phone': phone,
                'email': email,
                'whatsapp': whatsapp,
                'wechat': wechat,
                'telegram': telegram,
                'country_id': country_id,
                'payment_terms': payment_terms,
                'currency_id': currency_id,
                'lead_time_days': lead_time_days or 0,
                'notes': notes,
            }
            v = request.env['lugal.supply.vendor'].create({k: val for k, val in vals.items() if val is not None})
            crm_audit('vendor_created', record_model='lugal.supply.vendor', record_id=v.id,
                      details={'name': v.name, 'division': v.division})
            return {'success': True, 'data': _vendor_to_dict(v)}
        except Exception as e:
            _logger.exception('vendor_create error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def vendor_update(self, vendor_id, **kwargs):
        """Update a vendor card."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            v = request.env['lugal.supply.vendor'].browse(vendor_id)
            if not v.exists() or v.is_deleted:
                return {'success': False, 'error': 'Vendor not found'}
            allowed = {
                'name', 'name_ar', 'division', 'contact_name', 'phone', 'email', 'website',
                'whatsapp', 'wechat', 'telegram', 'country_id', 'city', 'address',
                'payment_terms', 'currency_id', 'lead_time_days', 'min_order_value', 'notes',
                'partner_id',
            }
            vals = {k: val for k, val in kwargs.items() if k in allowed and val is not None}
            if vals:
                v.write(vals)
            return {'success': True, 'data': _vendor_to_dict(v)}
        except Exception as e:
            _logger.exception('vendor_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/vendors/<int:vendor_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def vendor_delete(self, vendor_id, **kwargs):
        """Soft-delete a vendor."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            v = request.env['lugal.supply.vendor'].browse(vendor_id)
            if not v.exists():
                return {'success': False, 'error': 'Vendor not found'}
            v.write({'is_deleted': True, 'active': False})
            crm_audit('vendor_deleted', record_model='lugal.supply.vendor', record_id=vendor_id,
                      details={'name': v.name})
            return {'success': True}
        except Exception as e:
            _logger.exception('vendor_delete error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/containers/<int:container_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_update(self, container_id, **kwargs):
        """Update container (model in lugal_supply)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            c = request.env['lugal.supply.container'].browse(container_id)
            if not c.exists() or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            allow = set(request.env['lugal.supply.container']._fields) - {'id', 'create_date', 'create_uid', 'write_date', 'write_uid'}
            vals = {k: v for k, v in kwargs.items() if k in allow and v is not None}
            if vals:
                c.write(vals)
            return {'success': True, 'data': _container_to_dict(c)}
        except Exception as e:
            _logger.exception('container_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/containers/<int:container_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_delete(self, container_id, **kwargs):
        """Soft-delete a shipping container."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            c = request.env['lugal.supply.container'].browse(container_id)
            if not c.exists():
                return {'success': False, 'error': 'Container not found'}
            c.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as e:
            _logger.exception('container_delete error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/supply/containers/<int:container_id>/clearance_delivered', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def container_mark_clearance_delivered(self, container_id, **kwargs):
        """Mark clearance info as delivered to the clearance company (highlighted flag in UI)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            c = request.env['lugal.supply.container'].browse(container_id)
            if not c.exists() or c.is_deleted:
                return {'success': False, 'error': 'Container not found'}
            c.action_mark_clearance_delivered()
            return {'success': True, 'data': _container_to_dict(c)}
        except Exception as e:
            _logger.exception('container_mark_clearance_delivered error')
            return {'success': False, 'error': str(e)}
