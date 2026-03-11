# -*- coding: utf-8 -*-

"""
SAP integration for purchase.order.

Inherits sap.order.mixin for shared fields and helpers, then adds
purchase-specific create/write hooks and the SAP payload builder.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Fields whose change on an existing PO should trigger a re-sync to SAP
_WATCHED_FIELDS = frozenset({
    'partner_id', 'order_line', 'date_order',
    'date_planned', 'price_unit', 'product_qty',
})


class PurchaseOrder(models.Model):
    _name    = 'purchase.order'
    _inherit = ['purchase.order', 'sap.order.mixin']

    # ── Create / Write hooks ─────────────────────────────────────────────

    @api.model
    def create(self, vals):
        """Send purchase order to SAP after creation when conditions are met."""
        order = super().create(vals)

        error = self._validate_sap_preconditions(order)
        if error:
            _logger.warning("[SAP PO] Conditions not met for %s: %s", order.name, error)
            self._write_sap_status(order, synced=False, error=error)
            return order

        if not order.sap_synced:
            try:
                order._send_to_sap()
            except Exception as e:
                _logger.warning("[SAP PO] Could not send %s to SAP on create: %s", order.name, e)

        return order

    def write(self, vals):
        """Re-sync to SAP when state is confirmed or relevant fields change."""
        # Snapshot states before the write so we can detect transitions
        old_states = {po.id: po.state for po in self}
        result = super().write(vals)

        for order in self:
            if self._validate_sap_preconditions(order):
                continue   # skip — missing partner CardCode or lines

            state_just_confirmed = (
                'state' in vals
                and vals['state'] in ('purchase', 'done')
                and old_states.get(order.id) in ('draft', 'sent')
                and not order.sap_synced
            )
            fields_changed = bool(_WATCHED_FIELDS & set(vals))

            if state_just_confirmed or fields_changed:
                try:
                    order._send_to_sap()
                except Exception as e:
                    _logger.warning(
                        "[SAP PO] Could not update %s in SAP on write: %s", order.name, e
                    )

        return result

    # ── Core sync ────────────────────────────────────────────────────────

    def _send_to_sap(self):
        """Send (or update) this purchase order in SAP B1."""
        for po in self:
            _logger.info("[SAP PO] Starting sync for %s", po.name)

            backend = self._get_active_backend()
            if not backend:
                self._write_sap_status(po, synced=False, error='لا يوجد SAP backend نشط')
                return

            error = self._validate_sap_preconditions(po)
            if error:
                self._write_sap_status(po, synced=False, error=error)
                return

            if not po.order_line:
                self._write_sap_status(po, synced=False, error='طلب الشراء لا يحتوي على سطور')
                return

            try:
                payload    = self._prepare_purchase_data_for_sap(po, backend)
                connection = backend.get_connection()
                headers    = connection._get_headers()

                if po.sap_doc_entry and po.sap_doc_entry > 0:
                    self._sap_update(po, connection, headers, payload)
                else:
                    self._sap_create(po, connection, headers, payload)

            except Exception as e:
                _logger.error("[SAP PO] Exception for %s: %s", po.name, e, exc_info=True)
                self._write_sap_status(po, synced=False, error=str(e))

    def _sap_create(self, po, connection, headers, payload):
        """POST a new PurchaseOrder to SAP."""
        url      = f"{connection.base_url}/PurchaseOrders"
        response = connection.session.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            data = response.json() if response.content else {}
            self._write_sap_status(
                po, synced=True,
                doc_num=data.get('DocNum'),
                doc_entry=data.get('DocEntry'),
            )
            _logger.info("[SAP PO] ✅ Created %s → DocNum=%s DocEntry=%s",
                         po.name, data.get('DocNum'), data.get('DocEntry'))
        else:
            error = f"POST /PurchaseOrders → {response.status_code}: {response.text[:300]}"
            _logger.error("[SAP PO] ❌ %s — %s", po.name, error)
            self._write_sap_status(po, synced=False, error=error)

    def _sap_update(self, po, connection, headers, payload):
        """PATCH an existing PurchaseOrder in SAP."""
        url  = f"{connection.base_url}/PurchaseOrders({po.sap_doc_entry})"
        # CardCode must NOT be sent on update — SAP rejects it
        data = {k: v for k, v in payload.items() if k != 'CardCode'}
        response = connection.session.patch(url, json=data, headers=headers, timeout=30)

        if response.status_code in (200, 204):
            self._write_sap_status(po, synced=True)
            _logger.info("[SAP PO] ✅ Updated %s (DocEntry=%d)", po.name, po.sap_doc_entry)
        else:
            error = f"PATCH /PurchaseOrders({po.sap_doc_entry}) → {response.status_code}: {response.text[:300]}"
            _logger.error("[SAP PO] ❌ %s — %s", po.name, error)
            self._write_sap_status(po, synced=False, error=error)

    # ── Payload builder ──────────────────────────────────────────────────

    def _prepare_purchase_data_for_sap(self, po, backend=None):
        """
        Build the SAP Service Layer payload dict for a PurchaseOrder.

        UoM resolution order:
          1. sap.uom.sync matched by line's product_uom + backend
          2. sap.uom.sync matched by product's sales_uom_id (from sap.product.extended)
          3. No UoMEntry sent (SAP uses default)

        WarehouseCode resolution order:
          1. sap.product.warehouse.info for line's warehouse
          2. warehouse.code from picking_type_id.warehouse_id
        """
        backend_id = backend.id if backend else None
        document_lines = []

        for line in po.order_line:
            if not line.product_id:
                _logger.warning("[SAP PO] Skipping line %d — no product", line.id)
                continue
            if not line.product_qty or line.product_qty <= 0:
                _logger.warning("[SAP PO] Skipping line %d — qty=%s", line.id, line.product_qty)
                continue

            # ItemCode: default_code → barcode → empty (SAP will reject, but we log)
            item_code = (
                line.product_id.default_code
                or line.product_id.barcode
                or ''
            )
            if not item_code:
                _logger.warning("[SAP PO] Product %s has no ItemCode", line.product_id.name)

            line_data = {
                'ItemCode':  item_code,
                'Quantity':  line.product_qty,
                'UnitPrice': line.price_unit,
            }

            # UoMEntry
            uom_entry = self._resolve_uom_entry(line, backend_id)
            if uom_entry:
                line_data['UoMEntry'] = uom_entry

            # WarehouseCode
            warehouse_code = self._resolve_warehouse_code(line, po, backend_id)
            if warehouse_code:
                line_data['WarehouseCode'] = warehouse_code

            document_lines.append(line_data)
            _logger.info(
                "[SAP PO] Line: ItemCode=%s Qty=%s Price=%s UoMEntry=%s WH=%s",
                item_code, line.product_qty, line.price_unit,
                line_data.get('UoMEntry', '—'), line_data.get('WarehouseCode', '—'),
            )

        if not document_lines:
            raise UserError("لا يمكن إرسال طلب الشراء بدون سطور صالحة")

        payload = {
            'CardCode':      po.partner_id.ref,
            'DocumentLines': document_lines,
        }
        if po.notes:
            payload['Comments'] = po.notes.strip()
        if po.date_planned:
            payload['DocDueDate'] = po.date_planned.strftime('%Y-%m-%d')

        return payload

    # ── Resolution helpers ────────────────────────────────────────────────

    def _resolve_uom_entry(self, line, backend_id):
        """
        Resolve SAP UoMEntry for a purchase order line.

        Tries:
          1. sap.uom.sync by line product_uom + backend
          2. sap.uom.sync by product's sales_uom_id from sap.product.extended
        Returns the entry integer or None.
        """
        # 1. Explicit UoM on the line
        if line.product_uom:
            domain = [('odoo_uom_id', '=', line.product_uom.id)]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            sync = self.env['sap.uom.sync'].search(domain, limit=1)
            if sync and sync.sap_uom_entry and sync.sap_uom_entry > 0:
                return sync.sap_uom_entry

        # 2. Fallback: product's sales_uom_id from sap.product.extended
        if line.product_id and backend_id:
            ext_domain = [
                ('product_id', '=', line.product_id.id),
                ('backend_id', '=', backend_id),
            ]
            ext = self.env['sap.product.extended'].search(ext_domain, limit=1)
            if ext and ext.sales_uom_id:
                domain = [
                    ('odoo_uom_id', '=', ext.sales_uom_id.id),
                    ('backend_id', '=', backend_id),
                ]
                sync = self.env['sap.uom.sync'].search(domain, limit=1)
                if sync and sync.sap_uom_entry and sync.sap_uom_entry > 0:
                    _logger.info(
                        "[SAP PO] UoMEntry resolved via sales_uom_id (%s) for %s",
                        ext.sales_uom_id.name, line.product_id.default_code,
                    )
                    return sync.sap_uom_entry

        if line.product_uom:
            _logger.warning("[SAP PO] No UoMEntry found for UoM '%s'", line.product_uom.name)
        return None

    def _resolve_warehouse_code(self, line, po, backend_id):
        """
        Resolve SAP WarehouseCode for a purchase order line.

        Tries:
          1. sap.product.warehouse.info for line.product_warehouse_id
          2. warehouse.code from po.picking_type_id.warehouse_id
        """
        def _lookup(warehouse):
            if not warehouse:
                return None
            if backend_id:
                info = self.env['sap.product.warehouse.info'].search(
                    [('warehouse_id', '=', warehouse.id), ('backend_id', '=', backend_id)],
                    limit=1,
                )
                if info and info.sap_warehouse_code:
                    return info.sap_warehouse_code
            return warehouse.code or None

        wh = getattr(line, 'product_warehouse_id', None)
        code = _lookup(wh)
        if code:
            return code

        if po.picking_type_id and po.picking_type_id.warehouse_id:
            return _lookup(po.picking_type_id.warehouse_id)

        return None
