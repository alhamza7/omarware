"""Audits (inventory counts) CRUD API for lugal_inventory."""
from odoo import http
from odoo.http import request
from ._helpers import _success, _error, _serialize_audit, _parse_body, require_auth


class InventoryAuditsController(http.Controller):

    @http.route('/api/inventory/v1/audits', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_audits(self, page=1, per_page=50, search='', warehouse_id=None, session_id=None, **kwargs):
        """Return paginated audit lines with optional filters."""
        try:
            page = max(1, int(page))
            per_page = min(int(per_page), 200)
            offset = (page - 1) * per_page

            domain = []
            if warehouse_id:
                domain.append(('warehouse_id', '=', int(warehouse_id)))
            if session_id:
                domain.append(('session_id', '=', int(session_id)))
            if search:
                domain += ['|', ('product_code', 'ilike', search), ('product_name', 'ilike', search)]

            Audit = request.env['lugal.inventory.audit'].sudo()
            total = Audit.search_count(domain)
            audits = Audit.search(domain, limit=per_page, offset=offset, order='id desc')

            return _success({
                'audits': [_serialize_audit(a) for a in audits],
                'total': total,
                'page': page,
                'per_page': per_page,
            })
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/audits', type='http', auth='public', methods=['POST'], csrf=False)
    @require_auth
    def create_audit(self, **kwargs):
        """
        Submit an inventory count entry.
        Body: { "product_id": int, "warehouse_id": int, "quantity": float,
                "uom_id": int (opt), "barcode_used": str (opt),
                "session_id": int (opt), "note": str (opt) }
        """
        try:
            body = _parse_body()
            product_id = body.get('product_id')
            warehouse_id = body.get('warehouse_id')
            quantity = body.get('quantity')

            if not product_id or not warehouse_id or quantity is None:
                return _error('product_id, warehouse_id and quantity are required', status=400)

            # Use the authenticated user from token
            payload = getattr(request, '_inv_token_payload', {})
            user_id = payload.get('user_id') or request.env.uid

            vals = {
                'product_id': int(product_id),
                'warehouse_id': int(warehouse_id),
                'quantity': float(quantity),
                'user_id': user_id,
            }
            if body.get('uom_id'):
                vals['uom_id'] = int(body['uom_id'])
            if body.get('barcode_used'):
                vals['barcode_used'] = body['barcode_used']
            if body.get('session_id'):
                vals['session_id'] = int(body['session_id'])
            if body.get('note'):
                vals['note'] = body['note']

            audit = request.env['lugal.inventory.audit'].sudo().create(vals)
            return _success(_serialize_audit(audit), status=201)
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/audits/<int:audit_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    @require_auth
    def delete_audit(self, audit_id, **kwargs):
        """Delete a single audit line."""
        try:
            audit = request.env['lugal.inventory.audit'].sudo().browse(audit_id)
            if not audit.exists():
                return _error('Audit not found', status=404)
            audit.unlink()
            return _success({'deleted': True})
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/audits/warehouse/<int:warehouse_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    @require_auth
    def delete_warehouse_audits(self, warehouse_id, **kwargs):
        """Delete all audit lines for a specific warehouse (admin action)."""
        try:
            audits = request.env['lugal.inventory.audit'].sudo().search([
                ('warehouse_id', '=', warehouse_id)
            ])
            count = len(audits)
            audits.unlink()
            return _success({'deleted': True, 'count': count})
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/audits/all', type='http', auth='public', methods=['DELETE'], csrf=False)
    @require_auth
    def delete_all_audits(self, **kwargs):
        """Delete ALL audit lines — admin only action."""
        try:
            payload = getattr(request, '_inv_token_payload', {})
            if payload.get('role') != 'admin':
                return _error('Admin role required', status=403)

            audits = request.env['lugal.inventory.audit'].sudo().search([])
            count = len(audits)
            audits.unlink()
            return _success({'deleted': True, 'count': count})
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/sessions', type='http', auth='public', methods=['GET'], csrf=False)
    @require_auth
    def list_sessions(self, warehouse_id=None, **kwargs):
        """Return open sessions, optionally filtered by warehouse."""
        try:
            domain = [('state', '=', 'open')]
            if warehouse_id:
                domain.append(('warehouse_id', '=', int(warehouse_id)))

            sessions = request.env['lugal.inventory.session'].sudo().search(domain, order='id desc')
            data = [
                {
                    'id': s.id,
                    'name': s.name,
                    'warehouse_id': s.warehouse_id.id,
                    'warehouse': s.warehouse_id.name,
                    'state': s.state,
                    'audit_count': s.audit_count,
                    'date': s.create_date.isoformat() if s.create_date else '',
                }
                for s in sessions
            ]
            return _success(data)
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/sessions', type='http', auth='public', methods=['POST'], csrf=False)
    @require_auth
    def create_session(self, **kwargs):
        """
        Open a new inventory session.
        Body: { "warehouse_id": int, "name": str (opt) }
        """
        try:
            body = _parse_body()
            warehouse_id = body.get('warehouse_id')
            if not warehouse_id:
                return _error('warehouse_id is required', status=400)

            vals = {'warehouse_id': int(warehouse_id)}
            if body.get('name'):
                vals['name'] = body['name']

            session = request.env['lugal.inventory.session'].sudo().create(vals)
            return _success({
                'id': session.id,
                'name': session.name,
                'warehouse_id': session.warehouse_id.id,
                'state': session.state,
            }, status=201)
        except Exception as e:
            return _error(str(e), status=500)

    @http.route('/api/inventory/v1/sessions/<int:session_id>/close', type='http', auth='public', methods=['POST'], csrf=False)
    @require_auth
    def close_session(self, session_id, **kwargs):
        """Close an open inventory session."""
        try:
            session = request.env['lugal.inventory.session'].sudo().browse(session_id)
            if not session.exists():
                return _error('Session not found', status=404)
            session.action_close()
            return _success({'id': session.id, 'state': session.state})
        except Exception as e:
            return _error(str(e), status=500)
