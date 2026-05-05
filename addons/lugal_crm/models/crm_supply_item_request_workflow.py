# -*- coding: utf-8 -*-
"""Lead-time milestones, approval lines bootstrap, activities on item request."""

from odoo import fields, models, _

from .supply_workflow_config import (
    supply_workflow_level_count,
    supply_activity_notify_enabled,
)


class LugalSupplyItemRequestWorkflow(models.Model):
    _inherit = 'lugal.supply.item.request'

    workflow_milestone_start = fields.Datetime(
        string='Workflow started at',
        readonly=True,
        copy=False,
        help='Set when the request first moves to In Progress.',
    )
    workflow_milestone_completed = fields.Datetime(
        string='Workflow completed at',
        readonly=True,
        copy=False,
        help='Set when the request is marked completed.',
    )
    supply_workflow_approval_line_ids = fields.One2many(
        'lugal.supply.workflow.approval.line',
        'item_request_id',
        string='Multi-level approvals',
        copy=False,
    )

    def action_start_progress(self):
        super().action_start_progress()
        now = fields.Datetime.now()
        Line = self.env['lugal.supply.workflow.approval.line'].sudo()
        for rec in self:
            if not rec.workflow_milestone_start:
                rec.with_context(supply_chain_internal=True).write({'workflow_milestone_start': now})
            rec._supply_bootstrap_item_request_approval_lines()
            rec._supply_activity_item_request_progress()

    def action_mark_completed(self):
        super().action_mark_completed()
        now = fields.Datetime.now()
        for rec in self:
            rec.with_context(supply_chain_internal=True).write({'workflow_milestone_completed': now})
            rec._supply_activity_item_request_completed()

    def _supply_bootstrap_item_request_approval_lines(self):
        n = supply_workflow_level_count(self.env)
        if n <= 0:
            return
        Line = self.env['lugal.supply.workflow.approval.line'].sudo()
        for rec in self:
            if Line.search([('item_request_id', '=', rec.id)], limit=1):
                continue
            for level in range(1, n + 1):
                Line.create({
                    'item_request_id': rec.id,
                    'level': level,
                    'state': 'pending',
                })

    def _supply_activity_item_request_progress(self):
        if not supply_activity_notify_enabled(self.env):
            return
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo:
            return
        for rec in self:
            user = rec.requested_by_id
            if not user:
                continue
            rec.activity_schedule(
                activity_type_id=todo.id,
                user_id=user.id,
                summary=_('Item request In Progress: %s') % (rec.name or ''),
                note=rec.item_name or '',
            )

    def _supply_activity_item_request_completed(self):
        if not supply_activity_notify_enabled(self.env):
            return
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo:
            return
        for rec in self:
            user = rec.requested_by_id
            if not user:
                continue
            rec.activity_schedule(
                activity_type_id=todo.id,
                user_id=user.id,
                summary=_('Item request completed: %s') % (rec.name or ''),
                note=rec.item_name or '',
            )
