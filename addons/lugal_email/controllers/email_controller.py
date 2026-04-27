# -*- coding: utf-8 -*-
"""
Layer 1 — /api/lugal/email/*

Pure email engine REST endpoints (plain HTTP, Bearer JWT auth).
No CRM-specific logic. All endpoints return JSON directly (not JSON-RPC envelope).
"""

import json
import logging
import threading
from datetime import timedelta, timezone
from odoo import http
from odoo.http import request, Response
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

# Saudi Arabia timezone — UTC+3, no DST
_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')

ALLOWED_LINK_MODELS = {
    'lugal.crm.customer',
    'lugal.crm.ticket',
    'lugal.crm.interaction',
}

# HTML signatures may include inline data: URLs; keep a generous cap.
_MAX_EMAIL_SIGNATURE_LEN = 5 * 1024 * 1024


def _norm_addr_list(raw):
    """Normalize to a flat list of email address strings.
    Accepts: ["a@b.com", ...] or [{"email": "a@b.com"}, ...] or a bare string."""
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    result = []
    for item in raw:
        addr = item['email'] if isinstance(item, dict) else item
        if addr and isinstance(addr, str) and addr.strip():
            result.append(addr.strip())
    return result

# ── Background IMAP sync state ────────────────────────────────────────────────
# Per-account sync lock: prevents duplicate concurrent IMAP fetches.
_sync_lock = threading.Lock()
_syncing_accounts: set = set()

# Throttle mirrors (kept here so the controller doesn't import from the model).
_IMAP_THROTTLE_SECONDS = 15       # min gap between syncs when inbox has messages
_IMAP_THROTTLE_EMPTY_SECONDS = 10 # min gap when inbox is empty


def _needs_imap_sync(acc, force=False):
    """
    Return True if this account is overdue for an IMAP sync.
    Fast path: only reads already-loaded ORM fields + one indexed search_count.
    """
    if not (acc.password or '').strip():
        return False
    if force:
        return True
    if not acc.last_sync_date:
        return True
    from odoo import fields as odoo_fields
    delta = (odoo_fields.Datetime.now() - acc.last_sync_date).total_seconds()
    inbox_count = acc.env['lugal.email.message'].sudo().search_count([
        ('account_id', '=', acc.id),
        ('folder', '=', 'inbox'),
        ('is_deleted', '=', False),
    ])
    limit = _IMAP_THROTTLE_EMPTY_SECONDS if inbox_count == 0 else _IMAP_THROTTLE_SECONDS
    return delta >= limit


def _run_imap_sync_bg(acc_id, db_name):
    """
    Spawn a one-shot daemon thread to run IMAP inbox sync for a single account.
    Returns the Thread object so callers can optionally join/wait, or None if a
    sync is already running for that account.
    The thread commits its own transaction independently of the HTTP worker.
    """
    with _sync_lock:
        if acc_id in _syncing_accounts:
            return None
        _syncing_accounts.add(acc_id)

    def _do():
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                acc = env['lugal.email.account'].browse(acc_id)
                if acc.exists() and (acc.password or '').strip():
                    acc.action_sync()
        except Exception:
            _logger.exception('Background IMAP sync failed account_id=%s', acc_id)
        finally:
            with _sync_lock:
                _syncing_accounts.discard(acc_id)

    t = threading.Thread(target=_do, daemon=True, name=f'imap-bg-{acc_id}')
    t.start()
    return t


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_response(data, status=200):
    """Return a plain JSON HTTP response (not JSON-RPC)."""
    return Response(
        json.dumps(data, default=str),
        status=status,
        mimetype='application/json',
    )


def _unauthorized():
    return _json_response({'success': False, 'error': 'Unauthorized'}, status=401)


def _not_found(msg='Not found'):
    return _json_response({'success': False, 'error': msg}, status=404)


def _account_to_dict(acc):
    return {
        'id':                  acc.id,
        'name':                acc.name,
        'email_address':       acc.email_address,
        'username':            acc.username or acc.email_address or '',
        'display_name_field':  acc.display_name_field or '',
        'imap_host':           acc.imap_host or '',
        'imap_port':           acc.imap_port,
        'imap_use_ssl':        acc.imap_use_ssl,
        'smtp_host':           acc.smtp_host or '',
        'smtp_port':           acc.smtp_port,
        'smtp_use_tls':        acc.smtp_use_tls,
        'is_default':          acc.is_default,
        'is_active':           acc.is_active,
        'sync_status':         acc.sync_status or 'never',
        'last_sync_date':      _to_riyadh_iso(acc.last_sync_date),
        'unread_count':        acc.unread_count,
        # password_set lets the FE know whether the app password has been entered
        # without ever exposing the actual credential value.
        'password_set':        bool(acc.password),
    }


def _message_to_dict(msg, full=False):
    data = {
        'id':             msg.id,
        'account_id':     msg.account_id.id,
        'folder':         msg.folder,
        'subject':        msg.subject or '(no subject)',
        'from_name':      msg.from_name or '',
        'from_address':   msg.from_address or '',
        'to_addresses':   msg.to_addresses or '[]',
        'cc_addresses':   msg.cc_addresses or '[]',
        'date':           _to_riyadh_iso(msg.date),
        # received_at: when Odoo first imported this message (create_date = Saudi TZ)
        'received_at':    _to_riyadh_iso(msg.create_date),
        # read_at: first time the message was opened/marked-read (null if never read)
        'read_at':        _to_riyadh_iso(msg.read_at) if msg.read_at else None,
        'is_read':        msg.is_read,
        'is_starred':     msg.is_starred,
        'is_draft':       msg.is_draft,
        'smtp_delivered': msg.smtp_delivered,
        'smtp_error':     msg.smtp_error or None,
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket':   {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                        if msg.linked_ticket_id else None,
        },
    }
    if full:
        data['body_html']    = msg.body_html or ''
        data['body_text']    = msg.body_text or ''
        data['body_fetched'] = bool(msg.body_fetched)
        data['attachments']  = []
    return data


def _get_user_accounts(uid):
    return request.env['lugal.email.account'].sudo().search([
        ('user_id', '=', uid),
        ('is_deleted', '=', False),
        ('is_active', '=', True),
    ])


class LugalEmailController(http.Controller):

    # ── Accounts ─────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def accounts(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            if request.httprequest.method == 'GET':
                accs = _get_user_accounts(uid)

                # Auto-provision: existing employees who were created before the
                # auto-create logic existed will have no accounts. Build one from
                # their res.users profile so the FE always has something to show.
                if not accs:
                    user = request.env['res.users'].sudo().browse(uid)
                    if user.exists():
                        user_email = user.partner_id.email or user.login or ''
                        user_name  = user.partner_id.name or user.login or ''
                        if user_email:
                            try:
                                new_acc = request.env['lugal.email.account'].sudo().create({
                                    'user_id':       uid,
                                    'name':          user_name,
                                    'email_address': user_email,
                                    'username':      user_email,
                                    'password':      '',       # admin must enter the app password
                                    'imap_host':     'mail.nooralnibras.com',
                                    'imap_port':     993,
                                    'imap_use_ssl':  True,
                                    'smtp_host':     'mail.nooralnibras.com',
                                    'smtp_port':     465,
                                    'smtp_use_tls':  False,
                                    'is_default':    True,
                                    'is_active':     True,
                                    'sync_status':   'never',
                                })
                                accs = new_acc
                            except Exception:
                                _logger.warning(
                                    'accounts GET: auto-provision failed for uid=%s', uid,
                                    exc_info=True,
                                )
                                accs = request.env['lugal.email.account'].sudo().browse()

                return _json_response({
                    'success': True,
                    'data': [_account_to_dict(a) for a in accs],
                })
            # POST — create account
            body = json.loads(request.httprequest.data or '{}')
            vals = {
                'user_id':          uid,
                'name':             body.get('name', ''),
                'email_address':    body.get('email_address', ''),
                'display_name_field': body.get('display_name_field', ''),
                'username':         body.get('username', ''),
                'password':         body.get('password', ''),
                'imap_host':        body.get('imap_host', 'imap.gmail.com'),
                'imap_port':        body.get('imap_port', 993),
                'imap_use_ssl':     body.get('imap_use_ssl', True),
                'smtp_host':        body.get('smtp_host', 'smtp.gmail.com'),
                'smtp_port':        body.get('smtp_port', 587),
                'smtp_use_tls':     body.get('smtp_use_tls', True),
                'is_default':       body.get('is_default', False),
            }
            if not vals['email_address'] or not vals['name']:
                return _json_response({'success': False, 'error': 'name and email_address required'}, 400)
            acc = request.env['lugal.email.account'].sudo().create(vals)
            if vals['is_default']:
                acc.action_set_default()
            return _json_response({'success': True, 'data': _account_to_dict(acc)}, 201)
        except Exception as exc:
            _logger.exception('email accounts error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'DELETE', 'OPTIONS'])
    def account_detail(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid or acc.is_deleted:
                return _not_found('Account not found')

            method = request.httprequest.method
            if method == 'GET':
                return _json_response({'success': True, 'data': _account_to_dict(acc)})

            if method == 'DELETE':
                acc.write({'is_deleted': True, 'active': False})
                return _json_response({'success': True})

            # PATCH — partial update
            body = json.loads(request.httprequest.data or '{}')
            allowed = {
                'name', 'email_address', 'display_name_field', 'username', 'password',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls',
                'is_active',
            }
            vals = {k: v for k, v in body.items() if k in allowed}
            if vals:
                acc.write(vals)
            return _json_response({'success': True, 'data': _account_to_dict(acc)})
        except Exception as exc:
            _logger.exception('account_detail error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/test', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_test(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            result = acc.action_test_connection()
            return _json_response({'success': result.get('status') == 'ok', **result})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/sync/all', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def sync_all_accounts(self, **kwargs):
        """Kick off a background IMAP sync for every active account owned by the current user."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            accs = _get_user_accounts(uid)
            db_name = request.env.cr.dbname
            results = []
            for acc in accs:
                try:
                    t = _run_imap_sync_bg(acc.id, db_name)
                    results.append({'account_id': acc.id, 'sync_started': t is not None})
                except Exception as exc:
                    results.append({'account_id': acc.id, 'sync_started': False, 'error': str(exc)})
            return _json_response({
                'success': True,
                'message': 'Sync started in background',
                'synced': len(results),
                'data': results,
            })
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/sync', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_sync(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            t = _run_imap_sync_bg(acc.id, request.env.cr.dbname)
            return _json_response({
                'success': True,
                'sync_started': t is not None,
                'message': 'Sync started in background' if t is not None else 'Sync already running for this account',
            })
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/accounts/<int:account_id>/set_default', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def account_set_default(self, account_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found()
            acc.action_set_default()
            return _json_response({'success': True, 'data': _account_to_dict(acc)})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/signature', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'PUT', 'OPTIONS'])
    def user_email_signature(self, **kwargs):
        """Read or replace the JWT user's HTML email signature (``res.users.signature``)."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return _not_found('User not found')

            method = request.httprequest.method
            if method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {'signature': user.signature or ''},
                })

            raw = request.httprequest.data or b'{}'
            body = json.loads(raw)
            if 'signature' not in body:
                return _json_response(
                    {'success': False, 'error': 'signature field is required'},
                    400,
                )
            sig = body.get('signature')
            if sig is not None and not isinstance(sig, str):
                return _json_response(
                    {'success': False, 'error': 'signature must be a string or null'},
                    400,
                )
            sig = '' if sig is None else sig
            if len(sig) > _MAX_EMAIL_SIGNATURE_LEN:
                return _json_response(
                    {'success': False, 'error': 'signature exceeds maximum length'},
                    400,
                )
            user.write({'signature': sig})
            return _json_response({
                'success': True,
                'data': {'signature': user.signature or ''},
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('user_email_signature error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Push-webhook: instant notify without waiting for cron ─────────────────
    #
    # External services (Microsoft Graph, Gmail Pub/Sub, Mailgun, custom SMTP
    # forwarders, etc.) can POST to this endpoint the moment a new email lands
    # in a mailbox.  The sync runs synchronously inside the current request so
    # no extra DB connections are opened and the WS push event fires before
    # this response is returned.
    #
    # Authentication: callers MUST send a shared secret in the
    # X-Lugal-Webhook-Token header OR as a `token` query / body parameter.
    # Set the secret once via System Parameters:
    #   lugal.email.webhook.token = <random-string>
    # If the parameter is missing or empty the endpoint is disabled (401).
    #
    # Request body (JSON, all fields optional):
    #   { "email": "user@domain.com",   # narrow sync to one account
    #     "account_id": 3 }             # OR by internal account id
    # If neither is provided all active accounts are synced sequentially.

    @http.route('/api/lugal/email/webhook/notify',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def email_push_notify(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        # Validate shared secret
        cfg_secret = request.env['ir.config_parameter'].sudo().get_param(
            'lugal.email.webhook.token', ''
        ).strip()
        if not cfg_secret:
            return _json_response({'success': False, 'error': 'Webhook not configured'}, 401)

        incoming_token = (
            request.httprequest.headers.get('X-Lugal-Webhook-Token', '')
            or kwargs.get('token', '')
        ).strip()
        if incoming_token != cfg_secret:
            return _json_response({'success': False, 'error': 'Invalid token'}, 401)

        try:
            import json as _json_mod
            body_bytes = request.httprequest.get_data(cache=False)
            payload = {}
            if body_bytes:
                try:
                    payload = _json_mod.loads(body_bytes)
                except Exception:
                    pass

            email_addr = payload.get('email', '').strip().lower()
            account_id = payload.get('account_id')

            Acc = request.env['lugal.email.account'].sudo()
            if account_id:
                accs = Acc.browse(int(account_id)).filtered(
                    lambda a: a.exists() and (a.password or '').strip()
                )
            elif email_addr:
                accs = Acc.search([
                    ('email_address', '=ilike', email_addr),
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ])
            else:
                accs = Acc.search([
                    ('is_active', '=', True),
                    ('is_deleted', '=', False),
                ])

            synced = []
            for acc in accs:
                if not (acc.password or '').strip():
                    continue
                # Run synchronously inside this request's existing DB cursor —
                # no extra pool connections are opened, and the WS bus event
                # fires (and commits) before we return the response.
                try:
                    result = acc.action_sync()
                    request.env.cr.commit()
                    synced.append({
                        'account_id': acc.id,
                        'sync_ok': True,
                        'imported': (result or {}).get('imported', 0),
                    })
                except Exception as exc_inner:
                    _logger.exception('email_push_notify: sync failed for account %s', acc.id)
                    synced.append({'account_id': acc.id, 'sync_ok': False, 'error': str(exc_inner)})

            return _json_response({
                'success': True,
                'message': 'Sync complete',
                'accounts': synced,
            })
        except Exception as exc:
            _logger.exception('email_push_notify failed')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Messages / Mailbox ────────────────────────────────────────────────────

    @http.route([
        '/api/lugal/email/messages',
        '/api/lugal/email/mailbox/inbox',
        '/api/lugal/email/mailbox/<string:folder_name>',
    ], type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def messages_list(self, folder_name='inbox', **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            params      = request.httprequest.args
            folder      = params.get('folder', folder_name) or 'inbox'
            account_id  = params.get('account_id')
            query       = params.get('query', '').strip()
            starred     = params.get('starred')
            linked_model = params.get('linked_model')
            linked_id   = params.get('linked_id')
            limit       = int(params.get('limit', 50))
            offset      = int(params.get('offset', 0))
            auto_sync   = params.get('auto_sync', '1') != '0'
            force_sync  = params.get('force_sync', '0') == '1'

            # scope to this user's accounts
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            # Kick off IMAP sync if the account is stale, then wait up to 7 seconds
            # for it to complete before serving data.  Batch IMAP fetch means a typical
            # sync of ~150 messages finishes in 2-4 s.  If the server is unusually slow
            # we fall through and return whatever is already cached in the DB.
            if auto_sync and folder == 'inbox':
                db_name = request.env.cr.dbname
                sync_threads = []
                for acc in user_accounts:
                    try:
                        if _needs_imap_sync(acc, force=force_sync):
                            t = _run_imap_sync_bg(acc.id, db_name)
                            if t:
                                sync_threads.append(t)
                    except Exception:
                        _logger.exception('mailbox auto-sync kick failed for account %s', acc.id)
                # Wait for all kicked syncs to finish (or time out)
                for t in sync_threads:
                    t.join(timeout=7.0)

            domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
                ('folder', '=', folder),
            ]
            if account_id:
                domain.append(('account_id', '=', int(account_id)))
            if query:
                domain += ['|', ('subject', 'ilike', query), ('body_text', 'ilike', query)]
            if starred:
                domain.append(('is_starred', '=', True))
            if linked_model and linked_id:
                domain += [('linked_model', '=', linked_model), ('linked_record_id', '=', int(linked_id))]

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            msgs  = Msg.search(domain, limit=limit, offset=offset, order='date desc')

            return _json_response({
                'success': True,
                'data': {
                    'folder':  folder,
                    'total':   total,
                    'limit':   limit,
                    'offset':  offset,
                    'items':   [_message_to_dict(m) for m in msgs],
                },
            })
        except Exception as exc:
            _logger.exception('messages_list error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'DELETE', 'OPTIONS'])
    def message_detail(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            if request.httprequest.method == 'DELETE':
                prev_folder = msg.folder
                msg.write({'folder': 'trash'})
                # Push move to IMAP server (fire-and-forget)
                if msg.imap_uid:
                    imap_from = 'INBOX' if prev_folder == 'inbox' else prev_folder.upper()
                    msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'trash')
                return _json_response({'success': True})
            # Lazy-fetch full body if this message was imported headers-only.
            if msg.folder == 'inbox' and not msg.body_fetched and msg.imap_uid:
                try:
                    msg.account_id.sudo().fetch_message_body(msg.id)
                    msg.invalidate_recordset()  # reload from DB
                except Exception:
                    _logger.exception('Lazy body fetch failed for message %s', msg.id)
            # Auto mark as read on GET
            if not msg.is_read:
                msg.write({'is_read': True})
                # Push \Seen flag to IMAP server
                if msg.imap_uid and msg.folder == 'inbox':
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, 'INBOX', add_flags=['\\Seen']
                    )
                # Decrement unread counter
                if msg.folder == 'inbox':
                    msg.account_id.sudo().write({
                        'unread_count': max(0, msg.account_id.unread_count - 1)
                    })
            return _json_response({'success': True, 'data': _message_to_dict(msg, full=True)})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/details', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def message_details_bulk(self, **kwargs):
        """Return full body + attachments for a batch of message IDs in one call.

        Request body (JSON):
          { "message_ids": [1337, 1338, 1339] }   — max 50 IDs per call.

        Response:
          {
            "success": true,
            "data": {
              "items": [
                { "id": 1337, "body_html": "...", "body_text": "...", "attachments": [] }
              ],
              "missing_ids": [1339]   // IDs not found / not owned by caller / deleted
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            message_ids = body.get('message_ids')
            if not isinstance(message_ids, list) or not message_ids:
                return _json_response(
                    {'success': False, 'error': 'message_ids must be a non-empty array'},
                    400,
                )
            if len(message_ids) > 50:
                return _json_response(
                    {'success': False, 'error': 'message_ids may not exceed 50 items per request'},
                    400,
                )
            if not all(isinstance(i, int) for i in message_ids):
                return _json_response(
                    {'success': False, 'error': 'message_ids must be an array of integers'},
                    400,
                )

            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            Msg  = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids).filtered(
                lambda m: m.exists() and not m.is_deleted and m.account_id.id in account_ids
            )
            found_ids = set(msgs.ids)
            missing_ids = [i for i in message_ids if i not in found_ids]

            # Lazy-fetch bodies that were imported as headers-only
            for msg in msgs:
                if msg.folder == 'inbox' and not msg.body_fetched and msg.imap_uid:
                    try:
                        msg.account_id.sudo().fetch_message_body(msg.id)
                        msg.invalidate_recordset()
                    except Exception:
                        _logger.exception('Bulk lazy body fetch failed for message %s', msg.id)

            items = []
            for msg in msgs:
                items.append({
                    'id':          msg.id,
                    'body_html':   msg.body_html or '',
                    'body_text':   msg.body_text or '',
                    'attachments': [],
                })

            return _json_response({
                'success': True,
                'data': {
                    'items':       items,
                    'missing_ids': missing_ids,
                },
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('message_details_bulk error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Notifications & Unread ────────────────────────────────────────────────

    @http.route(['/api/lugal/email/notifications', '/api/lugal/email/unread'],
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def notifications(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            params = request.httprequest.args
            # Optional ISO datetime: only return new_messages received after this timestamp.
            # Pass the `data.checked_at` value from the previous poll response.
            since_str = params.get('since', '')

            accs = _get_user_accounts(uid)
            per_account = []
            total_unread = 0
            for acc in accs:
                # Count unread inbox messages from DB (source of truth)
                unread = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', '=', acc.id),
                    ('folder', '=', 'inbox'),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])
                total_unread += unread
                per_account.append({
                    'id':           acc.id,
                    'name':         acc.name,
                    'unread_count': unread,
                    'sync_status':  acc.sync_status or 'never',
                    'last_sync_date': _to_riyadh_iso(acc.last_sync_date),
                })

            # Per-folder unread totals across all accounts
            account_ids = accs.ids
            per_folder = {}
            for folder in ('inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'):
                per_folder[folder] = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', 'in', account_ids),
                    ('folder', '=', folder),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ])

            last_sync = None
            if accs:
                dates = [a.last_sync_date for a in accs if a.last_sync_date]
                if dates:
                    last_sync = _to_riyadh_iso(max(dates))

            Msg = request.env['lugal.email.message'].sudo()

            # ── New inbox messages (for browser/in-app notifications) ──────────
            # Returns up to 10 most recent UNREAD inbox messages.
            # If `?since=<ISO datetime>` is supplied only messages received after
            # that timestamp are returned, so the FE can detect new arrivals
            # without comparing counts.
            new_msg_domain = [
                ('account_id', 'in', account_ids),
                ('folder', '=', 'inbox'),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ]
            if since_str:
                try:
                    from odoo.fields import Datetime as OdooDatetime
                    since_dt = OdooDatetime.from_string(since_str.replace('T', ' ')[:19])
                    new_msg_domain.append(('date', '>', since_dt))
                except Exception:
                    pass  # ignore bad since value
            new_inbox = Msg.search(new_msg_domain, order='date desc', limit=10)
            new_messages = [
                {
                    'id':           m.id,
                    'account_id':   m.account_id.id,
                    'account_name': m.account_id.name or m.account_id.email_address,
                    'subject':      m.subject or '(no subject)',
                    'from_name':    m.from_name or '',
                    'from_address': m.from_address or '',
                    'date':         _to_riyadh_iso(m.date),
                    'is_read':      m.is_read,
                }
                for m in new_inbox
            ]

            # ── Recently sent messages and their SMTP delivery status ──────────
            # FE polls this to show ✓ (sent) / ✓✓ (delivered) indicators.
            recent_sent = Msg.search([
                ('account_id', 'in', account_ids),
                ('folder', '=', 'sent'),
                ('is_deleted', '=', False),
            ], order='date desc', limit=20)
            sent_status = [
                {
                    'id':             m.id,
                    'subject':        m.subject or '',
                    'date':           _to_riyadh_iso(m.date),
                    'to_addresses':   m.to_addresses or '[]',
                    'smtp_delivered': m.smtp_delivered,
                    'smtp_error':     m.smtp_error or None,
                }
                for m in recent_sent
            ]

            from datetime import datetime as _nowdt
            return _json_response({
                'success': True,
                'data': {
                    'inbox':              per_folder.get('inbox', 0),
                    'total':              total_unread,
                    'per_folder':         per_folder,
                    'account_configured': bool(accs),
                    'accounts':           per_account,
                    'sync_status':        accs[0].sync_status if accs else 'never',
                    'last_sync_date':     last_sync,
                    # Use this value as the `?since=` param on your next poll.
                    'checked_at':         _nowdt.now(tz=_RIYADH_TZ).strftime('%Y-%m-%dT%H:%M:%S+03:00'),
                    'new_messages':       new_messages,
                    'recently_sent':      sent_status,
                },
            })
        except Exception as exc:
            _logger.exception('notifications error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Compose: Send / Reply / Forward ──────────────────────────────────────

    @http.route('/api/lugal/email/send', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def send_email(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            account_id = body.get('account_id')
            to         = body.get('to', [])
            if isinstance(to, str):
                to = [to]
            # Normalize: FE may send [{"email": "..."}, ...] or ["email@...", ...]
            to_emails  = _norm_addr_list(to)
            subject    = body.get('subject', '')
            body_html  = body.get('body_html', body.get('body', ''))
            body_text  = body.get('body_text', '')
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))

            if not to_emails:
                return _json_response({'success': False, 'error': "'to' is required"}, 400)

            attachment_ids = body.get('attachment_ids', [])

            # Resolve account
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _not_found('Email account not found')
            else:
                accs = _get_user_accounts(uid).filtered('is_default')
                acc  = accs[0] if accs else _get_user_accounts(uid)[:1]
                if not acc:
                    return _json_response({'success': False, 'error': 'No email account configured'}, 400)

            # Store in sent folder
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':   acc.id,
                'folder':       'sent',
                'subject':      subject,
                'from_name':    acc.display_name_field or acc.email_address,
                'from_address': acc.email_address,
                'to_addresses': json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses': json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':    body_html,
                'body_text':    body_text,
                'is_read':      True,
                'body_fetched': True,
                'date':         __import__('odoo').fields.Datetime.now(),
            })

            delivered, smtp_error, refused = _send_via_smtp(
                acc, to_emails, subject, body_html, body_text, cc_emails, bcc_emails,
                msg_id=msg.id, attachment_ids=attachment_ids,
            )

            # Update delivery status in the same transaction so the FE sees it immediately.
            msg.write({
                'smtp_delivered': delivered and not refused,
                'smtp_error':     smtp_error or False,
            })

            # All recipients were rejected immediately → remove from sent, return error
            if refused and not delivered:
                msg.sudo().unlink()
                return _json_response({
                    'success': False,
                    'error':   smtp_error,
                    'code':    'recipient_not_found',
                }, 422)

            resp_data = _message_to_dict(msg)
            if smtp_error:
                resp_data['smtp_warning'] = smtp_error
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            _logger.exception('send_email error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/reply', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def reply(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()
            body    = json.loads(request.httprequest.data or '{}')
            acc     = orig.account_id
            to      = [orig.from_address] if orig.from_address else []
            subject = (orig.subject or '') if (orig.subject or '').startswith('Re:') \
                      else f"Re: {orig.subject or ''}"
            vals = {
                'account_id':   acc.id,
                'folder':       'sent',
                'subject':      subject,
                'from_name':    acc.display_name_field or acc.email_address,
                'from_address': acc.email_address,
                'to_addresses': json.dumps([{'email': e} for e in to]),
                'cc_addresses': json.dumps([{'email': e} for e in _norm_addr_list(body.get('cc', []))]),
                'bcc_addresses': json.dumps([{'email': e} for e in _norm_addr_list(body.get('bcc', []))]),
                'in_reply_to':  orig.message_id or '',
                'body_html':    body.get('body_html', ''),
                'body_text':    body.get('body_text', ''),
                'is_read':      True,
                'body_fetched': True,
                'date':         __import__('odoo').fields.Datetime.now(),
            }
            if orig.linked_customer_id:
                vals['linked_customer_id'] = orig.linked_customer_id
            if orig.linked_ticket_id:
                vals['linked_ticket_id'] = orig.linked_ticket_id
            msg = request.env['lugal.email.message'].sudo().create(vals)
            attachment_ids = body.get('attachment_ids', [])
            delivered, smtp_error, refused = _send_via_smtp(
                acc, to, subject, body.get('body_html', ''), body.get('body_text', ''),
                msg_id=msg.id, attachment_ids=attachment_ids,
            )
            msg.write({
                'smtp_delivered': delivered and not refused,
                'smtp_error':     smtp_error or False,
            })
            if refused and not delivered:
                msg.sudo().unlink()
                return _json_response({
                    'success': False,
                    'error':   smtp_error,
                    'code':    'recipient_not_found',
                }, 422)
            resp_data = _message_to_dict(msg)
            if smtp_error:
                resp_data['smtp_warning'] = smtp_error
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/forward', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def forward(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()
            body    = json.loads(request.httprequest.data or '{}')
            acc     = orig.account_id
            to      = body.get('to', [])
            to_fwd   = _norm_addr_list(to)
            cc_fwd   = _norm_addr_list(body.get('cc', []))
            bcc_fwd  = _norm_addr_list(body.get('bcc', []))
            subject = f"Fwd: {orig.subject or ''}"
            fwd_body = body.get('body_html', '') + (orig.body_html or '')
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':    acc.id,
                'folder':        'sent',
                'subject':       subject,
                'from_name':     acc.display_name_field or acc.email_address,
                'from_address':  acc.email_address,
                'to_addresses':  json.dumps([{'email': e} for e in to_fwd]),
                'cc_addresses':  json.dumps([{'email': e} for e in cc_fwd]),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_fwd]),
                'body_html':     fwd_body,
                'body_text':     body.get('body_text', ''),
                'is_read':       True,
                'body_fetched':  True,
                'date':          __import__('odoo').fields.Datetime.now(),
            })
            delivered, smtp_error, refused = _send_via_smtp(
                acc, to_fwd, subject, fwd_body, body.get('body_text', ''),
                cc=cc_fwd, bcc=bcc_fwd,
                msg_id=msg.id, attachment_ids=body.get('attachment_ids', []),
            )
            msg.write({
                'smtp_delivered': delivered and not refused,
                'smtp_error':     smtp_error or False,
            })
            if refused and not delivered:
                msg.sudo().unlink()
                return _json_response({
                    'success': False,
                    'error':   smtp_error,
                    'code':    'recipient_not_found',
                }, 422)
            resp_data = _message_to_dict(msg)
            if smtp_error:
                resp_data['smtp_warning'] = smtp_error
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Status Actions ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/read', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def toggle_read(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg  = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            body     = json.loads(request.httprequest.data or '{}')
            is_read  = body.get('is_read', True)
            msg.write({'is_read': is_read})
            # Push \Seen / -\Seen flag to IMAP server
            if msg.imap_uid:
                imap_folder = 'INBOX' if msg.folder == 'inbox' else msg.folder.upper()
                if is_read:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Seen']
                    )
                else:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, remove_flags=['\\Seen']
                    )
            return _json_response({'success': True, 'data': {
                'is_read': is_read,
                'read_at': _to_riyadh_iso(msg.read_at) if msg.read_at else None,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/star', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def toggle_star(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            new_starred = not msg.is_starred
            msg.write({'is_starred': new_starred})
            # Push \Flagged / -\Flagged to IMAP server
            if msg.imap_uid:
                imap_folder = 'INBOX' if msg.folder == 'inbox' else msg.folder.upper()
                if new_starred:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Flagged']
                    )
                else:
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, remove_flags=['\\Flagged']
                    )
            return _json_response({'success': True, 'data': {'is_starred': msg.is_starred}})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/restore', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def restore(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            prev_folder = msg.folder
            msg.write({'folder': 'inbox'})
            # Move back to INBOX on the IMAP server
            if msg.imap_uid:
                imap_from = 'INBOX' if prev_folder == 'inbox' else prev_folder.upper()
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'inbox')
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/archive', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def archive_msg(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            prev_folder = msg.folder
            msg.write({'folder': 'archive'})
            # Move to Archive folder on the IMAP server
            if msg.imap_uid:
                imap_from = 'INBOX' if prev_folder == 'inbox' else prev_folder.upper()
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'archive')
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/permanent', type='http', auth='none', csrf=False,
                methods=['DELETE', 'OPTIONS'])
    def message_permanent_delete(self, message_id, **kwargs):
        """Hard-delete a single message from the DB.

        The message MUST be in the 'trash' folder; attempting to permanently
        delete a message that is still in any other folder returns 409 so the
        FE can show a "move to trash first" hint.

        On success the record is gone from the DB — no recovery possible.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            if msg.folder != 'trash':
                return _json_response(
                    {'success': False, 'error': 'Message must be in trash before permanent deletion'},
                    409,
                )
            imap_uid = msg.imap_uid
            acc      = msg.account_id.sudo()
            msg.sudo().unlink()
            # Expunge from IMAP Trash folder so webmail also removes it permanently
            if imap_uid:
                trash_folder = acc._get_server_folder_name('trash')
                acc._imap_expunge_async(imap_uid, trash_folder)
            return _json_response({'success': True, 'deleted_id': message_id})
        except Exception as exc:
            _logger.exception('message_permanent_delete error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/bulk_delete', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def message_bulk_permanent_delete(self, **kwargs):
        """Hard-delete multiple messages in one call.

        All messages must be in the 'trash' folder and owned by the caller.
        Messages that are not in trash, not found, or belong to another user
        are silently skipped and reported in 'skipped_ids'.

        Request body (JSON):
          { "message_ids": [1, 2, 3] }   — max 50 IDs per call.

        Response:
          {
            "success": true,
            "data": {
              "deleted_ids": [1, 2],
              "skipped_ids": [3]
            }
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')
            message_ids = body.get('message_ids')
            if not isinstance(message_ids, list) or not message_ids:
                return _json_response(
                    {'success': False, 'error': 'message_ids must be a non-empty array'},
                    400,
                )
            if len(message_ids) > 50:
                return _json_response(
                    {'success': False, 'error': 'message_ids may not exceed 50 per request'},
                    400,
                )
            if not all(isinstance(i, int) for i in message_ids):
                return _json_response(
                    {'success': False, 'error': 'message_ids must be an array of integers'},
                    400,
                )

            user_account_ids = _get_user_accounts(uid).ids
            Msg = request.env['lugal.email.message'].sudo()
            msgs = Msg.browse(message_ids)

            to_delete = msgs.filtered(
                lambda m: m.exists()
                and not m.is_deleted
                and m.account_id.id in user_account_ids
                and m.folder == 'trash'
            )
            deleted_ids  = to_delete.ids
            skipped_ids  = [i for i in message_ids if i not in deleted_ids]
            to_delete.unlink()

            return _json_response({
                'success': True,
                'data': {
                    'deleted_ids': deleted_ids,
                    'skipped_ids': skipped_ids,
                },
            })
        except json.JSONDecodeError:
            return _json_response({'success': False, 'error': 'Invalid JSON body'}, 400)
        except Exception as exc:
            _logger.exception('message_bulk_permanent_delete error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Record Linking ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/link', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def link_message(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg  = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            body      = json.loads(request.httprequest.data or '{}')
            model     = body.get('model', '')
            record_id = body.get('record_id')
            if model not in ALLOWED_LINK_MODELS:
                return _json_response({'success': False, 'error': f'Model {model} not allowed'}, 400)
            vals = {
                'linked_model':       model,
                'linked_record_id':   record_id,
                'linked_record_name': body.get('record_name', ''),
            }
            if model == 'lugal.crm.customer':
                vals['linked_customer_id'] = record_id
                vals['linked_customer_name'] = body.get('record_name', '')
            elif model == 'lugal.crm.ticket':
                vals['linked_ticket_id'] = record_id
                vals['linked_ticket_name'] = body.get('record_name', '')
            msg.write(vals)
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/unlink', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def unlink_message(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            msg.write({
                'linked_model': False, 'linked_record_id': False,
                'linked_record_name': False,
                'linked_customer_id': False, 'linked_customer_name': False,
                'linked_ticket_id': False, 'linked_ticket_name': False,
            })
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)


    # ── Email attachment upload ────────────────────────────────────────────────

    @http.route('/api/lugal/email/attachments/upload', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def email_attachment_upload(self, **kwargs):
        """
        Multipart file upload for email compose.

        Form fields:
          - file | files | files[]  – one or more binary parts
          - account_id (optional)   – link attachment to this email account

        Response:
          {
            "success": true,
            "data": {
              "attachments": [
                { "id": 42, "name": "invoice.pdf", "mimetype": "application/pdf",
                  "size": 102400, "url": "/web/content/42?download=true" }
              ]
            }
          }

        Pass the returned "id" values in send/reply/forward as:
          { "attachment_ids": [42, 43] }
        """
        import base64
        import mimetypes as _mimetypes

        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        try:
            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json_response({'success': False, 'error': 'No files provided'}, 400)

            MAX_MB = 1024  # 1 GB
            max_bytes = MAX_MB * 1024 * 1024

            results = []
            Attachment = request.env['ir.attachment'].sudo()

            for f in files:
                data = f.read()
                if len(data) > max_bytes:
                    return _json_response(
                        {'success': False, 'error': f'{f.filename or "file"}: exceeds {MAX_MB} MB'},
                        400,
                    )
                mime = f.mimetype or _mimetypes.guess_type(f.filename or '')[0] or 'application/octet-stream'
                filename = f.filename or 'attachment'

                import uuid as _uuid
                att_token = _uuid.uuid4().hex
                att = Attachment.create({
                    'name': filename,
                    'mimetype': mime,
                    'datas': base64.b64encode(data).decode('utf-8'),
                    'type': 'binary',
                    'res_model': 'lugal.email.message',
                    'access_token': att_token,
                })
                att.flush_recordset(['access_token'])

                att_url = f"/web/content/{att.id}?access_token={att_token}"
                results.append({
                    'id': att.id,
                    'name': att.name or filename,
                    'mimetype': mime,
                    'size': len(data),
                    'url': att_url,
                    'file_url': att_url,
                })

            return _json_response({'success': True, 'data': {'attachments': results}})

        except Exception as exc:
            _logger.exception('email_attachment_upload')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _json_response({'success': False, 'error': str(exc)}, 500)


# ── SMTP helper ───────────────────────────────────────────────────────────────

_SMTP_RECIPIENT_ERROR_CODES = {
    550: 'Mailbox not found or recipient does not exist',
    551: 'User is not local',
    552: 'Mailbox storage quota exceeded',
    553: 'Mailbox name not allowed',
    554: 'Transaction failed / message rejected',
}


def _send_via_smtp(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                   msg_id=None, attachment_ids=None):
    """
    Send an email synchronously via SMTP.

    Returns a tuple:
        (delivered: bool, error_msg: str | None, refused: dict)

    - delivered=True, error_msg=None, refused={}  → all recipients accepted
    - delivered=False, refused={addr: (code, reason)}  → recipient(s) rejected by server
    - delivered=False, refused={}                 → connection / auth / other error

    Writes smtp_delivered / smtp_error back to lugal.email.message if msg_id given.
    Uses a 10-second SMTP timeout — fast on success and on immediate server rejections.

    attachment_ids: list of ir.attachment IDs to attach to the outgoing message.
    """
    import base64
    import smtplib
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.encoders import encode_base64
    from email.utils import formatdate, make_msgid

    smtp_host    = acc.smtp_host
    smtp_port    = acc.smtp_port
    smtp_use_tls = acc.smtp_use_tls
    username     = acc.username or acc.email_address
    password     = acc.password or ''
    from_address = acc.email_address
    display_name = (acc.display_name_field or '').strip()
    db_name      = acc.env.cr.dbname

    from_header = f'{display_name} <{from_address}>' if display_name else from_address

    # Resolve ir.attachment records
    att_records = []
    if attachment_ids:
        IrAtt = acc.env['ir.attachment'].sudo()
        for att_id in attachment_ids:
            att = IrAtt.browse(int(att_id)).exists()
            if att:
                att_records.append(att)

    if att_records:
        # mixed → contains alternative (text+html) + file parts
        mime_msg = MIMEMultipart('mixed')
        alt_part = MIMEMultipart('alternative')
        if body_text:
            alt_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
        if body_html:
            alt_part.attach(MIMEText(body_html, 'html', 'utf-8'))
        mime_msg.attach(alt_part)
        for att in att_records:
            try:
                data = base64.b64decode(att.datas or b'')
                mime_type = (att.mimetype or 'application/octet-stream').split('/')
                main_type = mime_type[0]
                sub_type = mime_type[1] if len(mime_type) > 1 else 'octet-stream'
                part = MIMEBase(main_type, sub_type)
                part.set_payload(data)
                encode_base64(part)
                filename = att.name or 'attachment'
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                mime_msg.attach(part)
            except Exception as att_exc:
                _logger.warning('Could not attach file %s: %s', att.name, att_exc)
    else:
        mime_msg = MIMEMultipart('alternative')
        if body_text:
            mime_msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        if body_html:
            mime_msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    mime_msg['Subject']    = subject
    mime_msg['From']       = from_header
    mime_msg['To']         = ', '.join(to_list)
    mime_msg['Date']       = formatdate(localtime=True)
    mime_msg['Message-ID'] = make_msgid(domain=from_address.split('@')[-1] if '@' in from_address else 'mail')
    if cc:
        mime_msg['Cc'] = ', '.join(cc)

    all_recipients = list(to_list) + list(cc or []) + list(bcc or [])
    raw_message    = mime_msg.as_string()

    delivered  = False
    error_msg  = None
    refused    = {}

    try:
        use_ssl = (not smtp_use_tls) or (smtp_port == 465)
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(username, password)

        # sendmail() returns a dict of per-recipient errors; raises
        # SMTPRecipientsRefused only when ALL recipients are rejected.
        partial_refused = server.sendmail(from_address, all_recipients, raw_message)
        server.quit()

        if partial_refused:
            # Some recipients accepted, some refused — still a partial delivery.
            delivered = True
            parts = []
            for addr, (code, reason) in partial_refused.items():
                hint = _SMTP_RECIPIENT_ERROR_CODES.get(code, 'Delivery failed')
                parts.append(f'{addr}: {hint} (code {code})')
            error_msg = 'Partial delivery — refused: ' + '; '.join(parts)
            refused   = partial_refused
        else:
            delivered = True

        _logger.info(
            'SMTP delivered: from=%s to=%s subject=%r host=%s:%s',
            from_address, all_recipients, subject, smtp_host, smtp_port,
        )

    except smtplib.SMTPRecipientsRefused as exc:
        refused = exc.recipients
        parts   = []
        for addr, (code, reason) in refused.items():
            if isinstance(reason, bytes):
                reason = reason.decode('utf-8', errors='replace')
            hint = _SMTP_RECIPIENT_ERROR_CODES.get(code, 'Delivery failed')
            parts.append(f'{addr}: {hint} (code {code})')
        error_msg = 'Recipient(s) not found or rejected: ' + '; '.join(parts)
        _logger.warning('SMTP rejected all recipients: %s', error_msg)

    except Exception as exc:
        error_msg = str(exc)
        _logger.error(
            'SMTP FAILED: from=%s to=%s host=%s:%s tls=%s error=%s',
            from_address, all_recipients, smtp_host, smtp_port, smtp_use_tls, exc,
        )

    # Write delivery result back to the stored message row (if we have one).
    # NOTE: This uses a separate cursor intentionally — in the "send" flow the
    # caller (HTTP handler) may not have committed yet, but in contexts where
    # msg_id is passed from an already-committed record this still works.
    # Callers should ALSO update the msg record via their own cursor post-call.
    if msg_id:
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                record = env['lugal.email.message'].browse(msg_id)
                if record.exists():
                    record.write({
                        'smtp_delivered': delivered and not refused,
                        'smtp_error':     error_msg or False,
                    })
        except Exception as write_exc:
            _logger.warning('Could not update smtp_delivered on msg %s: %s', msg_id, write_exc)

    return delivered, error_msg, refused
