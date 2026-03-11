# -*- coding: utf-8 -*-

"""
SapOrderMixin — shared SAP sync logic for sale.order and purchase.order.

Both models need identical:
  - 5 SAP tracking fields  (sap_doc_num, sap_doc_entry, sap_synced,
                             sap_error_message, sap_last_sync_date)
  - _get_active_backend()       — find the one active SAP backend
  - _validate_sap_preconditions() — check partner CardCode + lines exist
  - _write_sap_status()         — one-liner to persist sync outcome
  - action_manual_sync_to_sap() — shared button handler

The mixin is an AbstractModel so Odoo never creates a table for it.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapOrderMixin(models.AbstractModel):
    _name = 'sap.order.mixin'
    _description = 'SAP Order Sync Mixin'

    # ── SAP tracking fields ───────────────────────────────────────────────

    sap_doc_num = fields.Char(
        string='SAP Document Number',
        copy=False,
        help="رقم المستند الذي تم إرجاعه من SAP"
    )
    sap_doc_entry = fields.Integer(
        string='SAP Doc Entry',
        copy=False,
        help="رقم DocEntry الداخلي في SAP"
    )
    sap_synced = fields.Boolean(
        string='Synced to SAP',
        default=False,
        copy=False,
        help="تمت المزامنة مع SAP بنجاح"
    )
    sap_error_message = fields.Text(
        string='SAP Error Message',
        copy=False,
        help="آخر رسالة خطأ من SAP"
    )
    sap_last_sync_date = fields.Datetime(
        string='Last SAP Sync',
        copy=False,
        help="آخر وقت للمزامنة مع SAP"
    )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_active_backend(self):
        """Return the first active SAP backend, or None."""
        return self.env['sap.backend'].search([('active', '=', True)], limit=1) or None

    def _validate_sap_preconditions(self, record, partner_field='partner_id', lines_field='order_line'):
        """
        Check that the record has a partner with SAP CardCode and at least one order line.

        Returns a human-readable Arabic error string on failure, or None on success.
        """
        partner = getattr(record, partner_field, None)
        lines   = getattr(record, lines_field, None)

        missing = []
        if not partner:
            missing.append("لا يوجد شريك (عميل/مورد)")
        elif not partner.ref:
            missing.append(
                f"الشريك ({partner.name}) ليس لديه CardCode في SAP (حقل ref فارغ)"
            )
        if not lines:
            missing.append("لا توجد سطور في الطلب")

        return " | ".join(missing) if missing else None

    def _write_sap_status(self, record, *, synced, doc_num=None, doc_entry=None, error=None):
        """
        Persist SAP sync outcome on `record` using sudo to bypass access checks.

        Args:
            synced    — True on success, False on failure
            doc_num   — SAP DocNum string (only on success)
            doc_entry — SAP DocEntry integer (only on success)
            error     — error message string (only on failure)
        """
        vals = {
            'sap_synced': synced,
            'sap_error_message': False if synced else (error or 'خطأ غير معروف'),
            'sap_last_sync_date': fields.Datetime.now(),
        }
        if synced:
            if doc_num is not None:
                vals['sap_doc_num'] = str(doc_num)
            if doc_entry is not None:
                vals['sap_doc_entry'] = int(doc_entry)

        record.sudo().write(vals)

    # ── Shared button action ──────────────────────────────────────────────

    def action_manual_sync_to_sap(self):
        """
        Button handler: force re-sync this document to SAP.
        Subclasses must implement _send_to_sap().
        """
        self.ensure_one()
        error = self._validate_sap_preconditions(self)
        if error:
            raise UserError(f'تعذّر الإرسال إلى SAP:\n{error}')

        try:
            self._send_to_sap()
        except Exception as e:
            raise UserError(f'فشل الإرسال إلى SAP:\n{e}') from e

        if self.sap_synced:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تم الإرسال بنجاح',
                    'message': f'تم إرسال {self.name} إلى SAP. رقم SAP: {self.sap_doc_num or ""}',
                    'type': 'success',
                    'sticky': False,
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'فشل الإرسال إلى SAP',
                'message': self.sap_error_message or 'خطأ غير معروف',
                'type': 'danger',
                'sticky': True,
            },
        }
