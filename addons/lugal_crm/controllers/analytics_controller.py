# -*- coding: utf-8 -*-

import io
import csv
import logging
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request, Response
from ._auth import ensure_jwt_user_id
from ._permissions import is_supervisor_or_above, is_manager_or_above, forbidden
from ._error import crm_error

_logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_dt(value):
    """Parse ISO date string to datetime, return None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _date_domain(field, date_from, date_to):
    """Build domain clauses for a datetime field range."""
    clauses = []
    if date_from:
        clauses.append((field, '>=', date_from))
    if date_to:
        clauses.append((field, '<=', date_to))
    return clauses


# ─── Controller ───────────────────────────────────────────────────────────────

class AnalyticsController(http.Controller):

    @http.route('/api/crm/analytics/dashboard_stats', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def dashboard_stats(self, branch_id=None, date_from=None, date_to=None, **kwargs):
        """Aggregate stats for dashboard: customers, tickets, calls, messages, follow-ups."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            df = _parse_dt(date_from)
            dt = _parse_dt(date_to)

            base_c = [('is_deleted', '=', False), ('active', '=', True)]
            base_t = [('is_deleted', '=', False), ('active', '=', True)]
            base_call = [('is_deleted', '=', False), ('active', '=', True)]
            base_msg = [('is_deleted', '=', False)]

            if branch_id:
                base_c.append(('branch_ids', 'in', [branch_id]))
                base_t.append(('branch_id', '=', branch_id))
                base_call.append(('branch_id', '=', branch_id))
                base_msg.append(('branch_id', '=', branch_id))

            Customer = request.env['lugal.crm.customer']
            Ticket = request.env['lugal.crm.ticket']
            Call = request.env['lugal.crm.call']
            Msg = request.env['lugal.crm.omnichannel.message']
            Task = request.env['lugal.crm.task']

            total_customers = Customer.search_count(base_c)
            vip_customers = Customer.search_count(base_c + [('vip_status', '=', True)])
            new_today = Customer.search_count(base_c + [('create_date', '>=', datetime.now().replace(hour=0, minute=0, second=0))])

            open_tickets = Ticket.search_count(base_t + [('status', 'in', ['open', 'in_progress'])])
            resolved_tickets = Ticket.search_count(base_t + [('status', '=', 'resolved')])
            high_priority_tickets = Ticket.search_count(base_t + [('priority', '=', 'high'), ('status', 'not in', ['resolved', 'closed'])])

            call_domain = base_call + (_date_domain('started_at', df, dt) if df or dt else [])
            total_calls = Call.search_count(call_domain)
            missed_calls = Call.search_count(call_domain + [('outcome', '=', 'no_answer')])

            msg_domain = base_msg + (_date_domain('sent_at', df, dt) if df or dt else [])
            total_messages = Msg.search_count(msg_domain + [('direction', '=', 'inbound')])
            pending_messages = Msg.search_count(base_msg + [('status', '=', 'pending')])
            sla_breached_messages = Msg.search_count(base_msg + [('sla_breached', '=', True), ('status', '!=', 'resolved')])

            overdue_tasks = Task.search_count([
                ('is_deleted', '=', False),
                ('status', 'not in', ['done', 'overdue']),
                ('due_date', '<', datetime.now()),
            ])

            return {
                'success': True,
                'data': {
                    'customers': {
                        'total': total_customers,
                        'vip': vip_customers,
                        'new_today': new_today,
                    },
                    'tickets': {
                        'open': open_tickets,
                        'resolved': resolved_tickets,
                        'high_priority': high_priority_tickets,
                    },
                    'calls': {
                        'total': total_calls,
                        'missed': missed_calls,
                    },
                    'messages': {
                        'inbound': total_messages,
                        'pending_reply': pending_messages,
                        'sla_breached': sla_breached_messages,
                    },
                    'tasks': {
                        'overdue': overdue_tasks,
                    },
                },
            }
        except Exception as e:
            return crm_error(e, 'dashboard_stats')

    @http.route('/api/crm/analytics/channel_report', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def channel_report(self, branch_id=None, date_from=None, date_to=None, **kwargs):
        """Volume of inbound messages and calls per channel."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            df = _parse_dt(date_from)
            dt = _parse_dt(date_to)

            msg_domain = [('is_deleted', '=', False), ('direction', '=', 'inbound')]
            call_domain = [('is_deleted', '=', False), ('active', '=', True)]
            if branch_id:
                msg_domain.append(('branch_id', '=', branch_id))
                call_domain.append(('branch_id', '=', branch_id))
            msg_domain += _date_domain('sent_at', df, dt)
            call_domain += _date_domain('started_at', df, dt)

            Msg = request.env['lugal.crm.omnichannel.message']
            Call = request.env['lugal.crm.call']

            # Count messages per channel
            channels = ['whatsapp', 'instagram', 'telegram', 'tiktok', 'x', 'snapchat', 'email', 'website']
            channel_data = []
            for ch in channels:
                msg_count = Msg.search_count(msg_domain + [('channel', '=', ch)])
                resolved = Msg.search_count(msg_domain + [('channel', '=', ch), ('status', '=', 'resolved')])
                sla_breached = Msg.search_count(msg_domain + [('channel', '=', ch), ('sla_breached', '=', True)])
                channel_data.append({
                    'channel': ch,
                    'messages': msg_count,
                    'resolved': resolved,
                    'sla_breached': sla_breached,
                })

            # Calls per call_type (channel field is free text in calls)
            total_calls = Call.search_count(call_domain)
            inbound_calls = Call.search_count(call_domain + [('call_type', '=', 'inbound')])
            outbound_calls = Call.search_count(call_domain + [('call_type', '=', 'outbound')])
            missed_calls = Call.search_count(call_domain + [('outcome', '=', 'no_answer')])

            return {
                'success': True,
                'data': {
                    'channels': channel_data,
                    'calls': {
                        'total': total_calls,
                        'inbound': inbound_calls,
                        'outbound': outbound_calls,
                        'missed': missed_calls,
                    },
                },
            }
        except Exception as e:
            return crm_error(e, 'channel_report')

    @http.route('/api/crm/analytics/employee_kpi', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def employee_kpi(self, employee_id=None, branch_id=None, period_start=None, period_end=None, live=False, **kwargs):
        """
        Get KPI for an employee.
        - live=True: compute on-the-fly from raw data for the given period.
        - live=False: return the last stored KPI snapshot.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            uid = employee_id or request.env.uid

            if live:
                return self._compute_live_kpi(uid, branch_id, period_start, period_end)

            # Stored snapshot
            domain = [('employee_id', '=', uid), ('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if period_start:
                domain.append(('period_start', '>=', period_start))
            if period_end:
                domain.append(('period_end', '<=', period_end))
            kpi = request.env['lugal.crm.employee.kpi'].search(domain, limit=1, order='period_end desc')
            if not kpi:
                return {'success': True, 'data': None}
            return {'success': True, 'data': self._kpi_to_dict(kpi[0])}
        except Exception as e:
            return crm_error(e, 'employee_kpi')

    def _compute_live_kpi(self, employee_id, branch_id, period_start, period_end):
        """Compute KPI metrics directly from calls and messages for the period."""
        df = _parse_dt(period_start) or (datetime.now() - timedelta(days=30))
        dt = _parse_dt(period_end) or datetime.now()

        call_domain = [
            ('agent_id', '=', employee_id),
            ('is_deleted', '=', False),
            ('started_at', '>=', df),
            ('started_at', '<=', dt),
        ]
        if branch_id:
            call_domain.append(('branch_id', '=', branch_id))

        msg_domain = [
            ('assigned_to_id', '=', employee_id),
            ('is_deleted', '=', False),
            ('sent_at', '>=', df),
            ('sent_at', '<=', dt),
        ]
        if branch_id:
            msg_domain.append(('branch_id', '=', branch_id))

        Call = request.env['lugal.crm.call']
        Msg = request.env['lugal.crm.omnichannel.message']

        all_calls = Call.search(call_domain)
        total_calls = len(all_calls)
        answered_calls = len(all_calls.filtered(lambda c: c.outcome != 'no_answer'))
        missed_calls = total_calls - answered_calls

        durations = [c.duration_seconds for c in all_calls if c.duration_seconds]
        avg_call_duration = round(sum(durations) / len(durations), 2) if durations else 0

        total_messages = Msg.search_count(msg_domain + [('direction', '=', 'inbound')])
        outbound_messages = Msg.search_count(msg_domain + [('direction', '=', 'outbound')])
        late_messages = Msg.search_count(msg_domain + [('sla_breached', '=', True)])

        # FRT: seconds from inbound message sent_at to next outbound message in same conversation
        frt_values = []
        inbound_msgs = Msg.search(msg_domain + [('direction', '=', 'inbound'), ('conversation_id', '!=', False)])
        for msg in inbound_msgs:
            reply = Msg.search([
                ('conversation_id', '=', msg.conversation_id),
                ('direction', '=', 'outbound'),
                ('assigned_to_id', '=', employee_id),
                ('sent_at', '>', msg.sent_at),
            ], limit=1, order='sent_at asc')
            if reply:
                delta = (reply.sent_at - msg.sent_at).total_seconds()
                if delta > 0:
                    frt_values.append(delta)

        avg_frt = round(sum(frt_values) / len(frt_values), 2) if frt_values else 0

        return {
            'success': True,
            'data': {
                'employee_id': employee_id,
                'period_start': df.isoformat(),
                'period_end': dt.isoformat(),
                'total_calls': total_calls,
                'answered_calls': answered_calls,
                'missed_calls': missed_calls,
                'avg_call_duration_seconds': avg_call_duration,
                'total_messages': total_messages,
                'answered_messages': outbound_messages,
                'late_messages': late_messages,
                'avg_frt_seconds': avg_frt,
                'source': 'live',
            },
        }

    def _kpi_to_dict(self, k):
        return {
            'employee_id': k.employee_id.id if k.employee_id else None,
            'employee_name': k.employee_id.name if k.employee_id else '',
            'period_start': k.period_start.isoformat() if k.period_start else None,
            'period_end': k.period_end.isoformat() if k.period_end else None,
            'total_calls': k.total_calls,
            'answered_calls': k.answered_calls,
            'total_messages': k.total_messages,
            'answered_messages': k.answered_messages,
            'avg_frt_seconds': k.avg_frt_seconds,
            'avg_ttr_seconds': k.avg_ttr_seconds,
            'late_messages': k.late_messages,
            'late_calls': k.late_calls,
            'conversions_to_order': k.conversions_to_order,
            'source': 'snapshot',
        }

    @http.route('/api/crm/analytics/branch_report', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def branch_report(self, date_from=None, date_to=None, **kwargs):
        """Report per branch: customers, tickets, calls, messages.

        Uses a single SQL aggregation instead of 4 × N search_count() calls.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            df = _parse_dt(date_from)
            dt = _parse_dt(date_to)

            # Build optional date filters for calls and messages
            call_date_filter = ''
            call_params = []
            if df:
                call_date_filter += ' AND c.started_at >= %s'
                call_params.append(df)
            if dt:
                call_date_filter += ' AND c.started_at <= %s'
                call_params.append(dt)

            msg_date_filter = ''
            msg_params = []
            if df:
                msg_date_filter += ' AND m.sent_at >= %s'
                msg_params.append(df)
            if dt:
                msg_date_filter += ' AND m.sent_at <= %s'
                msg_params.append(dt)

            # Single query: all four counts per branch in one pass
            sql = f"""
                SELECT
                    b.id                          AS branch_id,
                    b.name                        AS branch_name,
                    COUNT(DISTINCT rel.customer_id) FILTER (
                        WHERE cust.is_deleted = false AND cust.active = true
                    )                             AS customers,
                    COUNT(DISTINCT t.id) FILTER (
                        WHERE t.is_deleted = false
                          AND t.status IN ('open', 'in_progress')
                    )                             AS open_tickets,
                    COUNT(DISTINCT call.id) FILTER (
                        WHERE call.is_deleted = false
                          AND call.active = true
                          {call_date_filter.replace('%s', '%s')}
                    )                             AS calls,
                    COUNT(DISTINCT msg.id) FILTER (
                        WHERE msg.is_deleted = false
                          {msg_date_filter.replace('%s', '%s')}
                    )                             AS messages
                FROM lugal_crm_branch b
                LEFT JOIN lugal_crm_customer_branch_rel rel ON rel.branch_id = b.id
                LEFT JOIN lugal_crm_customer cust ON cust.id = rel.customer_id
                LEFT JOIN lugal_crm_ticket t ON t.branch_id = b.id
                LEFT JOIN lugal_crm_call call ON call.branch_id = b.id
                LEFT JOIN lugal_crm_omnichannel_message msg ON msg.branch_id = b.id
                WHERE b.active = true
                  AND b.is_deleted = false
                GROUP BY b.id, b.name
                ORDER BY b.name
            """

            request.env.cr.execute(sql, call_params + msg_params)
            rows = request.env.cr.dictfetchall()

            result = [
                {
                    'branch_id':    row['branch_id'],
                    'branch_name':  row['branch_name'],
                    'customers':    row['customers'] or 0,
                    'open_tickets': row['open_tickets'] or 0,
                    'calls':        row['calls'] or 0,
                    'messages':     row['messages'] or 0,
                }
                for row in rows
            ]

            return {'success': True, 'data': {'branches': result}}
        except Exception as e:
            return crm_error(e, 'branch_report')

    @http.route('/api/crm/analytics/all_employees_kpi', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def all_employees_kpi(self, branch_id=None, period_start=None, period_end=None, **kwargs):
        """Supervisor view: KPI snapshot for every employee. Requires Supervisor or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Supervisor role required to view all employees KPI')

            domain = [('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if period_start:
                domain.append(('period_start', '>=', period_start))
            if period_end:
                domain.append(('period_end', '<=', period_end))

            # Latest snapshot per employee
            kpis = request.env['lugal.crm.employee.kpi'].search(domain, order='period_end desc')
            seen = set()
            result = []
            for k in kpis:
                if k.employee_id.id not in seen:
                    seen.add(k.employee_id.id)
                    result.append(self._kpi_to_dict(k))

            return {'success': True, 'data': {'items': result}}
        except Exception as e:
            return crm_error(e, 'all_employees_kpi')

    @http.route('/api/crm/analytics/supervisor_dashboard', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supervisor_dashboard(self, branch_id=None, **kwargs):
        """
        Supervisor real-time panel. Requires Supervisor or above.
        - open conversations per employee
        - unassigned pending messages
        - overdue follow-up tasks
        - high priority tickets
        - VIP customers with recent activity
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_supervisor_or_above():
                return forbidden('Supervisor role required')

            msg_base = [('is_deleted', '=', False)]
            task_base = [('is_deleted', '=', False)]
            ticket_base = [('is_deleted', '=', False)]
            if branch_id:
                msg_base.append(('branch_id', '=', branch_id))
                ticket_base.append(('branch_id', '=', branch_id))

            Msg = request.env['lugal.crm.omnichannel.message']
            Task = request.env['lugal.crm.task']
            Ticket = request.env['lugal.crm.ticket']
            Customer = request.env['lugal.crm.customer']

            # Open conversations per agent (status = assigned, grouped by assigned_to_id)
            open_msgs = Msg.search(msg_base + [('status', '=', 'assigned')])
            agent_conv = {}
            for m in open_msgs:
                aid = m.assigned_to_id.id if m.assigned_to_id else 0
                aname = m.assigned_to_id.name if m.assigned_to_id else 'Unassigned'
                if aid not in agent_conv:
                    agent_conv[aid] = {'agent_id': aid, 'agent_name': aname, 'open_conversations': 0}
                agent_conv[aid]['open_conversations'] += 1

            # Unassigned pending messages (can be grabbed by supervisor)
            unassigned_pending = Msg.search(msg_base + [('status', '=', 'pending'), ('assigned_to_id', '=', False)], limit=50)
            unassigned_list = [{
                'id': m.id,
                'channel': m.channel,
                'customer_id': m.customer_id.id if m.customer_id else None,
                'customer_name': m.customer_id.name if m.customer_id else '',
                'content': (m.content or '')[:80],
                'sent_at': m.sent_at.isoformat() if m.sent_at else None,
                'sla_breached': m.sla_breached,
            } for m in unassigned_pending]

            # Overdue follow-up tasks
            overdue_tasks = Task.search(task_base + [
                ('status', 'not in', ['done', 'overdue']),
                ('due_date', '<', datetime.now()),
            ], limit=50)
            overdue_list = [{
                'id': t.id,
                'title': t.title or '',
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'assigned_to': t.assigned_to_id.name if t.assigned_to_id else '',
                'customer_name': t.customer_id.name if t.customer_id else '',
            } for t in overdue_tasks]

            # High priority open tickets
            hp_tickets = Ticket.search(ticket_base + [
                ('priority', '=', 'high'),
                ('status', 'not in', ['resolved', 'closed']),
            ], limit=30)
            hp_list = [{
                'id': t.id,
                'title': t.title or '',
                'status': t.status,
                'priority': t.priority or '',
                'assigned_to': t.assigned_to_id.name if t.assigned_to_id else '',
                'customer_name': t.customer_id.name if t.customer_id else '',
                'sla_deadline': t.sla_deadline.isoformat() if t.sla_deadline else None,
            } for t in hp_tickets]

            # VIP customers with no activity in 30 days
            vip_base = [('is_deleted', '=', False), ('active', '=', True), ('vip_status', '=', True)]
            if branch_id:
                vip_base.append(('branch_ids', 'in', [branch_id]))
            thirty_days_ago = datetime.now() - timedelta(days=30)
            dormant_vip = Customer.search(vip_base + [
                '|',
                ('last_call_date', '=', False),
                ('last_call_date', '<', thirty_days_ago),
            ], limit=20)
            dormant_list = [{
                'id': c.id,
                'name': c.name,
                'last_call_date': c.last_call_date.isoformat() if c.last_call_date else None,
                'account_manager': c.account_manager_id.name if c.account_manager_id else '',
            } for c in dormant_vip]

            return {
                'success': True,
                'data': {
                    'agent_conversations': list(agent_conv.values()),
                    'unassigned_messages': unassigned_list,
                    'unassigned_count': len(unassigned_pending),
                    'overdue_tasks': overdue_list,
                    'overdue_count': len(overdue_tasks),
                    'high_priority_tickets': hp_list,
                    'dormant_vip_customers': dormant_list,
                },
            }
        except Exception as e:
            return crm_error(e, 'supervisor_dashboard')

    @http.route('/api/crm/analytics/ai_vs_human', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def ai_vs_human(self, branch_id=None, date_from=None, date_to=None, **kwargs):
        """
        AI vs Human report.
        Counts messages where replied_by_agent_at is set (human) vs those resolved
        with no agent reply but status=resolved (assumed AI/bot handled outside hours).
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            df = _parse_dt(date_from)
            dt = _parse_dt(date_to)

            base = [('is_deleted', '=', False), ('direction', '=', 'inbound')]
            if branch_id:
                base.append(('branch_id', '=', branch_id))
            base += _date_domain('sent_at', df, dt)

            Msg = request.env['lugal.crm.omnichannel.message']
            total_inbound = Msg.search_count(base)
            human_replied = Msg.search_count(base + [('replied_by_agent_at', '!=', False)])
            ai_resolved = Msg.search_count(base + [
                ('replied_by_agent_at', '=', False),
                ('status', '=', 'resolved'),
            ])
            unresolved = total_inbound - human_replied - ai_resolved

            human_pct = round(human_replied / total_inbound * 100, 1) if total_inbound else 0
            ai_pct = round(ai_resolved / total_inbound * 100, 1) if total_inbound else 0

            return {
                'success': True,
                'data': {
                    'total_inbound': total_inbound,
                    'human_replied': human_replied,
                    'ai_resolved': ai_resolved,
                    'unresolved': unresolved,
                    'human_pct': human_pct,
                    'ai_pct': ai_pct,
                },
            }
        except Exception as e:
            return crm_error(e, 'ai_vs_human')

    @http.route('/api/crm/analytics/export_kpi', type='http', auth='none', csrf=False, methods=['POST'])
    def export_kpi_csv(self, **kwargs):
        """
        Export employee KPI snapshot as CSV. Requires Manager or above.
        Accepts: branch_id (optional), period_start, period_end as form params.
        """
        try:
            if not ensure_jwt_user_id():
                return Response('Unauthorized', status=401)
            if not is_manager_or_above():
                return Response('Forbidden — Manager role required', status=403)

            branch_id = kwargs.get('branch_id')
            period_start = kwargs.get('period_start')
            period_end = kwargs.get('period_end')

            domain = [('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', int(branch_id)))
            if period_start:
                domain.append(('period_start', '>=', period_start))
            if period_end:
                domain.append(('period_end', '<=', period_end))

            kpis = request.env['lugal.crm.employee.kpi'].sudo().search(domain, order='period_end desc, employee_id asc')

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'Employee', 'Branch', 'Period Start', 'Period End',
                'Total Calls', 'Answered Calls', 'Total Messages', 'Answered Messages',
                'Avg FRT (s)', 'Avg TTR (s)', 'Late Messages', 'Late Calls', 'Conversions',
            ])
            for k in kpis:
                writer.writerow([
                    k.employee_id.name if k.employee_id else '',
                    k.branch_id.name if k.branch_id else '',
                    k.period_start.isoformat() if k.period_start else '',
                    k.period_end.isoformat() if k.period_end else '',
                    k.total_calls, k.answered_calls, k.total_messages, k.answered_messages,
                    k.avg_frt_seconds, k.avg_ttr_seconds, k.late_messages, k.late_calls,
                    k.conversions_to_order,
                ])

            csv_bytes = output.getvalue().encode('utf-8-sig')
            return Response(
                csv_bytes,
                headers={
                    'Content-Type': 'text/csv; charset=utf-8',
                    'Content-Disposition': 'attachment; filename="kpi_report.csv"',
                },
                status=200,
            )
        except Exception as e:
            _logger.exception('export_kpi_csv error')
            return Response(str(e), status=500)

    @http.route('/api/crm/analytics/audit_log', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def audit_log_list(self, page=1, per_page=50, action=None, user_id=None,
                      customer_id=None, branch_id=None, date_from=None, date_to=None, **kwargs):
        """
        List CRM audit log entries for supervisor review.
        Filterable by action type, user, customer, branch, and date range.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = []
            if action:
                domain.append(('action', '=', action))
            if user_id:
                domain.append(('user_id', '=', user_id))
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if branch_id:
                domain.append(('branch_id', '=', branch_id))
            if date_from:
                domain.append(('timestamp', '>=', date_from))
            if date_to:
                domain.append(('timestamp', '<=', date_to))

            AuditLog = request.env['lugal.crm.audit.log']
            total = AuditLog.search_count(domain)
            logs = AuditLog.search(domain, limit=per_page, offset=(page - 1) * per_page,
                                   order='timestamp desc')
            items = [{
                'id': log.id,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                'action': log.action,
                'user_id': log.user_id.id if log.user_id else None,
                'user_name': log.user_id.name if log.user_id else '',
                'customer_id': log.customer_id.id if log.customer_id else None,
                'customer_name': log.customer_id.name if log.customer_id else '',
                'branch_id': log.branch_id.id if log.branch_id else None,
                'branch_name': log.branch_id.name if log.branch_id else '',
                'record_model': log.record_model or '',
                'record_id': log.record_id or 0,
                'ip_address': log.ip_address or '',
                'details': log.details or '',
            } for log in logs]
            return {
                'success': True,
                'data': {
                    'items': items,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            return crm_error(e, 'audit_log_list')
