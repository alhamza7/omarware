# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/crm_email_controller.py
"""
Layer 2 — /api/crm/email/*
CRM-context wrappers around the email engine (JSON-RPC format).
"""

import logging
from datetime import timedelta, timezone
from odoo import http, fields
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id
from odoo.addons.lugal_email.controllers.email_controller import (
    _message_attachment_buckets,
    _resolve_cid_refs,
)

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields, so we guard for both."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _folder_role(folder):
    value = (folder or 'inbox').strip().lower()
    return value if value in {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'} else 'custom'


def _is_sent_folder(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent',
        'sent items',
        'sent messages',
    }


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
        'folder_role':  _folder_role(msg.folder),
        'subject':      msg.subject or '(no subject)',
        'from_name':    msg.from_name or '',
        'from_address': msg.from_address or '',
        'to_addresses': msg.to_addresses or '[]',
        'date':         _to_riyadh_iso(msg.date),
        'read_at':      _to_riyadh_iso(msg.read_at) if msg.read_at else None,
        'is_read':      msg.is_read,
        'is_starred':   msg.is_starred,
        'version':      _to_riyadh_iso(msg.write_date),
        'write_date':   _to_riyadh_iso(msg.write_date),
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket': {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                      if msg.linked_ticket_id else None,
        },
    }
    if full:
        raw_html = msg.body_html or ''
        att_list, inline_list = _message_attachment_buckets(msg)
        data['body_html']          = raw_html
        data['body_html_resolved'] = _resolve_cid_refs(raw_html, inline_list)
        data['body_text']          = msg.body_text or ''
        data['attachments']        = att_list
        data['inline_attachments'] = inline_list
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
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='create_date desc, id desc')
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
            msgs  = Msg.search(domain, limit=int(per_page), offset=offset, order='create_date desc, id desc')
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
            if not msg.exists() or msg.account_id.user_id.id != uid or msg.is_deleted:
                return {'success': False, 'error': 'Not found'}
            if not preview and not msg.is_read and not _is_sent_folder(msg.folder):
                was_already_read = bool(msg.read_at)
                read_at = fields.Datetime.now()
                msg.write({'is_read': True, 'read_at': read_at})
                try:
                    from odoo.addons.lugal_email.controllers.email_controller import (
                        _propagate_read_to_sent_copies,
                        _refresh_account_unread_count,
                        _resolve_imap_folder,
                        _send_mdn_async,
                    )
                    if not was_already_read and msg.message_id:
                        _propagate_read_to_sent_copies(request.env, msg.message_id, msg.read_at or read_at)
                    _refresh_account_unread_count(msg.account_id)
                    if msg.imap_uid:
                        msg.account_id.sudo()._imap_store_async(
                            msg.imap_uid,
                            _resolve_imap_folder(msg.account_id, msg.folder),
                            add_flags=['\\Seen'],
                        )
                    if (not was_already_read
                            and msg.request_read_receipt
                            and msg.from_address
                            and msg.message_id):
                        _send_mdn_async(
                            acc=msg.account_id,
                            to_address=msg.from_address,
                            original_message_id=msg.message_id,
                            original_subject=msg.subject or '',
                            recipient_email=msg.account_id.email_address,
                        )
                except Exception:
                    _logger.warning('CRM email detail read sync failed msg=%s', msg.id)
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
            msgs = request.env['lugal.email.message'].sudo().browse(message_ids).filtered(
                lambda msg: msg.exists() and msg.account_id.user_id.id == uid and not msg.is_deleted
            )
            readable_msgs = msgs.filtered(lambda msg: not _is_sent_folder(msg.folder))
            unread_msgs = readable_msgs.filtered(lambda msg: not msg.is_read or not msg.read_at)
            read_at = fields.Datetime.now()
            if unread_msgs:
                unread_msgs.write({'is_read': True, 'read_at': read_at})
                try:
                    from odoo.addons.lugal_email.controllers.email_controller import (
                        _propagate_read_to_sent_copies,
                        _refresh_account_unread_count,
                        _resolve_imap_folder,
                        _send_mdn_async,
                    )
                    for msg in unread_msgs:
                        if msg.message_id:
                            _propagate_read_to_sent_copies(request.env, msg.message_id, msg.read_at or read_at)
                        _refresh_account_unread_count(msg.account_id)
                        if msg.imap_uid:
                            msg.account_id.sudo()._imap_store_async(
                                msg.imap_uid,
                                _resolve_imap_folder(msg.account_id, msg.folder),
                                add_flags=['\\Seen'],
                            )
                        if msg.request_read_receipt and msg.from_address and msg.message_id:
                            _send_mdn_async(
                                acc=msg.account_id,
                                to_address=msg.from_address,
                                original_message_id=msg.message_id,
                                original_subject=msg.subject or '',
                                recipient_email=msg.account_id.email_address,
                            )
                except Exception:
                    _logger.warning('CRM email bulk read sync failed ids=%s', unread_msgs.ids)
            return {
                'success': True,
                'updated': len(unread_msgs),
                'skipped_sent_ids': msgs.filtered(lambda msg: _is_sent_folder(msg.folder)).ids,
            }
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

    @http.route('/api/crm/email/subscribe',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def subscribe(self, **kwargs):
        """Ensure the IMAP IDLE worker is running for all of this user's accounts.

        The FE calls this once after the WebSocket connects (fire-and-forget).
        It is idempotent — calling it multiple times has no side-effect.

        Response:
          {
            "subscribed": true,
            "accounts": ["user@domain.com", ...],
            "polling_interval_seconds": 30
          }

        The IMAP IDLE threads are persistent daemons owned by a single Odoo worker
        process. This endpoint wakes the supervisor immediately (instead of waiting
        up to 5 s for the background watchdog) so notifications start instantly.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            # Wake the IDLE supervisor immediately.
            # We trigger the dedicated cron job instead of calling start_all()
            # directly so that the IMAP threads are always owned by the
            # long-lived cron worker (SNl process) rather than a short-lived
            # HTTP worker that gets recycled after ~N requests.  The cron
            # trigger wakes the cron worker within seconds.
            try:
                cron = request.env.ref(
                    'lugal_email.ir_cron_lugal_email_idle_supervisor',
                    raise_if_not_found=False,
                )
                if cron:
                    cron.sudo()._trigger()
                else:
                    # Fallback if the cron ref is not found
                    request.env['lugal.email.idle.watcher'].sudo().start_all()
            except Exception as exc:
                _logger.warning('subscribe: cron trigger failed: %s', exc)

            # Return which accounts are being monitored for this user.
            accounts = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid),
                ('is_active', '=', True),
                ('is_deleted', '=', False),
            ])
            monitored = [
                acc.email_address
                for acc in accounts
                if (acc.password or '').strip()
            ]

            # Trigger one background IMAP sync per credential group on connect.
            # Force=True bypasses the 30-second throttle so the user always gets
            # fresh emails immediately when they open the app or reconnect.
            try:
                db_name = request.env.cr.dbname
                from odoo.addons.lugal_email.controllers.email_controller import (
                    _run_imap_sync_bg,
                )
                seen_creds: set = set()
                for acc in accounts:
                    if not (acc.password or '').strip():
                        continue
                    cred = (
                        (acc.imap_host or '').strip(),
                        int(acc.imap_port or 993),
                        (acc.username or acc.email_address or '').strip(),
                    )
                    if cred in seen_creds:
                        continue
                    seen_creds.add(cred)
                    # Always force a sync on WS connect — user expects fresh data
                    _run_imap_sync_bg(acc.id, db_name, force=True)
            except Exception as exc_sync:
                _logger.warning('subscribe: immediate email sync failed: %s', exc_sync)

            # Return current unread count so the FE can reconcile immediately on
            # connect without waiting for the next IMAP sync or push event.
            # This closes the race where an email arrives between page load and
            # WebSocket subscription.
            total_unread = 0
            try:
                total_unread = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', 'in', accounts.ids),
                    ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])
            except Exception:
                pass

            return {
                'success': True,
                'subscribed': True,
                'accounts': monitored,
                'polling_interval_seconds': 30,
                'unread_count': total_unread,
            }
        except Exception as exc:
            return _crm_error(exc, 'subscribe')

    @http.route('/api/crm/email/messages/bulk_delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def bulk_permanent_delete(self, message_ids=None, **kwargs):
        """Hard-delete messages that are already in the trash folder.

        Only messages owned by the caller that are in the 'trash' folder are
        deleted. Messages in any other folder, or belonging to another user,
        are skipped (reported in skipped_ids) without raising an error.

        Params (JSON-RPC):
          message_ids: list[int]  — max 1000 per call, required.

        Response:
          { "success": true, "data": { "deleted_ids": [...], "skipped_ids": [...] } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids or not isinstance(message_ids, list):
                return {'success': False, 'error': 'message_ids must be a non-empty list'}
            if len(message_ids) > 1000:
                return {'success': False, 'error': 'message_ids may not exceed 1000 per request'}

            user_accounts = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid),
                ('is_deleted', '=', False),
                ('is_active', '=', True),
            ])
            user_account_ids = user_accounts.ids

            Msg = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids)

            to_delete = msgs.filtered(
                lambda m: m.exists()
                and not m.is_deleted
                and m.account_id.id in user_account_ids
                and m.folder == 'trash'
            )
            deleted_ids = to_delete.ids
            skipped_ids = [i for i in message_ids if i not in deleted_ids]
            to_delete.unlink()

            return {
                'success': True,
                'data': {
                    'deleted_ids': deleted_ids,
                    'skipped_ids': skipped_ids,
                },
            }
        except Exception as exc:
            return _crm_error(exc, 'bulk_permanent_delete')

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
# TODO: remove - cherry-pick marker
