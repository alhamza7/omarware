# -*- coding: utf-8 -*-
"""Stock check on confirm, budget hook, approval line bootstrap, lead-time metrics, activities."""

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .supply_workflow_config import (
    supply_budget_enabled,
    supply_stock_validate_enabled,
    supply_activity_notify_enabled,
)


class CrmSupplyPoChainEnhance(models.Model):
    _inherit = 'lugal.crm.supply.po'

    budget_allocation_id = fields.Many2one(
        'lugal.supply.budget.allocation',
        string='Budget allocation',
        ondelete='set null',
        tracking=True,
        help='Optional budget envelope; enforced only when budget control is enabled in settings.',
    )
    supply_workflow_approval_line_ids = fields.One2many(
        'lugal.supply.workflow.approval.line',
        'po_id',
        string='PO multi-level approvals',
        copy=False,
    )
    supplier_commitment_date = fields.Date(
        string='Supplier commitment date',
        tracking=True,
        help='Promised readiness / ex-works date from supplier.',
    )
    planned_receipt_date = fields.Date(
        string='Planned receipt date',
        tracking=True,
        help='Internal ETA for goods arrival.',
    )
    order_acknowledged_at = fields.Datetime(
        string='Order acknowledged at',
        readonly=True,
        copy=False,
        help='Set when the PO is first confirmed.',
    )
    lead_time_delay_days = fields.Integer(
        string='Receipt delay (days)',
        compute='_compute_lead_time_delay_days',
        help='Positive when today is past planned receipt and order is still active.',
    )

    @api.depends('planned_receipt_date', 'status')
    def _compute_lead_time_delay_days(self):
        today = fields.Date.context_today(self)
        for po in self:
            delay = 0
            if po.planned_receipt_date and po.status == 'confirmed':
                if today > po.planned_receipt_date:
                    delay = (today - po.planned_receipt_date).days
            po.lead_time_delay_days = delay

    def write(self, vals):
        if vals.get('status') == 'confirmed':
            self._supply_pre_confirm_validations()
        res = super().write(vals)
        if vals.get('status') == 'confirmed':
            now = fields.Datetime.now()
            for po in self:
                if not po.order_acknowledged_at:
                    po.with_context(supply_chain_internal=True).write({'order_acknowledged_at': now})
            self._supply_activity_po_confirmed()
        return res

    def _supply_pre_confirm_validations(self):
        if supply_stock_validate_enabled(self.env):
            self._supply_validate_stock_before_confirm()
        if supply_budget_enabled(self.env):
            self._supply_validate_budget_before_confirm()

    def _supply_validate_stock_before_confirm(self):
        Product = self.env['product.product'].sudo()
        for po in self:
            for line in po.line_ids:
                product = line.product_id
                if not product and line.item_code:
                    code = (line.item_code or '').strip()
                    if code:
                        product = Product.search([('default_code', '=', code)], limit=1)
                if not product:
                    continue
                need = line.quantity or line.quantity_pcs or 0.0
                available = product.qty_available
                if need > available + 1e-6:
                    raise UserError(
                        _('Insufficient stock for %(prod)s (code %(code)s): required %(need)s, available %(avail)s.')
                        % {
                            'prod': product.display_name,
                            'code': line.item_code or '',
                            'need': need,
                            'avail': available,
                        }
                    )

    def _supply_validate_budget_before_confirm(self):
        for po in self:
            alloc = po.budget_allocation_id
            if not alloc or not alloc.amount_limit:
                continue
            total = po.total_amount or 0.0
            if total > alloc.amount_limit + 1e-6:
                raise UserError(
                    _('PO total (%(total)s) exceeds budget allocation limit (%(lim)s) for %(name)s.')
                    % {
                        'total': total,
                        'lim': alloc.amount_limit,
                        'name': alloc.name,
                    }
                )

    def _supply_activity_po_confirmed(self):
        if not supply_activity_notify_enabled(self.env):
            return
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo:
            return
        for po in self:
            user = po.create_uid
            if not user:
                continue
            po.activity_schedule(
                activity_type_id=todo.id,
                user_id=user.id,
                summary=_('Supply PO confirmed: %s') % (po.name or ''),
                note=_('Total: %s') % (po.total_amount or 0.0),
            )
