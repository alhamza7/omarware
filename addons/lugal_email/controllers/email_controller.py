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
# Per-account lock: prevents the same account running two syncs simultaneously.
_sync_lock = threading.Lock()
_syncing_accounts: set = set()

# Per-credential lock: prevents multiple accounts sharing the same IMAP login
# (same imap_host + username) from opening concurrent IMAP connections.
# Without this lock, logging in with 15 accounts that share one IMAP username
# fires 15 simultaneous connections → server limit exceeded → IDLE crashes.
_cred_sync_lock = threading.Lock()
_syncing_credentials: set = set()   # set of (imap_host, imap_port, username)

# Throttle mirrors (kept here so the controller doesn't import from the model).
_IMAP_THROTTLE_SECONDS = 30        # min gap between syncs when inbox has messages
_IMAP_THROTTLE_EMPTY_SECONDS = 20  # min gap when inbox is empty


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


def _run_imap_sync_bg(acc_id, db_name, force=False):
    """
    Spawn a one-shot daemon thread to run IMAP inbox sync for a single account.

    Two-level de-duplication:
      1. Per account_id  — prevents the same account syncing twice in parallel.
      2. Per IMAP credential (host + username) — prevents multiple accounts that
         share one IMAP login from opening concurrent connections to the mail
         server, which would hit the server's max-connections-per-user limit and
         cause the IDLE watcher's persistent connection to be force-closed.

    force=True bypasses the 30-second throttle (use on login / WS connect).

    Returns the Thread object, or None if a sync is already running.
    """
    with _sync_lock:
        if acc_id in _syncing_accounts:
            return None
        _syncing_accounts.add(acc_id)

    def _do():
        cred_key = None
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                acc = env['lugal.email.account'].browse(acc_id)
                if not acc.exists() or not acc.is_active or not (acc.password or '').strip():
                    return

                # Build the credential key
                imap_host = (acc.imap_host or '').strip()
                imap_port = int(acc.imap_port or 993)
                username  = (acc.username or acc.email_address or '').strip()
                cred_key  = (imap_host, imap_port, username)

                # Credential-level check: skip if another sync is already open
                # for this IMAP username+server combination.
                with _cred_sync_lock:
                    if cred_key in _syncing_credentials:
                        _logger.debug(
                            'Skipping bg sync for acc %s — credential %s already syncing',
                            acc_id, cred_key,
                        )
                        cred_key = None  # don't discard it on exit — we didn't add it
                        return
                    _syncing_credentials.add(cred_key)

                if force:
                    acc.action_sync()
                else:
                    acc.action_sync_if_stale()

        except Exception:
            _logger.exception('Background IMAP sync failed account_id=%s', acc_id)
        finally:
            with _sync_lock:
                _syncing_accounts.discard(acc_id)
            if cred_key:
                with _cred_sync_lock:
                    _syncing_credentials.discard(cred_key)

    t = threading.Thread(target=_do, daemon=True, name=f'imap-bg-{acc_id}')
    t.start()
    return t


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_response(data, status=200):
    """Return a plain JSON HTTP response with permissive CORS headers.

    CORS headers are set unconditionally so any FE origin (any port, any host)
    can consume these endpoints without needing a dev-proxy workaround.
    """
    resp = Response(
        json.dumps(data, default=str),
        status=status,
        mimetype='application/json',
    )
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Odoo-Database'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    return resp


def _unauthorized():
    return _json_response({'success': False, 'error': 'Unauthorized'}, status=401)


def _not_found(msg='Not found'):
    return _json_response({'success': False, 'error': msg}, status=404)


def _imap_connect_with_retry(acc, attempts=3, delay=2.0):
    """Open an IMAP connection, retrying on connection-limit errors.

    The polling watcher holds persistent IMAP connections; when a folder
    management API call coincides with a sync, the server's
    mail_max_userip_connections limit may be briefly exceeded.
    Waiting a couple of seconds usually frees a slot.

    Returns the open connection on success, or None after all retries fail.
    """
    import time as _time
    last_exc = None
    for attempt in range(attempts):
        try:
            return acc._imap_connect()
        except Exception as exc:
            last_exc = exc
            err_lower = str(exc).lower()
            if any(kw in err_lower for kw in ('limit', 'maximum', 'too many', 'connection')):
                if attempt < attempts - 1:
                    _time.sleep(delay)
                    continue
            raise  # non-limit errors propagate immediately
    _logger.warning('_imap_connect_with_retry exhausted %d attempts: %s', attempts, last_exc)
    return None


def _resolve_imap_folder(account, local_folder):
    """Map a local folder label to the real IMAP server folder name.

    Uses the account's cached folder discovery so the result is correct for
    Gmail ('[Gmail]/Sent Mail'), Dovecot ('Sent'), cPanel ('INBOX.Sent'), etc.
    Falls back to a sensible default if discovery is unavailable.
    """
    if local_folder == 'inbox':
        return 'INBOX'
    try:
        return account.sudo()._get_server_folder_name(local_folder)
    except Exception:
        return local_folder.capitalize()


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
        'is_flagged':     msg.is_flagged,    # IMAP \Flagged — independent of is_starred
        'is_important':   msg.is_important,
        'is_draft':       msg.is_draft,
        'is_mentioned':   msg.is_mentioned,
        'message_size':   msg.message_size or 0,
        'smtp_delivered': msg.smtp_delivered,
        'smtp_error':     msg.smtp_error or None,
        'smtp_status':    msg.smtp_status or 'pending',
        'thread_id':      msg.thread_id or None,
        'in_reply_to':    msg.in_reply_to or None,
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket':   {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                        if msg.linked_ticket_id else None,
        },
    }
    # Split attachments into two distinct buckets:
    #   att_list        → files added via the paperclip/attachment UI (downloadable)
    #   inline_att_list → images pasted / drag-dropped / inserted / signature images
    #                     (embedded in the email body via Content-ID / CID)
    # The split marker is the `description` field: inline items are tagged
    # "__inline_cid__:<cid>" by the upload endpoint (for outgoing mail) or by
    # _store_imap_attachments (for incoming mail with Content-Disposition: inline).
    _CID_PREFIX = '__inline_cid__:'
    try:
        atts = msg.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', msg.id),
        ])

        def _att_entry(a):
            url = (
                f'/web/content/{a.id}?access_token={a.access_token}'
                if a.access_token
                else f'/web/content/{a.id}?download=true'
            )
            return {
                'id':       a.id,
                'name':     a.name or 'attachment',
                'mimetype': a.mimetype or 'application/octet-stream',
                'size':     a.file_size or 0,
                'url':      url,
            }

        att_list    = []
        inline_list = []
        for a in atts:
            desc = a.description or ''
            if desc.startswith(_CID_PREFIX):
                cid_value = desc[len(_CID_PREFIX):]
                entry = _att_entry(a)
                entry['cid'] = f'cid:{cid_value}'
                inline_list.append(entry)
            else:
                att_list.append(_att_entry(a))
    except Exception:
        att_list    = []
        inline_list = []

    # These counters are always in the response (list view needs them for icons)
    data['has_attachments']         = bool(att_list)
    data['attachment_count']        = len(att_list)
    data['has_inline_attachments']  = bool(inline_list)
    data['inline_attachment_count'] = len(inline_list)

    if full:
        data['body_html']          = msg.body_html or ''
        data['body_text']          = msg.body_text or ''
        data['body_fetched']       = bool(msg.body_fetched)
        data['attachments']        = att_list      # paperclip-added files only
        data['inline_attachments'] = inline_list   # pasted / dropped / inserted images
    return data


def _build_quoted_html(msg):
    """Return an HTML block with the original message quoted below the reply area."""
    date_str = _to_riyadh_iso(msg.date) or ''
    sender   = msg.from_name or msg.from_address or 'Unknown'
    addr     = msg.from_address or ''
    header   = (
        f'<div style="color:#555;font-size:0.9em;margin-top:16px;border-top:1px solid #e0e0e0;padding-top:8px;">'
        f'<b>On {date_str}, {sender}'
        f'{(" &lt;" + addr + "&gt;") if addr else ""} wrote:</b>'
        f'</div>'
    )
    original = msg.body_html or (msg.body_text or '').replace('\n', '<br>')
    return (
        f'<br><br>{header}'
        f'<blockquote style="margin:8px 0 0 8px;padding-left:12px;'
        f'border-left:3px solid #ccc;color:#333;">'
        f'{original}'
        f'</blockquote>'
    )


def _build_quoted_text(msg):
    """Return a plain-text block with the original message quoted (> prefix)."""
    date_str = _to_riyadh_iso(msg.date) or ''
    sender   = msg.from_name or msg.from_address or 'Unknown'
    addr     = msg.from_address or ''
    header   = f'On {date_str}, {sender}{(" <" + addr + ">") if addr else ""} wrote:'
    original = (msg.body_text or '').strip()
    quoted   = '\n'.join('> ' + line for line in original.splitlines()) if original else ''
    return f'\n\n{header}\n{quoted}'


def _thread_vals_for_reply(orig):
    """Return the thread_id / references / in_reply_to values for a reply or reply-all.

    Thread-ID is the root of the conversation — the very first message's
    Message-ID.  The References chain grows with each reply so email clients
    can reconstruct the full conversation tree.

    RFC 2822 rules:
    - in_reply_to  = Message-ID of the immediate parent
    - references   = parent.references + parent.message_id (space-joined)
    - thread_id    = first entry in the final references list (= root msg-id)
    """
    parent_msg_id  = (orig.message_id or '').strip()
    parent_refs    = (orig.references or '').strip()
    parent_tid     = (orig.thread_id or '').strip()

    # Build the new References chain
    if parent_refs:
        new_refs = f'{parent_refs} {parent_msg_id}'.strip() if parent_msg_id else parent_refs
    elif parent_msg_id:
        new_refs = parent_msg_id
    else:
        new_refs = ''

    # thread_id is inherited from the parent, falling back to the parent's
    # own Message-ID (making it the implicit root).
    new_thread_id = parent_tid or parent_msg_id or ''

    return {
        'in_reply_to': parent_msg_id or False,
        'references':  new_refs or False,
        'thread_id':   new_thread_id or False,
    }


def _thread_vals_for_forward(orig):
    """Return thread values for a forward.

    Forwards start a NEW thread in the recipient's mailbox — the forward
    itself is the root.  The original thread_id is NOT propagated.
    We still carry a References header pointing to the original so that
    mail servers can link them loosely.
    """
    parent_msg_id = (orig.message_id or '').strip()
    new_refs      = parent_msg_id if parent_msg_id else ''
    return {
        'in_reply_to': parent_msg_id or False,
        'references':  new_refs or False,
        'thread_id':   False,   # will be set to the new message's own Message-ID after create
    }


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

    # ── Manual Force-Sync ─────────────────────────────────────────────────────
    #
    # FE can call this endpoint to immediately (re)sync one or all of the
    # logged-in user's email accounts.  Runs synchronously and waits for
    # completion so the response already contains the fresh message counts.
    #
    # POST /api/lugal/email/sync
    # Body (JSON, all optional):
    #   { "account_id": 55 }     // sync a specific account
    #   {}                       // sync all of this user's accounts
    #
    # Response:
    #   { "success": true, "accounts": [{ "id":55, "sync_ok":true, "imported":12,
    #     "unread":5, "sync_status":"ok", "sync_error": null }] }

    @http.route('/api/lugal/email/sync',
                type='http', auth='none', csrf=False, methods=['GET', 'POST', 'OPTIONS'])
    def force_sync(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})

        # GET /api/lugal/email/sync?account_id=&folder=&limit=&offset= →
        # acts as an alias for GET /api/lugal/email/messages with the same params.
        # Some FE builds use /sync as the message-list endpoint.
        if request.httprequest.method == 'GET':
            return self.messages_list(**kwargs)
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = {}
            raw = request.httprequest.get_data(cache=False)
            if raw:
                try:
                    body = json.loads(raw)
                except Exception:
                    pass

            account_id = body.get('account_id')
            Acc = request.env['lugal.email.account'].sudo()

            if account_id:
                accs = Acc.browse(int(account_id))
                if not accs.exists() or accs.user_id.id != uid:
                    return _not_found('Email account not found')
            else:
                accs = _get_user_accounts(uid)

            if not accs:
                return _json_response({'success': False, 'error': 'No email accounts configured'}, 400)

            results = []
            for acc in accs:
                if not (acc.password or '').strip():
                    results.append({
                        'id':          acc.id,
                        'sync_ok':     False,
                        'error':       'No app password configured on this account',
                        'sync_status': acc.sync_status or 'never',
                        'imported':    0,
                        'unread':      0,
                    })
                    continue

                try:
                    sync_result = acc.action_sync()
                    request.env.cr.commit()
                    unread = request.env['lugal.email.message'].sudo().search_count([
                        ('account_id', '=', acc.id),
                        ('folder', '=', 'inbox'),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ])
                    results.append({
                        'id':          acc.id,
                        'name':        acc.name,
                        'email':       acc.email_address,
                        'sync_ok':     (sync_result or {}).get('sync_status') == 'ok',
                        'imported':    (sync_result or {}).get('imported', 0),
                        'unread':      unread,
                        'sync_status': acc.sync_status or 'never',
                        'sync_error':  acc.sync_error_msg or None,
                    })
                except Exception as exc:
                    _logger.exception('force_sync failed for account %s', acc.id)
                    results.append({
                        'id':          acc.id,
                        'sync_ok':     False,
                        'error':       str(exc),
                        'sync_status': 'error',
                        'imported':    0,
                        'unread':      0,
                    })

            return _json_response({'success': True, 'accounts': results})
        except Exception as exc:
            _logger.exception('force_sync endpoint error')
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
            folder_raw  = (params.get('folder', folder_name) or 'inbox').strip()
            folder_q    = folder_raw   # canonical path for DB queries (may change after IMAP resolve)
            account_id  = params.get('account_id')
            query       = params.get('query', '').strip()
            starred     = params.get('starred')
            linked_model = params.get('linked_model')
            linked_id   = params.get('linked_id')
            limit       = int(params.get('limit', 50))
            offset      = int(params.get('offset', 0))
            auto_sync   = params.get('auto_sync', '1') != '0'
            force_sync  = params.get('force_sync', '0') == '1'
            # since_id: when provided, NEW messages (id > since_id) are fetched
            # first and prepended before the paginated list.  Use this after
            # receiving a crm.email.message.new WS event to guarantee the newly
            # arrived email appears at the top even if its Date header is old.
            since_id    = int(params.get('since_id', 0) or 0)

            # Optional server-side filter params
            filter_unread         = params.get('unread')
            filter_flagged        = params.get('flagged')
            filter_important      = params.get('important')
            filter_has_attachment = params.get('has_attachments')
            filter_mentioned      = params.get('mentioned')
            filter_sent_to_me     = params.get('sent_to_me')

            # scope to this user's accounts
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            _LOGICAL_MAILBOX = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            is_custom_mailbox = folder_raw.lower() not in _LOGICAL_MAILBOX
            imap_folder_sync = None

            # Kick off IMAP sync if the account is stale, then wait for completion.
            # For accounts that have NEVER been synced (sync_status='never') we use
            # force=True and a longer 15-second timeout so the first inbox load
            # always shows real emails rather than an empty list.
            # For routine syncs a 7-second timeout is sufficient.
            if auto_sync and folder_raw == 'inbox':
                db_name = request.env.cr.dbname
                sync_threads = []
                has_never_synced = False
                for acc in user_accounts:
                    try:
                        acc_never = not acc.last_sync_date or acc.sync_status == 'never'
                        effective_force = force_sync or acc_never
                        if effective_force or _needs_imap_sync(acc, force=False):
                            t = _run_imap_sync_bg(acc.id, db_name, force=effective_force)
                            if t:
                                sync_threads.append(t)
                                if acc_never:
                                    has_never_synced = True
                                    _logger.info(
                                        'mailbox: first-time sync triggered for account %s',
                                        acc.id,
                                    )
                    except Exception:
                        _logger.exception('mailbox auto-sync kick failed for account %s', acc.id)
                # Wait longer for first-time syncs (cold start from mail server).
                wait_secs = 15.0 if has_never_synced else 7.0
                for t in sync_threads:
                    t.join(timeout=wait_secs)

            # User-created IMAP folders (rule destinations) are not part of action_sync
            # (INBOX+Sent only).  Pull them on-demand so list/sync APIs return messages.
            if auto_sync and is_custom_mailbox:
                imap_folder_sync = []
                try:
                    aid = int(str(account_id).strip()) if account_id else None
                except (TypeError, ValueError):
                    aid = None
                targets = user_accounts.filtered(lambda a: a.id == aid) if aid else user_accounts
                for acc in targets:
                    if not (acc.password or '').strip():
                        imap_folder_sync.append({
                            'account_id': acc.id,
                            'imported': 0,
                            'error': 'no password',
                            'resolved_path': folder_raw,
                        })
                        continue
                    try:
                        res = acc.sudo().sync_custom_imap_folder(folder_raw)
                        imap_folder_sync.append({'account_id': acc.id, **res})
                        if res.get('resolved_path'):
                            folder_q = res['resolved_path']
                    except Exception:
                        _logger.exception(
                            'mailbox custom-folder sync failed acc=%s folder=%s',
                            acc.id, folder_raw,
                        )
                        imap_folder_sync.append({
                            'account_id': acc.id,
                            'imported': 0,
                            'error': 'exception',
                            'resolved_path': folder_raw,
                        })

            base_domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
                ('folder', '=', folder_q),
            ]
            if account_id:
                base_domain.append(('account_id', '=', int(account_id)))
            if query:
                base_domain += ['|', ('subject', 'ilike', query), ('body_text', 'ilike', query)]
            if starred:
                base_domain.append(('is_starred', '=', True))
            if linked_model and linked_id:
                base_domain += [('linked_model', '=', linked_model), ('linked_record_id', '=', int(linked_id))]

            # Optional server-side filters
            if filter_unread == '1':
                base_domain.append(('is_read', '=', False))
            if filter_flagged == '1':
                base_domain.append(('is_starred', '=', True))
            if filter_important == '1':
                base_domain.append(('is_important', '=', True))
            if filter_mentioned == '1':
                base_domain.append(('is_mentioned', '=', True))
            if filter_has_attachment == '1':
                att_msg_ids = request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'lugal.email.message'),
                ]).mapped('res_id')
                base_domain.append(('id', 'in', att_msg_ids))
            if filter_sent_to_me == '1':
                user_emails = [a.email_address for a in user_accounts if a.email_address]
                if user_emails:
                    to_clauses = [('to_addresses', 'ilike', e) for e in user_emails]
                    if len(to_clauses) == 1:
                        base_domain += to_clauses
                    else:
                        or_clause = ['|'] * (len(to_clauses) - 1) + to_clauses
                        base_domain += or_clause

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(base_domain)

            # Sort by create_date desc (when Odoo stored the message) then id desc.
            # Using create_date instead of the email Date header avoids future-dated
            # messages (mail servers with wrong clocks) from appearing above genuinely
            # newer messages that arrived later.
            sort_order = 'create_date desc, id desc'

            new_msgs = Msg.browse()
            if since_id:
                # When since_id is provided we intentionally search across ALL of
                # the user's accounts, ignoring any ?account_id= filter, so that
                # a new message for account A is still returned even when the
                # caller currently has account B selected.  The regular paginated
                # list still respects the account_id filter.
                all_accs_domain = [
                    ('account_id', 'in', account_ids),
                    ('is_deleted', '=', False),
                    ('folder',     '=', folder_q),
                    ('id',         '>',  since_id),
                ]
                new_msgs = Msg.search(all_accs_domain, order='id desc')

            page_msgs = Msg.search(base_domain, limit=limit, offset=offset, order=sort_order)

            if new_msgs:
                new_ids  = set(new_msgs.ids)
                # New messages pinned at top; de-duplicate from paginated list
                combined = list(new_msgs) + [m for m in page_msgs if m.id not in new_ids]
                items = [_message_to_dict(m) for m in combined[:limit]]
            else:
                items = [_message_to_dict(m) for m in page_msgs]

            # Include the highest message ID across all user accounts so the FE
            # can poll with ?since_id=<max_id> to discover newly arrived messages
            # regardless of which account_id filter is active.
            all_max = Msg.search([
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
                ('folder',     '=', folder_q),
            ], order='id desc', limit=1)
            max_id = all_max[0].id if all_max else 0

            return _json_response({
                'success': True,
                'data': {
                    'folder':           folder_q,
                    'total':            total,
                    'limit':            limit,
                    'offset':           offset,
                    'max_id':           max_id,
                    'items':            items,
                    'imap_folder_sync': imap_folder_sync,
                },
            })
        except Exception as exc:
            _logger.exception('messages_list error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PATCH', 'DELETE', 'OPTIONS'])
    def message_detail(self, message_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        # ?preview=true → return message data without marking it as read.
        # Used by notification handlers that need the payload without side-effects.
        preview_mode = str(kwargs.get('preview', '')).lower() in ('1', 'true', 'yes')
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found()
            if request.httprequest.method == 'PATCH':
                body = json.loads(request.httprequest.data or '{}')
                vals = {}
                imap_uid    = msg.imap_uid
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)

                if 'is_flagged' in body:
                    is_flagged = bool(body['is_flagged'])
                    vals['is_flagged'] = is_flagged   # independent field from is_starred
                    if imap_uid:
                        if is_flagged:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, add_flags=['\\Flagged']
                            )
                        else:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, remove_flags=['\\Flagged']
                            )

                if 'is_starred' in body:
                    vals['is_starred'] = bool(body['is_starred'])

                if 'is_important' in body:
                    vals['is_important'] = bool(body['is_important'])

                if 'is_read' in body:
                    is_read = bool(body['is_read'])
                    vals['is_read'] = is_read
                    if is_read and not msg.read_at:
                        from datetime import datetime
                        vals['read_at'] = datetime.utcnow()
                    if imap_uid:
                        if is_read:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, add_flags=['\\Seen']
                            )
                        else:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, remove_flags=['\\Seen']
                            )

                if not vals:
                    return _json_response(
                        {'success': False, 'error': 'Provide at least one of: is_flagged, is_starred, is_important, is_read'},
                        400,
                    )
                msg.write(vals)
                return _json_response({'success': True, 'data': _message_to_dict(msg)})

            if request.httprequest.method == 'DELETE':
                prev_folder = msg.folder
                msg.write({'folder': 'trash'})
                # Push move to IMAP server (fire-and-forget)
                if msg.imap_uid:
                    imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                    msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'trash')
                return _json_response({'success': True})
            # Lazy-fetch full body if this message was imported headers-only.
            if not msg.body_fetched and msg.imap_uid:
                try:
                    msg.account_id.sudo().fetch_message_body(msg.id)
                    msg.invalidate_recordset()  # reload from DB
                except Exception:
                    _logger.exception('Lazy body fetch failed for message %s', msg.id)
            # GET does NOT auto-mark as read.
            # To mark a message as read, use: POST /api/lugal/email/messages/<id>/read
            return _json_response({'success': True, 'data': _message_to_dict(msg, full=True)})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/thread', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def message_thread(self, message_id, **kwargs):
        """Return all messages in the same email thread, ordered oldest → newest.

        A thread is the full conversation: the original email plus all replies,
        reply-alls that share the same root Message-ID (thread_id).

        The requesting message itself is always included.  Messages from all
        folders (inbox, sent) are included so the user sees both sides of the
        conversation.  Deleted messages are excluded.

        Query params:
          include_body=1   — include body_html / body_text for each message
                             (default: 0, returns headers only to keep response small)
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            anchor = request.env['lugal.email.message'].sudo().browse(message_id)
            if not anchor.exists() or anchor.account_id.user_id.id != uid:
                return _not_found()

            thread_id = anchor.thread_id or anchor.message_id
            account_ids = _get_user_accounts(uid).ids
            include_body = request.httprequest.args.get('include_body', '0') == '1'

            Msg = request.env['lugal.email.message'].sudo()
            if thread_id:
                thread_msgs = Msg.search([
                    ('account_id', 'in', account_ids),
                    ('is_deleted', '=', False),
                    ('thread_id',  '=', thread_id),
                ], order='date asc, id asc')
            else:
                # Fallback: no thread_id — return just this message
                thread_msgs = anchor

            # Always ensure the anchor itself is in the list even if thread_id is missing
            if anchor.id not in thread_msgs.ids:
                thread_msgs = anchor | thread_msgs

            items = [_message_to_dict(m, full=include_body) for m in thread_msgs]
            return _json_response({
                'success': True,
                'data': {
                    'thread_id':    thread_id or None,
                    'total':        len(items),
                    'messages':     items,
                },
            })
        except Exception as exc:
            _logger.exception('message_thread error')
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

            # If we have missing IDs it likely means the inbox hasn't synced yet.
            # Kick off a background sync for every account that is overdue so
            # subsequent requests pick up the messages. Non-blocking / non-fatal.
            if missing_ids:
                try:
                    db_name = request.env.cr.dbname
                    for acc in user_accounts:
                        if (acc.password or '').strip() and _needs_imap_sync(acc):
                            _run_imap_sync_bg(acc.id, db_name)
                except Exception:
                    pass

            # Lazy-fetch bodies that were imported as headers-only (any folder)
            for msg in msgs:
                if not msg.body_fetched and msg.imap_uid:
                    try:
                        msg.account_id.sudo().fetch_message_body(msg.id)
                        msg.invalidate_recordset()
                    except Exception:
                        _logger.exception('Bulk lazy body fetch failed for message %s', msg.id)

            # Pre-fetch all attachments for the batch in one SQL query
            msg_ids_found = list(found_ids)
            IrAtt = request.env['ir.attachment'].sudo()
            all_atts = IrAtt.search([
                ('res_model', '=', 'lugal.email.message'),
                ('res_id',    'in', msg_ids_found),
            ])
            att_by_msg: dict = {}
            for a in all_atts:
                att_by_msg.setdefault(a.res_id, []).append({
                    'id':       a.id,
                    'name':     a.name or 'attachment',
                    'mimetype': a.mimetype or 'application/octet-stream',
                    'size':     a.file_size or 0,
                    'url': (
                        f'/web/content/{a.id}?access_token={a.access_token}'
                        if a.access_token
                        else f'/web/content/{a.id}?download=true'
                    ),
                })

            items = []
            for msg in msgs:
                items.append({
                    'id':          msg.id,
                    'body_html':   msg.body_html or '',
                    'body_text':   msg.body_text or '',
                    'attachments': att_by_msg.get(msg.id, []),
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
            # Optional integer: only return messages with id > last_seen_id.
            # Complements since= for browsers that missed a push notification
            # (e.g. second browser session that connected after the push was sent).
            last_seen_id = int(params.get('last_seen_id', 0) or 0)

            accs = _get_user_accounts(uid)

            # ── Auto-sync for accounts that have never been synced or errored ─
            # The notifications endpoint is often called before the inbox is opened.
            # Without this, a newly-configured account (sync_status='never') would
            # show 0 emails indefinitely until the user navigates to the inbox view.
            db_name = request.env.cr.dbname
            sync_threads = []
            for acc in accs:
                needs_urgent_sync = (
                    (acc.password or '').strip() and
                    (acc.sync_status in ('never', 'error') or not acc.last_sync_date)
                )
                if needs_urgent_sync:
                    try:
                        t = _run_imap_sync_bg(acc.id, db_name, force=True)
                        if t:
                            sync_threads.append(t)
                            _logger.info(
                                'notifications: triggered urgent sync for account %s '
                                '(sync_status=%s)', acc.id, acc.sync_status,
                            )
                    except Exception:
                        _logger.exception(
                            'notifications: urgent sync kick failed for account %s', acc.id,
                        )

            # Wait up to 8 seconds for urgent syncs so the response contains fresh counts.
            # If the sync takes longer the FE will get the cached (possibly stale) counts
            # and the sync will complete in the background.
            for t in sync_threads:
                t.join(timeout=8.0)

            # Re-read accounts after sync to pick up updated unread_count / sync_status.
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
                has_pw     = bool((acc.password or '').strip())
                err_msg    = acc.sync_error_msg or ''
                is_auth    = 'AUTHENTICATIONFAILED' in err_msg.upper() or 'INVALID CREDENTIALS' in err_msg.upper()
                needs_setup = not has_pw or is_auth
                per_account.append({
                    'id':             acc.id,
                    'name':           acc.name,
                    'unread_count':   unread,
                    'sync_status':    acc.sync_status or 'never',
                    'last_sync_date': _to_riyadh_iso(acc.last_sync_date),
                    'sync_error':     err_msg or None,
                    'password_set':   has_pw,
                    # needs_setup=true means inbox will remain empty until
                    # the user (or admin) configures valid credentials.
                    'needs_setup':    needs_setup,
                    'setup_reason':   ('invalid_credentials' if is_auth
                                       else ('no_password' if not has_pw else None)),
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
            # last_seen_id allows the FE to detect messages it missed (e.g. if the
            # WebSocket push was lost because the browser wasn't subscribed yet).
            # On each poll, send the highest message id seen so far; the server
            # returns any inbox messages with id > last_seen_id.
            if last_seen_id:
                new_msg_domain.append(('id', '>', last_seen_id))
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
                    # account_configured=true only when at least one account
                    # has a password set AND is NOT in an auth-failure state.
                    'account_configured': any(
                        not a.get('needs_setup') for a in per_account
                    ),
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
            # New compose: this message IS the root of its own thread.
            if msg.message_id and not msg.thread_id:
                msg.write({'thread_id': msg.message_id})

            # Link uploaded attachments to this message so they appear in
            # message details APIs and are preserved for thread display.
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass

            # Commit NOW so the background SMTP thread can see the message row
            # and attachments immediately via its own fresh cursor.
            request.env.cr.commit()

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))

            # Fire SMTP in background — all file I/O + network happens in daemon
            # thread; the HTTP response is returned without waiting.
            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text, cc_emails, bcc_emails,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
            )

            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True  # SMTP running in background
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            _logger.exception('send_email error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/reply', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def reply(self, message_id, **kwargs):
        """GET → returns compose prefill (to, subject, quoted_body_html, quoted_body_text).
           POST → sends the reply immediately.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()

            acc       = orig.account_id
            own_email = (acc.email_address or '').strip().lower()

            # Reply-To takes precedence over From per RFC 5322
            reply_addr = (orig.reply_to or '').strip() or (orig.from_address or '').strip()
            reply_name = orig.from_name or orig.from_address or ''
            to_addr    = [reply_addr] if reply_addr else []

            subject = (orig.subject or '') if (orig.subject or '').startswith('Re:') \
                      else f"Re: {orig.subject or ''}"

            if request.httprequest.method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {
                        'to':  [{'name': reply_name, 'email': reply_addr}] if reply_addr else [],
                        'cc':  [],
                        'bcc': [],
                        'subject':          subject,
                        'in_reply_to':      orig.message_id or '',
                        # body_html/body_text: initialize the compose box to empty.
                        # The user types their reply here; the backend appends the
                        # quoted block automatically on POST so raw HTML never appears
                        # in the editor.
                        'body_html':        '',
                        'body_text':        '',
                        # quoted_body_html/text: the formatted quote block (for display
                        # as a read-only preview below the editor if the FE wishes).
                        # Do NOT insert these into the editable composer.
                        'quoted_body_html': _build_quoted_html(orig),
                        'quoted_body_text': _build_quoted_text(orig),
                    },
                })

            body = json.loads(request.httprequest.data or '{}')

            # Build complete email body: user's content + quoted original.
            # The FE compose box only collects the user's new reply text;
            # the quoted block is assembled here so raw HTML never appears in the editor.
            user_html   = (body.get('body_html', '') or '').strip()
            user_text   = (body.get('body_text', '') or '').strip()
            quoted_html = _build_quoted_html(orig)
            quoted_text = _build_quoted_text(orig)
            final_html  = (user_html + quoted_html) if user_html else quoted_html
            final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            thread_vals = _thread_vals_for_reply(orig)
            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            vals = {
                'account_id':    acc.id,
                'folder':        'sent',
                'subject':       subject,
                'from_name':     acc.display_name_field or acc.email_address,
                'from_address':  acc.email_address,
                'to_addresses':  json.dumps([{'email': e} for e in to_addr]),
                'cc_addresses':  json.dumps([{'email': e} for e in _norm_addr_list(body.get('cc', []))]),
                'bcc_addresses': json.dumps([{'email': e} for e in _norm_addr_list(body.get('bcc', []))]),
                'body_html':     final_html,
                'body_text':     final_text,
                'is_read':       True,
                'body_fetched':  True,
                'is_important':  importance_raw == 'high',
                'date':          __import__('odoo').fields.Datetime.now(),
                **thread_vals,
            }
            if orig.linked_customer_id:
                vals['linked_customer_id'] = orig.linked_customer_id
            if orig.linked_ticket_id:
                vals['linked_ticket_id'] = orig.linked_ticket_id
            msg = request.env['lugal.email.message'].sudo().create(vals)
            attachment_ids = body.get('attachment_ids', [])
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass
            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_addr, subject, final_html, final_text,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/reply_all', type='http', auth='none', csrf=False,
                methods=['GET', 'POST', 'OPTIONS'])
    def reply_all(self, message_id, **kwargs):
        """GET  → returns compose prefill (to, cc, subject, quoted body).
           POST → sends the reply-all immediately.

        To field rules (RFC 5322):
          - If original has Reply-To, that goes in To (primary).
          - Plus all original To addresses excluding the sender's own address.
          - Original From is added to To only when Reply-To is absent.
        Cc  = all original Cc addresses, excluding the sender's own address.
        Bcc = never copied from original (not transmitted in received emails).
              POST body may include extra bcc:[...] addresses.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            orig = request.env['lugal.email.message'].sudo().browse(message_id)
            if not orig.exists() or orig.account_id.user_id.id != uid:
                return _not_found()

            acc       = orig.account_id
            own_email = (acc.email_address or '').strip().lower()

            # ── Build To list (RFC 5322 §3.6.2) ──────────────────────────────
            # If Reply-To is set, it replaces From as the primary reply target.
            # All original To recipients are still included (Reply All = everyone).
            orig_to_parsed = []
            try:
                orig_to_parsed = json.loads(orig.to_addresses or '[]')
            except Exception:
                pass

            reply_to_override = (orig.reply_to or '').strip()
            to_entries: list[dict] = []   # {'name': ..., 'email': ...}
            seen_emails: set[str] = set()

            def _add_to(name: str, email: str, target: list):
                """Append to target list, skipping own address and duplicates."""
                e = email.strip()
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    target.append({'name': name, 'email': e})

            if reply_to_override:
                # Reply-To takes precedence as the primary reply address
                _add_to('', reply_to_override, to_entries)
            else:
                # No Reply-To: use the original From
                _add_to(orig.from_name or '', orig.from_address or '', to_entries)

            # Add remaining original To recipients (they're already part of "all")
            for entry in orig_to_parsed:
                _add_to(
                    entry.get('name') or '',
                    entry.get('email') or '',
                    to_entries,
                )

            # ── Build Cc list ──────────────────────────────────────────────────
            orig_cc_parsed = []
            try:
                orig_cc_parsed = json.loads(orig.cc_addresses or '[]')
            except Exception:
                pass

            cc_entries: list[dict] = []
            for entry in orig_cc_parsed:
                e  = (entry.get('email') or '').strip()
                el = e.lower()
                # Skip own address AND addresses already in To (no duplicates)
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    cc_entries.append({'name': entry.get('name') or '', 'email': e})

            subject = (orig.subject or '') if (orig.subject or '').startswith('Re:') \
                      else f"Re: {orig.subject or ''}"

            if request.httprequest.method == 'GET':
                return _json_response({
                    'success': True,
                    'data': {
                        'to':      to_entries,
                        'cc':      cc_entries,
                        'bcc':     [],
                        'subject': subject,
                        'in_reply_to':      orig.message_id or '',
                        # body_html/body_text: initialize the compose box to empty.
                        'body_html':        '',
                        'body_text':        '',
                        # quoted_body_html/text: read-only preview below the editor.
                        # Do NOT insert these into the editable composer.
                        'quoted_body_html': _build_quoted_html(orig),
                        'quoted_body_text': _build_quoted_text(orig),
                    },
                })

            # ── POST: send the reply ───────────────────────────────────────────
            body = json.loads(request.httprequest.data or '{}')

            # Merge any extra addresses the FE added in the compose window
            for e in _norm_addr_list(body.get('to', [])):
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    to_entries.append({'name': '', 'email': e})
            for e in _norm_addr_list(body.get('cc', [])):
                el = e.lower()
                if e and el != own_email and el not in seen_emails:
                    seen_emails.add(el)
                    cc_entries.append({'name': '', 'email': e})

            to_addrs  = [entry['email'] for entry in to_entries]
            cc_addrs  = [entry['email'] for entry in cc_entries]
            bcc_addrs = _norm_addr_list(body.get('bcc', []))

            if not to_addrs:
                return _json_response(
                    {'success': False, 'error': 'No recipients to reply to'}, 400
                )

            # Build complete email body: user's content + quoted original.
            user_html   = (body.get('body_html', '') or '').strip()
            user_text   = (body.get('body_text', '') or '').strip()
            quoted_html = _build_quoted_html(orig)
            quoted_text = _build_quoted_text(orig)
            final_html  = (user_html + quoted_html) if user_html else quoted_html
            final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            thread_vals = _thread_vals_for_reply(orig)
            vals = {
                'account_id':    acc.id,
                'folder':        'sent',
                'subject':       subject,
                'from_name':     acc.display_name_field or acc.email_address,
                'from_address':  acc.email_address,
                'to_addresses':  json.dumps(to_entries),
                'cc_addresses':  json.dumps(cc_entries),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_addrs]),
                'body_html':     final_html,
                'body_text':     final_text,
                'is_read':       True,
                'body_fetched':  True,
                'is_important':  importance_raw == 'high',
                'date':          __import__('odoo').fields.Datetime.now(),
                **thread_vals,
            }
            if orig.linked_customer_id:
                vals['linked_customer_id'] = orig.linked_customer_id
            if orig.linked_ticket_id:
                vals['linked_ticket_id'] = orig.linked_ticket_id

            msg = request.env['lugal.email.message'].sudo().create(vals)
            attachment_ids = body.get('attachment_ids', [])
            if attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in attachment_ids]
                    ).write({'res_id': msg.id})
                except Exception:
                    pass

            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_addrs, subject,
                final_html, final_text,
                cc=cc_addrs, bcc=bcc_addrs,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 201)
        except Exception as exc:
            _logger.exception('reply_all error')
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
            importance_raw = (body.get('importance') or 'normal').lower()
            # Combine the user's intro text (if any) with the properly formatted
            # quoted original message.  Using _build_quoted_html gives a consistent
            # "---------- Forwarded message ----------" style header.
            fwd_user_html = (body.get('body_html', '') or '').strip()
            fwd_quoted    = _build_quoted_html(orig)
            fwd_body      = (fwd_user_html + fwd_quoted) if fwd_user_html else fwd_quoted
            fwd_thread = _thread_vals_for_forward(orig)
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
                'is_important':  importance_raw == 'high',
                'date':          __import__('odoo').fields.Datetime.now(),
                **fwd_thread,
            })
            # Forward is the root of a new thread on OUR side — use its own msg-id
            if not msg.thread_id and msg.message_id:
                msg.write({'thread_id': msg.message_id})
            fwd_attachment_ids   = body.get('attachment_ids', [])
            request_read_receipt = bool(body.get('request_read_receipt', False))
            if fwd_attachment_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in fwd_attachment_ids]
                    ).write({'res_id': msg.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass
            request.env.cr.commit()
            _send_via_smtp_async(
                acc, to_fwd, subject, fwd_body, body.get('body_text', ''),
                cc=cc_fwd, bcc=bcc_fwd,
                msg_id=msg.id, attachment_ids=fwd_attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
            )
            resp_data = _message_to_dict(msg)
            resp_data['smtp_pending'] = True
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
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
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
                imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
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
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
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
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'archive')
            return _json_response({'success': True})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/unarchive', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def unarchive_msg(self, message_id, **kwargs):
        """Move a message from the archive folder back to the inbox."""
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _not_found()
            if msg.folder != 'archive':
                return _json_response(
                    {'success': False, 'error': 'Message is not in the archive folder'},
                    409,
                )
            msg.write({'folder': 'inbox'})
            if msg.imap_uid:
                imap_archive = _resolve_imap_folder(msg.account_id, 'archive')
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_archive, 'inbox')
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


    # ── Draft Emails ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/drafts', type='http', auth='none', csrf=False,
                methods=['POST', 'GET', 'OPTIONS'])
    def drafts(self, **kwargs):
        """
        GET  /api/lugal/email/drafts
             List all drafts for the authenticated user.
             Query params: limit (int, default 50), offset (int, default 0)

        POST /api/lugal/email/drafts
             Create a new draft (or auto-save an existing one by passing "id").
             Body (JSON):
               {
                 "account_id":    4,           // required
                 "to":            ["a@b.com"],  // optional
                 "cc":            [],
                 "bcc":           [],
                 "subject":       "...",
                 "body_html":     "<p>...</p>",
                 "body_text":     "...",
                 "attachment_ids": [42, 43],    // already-uploaded ir.attachment IDs
                 "id":            123           // if present: UPDATE existing draft
               }
             Response: { "success": true, "data": { <draft message dict> } }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        # ── GET: list drafts ──────────────────────────────────────────────────
        if request.httprequest.method == 'GET':
            try:
                args = request.httprequest.args
                limit  = int(args.get('limit', 50))
                offset = int(args.get('offset', 0))
                account_ids = [a.id for a in _get_user_accounts(uid)]
                if not account_ids:
                    return _json_response({'success': True, 'data': {'total': 0, 'items': []}})
                Msg   = request.env['lugal.email.message'].sudo()
                domain = [
                    ('account_id', 'in', account_ids),
                    ('is_draft',   '=', True),
                    ('is_deleted', '=', False),
                ]
                total = Msg.search_count(domain)
                msgs  = Msg.search(domain, limit=limit, offset=offset, order='write_date desc')
                return _json_response({
                    'success': True,
                    'data': {
                        'total':  total,
                        'limit':  limit,
                        'offset': offset,
                        'items':  [_message_to_dict(m, full=True) for m in msgs],
                    },
                })
            except Exception as exc:
                _logger.exception('drafts GET error')
                return _json_response({'success': False, 'error': str(exc)}, 500)

        # ── POST: create / update draft ───────────────────────────────────────
        try:
            body       = json.loads(request.httprequest.data or '{}')
            draft_id   = body.get('id')
            account_id = body.get('account_id')
            to_emails  = _norm_addr_list(body.get('to', []))
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))
            subject    = body.get('subject', '')
            body_html  = body.get('body_html', body.get('body', ''))
            body_text  = body.get('body_text', '')
            att_ids    = body.get('attachment_ids', [])

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

            vals = {
                'account_id':   acc.id,
                'folder':       'drafts',
                'is_draft':     True,
                'is_read':      True,
                'body_fetched': True,
                'from_name':    acc.display_name_field or acc.email_address,
                'from_address': acc.email_address,
                'to_addresses': json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses': json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_emails]),
                'subject':      subject,
                'body_html':    body_html,
                'body_text':    body_text,
                'date':         __import__('odoo').fields.Datetime.now(),
            }

            Msg = request.env['lugal.email.message'].sudo()
            if draft_id:
                # Update existing draft
                draft = Msg.browse(int(draft_id))
                if not draft.exists() or not draft.is_draft or draft.account_id.user_id.id != uid:
                    return _not_found('Draft not found')
                draft.write(vals)
                msg = draft
            else:
                msg = Msg.create(vals)

            # Link attachments to this draft
            if att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in att_ids]
                    ).write({'res_id': msg.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass

            return _json_response({'success': True, 'data': _message_to_dict(msg, full=True)},
                                  200 if draft_id else 201)
        except Exception as exc:
            _logger.exception('drafts POST error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/drafts/<int:draft_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    def draft_detail(self, draft_id, **kwargs):
        """
        GET    /api/lugal/email/drafts/<id>  — fetch a single draft with full body + attachments
        PUT    /api/lugal/email/drafts/<id>  — replace draft content (same body as POST /drafts)
        PATCH  /api/lugal/email/drafts/<id>  — partial update (same body, only provided fields updated)
        DELETE /api/lugal/email/drafts/<id>  — permanently discard the draft
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()

        try:
            draft = request.env['lugal.email.message'].sudo().browse(draft_id)
            if not draft.exists() or not draft.is_draft \
                    or draft.is_deleted or draft.account_id.user_id.id != uid:
                return _not_found('Draft not found')

            method = request.httprequest.method

            if method == 'GET':
                return _json_response({'success': True, 'data': _message_to_dict(draft, full=True)})

            if method == 'DELETE':
                draft.write({'is_deleted': True, 'active': False})
                return _json_response({'success': True})

            # PUT / PATCH — update fields
            body       = json.loads(request.httprequest.data or '{}')
            to_emails  = _norm_addr_list(body.get('to', []))
            cc_emails  = _norm_addr_list(body.get('cc', []))
            bcc_emails = _norm_addr_list(body.get('bcc', []))
            att_ids    = body.get('attachment_ids', [])

            vals = {}
            if 'to'        in body: vals['to_addresses']  = json.dumps([{'email': e} for e in to_emails])
            if 'cc'        in body: vals['cc_addresses']  = json.dumps([{'email': e} for e in cc_emails])
            if 'bcc'       in body: vals['bcc_addresses'] = json.dumps([{'email': e} for e in bcc_emails])
            if 'subject'   in body: vals['subject']    = body['subject']
            if 'body_html' in body: vals['body_html']  = body.get('body_html', '')
            if 'body_text' in body: vals['body_text']  = body.get('body_text', '')
            if 'body'      in body: vals['body_html']  = body.get('body', '')

            if vals:
                draft.write(vals)
            if att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(
                        [int(i) for i in att_ids]
                    ).write({'res_id': draft.id, 'res_model': 'lugal.email.message'})
                except Exception:
                    pass

            return _json_response({'success': True, 'data': _message_to_dict(draft, full=True)})
        except Exception as exc:
            _logger.exception('draft_detail error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    @http.route('/api/lugal/email/drafts/<int:draft_id>/send', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def send_draft(self, draft_id, **kwargs):
        """
        POST /api/lugal/email/drafts/<id>/send

        Sends an existing draft via SMTP (async — returns immediately).
        Optionally accepts a body to make final edits before sending:
          {
            "to":             [...],   // override recipients
            "subject":        "...",   // override subject
            "body_html":      "...",   // override body
            "attachment_ids": [...]    // additional attachment IDs
          }
        The draft is moved to the sent folder on success.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            draft = request.env['lugal.email.message'].sudo().browse(draft_id)
            if not draft.exists() or not draft.is_draft \
                    or draft.is_deleted or draft.account_id.user_id.id != uid:
                return _not_found('Draft not found')

            # Idempotency guard: atomically claim the draft send with a row-level
            # lock so double-clicks or concurrent requests only trigger one SMTP send.
            try:
                request.env.cr.execute(
                    "SELECT id FROM lugal_email_message "
                    "WHERE id = %s AND is_draft = TRUE FOR UPDATE NOWAIT",
                    (draft_id,),
                )
                if not request.env.cr.fetchone():
                    return _json_response(
                        {'success': False, 'error': 'Draft already sent or is being sent'},
                        409,
                    )
            except Exception:
                # Lock contention: another request is already sending this draft.
                return _json_response(
                    {'success': False, 'error': 'Draft send already in progress'},
                    409,
                )

            body = json.loads(request.httprequest.data or '{}')

            # Apply any last-minute overrides
            to_emails  = _norm_addr_list(body['to']) if 'to' in body \
                         else _norm_addr_list(json.loads(draft.to_addresses or '[]'))
            cc_emails  = _norm_addr_list(body['cc']) if 'cc' in body \
                         else _norm_addr_list(json.loads(draft.cc_addresses or '[]'))
            bcc_emails = _norm_addr_list(body.get('bcc', [])) \
                         if 'bcc' in body \
                         else _norm_addr_list(json.loads(draft.bcc_addresses or '[]'))
            subject        = body.get('subject', draft.subject or '')
            body_html      = body.get('body_html', body.get('body', draft.body_html or ''))
            body_text      = body.get('body_text', draft.body_text or '')
            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))

            if not to_emails:
                return _json_response({'success': False, 'error': "'to' is required to send"}, 400)

            # Merge attachment IDs: already linked + any extras passed now
            existing_att_ids = [
                a.id for a in request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'lugal.email.message'),
                    ('res_id',    '=', draft.id),
                ])
            ]
            extra_att_ids = [int(i) for i in body.get('attachment_ids', [])]
            all_att_ids = list({*existing_att_ids, *extra_att_ids})

            # Move draft → sent
            import odoo as _odoo
            draft.write({
                'folder':       'sent',
                'is_draft':     False,
                'subject':      subject,
                'to_addresses': json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses': json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses': json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':    body_html,
                'body_text':    body_text,
                'is_important': importance_raw == 'high',
                'date':         _odoo.fields.Datetime.now(),
            })
            # Link any extra attachments
            if extra_att_ids:
                try:
                    request.env['ir.attachment'].sudo().browse(extra_att_ids).write({
                        'res_id': draft.id, 'res_model': 'lugal.email.message',
                    })
                except Exception:
                    pass

            request.env.cr.commit()

            acc = draft.account_id
            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text,
                cc=cc_emails, bcc=bcc_emails,
                msg_id=draft.id, attachment_ids=all_att_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
            )

            resp_data = _message_to_dict(draft)
            resp_data['smtp_pending'] = True
            return _json_response({'success': True, 'data': resp_data}, 200)
        except Exception as exc:
            _logger.exception('send_draft error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Mailbox folders ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def account_folders(self, account_id, **kwargs):
        """List all IMAP folders for an account (including user-created ones).

        Returns stable folder objects:
          { "name": "INBOX", "path": "INBOX", "role": "inbox",
            "message_count": 42, "unread_count": 5 }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            import imaplib, time as _time
            conn = _imap_connect_with_retry(acc)
            if conn is None:
                return _json_response(
                    {'success': False,
                     'error': 'Mail server connection limit reached. Please try again in a few seconds.'},
                    503,
                )
            typ, raw_list = conn.list()
            conn.logout()

            if typ != 'OK':
                return _json_response({'success': False, 'error': 'IMAP LIST failed'}, 502)

            import re
            _LIST_RE = re.compile(r'\((?P<flags>[^)]*)\)\s+"(?P<delim>[^"]*)"\s+(?P<name>.+)')

            # Map common folder names to semantic roles (checked against full path
            # AND the last path segment so "INBOX.Sent", "INBOX/Sent", "Sent" all → "sent")
            _ROLE_MAP = {
                'inbox':          'inbox',
                'sent':           'sent', 'sent items': 'sent', 'sent messages': 'sent',
                'drafts':         'drafts', 'draft': 'drafts',
                'trash':          'trash', 'deleted': 'trash', 'deleted items': 'trash',
                'spam':           'spam', 'junk':  'spam', 'junk e-mail': 'spam',
                'archive':        'archive', 'archives': 'archive',
            }

            # IMAP special-use flags → role (RFC 6154)
            _FLAG_ROLE = {
                '\\sent':    'sent',
                '\\drafts':  'drafts',
                '\\trash':   'trash',
                '\\junk':    'spam',
                '\\spam':    'spam',
                '\\archive': 'archive',
                '\\all':     'archive',
                '\\inbox':   'inbox',
                # Some servers use bare names without backslash
                'sent':      'sent',
                'drafts':    'drafts',
                'trash':     'trash',
                'junk':      'spam',
                'spam':      'spam',
                'archive':   'archive',
            }

            def _resolve_role(raw_name, flags_str):
                """Determine semantic role from IMAP flags first, then folder name."""
                # 1. Check IMAP special-use flags (most reliable)
                for flag in flags_str.split():
                    role = _FLAG_ROLE.get(flag.lower())
                    if role:
                        return role
                # 2. Check full path
                role = _ROLE_MAP.get(raw_name.lower())
                if role:
                    return role
                # 3. Check last path segment (handles INBOX.Sent, INBOX/Trash, etc.)
                last_seg = raw_name.replace('/', '.').rsplit('.', 1)[-1].lower()
                return _ROLE_MAP.get(last_seg, 'custom')

            Msg = request.env['lugal.email.message'].sudo()

            # Detect the hierarchy delimiter from the first folder entry.
            delimiter = '.'
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                dm = _LIST_RE.match(line.strip())
                if dm:
                    delimiter = dm.group('delim') or '.'
                    break

            _STANDARD_ROLES = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

            folders = []
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = _LIST_RE.match(line.strip())
                if not m:
                    continue
                flags    = m.group('flags').lower()
                raw_name = m.group('name').strip().strip('"')
                if '\\noselect' in flags:
                    continue
                role = _resolve_role(raw_name, m.group('flags'))

                # ── Count messages ──────────────────────────────────────────────
                # Standard folders: DB stores logical key ('inbox', 'sent', …)
                # Custom folders:   DB stores the raw IMAP path ('INBOX.omar.Important')
                local_folder_key = role if role in _STANDARD_ROLES else raw_name
                total  = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('folder',     '=', local_folder_key),
                    ('is_deleted', '=', False),
                ])
                unread = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('folder',     '=', local_folder_key),
                    ('is_read',    '=', False),
                    ('is_deleted', '=', False),
                ])

                # ── Tree metadata ───────────────────────────────────────────────
                # Split by the detected delimiter to compute depth and parent.
                parts = raw_name.split(delimiter)
                depth = len(parts) - 1   # INBOX → 0, INBOX.Sent → 1, INBOX.omar.Important → 2
                parent_path = delimiter.join(parts[:-1]) if depth > 0 else None

                folders.append({
                    'path':          raw_name,
                    'name':          parts[-1] or raw_name,
                    'parent_path':   parent_path,
                    'depth':         depth,
                    'role':          role,
                    'flags':         [f.strip().lstrip('\\') for f in m.group('flags').split() if f.strip()],
                    'message_count': total,
                    'unread_count':  unread,
                })

            # ── Build nested tree ───────────────────────────────────────────────
            # Index folders by path for O(1) child insertion.
            by_path = {f['path']: dict(f, children=[]) for f in folders}
            roots   = []
            for f in folders:
                node = by_path[f['path']]
                pp   = f['parent_path']
                if pp and pp in by_path:
                    by_path[pp]['children'].append(node)
                else:
                    roots.append(node)

            return _json_response({'success': True, 'data': {
                'total':     len(folders),
                'items':     folders,   # flat list (unchanged — FE may already use this)
                'tree':      roots,     # nested tree (new — use for sidebar rendering)
                'delimiter': delimiter,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Create folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/create',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_create(self, account_id, **kwargs):
        """Create a new IMAP folder for an account.

        Body:
          {
            "name":   "From Umar",   // required — display name (no separators)
            "parent": "INBOX"        // optional — parent path.
                                     //   Pass "" or omit → top-level folder.
                                     //   The server's hierarchy delimiter is
                                     //   detected automatically (. or /).
          }

        Returns:
          { "path": "INBOX.From Umar", "name": "From Umar",
            "parent": "INBOX", "delimiter": "." }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body   = json.loads(request.httprequest.data or '{}')
            name   = (body.get('name') or '').strip()
            # parent=None / "" / missing → top-level folder (no parent prefix)
            parent_raw = body.get('parent')
            parent = (parent_raw or '').strip() if parent_raw is not None else None

            if not name:
                return _json_response({'success': False, 'error': 'name is required'}, 400)
            if '"' in name:
                return _json_response({'success': False, 'error': 'name must not contain double-quotes'}, 400)

            import imaplib, re as _re, time as _time
            conn = _imap_connect_with_retry(acc)
            if conn is None:
                return _json_response(
                    {'success': False,
                     'error': 'Mail server connection limit reached. Please try again in a few seconds.'},
                    503,
                )
            try:
                # ── Detect the server's hierarchy delimiter ──────────────────
                # IMAP LIST "" "" returns a line like: (\Noselect) "." ""
                # which tells us the delimiter (. or / or something else).
                delimiter = '.'   # safe default for most corporate IMAP servers
                try:
                    _t, _l = conn.list('', '')
                    if _t == 'OK' and _l:
                        _dl = _l[0]
                        if isinstance(_dl, bytes):
                            _dl = _dl.decode('utf-8', errors='replace')
                        _dm = _re.search(r'\)\s+"([^"]+)"', _dl)
                        if _dm:
                            delimiter = _dm.group(1)
                except Exception:
                    pass   # fallback to '.'

                # Reject names that contain the delimiter (would create sub-levels)
                if delimiter in name:
                    return _json_response(
                        {'success': False,
                         'error': f'name must not contain the hierarchy delimiter "{delimiter}"'},
                        400,
                    )

                # Build full IMAP path
                if parent:
                    folder_path = f'{parent}{delimiter}{name}'
                else:
                    folder_path = name   # top-level folder

                typ, data = conn.create(folder_path)
            finally:
                try:
                    conn.logout()
                except Exception:
                    pass

            if typ != 'OK':
                err = data[0].decode('utf-8', errors='replace') if data else 'CREATE failed'
                return _json_response({'success': False, 'error': err}, 502)

            return _json_response({'success': True, 'data': {
                'path':      folder_path,
                'name':      name,
                'parent':    parent or '',
                'delimiter': delimiter,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Rename folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/rename',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_rename(self, account_id, **kwargs):
        """Rename (or move) an IMAP folder.

        Body: { "old_path": "INBOX/Projects", "new_path": "INBOX/Active Projects" }
          old_path (required) — current full IMAP folder path
          new_path (required) — desired full IMAP folder path

        Note: renaming INBOX itself is not allowed by IMAP spec.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body     = json.loads(request.httprequest.data or '{}')
            old_path = (body.get('old_path') or '').strip()
            new_path = (body.get('new_path') or '').strip()

            if not old_path or not new_path:
                return _json_response({'success': False, 'error': 'old_path and new_path are required'}, 400)
            if old_path.upper() == 'INBOX':
                return _json_response({'success': False, 'error': 'Cannot rename INBOX'}, 400)

            import imaplib, time as _time
            conn = _imap_connect_with_retry(acc)
            if conn is None:
                return _json_response(
                    {'success': False,
                     'error': 'Mail server connection limit reached. Please try again in a few seconds.'},
                    503,
                )
            try:
                typ, data = conn.rename(old_path, new_path)
            finally:
                try:
                    conn.logout()
                except Exception:
                    pass

            if typ != 'OK':
                msg = data[0].decode('utf-8', errors='replace') if data else 'RENAME failed'
                return _json_response({'success': False, 'error': msg}, 502)

            return _json_response({'success': True, 'data': {
                'old_path': old_path,
                'new_path': new_path,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Delete folder ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/accounts/<int:account_id>/folders/delete',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def folder_delete(self, account_id, **kwargs):
        """Permanently delete an IMAP folder and all its messages.

        Body: { "path": "INBOX/OldProjects" }
          path (required) — full IMAP folder path to delete

        Protected folders (INBOX, Sent, Drafts, Trash, Spam/Junk) cannot be deleted.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')
            if not (acc.password or '').strip():
                return _json_response({'success': False, 'error': 'No app password configured'}, 400)

            body = json.loads(request.httprequest.data or '{}')
            path = (body.get('path') or '').strip()

            if not path:
                return _json_response({'success': False, 'error': 'path is required'}, 400)

            # Protected by full path match, last segment, OR any segment containing
            # known system/server-internal names (e.g. Dovecot internal folders).
            _PROTECTED_NAMES = {
                'inbox', 'sent', 'sent items', 'sent messages',
                'drafts', 'draft', 'trash', 'deleted', 'deleted items',
                'spam', 'junk', 'junk e-mail', 'archive', 'archives',
            }
            # Server-internal prefixes/substrings — protect entire path if any segment matches
            _INTERNAL_KEYWORDS = {'dovecot', 'sieve', 'courier', 'cyrus', '.subscriptions'}
            path_lower = path.lower()
            segments   = [s.lower() for s in path.replace('/', '.').split('.')]
            if (path_lower in _PROTECTED_NAMES
                    or segments[-1] in _PROTECTED_NAMES
                    or any(kw in path_lower for kw in _INTERNAL_KEYWORDS)):
                return _json_response(
                    {'success': False, 'error': f'Cannot delete protected/system folder: {path}'},
                    400,
                )

            import imaplib, re as _re, time as _time
            conn = _imap_connect_with_retry(acc)
            if conn is None:
                return _json_response(
                    {'success': False,
                     'error': 'Mail server connection limit reached. Please try again in a few seconds.'},
                    503,
                )
            deleted_paths = []
            try:
                # List ALL folders once — we need this both for flag checks and to
                # discover children.  Avoids pattern-based LIST which fails on many
                # servers when the path contains dots.
                _SYSTEM_FLAGS = {'\\sent', '\\drafts', '\\trash', '\\junk',
                                 '\\spam', '\\archive', '\\all', '\\inbox'}
                _LR = _re.compile(r'\((?P<flags>[^)]*)\)\s+"(?P<delim>[^"]*)"\s+"?(?P<name>.+?)"?\s*$')
                typ_all, all_raw = conn.list()

                all_folder_names = []   # [(name, flags_set)]
                delimiter = '.'
                if typ_all == 'OK' and all_raw:
                    for item in all_raw:
                        if not item:
                            continue
                        line = item.decode('utf-8', errors='replace') \
                               if isinstance(item, bytes) else item
                        fm = _LR.search(line.strip())
                        if not fm:
                            continue
                        fname  = fm.group('name').strip().strip('"')
                        fdelim = fm.group('delim') or '.'
                        fflags = {f.lower() for f in fm.group('flags').split()}
                        all_folder_names.append((fname, fflags))
                        delimiter = fdelim   # use last seen delimiter

                # Locate the target folder and check for system flags
                target_flags = set()
                for fname, fflags in all_folder_names:
                    if fname.lower() == path.lower():
                        target_flags = fflags
                        break

                if target_flags & _SYSTEM_FLAGS:
                    conn.logout()
                    return _json_response(
                        {'success': False,
                         'error': f'Cannot delete system folder: {path}'},
                        400,
                    )

                # Collect all folders to delete: the target itself + any descendants.
                # Children are any folders whose path starts with "<path><delimiter>".
                prefix_lower = path.lower() + delimiter
                to_delete = [
                    fname for fname, _ in all_folder_names
                    if fname.lower() == path.lower()
                    or fname.lower().startswith(prefix_lower)
                ]

                # Sort deepest first so children are deleted before their parent.
                # Depth = number of delimiter occurrences.
                to_delete.sort(key=lambda p: p.count(delimiter), reverse=True)

                for folder_path in to_delete:
                    try:
                        conn.unsubscribe(folder_path)
                    except Exception:
                        pass
                    typ_d, data_d = conn.delete(folder_path)
                    if typ_d == 'OK':
                        deleted_paths.append(folder_path)
                        # Remove DB records for this folder so they stop appearing in
                        # the messages list.
                        try:
                            request.env['lugal.email.message'].sudo().search([
                                ('account_id', '=', account_id),
                                ('folder',     '=', folder_path),
                                ('is_deleted', '=', False),
                            ]).write({'is_deleted': True})
                            request.env.cr.commit()
                        except Exception:
                            pass
                    else:
                        # If a virtual parent doesn't physically exist on the server,
                        # the server returns NONEXISTENT — that's fine, just skip it.
                        err_str = (data_d[0].decode('utf-8', errors='replace')
                                   if data_d else '')
                        if 'nonexistent' not in err_str.lower():
                            _logger.warning(
                                'IMAP DELETE %r returned %s: %s', folder_path, typ_d, err_str)

            finally:
                try:
                    conn.logout()
                except Exception:
                    pass

            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Move to custom folder ──────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/move',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def message_move(self, message_id, **kwargs):
        """Move a message to any folder — including user-created custom ones.

        Body: { "folder": "INBOX/Projects" }
          folder may be a logical name (inbox, sent, drafts, trash, archive, spam)
          or a raw IMAP folder path (e.g. "INBOX/Work/2026").
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
            body       = json.loads(request.httprequest.data or '{}')
            target_raw = (body.get('folder') or '').strip()
            if not target_raw:
                return _json_response({'success': False, 'error': 'folder is required'}, 400)

            # Map logical names → IMAP folder via account helper, otherwise use raw path
            LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            if target_raw.lower() in LOGICAL:
                target_logical = target_raw.lower()
                imap_dest = msg.account_id.sudo()._get_server_folder_name(target_logical)
            else:
                target_logical = 'custom'
                imap_dest = target_raw

            prev_folder = msg.folder
            imap_from   = _resolve_imap_folder(msg.account_id, prev_folder)

            # Update local DB record
            msg.write({
                'folder':     target_logical if target_logical != 'custom' else prev_folder,
                'custom_folder': target_raw if target_logical == 'custom' else False,
            } if hasattr(msg, 'custom_folder') else {
                'folder': target_logical if target_logical != 'custom' else prev_folder,
            })

            # Push IMAP move asynchronously
            if msg.imap_uid:
                import threading
                acc        = msg.account_id
                imap_uid   = msg.imap_uid
                db_name    = request.env.cr.dbname
                acc_id     = acc.id

                def _bg_move():
                    try:
                        import imaplib
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as _cr:
                            from odoo.api import Environment
                            _env = Environment(_cr, 1, {})
                            _acc = _env['lugal.email.account'].browse(acc_id)
                            conn = _acc._imap_connect()
                            conn.select(imap_from)
                            # Try MOVE (RFC 6851), fall back to COPY + STORE \Deleted + EXPUNGE
                            result = conn.uid('move', str(imap_uid), imap_dest)
                            if result[0] != 'OK':
                                conn.uid('copy', str(imap_uid), imap_dest)
                                conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                                conn.expunge()
                            conn.logout()
                    except Exception as _e:
                        _logger.warning('message_move IMAP failed uid=%s: %s', imap_uid, _e)

                threading.Thread(target=_bg_move, daemon=True, name=f'imap-move-{message_id}').start()

            return _json_response({'success': True, 'data': {
                'id': msg.id, 'folder': target_raw,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Related messages ───────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/<int:message_id>/related',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def message_related(self, message_id, **kwargs):
        """Return messages related to a given message.

        Query params:
          type   = "sender"       → all messages from the same from_address
                 | "conversation" → all messages in the same thread (by subject / thread_id)
          scope  = "inbox"        → only inbox folder (default)
                 | "all"          → all folders the user owns
          limit  = int (default 50, max 500)
          offset = int (default 0)

        Always excludes the source message itself and soft-deleted rows.
        Results ordered: newest first.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _not_found('Message not found')

            args      = request.httprequest.args
            rel_type  = (args.get('type') or 'sender').lower()     # sender | conversation
            scope     = (args.get('scope') or 'inbox').lower()     # inbox  | all
            limit     = min(int(args.get('limit') or 50), 500)
            offset    = max(int(args.get('offset') or 0), 0)

            # Base domain — restrict to accounts owned by this user
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids

            domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
                ('id',         '!=', message_id),
            ]

            if scope == 'inbox':
                domain.append(('folder', '=', 'inbox'))

            if rel_type == 'sender':
                sender = (msg.from_address or '').strip().lower()
                if not sender:
                    return _json_response({'success': False, 'error': 'Source message has no sender'}, 400)
                # Case-insensitive match on from_address
                domain.append(('from_address', 'ilike', sender))

            elif rel_type == 'conversation':
                # Match by thread_id first (most reliable), then fall back to
                # normalised subject scan so threaded replies without proper
                # References headers are still grouped.
                thread_id  = (msg.thread_id or '').strip()
                raw_subject = (msg.subject or '').strip()

                # Strip common prefixes: Re:, Fwd:, Fw:, AW:, ... (case-insensitive)
                import re as _re
                _PREFIX = _re.compile(r'^(?:(?:re|fwd?|aw|tr|rép|sv)\s*:\s*)+', _re.IGNORECASE)
                norm_subject = _PREFIX.sub('', raw_subject).strip()

                if thread_id:
                    # Prefer thread_id — exact match OR subject fallback via OR
                    if norm_subject:
                        domain += ['|',
                            ('thread_id', '=', thread_id),
                            ('subject',   'ilike', norm_subject),
                        ]
                    else:
                        domain.append(('thread_id', '=', thread_id))
                elif norm_subject:
                    domain.append(('subject', 'ilike', norm_subject))
                else:
                    return _json_response({'success': False, 'error': 'Cannot determine conversation — no thread_id or subject'}, 400)

            else:
                return _json_response({'success': False, 'error': f'Unknown type "{rel_type}". Use sender or conversation'}, 400)

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(domain)
            msgs  = Msg.search(domain, limit=limit, offset=offset, order='create_date desc, id desc')

            return _json_response({
                'success': True,
                'data': {
                    'type':   rel_type,
                    'scope':  scope,
                    'total':  total,
                    'limit':  limit,
                    'offset': offset,
                    'items':  [_message_to_dict(m) for m in msgs],
                },
            })
        except Exception as exc:
            _logger.exception('message_related error')
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Sender contact resolve ─────────────────────────────────────────────────

    @http.route('/api/lugal/email/senders/resolve',
                type='http', auth='none', csrf=False, methods=['GET', 'OPTIONS'])
    def sender_resolve(self, **kwargs):
        """Resolve a sender email address → contact info (phone, mobile, social links).

        Query param: ?email=someone@example.com

        Looks up res.partner, then lugal.crm.employee (by work email / email).
        Returns the first match.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            email = (request.httprequest.args.get('email') or '').strip().lower()
            if not email:
                return _json_response({'success': False, 'error': 'email param required'}, 400)

            result = {'email': email, 'found': False}

            # 1. Try res.partner
            partner = request.env['res.partner'].sudo().search(
                [('email', '=ilike', email)], limit=1,
            )
            if partner:
                result.update({
                    'found':   True,
                    'source':  'partner',
                    'name':    partner.name or '',
                    'phone':   partner.phone or '',
                    'mobile':  partner.mobile or '',
                    'website': partner.website or '',
                })

            # 2. Try res.users (internal employee)
            if not result['found']:
                user = request.env['res.users'].sudo().search(
                    [('email', '=ilike', email)], limit=1,
                )
                if user:
                    result.update({
                        'found':   True,
                        'source':  'user',
                        'name':    user.name or '',
                        'phone':   getattr(user.partner_id, 'phone', '') or '',
                        'mobile':  getattr(user.partner_id, 'mobile', '') or '',
                        'website': '',
                    })

            return _json_response({'success': True, 'data': result})
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
          - inline (optional, "true") – mark as inline image; returns a `cid` for use
            in body HTML as <img src="cid:…">  Inline images are excluded from the
            attachments[] list returned by message detail APIs.

        Response:
          {
            "success": true,
            "data": {
              "attachments": [
                { "id": 42, "name": "invoice.pdf", "mimetype": "application/pdf",
                  "size": 102400, "url": "/web/content/42?download=true",
                  "inline": false }
              ]
            }
          }

        For inline images the response also includes:
          "cid": "cid:img-<uuid>@lugal.mail"
        Embed this value in the HTML body as <img src="cid:img-<uuid>@lugal.mail">.

        Pass ALL returned "id" values (inline + regular) in send/reply/forward as:
          { "attachment_ids": [42, 43] }
        The backend automatically separates inline from regular when building the email.
        """
        import base64
        import mimetypes as _mimetypes
        import uuid as _uuid

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

            is_inline = str(kwargs.get('inline') or request.httprequest.form.get('inline', '')).lower() == 'true'

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

                att_token = _uuid.uuid4().hex

                # For inline images: generate a Content-ID and store it in `description`
                # so the MIME builder can embed the image as multipart/related.
                cid_value = None
                description = None
                if is_inline:
                    cid_value = f'img-{_uuid.uuid4().hex}@lugal.mail'
                    description = f'__inline_cid__:{cid_value}'

                att = Attachment.create({
                    'name': filename,
                    'mimetype': mime,
                    'datas': base64.b64encode(data).decode('utf-8'),
                    'type': 'binary',
                    'res_model': 'lugal.email.message',
                    'access_token': att_token,
                    **(({'description': description}) if description else {}),
                })
                att.flush_recordset(['access_token'])

                att_url = f"/web/content/{att.id}?access_token={att_token}"
                entry = {
                    'id': att.id,
                    'name': att.name or filename,
                    'mimetype': mime,
                    'size': len(data),
                    'url': att_url,
                    'file_url': att_url,
                    'inline': is_inline,
                }
                if cid_value:
                    entry['cid'] = f'cid:{cid_value}'
                results.append(entry)

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


def _read_att_parts(attachment_ids, cr, db_name):
    """
    Read raw binary data for each attachment from filestore or DB.

    Returns (regular_parts, inline_parts):
      regular_parts – list of (filename, mimetype, raw_bytes)   → Content-Disposition: attachment
      inline_parts  – list of (cid, filename, mimetype, raw_bytes) → multipart/related embed

    Inline images are identified by a description field starting with
    ``__inline_cid__:<cid_value>`` — set by the upload endpoint when
    ``inline=true`` is passed.

    Uses direct SQL — avoids ir.attachment.datas ORM computed field which in
    Odoo 17+ returns raw bytes (not base64), causing silent corruption when
    base64.b64decode() is applied.
    """
    import os as _os
    import odoo as _odoo_mod

    regular_parts = []
    inline_parts  = []
    if not attachment_ids:
        return regular_parts, inline_parts

    ids_int = [int(i) for i in attachment_ids]
    cr.execute(
        "SELECT id, name, mimetype, store_fname, description FROM ir_attachment WHERE id = ANY(%s)",
        (ids_int,),
    )
    att_meta = {row[0]: row for row in cr.fetchall()}
    filestore_base = _os.path.join(
        _odoo_mod.tools.config['data_dir'], 'filestore', db_name
    )

    for att_id in ids_int:
        if att_id not in att_meta:
            _logger.warning('_read_att_parts: attachment %s not found — skipping', att_id)
            continue
        _, att_name, att_mime, store_fname, description = att_meta[att_id]
        att_name = att_name or 'attachment'
        att_mime = att_mime or 'application/octet-stream'
        data = b''

        if store_fname:
            file_path = _os.path.join(filestore_base, store_fname)
            try:
                with open(file_path, 'rb') as fh:
                    data = fh.read()
            except Exception as exc:
                _logger.warning(
                    '_read_att_parts: filestore read failed for att %s at %s: %s',
                    att_id, file_path, exc,
                )
        else:
            cr.execute("SELECT db_datas FROM ir_attachment WHERE id = %s", (att_id,))
            row = cr.fetchone()
            if row and row[0]:
                raw = row[0]
                data = bytes(raw) if not isinstance(raw, bytes) else raw

        if not data:
            _logger.warning('_read_att_parts: no binary data for att %s (%s)', att_id, att_name)
            continue

        _logger.debug('_read_att_parts: loaded %s (%s, %d bytes)', att_name, att_mime, len(data))

        # Inline images: description = "__inline_cid__:<cid_value>"
        cid_prefix = '__inline_cid__:'
        if description and description.startswith(cid_prefix):
            cid_value = description[len(cid_prefix):]
            inline_parts.append((cid_value, att_name, att_mime, data))
        else:
            regular_parts.append((att_name, att_mime, data))

    return regular_parts, inline_parts


def _build_mime_message(from_header, to_list, subject, body_html, body_text,
                        cc, att_parts, from_address, importance='normal',
                        inline_parts=None, request_read_receipt=False):
    """
    Build a MIME message from pre-loaded data. Returns raw RFC-2822 string.

    att_parts     – list of (filename, mimetype, raw_bytes) for regular attachments
    inline_parts  – list of (cid, filename, mimetype, raw_bytes) for CID-embedded images.
                    These are wrapped in multipart/related so <img src="cid:…"> renders.
    request_read_receipt – when True, adds Disposition-Notification-To header (read receipt).
    """
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.encoders import encode_base64
    from email.utils import formatdate, make_msgid

    inline_parts = inline_parts or []

    # ── Build the text/alternative part ─────────────────────────────────────
    alt_part = MIMEMultipart('alternative')
    if body_text:
        alt_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
    if body_html:
        alt_part.attach(MIMEText(body_html, 'html', 'utf-8'))

    # ── Wrap in multipart/related when inline (CID) images are present ──────
    # Structure:  multipart/related
    #               multipart/alternative (text + html)
    #               image/png (Content-ID: <cid>, Content-Disposition: inline)
    if inline_parts:
        related_part = MIMEMultipart('related')
        related_part.attach(alt_part)
        for cid_value, img_name, img_mime, img_data in inline_parts:
            try:
                mime_type = img_mime.split('/')
                main_type = mime_type[0]
                sub_type  = mime_type[1] if len(mime_type) > 1 else 'octet-stream'
                img_part = MIMEBase(main_type, sub_type)
                img_part.set_payload(img_data)
                encode_base64(img_part)
                img_part.add_header('Content-ID', f'<{cid_value}>')
                img_part.add_header('Content-Disposition', 'inline', filename=img_name)
                related_part.attach(img_part)
                _logger.debug('_build_mime_message: inline image %s cid=%s', img_name, cid_value)
            except Exception as exc:
                _logger.warning('_build_mime_message: inline image failed %s: %s', img_name, exc)
        body_part = related_part
    else:
        body_part = alt_part

    # ── Wrap in multipart/mixed when regular attachments are present ─────────
    if att_parts:
        mime_msg = MIMEMultipart('mixed')
        mime_msg.attach(body_part)
        for att_name, att_mime, data in att_parts:
            try:
                mime_type = att_mime.split('/')
                main_type = mime_type[0]
                sub_type  = mime_type[1] if len(mime_type) > 1 else 'octet-stream'
                part = MIMEBase(main_type, sub_type)
                part.set_payload(data)
                encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=att_name)
                mime_msg.attach(part)
                _logger.debug('_build_mime_message: attached %s (%s, %d bytes)',
                              att_name, att_mime, len(data))
            except Exception as att_exc:
                _logger.warning('_build_mime_message: MIME build failed for %s: %s',
                                att_name, att_exc)
    else:
        mime_msg = body_part

    mime_msg['Subject']    = subject
    mime_msg['From']       = from_header
    mime_msg['To']         = ', '.join(to_list)
    mime_msg['Date']       = formatdate(localtime=True)
    mime_msg['Message-ID'] = make_msgid(
        domain=from_address.split('@')[-1] if '@' in from_address else 'mail'
    )
    if cc:
        mime_msg['Cc'] = ', '.join(cc)

    # High-importance headers (honoured by Outlook, Apple Mail, Gmail)
    if (importance or 'normal').lower() == 'high':
        mime_msg['X-Priority']        = '1'
        mime_msg['X-MSMail-Priority'] = 'High'
        mime_msg['Importance']        = 'High'

    # Read/Delivery receipt — asks the recipient's mail client to send a notification
    # when the message is read (RFC 3798).  Not all clients honour this.
    if request_read_receipt:
        mime_msg['Disposition-Notification-To'] = from_address
        mime_msg['Return-Receipt-To']           = from_address

    return mime_msg.as_string()


def _do_smtp_send(smtp_host, smtp_port, smtp_use_tls, username, password,
                  from_address, all_recipients, raw_message, msg_id, db_name):
    """
    Perform the actual SMTP send and write result back to lugal.email.message.
    Safe to call from a background thread — uses its own Registry cursor for
    the write-back so it never touches the HTTP request cursor.

    Returns (delivered: bool, error_msg: str|None, refused: dict).
    """
    import smtplib

    delivered = False
    error_msg = None
    refused   = {}

    try:
        # Port 465 = implicit TLS (SMTP_SSL).
        # smtp_use_tls + other ports = STARTTLS (explicit TLS, common on 587).
        # No TLS + non-465 = plain SMTP (port 25 or custom relay).
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            server.ehlo()
        elif smtp_use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.ehlo()

        server.login(username, password)
        partial_refused = server.sendmail(from_address, all_recipients, raw_message)
        server.quit()

        if partial_refused:
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
            'SMTP delivered: from=%s to=%s subject=(see msg %s) host=%s:%s',
            from_address, all_recipients, msg_id, smtp_host, smtp_port,
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

    # Write delivery result back via a fresh cursor (safe from any thread).
    final_delivered = delivered and not refused
    if msg_id:
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as _cr:
                env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                record = env['lugal.email.message'].browse(msg_id)
                if record.exists():
                    record.write({
                        'smtp_delivered': final_delivered,
                        'smtp_error':     error_msg or False,
                        'smtp_status':    'delivered' if final_delivered else 'failed',
                    })
                    # Push a real-time failure notification so the FE can show a
                    # "delivery failed" banner without waiting for the next poll.
                    if not final_delivered:
                        try:
                            user_id = record.account_id.user_id.id
                            env['bus.bus']._sendone(
                                f'supply_user.{user_id}',
                                'crm.email.smtp.failed',
                                {
                                    'msg_id':  msg_id,
                                    'subject': record.subject or '',
                                    'error':   error_msg or 'Delivery failed',
                                },
                            )
                        except Exception as bus_exc:
                            _logger.debug('smtp.failed bus push error: %s', bus_exc)
        except Exception as write_exc:
            _logger.warning('_do_smtp_send: write-back failed for msg %s: %s', msg_id, write_exc)

    return delivered, error_msg, refused


def _send_via_smtp_async(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                         msg_id=None, attachment_ids=None, importance='normal',
                         request_read_receipt=False):
    """
    Fire-and-forget SMTP send.

    Captures SMTP credentials and other primitives from the Odoo record objects
    (which must not be accessed from another thread), then hands all work —
    file reading, MIME building, SMTP network I/O — to a daemon thread.

    The HTTP handler calls this AFTER committing the message row to the DB and
    returns immediately; the background thread writes smtp_delivered/smtp_error
    back via its own Registry cursor.
    """
    import threading

    # Capture all credentials and config as plain Python primitives before the
    # thread starts — Odoo ORM objects are NOT thread-safe across threads.
    db_name       = acc.env.cr.dbname
    acc_id        = acc.id
    smtp_host     = acc.smtp_host
    smtp_port     = acc.smtp_port
    smtp_use_tls  = acc.smtp_use_tls
    imap_host     = acc.imap_host
    imap_port     = int(acc.imap_port or 993)
    imap_use_ssl  = bool(acc.imap_use_ssl)
    username      = acc.username or acc.email_address
    password      = acc.password or ''
    from_address  = acc.email_address
    display_name  = (acc.display_name_field or '').strip()
    from_header   = f'{display_name} <{from_address}>' if display_name else from_address
    att_ids       = [int(i) for i in (attachment_ids or [])]
    all_recipients = list(to_list) + list(cc or []) + list(bcc or [])

    _logger.info(
        'SMTP async queued: from=%s to=%s attachments=%s msg_id=%s',
        from_address, all_recipients, att_ids, msg_id,
    )

    def _bg():
        """Background worker: reads files, builds MIME, sends, then appends to IMAP Sent."""
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            import imaplib as _imaplib

            # Open a fresh cursor to read attachment binary data.
            with _Registry(db_name).cursor() as _cr:
                att_parts, inline_parts = _read_att_parts(att_ids, _cr, db_name)

            raw_message = _build_mime_message(
                from_header, to_list, subject, body_html, body_text, cc, att_parts,
                from_address, importance=importance,
                inline_parts=inline_parts,
                request_read_receipt=request_read_receipt,
            )

            delivered, error_msg, refused = _do_smtp_send(
                smtp_host, smtp_port, smtp_use_tls, username, password,
                from_address, all_recipients, raw_message, msg_id, db_name,
            )

            # ── IMAP APPEND ───────────────────────────────────────────────────
            # After successful SMTP delivery, upload a copy to the IMAP Sent
            # folder so the message appears in webmail, Outlook, etc.
            if delivered:
                try:
                    # Discover the server-side Sent folder name (cached after first run).
                    sent_folder = 'Sent'
                    try:
                        with _Registry(db_name).cursor() as _cr2:
                            env2 = _odoo.api.Environment(_cr2, _odoo.SUPERUSER_ID, {})
                            acc_rec = env2['lugal.email.account'].browse(acc_id)
                            if acc_rec.exists():
                                sent_folder = acc_rec._get_server_folder_name('sent')
                    except Exception:
                        pass  # fall back to 'Sent'

                    # Throttle APPEND connections with the same per-server semaphore
                    # used by IDLE threads so we don't exceed the server's
                    # max-connections-per-user limit during bulk sends.
                    _append_conn = None
                    _append_sem = None
                    _append_sem_acquired = False
                    try:
                        from odoo.addons.lugal_email.models.email_idle_watcher import _server_semaphore
                        _append_sem = _server_semaphore(imap_host, imap_port, username)
                        _append_sem_acquired = _append_sem.acquire(timeout=30)
                        if not _append_sem_acquired:
                            _logger.warning(
                                'IMAP APPEND skipped (server %s:%s at capacity) for msg=%s',
                                imap_host, imap_port, msg_id,
                            )
                            raise RuntimeError('semaphore timeout')
                    except ImportError:
                        pass  # watcher not loaded — no throttle, proceed anyway

                    try:
                        conn_cls = _imaplib.IMAP4_SSL if imap_use_ssl else _imaplib.IMAP4
                        _append_conn = conn_cls(imap_host, imap_port)
                        _append_conn.login(username, password)

                        msg_bytes = (
                            raw_message.encode('utf-8')
                            if isinstance(raw_message, str)
                            else raw_message
                        )
                        typ, data = _append_conn.append(sent_folder, '(\\Seen)', None, msg_bytes)
                        _append_conn.logout()
                        _append_conn = None

                        if typ == 'OK':
                            _logger.info(
                                'SMTP+APPEND: msg=%s appended to %s folder=%s',
                                msg_id, imap_host, sent_folder,
                            )
                        else:
                            _logger.warning(
                                'IMAP APPEND returned %s for msg=%s folder=%s: %s',
                                typ, msg_id, sent_folder, data,
                            )
                    finally:
                        if _append_conn:
                            try:
                                _append_conn.logout()
                            except Exception:
                                pass
                        if _append_sem and _append_sem_acquired:
                            _append_sem.release()
                except Exception as append_exc:
                    _logger.warning(
                        'IMAP APPEND to Sent failed for msg=%s acc=%s: %s',
                        msg_id, acc_id, append_exc,
                    )

        except Exception as exc:
            _logger.error('SMTP background worker crashed for msg %s: %s', msg_id, exc, exc_info=True)

    threading.Thread(target=_bg, daemon=True, name=f'smtp-{msg_id}').start()


def _send_via_smtp(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                   msg_id=None, attachment_ids=None):
    """
    Synchronous SMTP send — kept for backward compatibility / direct callers.
    New callers should prefer _send_via_smtp_async.
    """
    db_name      = acc.env.cr.dbname
    smtp_host    = acc.smtp_host
    smtp_port    = acc.smtp_port
    smtp_use_tls = acc.smtp_use_tls
    username     = acc.username or acc.email_address
    password     = acc.password or ''
    from_address = acc.email_address
    display_name = (acc.display_name_field or '').strip()
    from_header  = f'{display_name} <{from_address}>' if display_name else from_address

    att_parts, inline_parts = _read_att_parts(attachment_ids or [], acc.env.cr, db_name)
    all_recipients = list(to_list) + list(cc or []) + list(bcc or [])
    raw_message    = _build_mime_message(
        from_header, to_list, subject, body_html, body_text, cc, att_parts, from_address,
        inline_parts=inline_parts,
    )
    return _do_smtp_send(
        smtp_host, smtp_port, smtp_use_tls, username, password,
        from_address, all_recipients, raw_message, msg_id, db_name,
    )
