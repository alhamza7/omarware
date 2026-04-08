# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmEmployeeKpi(models.Model):
    """Employee KPI snapshot — FRT, TTR, calls, messages, conversions (stored for reporting)."""
    _name = 'lugal.crm.employee.kpi'
    _description = 'CRM Employee KPI'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_end desc, employee_id asc, id desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'res.users',
        string='Employee / الموظف',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    period_start = fields.Datetime(string='Period Start / بداية الفترة', required=True, index=True, tracking=True)
    period_end = fields.Datetime(string='Period End / نهاية الفترة', required=True, index=True, tracking=True)

    total_calls = fields.Integer(string='Total Calls / إجمالي المكالمات', default=0, tracking=True)
    answered_calls = fields.Integer(string='Answered Calls / المكالمات المجابة', default=0, tracking=True)
    total_messages = fields.Integer(string='Total Messages / إجمالي الرسائل', default=0, tracking=True)
    answered_messages = fields.Integer(string='Answered Messages / الرسائل المجابة', default=0, tracking=True)

    avg_frt_seconds = fields.Float(string='Avg FRT (sec) / متوسط وقت أول رد', digits=(10, 2), tracking=True)
    avg_ttr_seconds = fields.Float(string='Avg TTR (sec) / متوسط وقت الحل', digits=(10, 2), tracking=True)
    late_messages = fields.Integer(string='Late Messages / رسائل متأخرة', default=0, tracking=True)
    late_calls = fields.Integer(string='Late Calls / مكالمات متأخرة', default=0, tracking=True)
    conversions_to_order = fields.Integer(string='Conversions to Order / تحويلات لطلبية', default=0, tracking=True)

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.model
    def _cron_daily_kpi_snapshot(self):
        """
        Daily cron: compute and store a KPI snapshot for every active user
        for yesterday's period. Avoids duplicates by checking existing records.
        """
        yesterday_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59)

        users = self.env['res.users'].search([('active', '=', True), ('share', '=', False)])
        for user in users:
            try:
                # Skip if already computed
                existing = self.search([
                    ('employee_id', '=', user.id),
                    ('period_start', '=', yesterday_start),
                ], limit=1)
                if existing:
                    continue

                call_domain = [
                    ('agent_id', '=', user.id),
                    ('is_deleted', '=', False),
                    ('started_at', '>=', yesterday_start),
                    ('started_at', '<=', yesterday_end),
                ]
                calls = self.env['lugal.crm.call'].search(call_domain)
                total_calls = len(calls)
                answered = len(calls.filtered(lambda c: c.outcome != 'no_answer'))
                missed = total_calls - answered

                msg_domain = [
                    ('assigned_to_id', '=', user.id),
                    ('is_deleted', '=', False),
                    ('sent_at', '>=', yesterday_start),
                    ('sent_at', '<=', yesterday_end),
                ]
                inbound = self.env['lugal.crm.omnichannel.message'].search_count(
                    msg_domain + [('direction', '=', 'inbound')])
                outbound = self.env['lugal.crm.omnichannel.message'].search_count(
                    msg_domain + [('direction', '=', 'outbound')])
                late_msgs = self.env['lugal.crm.omnichannel.message'].search_count(
                    msg_domain + [('sla_breached', '=', True)])

                self.create({
                    'employee_id': user.id,
                    'period_start': yesterday_start,
                    'period_end': yesterday_end,
                    'total_calls': total_calls,
                    'answered_calls': answered,
                    'late_calls': missed,
                    'total_messages': inbound,
                    'answered_messages': outbound,
                    'late_messages': late_msgs,
                })
            except Exception:
                _logger.exception('KPI cron error for user %s', user.id)
