# -*- coding: utf-8 -*-
"""
Extension of res.partner that keeps lugal.crm.customer in sync.

Rules:
  - When a partner is created with customer_rank > 0  → auto-create CRM record.
  - When a partner is written and key fields change    → update linked CRM record.
  - When customer_rank is raised from 0 to > 0        → create CRM record if missing.
  - When a partner is archived (active=False)          → archive linked CRM record.
"""

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

# Fields on res.partner that must be mirrored to lugal.crm.customer
_SYNC_TO_CRM = {
    'name':       'name',
    'email':      'email',
    'phone':      'phone_1',
    'city':       'city',
    'country_id': 'country_id',
}


def _build_crm_vals_from_partner(partner):
    """Build a vals dict for lugal.crm.customer from a res.partner record."""
    return {
        'name':       partner.name or 'Unnamed',
        'partner_id': partner.id,
        'phone_1':    partner.phone or partner.mobile or '',
        'email':      partner.email or '',
        'city':       partner.city or '',
        'country_id': partner.country_id.id if partner.country_id else False,
    }


class ResPartnerCrmSync(models.Model):
    _inherit = 'res.partner'

    # ── Helpers ──────────────────────────────────────────────────────────

    def _crm_customer(self):
        """Return the linked lugal.crm.customer record (or empty recordset)."""
        return self.env['lugal.crm.customer'].sudo().search(
            [('partner_id', 'in', self.ids)], order='id asc'
        )

    def _ensure_crm_customers(self):
        """
        For each partner in self that has customer_rank > 0 and no linked
        CRM customer, create one automatically.
        """
        Customer = self.env['lugal.crm.customer'].sudo()
        existing_partner_ids = Customer.search(
            [('partner_id', 'in', self.ids)]
        ).mapped('partner_id').ids

        for partner in self:
            if partner.customer_rank > 0 and partner.id not in existing_partner_ids:
                try:
                    Customer.with_context(_skip_partner_sync=True).create(
                        _build_crm_vals_from_partner(partner)
                    )
                except Exception:
                    _logger.warning(
                        'Could not auto-create CRM customer for partner %s (%s)',
                        partner.id, partner.name,
                    )

    # ── ORM overrides ────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create CRM customer when a new contact with customer_rank > 0 is saved."""
        records = super().create(vals_list)
        if not self.env.context.get('_skip_crm_sync'):
            records._ensure_crm_customers()
        return records

    def write(self, vals):
        result = super().write(vals)
        if self.env.context.get('_skip_crm_sync'):
            return result

        # ── Sync identity fields → CRM ───────────────────────────────────
        crm_vals = {
            crm_field: vals[partner_field]
            for partner_field, crm_field in _SYNC_TO_CRM.items()
            if partner_field in vals
        }
        if crm_vals:
            Customer = self.env['lugal.crm.customer'].sudo()
            for partner in self:
                crm = Customer.search([('partner_id', '=', partner.id)], limit=1)
                if crm:
                    crm.with_context(_skip_partner_sync=True).write(crm_vals)

        # ── Archive / un-archive ALL CRM records when partner active changes ──
        if 'active' in vals:
            Customer = self.env['lugal.crm.customer'].sudo().with_context(active_test=False)
            partner_ids = self.ids
            crm_records = Customer.search([('partner_id', 'in', partner_ids)])
            if crm_records:
                crm_records.with_context(_skip_partner_sync=True).write({
                    'active':     vals['active'],
                    'is_deleted': not vals['active'],
                })

        # ── Auto-create CRM record when customer_rank becomes > 0 ────────
        if vals.get('customer_rank', 0) > 0:
            self._ensure_crm_customers()

        return result
