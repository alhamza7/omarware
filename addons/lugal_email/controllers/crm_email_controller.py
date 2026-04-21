# -*- coding: utf-8 -*-
"""
Layer 2 — /api/crm/email/*
CRM-context wrappers around the email engine (JSON-RPC format).
"""

import logging
from odoo import http
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


def _crm_error(exc, handler=''):
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass
    return {'success': False, 'error': str(exc)}


def _msg_to_dict(msg, full=False):
    import json as _json
    data = {
        'id':           msg.id,
        'account_id':   msg.account_id.id,
        'folder':       msg.folder,
        'subject':      msg.subject or '(no subject)',
        'from_name':    msg.from_name or '',
        'from_address': msg.from_address or '',
        'to_addresses': msg.to_addresses or '[]',
        'date':         msg.date.isoformat() if msg.date else None,
        'is_read':      msg.is_read,
        'is_starred':   msg.is_starred,
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket': {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                      if msg.linked_ticket_id else None,
        },
    }
    if full:
        data['body_html']   = msg.body_html or ''
        data['body_text']   = msg.body_text or ''
        data['attachments'] = []
    return data


class CrmEmailController(http.Controller):

    # ── Customer-scoped inbox ─────────────────────────────────────────────────

    @http.route('/api/crm/email/customer/<int:customer_id>/messages',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_messages(self, customer_id, folder=None, page=1, per_page=30, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [
                ('linked_customer_id', '=', customer_id),
                ('is_deleted', '=', False),
            ]
            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            if folder:
                domain.append(('folder', '=', folder))
            offset = (int(page) - 1) * int(per_page)
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='date desc')
            # Try to resolve customer name from CRM model if available
            customer_name = ''
            try:
                customer = request.env['lugal.crm.customer'].browse(customer_id)
                customer_name = customer.name if customer.exists() else ''
            except Exception:
                pass
            return {
                'success':       True,
                'data': {
                    'customer_id':   customer_id,
                    'customer_name': customer_name,
                    'total':         total,
                    'page':          int(page),
                    'per_page':      int(per_page),
                    'items':         [_msg_to_dict(m) for m in msgs],
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'customer_messages')

    @http.route('/api/crm/email/customer/<int:customer_id>/thread',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def customer_thread(self, customer_id, subject_contains=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('linked_customer_id', '=', customer_id), ('is_deleted', '=', False)]
            if subject_contains:
                domain.append(('subject', 'ilike', subject_contains))
            msgs = request.env['lugal.email.message'].sudo().search(domain, order='subject, date desc')
            # Group by subject
            threads = {}
            for m in msgs:
                key = (m.subject or '').strip()
                threads.setdefault(key, []).append(_msg_to_dict(m))
            thread_list = [{'subject': k, 'count': len(v), 'messages': v} for k, v in threads.items()]
            return {
                'success': True,
                'data': {
                    'customer_id': customer_id,
                    'total_threads': len(thread_list),
                    'threads': thread_list,
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'customer_thread')

    # ── Personal CRM inbox ────────────────────────────────────────────────────

    @http.route('/api/crm/email/messages/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def messages_list(self, folder='inbox', page=1, per_page=30,
                      customer_id=None, ticket_id=None, is_read=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            accs = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid), ('is_deleted', '=', False),
            ])
            domain = [
                ('account_id', 'in', accs.ids),
                ('folder', '=', folder),
                ('is_deleted', '=', False),
            ]
            if customer_id:
                domain.append(('linked_customer_id', '=', int(customer_id)))
            if ticket_id:
                domain.append(('linked_ticket_id', '=', int(ticket_id)))
            if is_read is not None:
                domain.append(('is_read', '=', bool(is_read)))
            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            offset = (int(page) - 1) * int(per_page)
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='date desc')
            return {
                'success': True,
                'data': {
                    'total': total, 'page': int(page), 'per_page': int(per_page),
                    'items': [_msg_to_dict(m) for m in msgs],
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'messages_list')

    @http.route('/api/crm/email/messages/<int:message_id>',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def message_detail(self, message_id, preview=False, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists():
                return {'success': False, 'error': 'Not found'}
            if not preview and not msg.is_read:
                msg.write({'is_read': True})
            return {'success': True, 'data': _msg_to_dict(msg, full=True)}
        except Exception as exc:
            return _crm_error(exc, 'message_detail')

    # ── Templates ─────────────────────────────────────────────────────────────

    @http.route('/api/crm/email/templates/list',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def templates_list(self, branch_id=None, category=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('channel', '=', 'email'), ('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_id', '=', int(branch_id)))
            if category:
                domain.append(('category', '=', category))
            templates = request.env['lugal.crm.message.template'].search(domain)
            items = [{
                'id':       t.id, 'name': t.name, 'name_ar': t.name_ar or '',
                'channel':  t.channel, 'category': t.category,
                'body':     t.body, 'body_ar': t.body_ar or '',
                'branch_id': t.branch_id.id if t.branch_id else None,
            } for t in templates]
            return {'success': True, 'data': {'total': len(items), 'items': items}}
        except Exception as exc:
            return _crm_error(exc, 'templates_list')

    @http.route('/api/crm/email/templates/<int:template_id>/apply',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def template_apply(self, template_id, customer_id=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            t = request.env['lugal.crm.message.template'].browse(template_id)
            if not t.exists():
                return {'success': False, 'error': 'Template not found'}
            customer_name = ''
            if customer_id:
                c = request.env['lugal.crm.customer'].browse(int(customer_id))
                if c.exists():
                    customer_name = c.name
            user = request.env.user
            vars_ = {
                'customer_name': customer_name,
                'agent_name':    user.name or '',
                'branch_name':   t.branch_id.name if t.branch_id else '',
            }
            rendered    = t.body or ''
            rendered_ar = t.body_ar or ''
            for k, v in vars_.items():
                rendered    = rendered.replace(f'{{{k}}}', v)
                rendered_ar = rendered_ar.replace(f'{{{k}}}', v)
            return {'success': True, 'data': {'rendered': rendered, 'rendered_ar': rendered_ar}}
        except Exception as exc:
            return _crm_error(exc, 'template_apply')

    # ── Bulk actions ──────────────────────────────────────────────────────────

    @http.route('/api/crm/email/bulk/read',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_read(self, message_ids=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids:
                return {'success': False, 'error': 'message_ids required'}
            msgs = request.env['lugal.email.message'].sudo().browse(message_ids)
            msgs.write({'is_read': True})
            return {'success': True, 'updated': len(msgs)}
        except Exception as exc:
            return _crm_error(exc, 'bulk_read')

    @http.route('/api/crm/email/bulk/trash',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_trash(self, message_ids=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids:
                return {'success': False, 'error': 'message_ids required'}
            msgs = request.env['lugal.email.message'].sudo().browse(message_ids)
            msgs.write({'folder': 'trash'})
            return {'success': True, 'updated': len(msgs)}
        except Exception as exc:
            return _crm_error(exc, 'bulk_trash')

    # ── Stats ─────────────────────────────────────────────────────────────────

    @http.route('/api/crm/email/stats',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stats(self, customer_id=None, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if customer_id:
                domain.append(('linked_customer_id', '=', int(customer_id)))
            Msg = request.env['lugal.email.message'].sudo()
            return {
                'success': True,
                'data': {
                    'total':    Msg.search_count(domain),
                    'unread':   Msg.search_count(domain + [('is_read', '=', False)]),
                    'starred':  Msg.search_count(domain + [('is_starred', '=', True)]),
                    'by_folder': {
                        f: Msg.search_count(domain + [('folder', '=', f)])
                        for f in ('inbox', 'sent', 'drafts', 'trash', 'archive', 'spam')
                    },
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'stats')
