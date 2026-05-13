# TakeAwayEmailBe — bundled lugal_email sources

Each section is one file path, then contents, then four `---` lines.

---
---
---
---

## File: `addons/lugal_email/__init__.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/__init__.py
from . import models
from . import controllers

```

---
---
---
---

## File: `addons/lugal_email/__manifest__.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/__manifest__.py
# Component: Lugal Email — module manifest (lugal_email / __manifest__.py)
{
    'name': 'Lugal Email',
    'version': '1.1.2',
    'category': 'Communication',
    'summary': 'IMAP/SMTP email engine for the Lugal suite — accounts, inbox, send, notifications',
    'description': """
Lugal Email
===========
Full email management module for the Lugal suite.

Features
--------
- lugal.email.account  — IMAP/SMTP account configuration per user
- lugal.email.message  — Stored/cached email messages
- /api/lugal/email/*   — REST HTTP API (Bearer-JWT auth)
- /api/crm/email/*     — CRM-context wrappers (JSON-RPC)
- /api/crm/settings/email/* — Settings CRUD (JSON-RPC)
""",
    'depends': ['base', 'mail', 'lugal_auth'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

```

---
---
---
---

## File: `addons/lugal_email/.gitkeep`

```
# File: addons/lugal_email/.gitkeep
# Submodule not cloned (private repo). Clone with: git clone <url> addons/lugal_email

```

---
---
---
---

## File: `addons/lugal_email/controllers/__init__.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/__init__.py
from . import email_controller
from . import crm_email_controller
from . import settings_email_controller
from . import rules_controller

```

---
---
---
---

## File: `addons/lugal_email/controllers/email_controller.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/email_controller.py
# Component: Lugal Email — REST API controller for /api/lugal/email/* (email_controller.py)
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


def _format_imap_error(exc):
    """Turn imaplib errors (often bytes in .args[0]) into a clean API string."""
    args = getattr(exc, 'args', None)
    if args and isinstance(args[0], bytes):
        return args[0].decode('utf-8', errors='replace')
    return str(exc)


def _is_imap_connection_limit_error(text: str) -> bool:
    t = (text or '').lower()
    return any(k in t for k in ('limit', 'maximum', 'too many', '[limit]', 'mail_max_userip'))


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
            folder_branch_expand = False

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
                folder_branch_expand = False
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
                        children_paths = acc.sudo().imap_child_mailboxes(folder_raw)
                    except Exception:
                        _logger.exception(
                            'imap_child_mailboxes failed acc=%s parent=%s',
                            acc.id, folder_raw,
                        )
                        children_paths = []
                    try:
                        if children_paths:
                            br = acc.sudo().sync_imap_branch_mailboxes(folder_raw)
                            folder_branch_expand = True
                            imap_folder_sync.append({
                                'account_id':       acc.id,
                                'branch':           True,
                                'child_mailboxes':  br.get('children', []),
                                'imported':         br.get('imported_total', 0),
                                'error':            None,
                                'resolved_path':    br.get('parent_resolved', folder_raw),
                                'per_mailbox':      br.get('per_mailbox', []),
                            })
                            if br.get('parent_resolved'):
                                folder_q = br['parent_resolved']
                        else:
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

            # Namespace parent (e.g. INBOX.syednaqvi): include messages stored under
            # child folders (INBOX.syednaqvi.Important) in the same list response.
            _folder_domain = [('folder', '=', folder_q)]
            if is_custom_mailbox and folder_branch_expand:
                _folder_domain = [
                    '|', '|',
                    ('folder', '=', folder_q),
                    ('folder', 'like', folder_q + '.%'),
                    ('folder', 'like', folder_q + '/%'),
                ]

            base_domain = [
                ('account_id', 'in', account_ids),
                ('is_deleted', '=', False),
            ] + _folder_domain
            if account_id:
                try:
                    base_domain.append(('account_id', '=', int(str(account_id).strip())))
                except (TypeError, ValueError):
                    pass
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
                ] + _folder_domain + [
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
            ] + _folder_domain, order='id desc', limit=1)
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
                    'includes_descendant_folders': bool(
                        is_custom_mailbox and folder_branch_expand
                    ),
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

            import imaplib
            try:
                with acc._imap_session() as conn:
                    typ, raw_list = conn.list()
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP / per-user limit). '
                            'Wait a few seconds and retry; the app now queues IMAP access so this should be rare.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

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
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

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
            try:
                with acc._imap_session() as conn:
                    # ── Detect the server's hierarchy delimiter ──────────────────
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
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

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
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

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
            try:
                with acc._imap_session() as conn:
                    typ, data = conn.rename(old_path, new_path)
            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            if typ != 'OK':
                msg = data[0].decode('utf-8', errors='replace') if data else 'RENAME failed'
                return _json_response({'success': False, 'error': msg}, 502)

            return _json_response({'success': True, 'data': {
                'old_path': old_path,
                'new_path': new_path,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

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
            deleted_paths = []
            try:
                with acc._imap_session() as conn:
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

            except Exception as exc:
                fe = _format_imap_error(exc)
                if _is_imap_connection_limit_error(fe):
                    return _json_response({
                        'success': False,
                        'error': (
                            'Mail server refused another IMAP connection (per-IP limit). '
                            'Wait a few seconds and retry.'
                        ),
                        'error_detail': fe,
                    }, 503)
                return _json_response({'success': False, 'error': fe}, 502)

            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

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
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as _cr:
                            from odoo.api import Environment
                            _env = Environment(_cr, 1, {})
                            _acc = _env['lugal.email.account'].browse(acc_id)
                            with _acc._imap_session() as conn:
                                conn.select(imap_from)
                                result = conn.uid('move', str(imap_uid), imap_dest)
                                if result[0] != 'OK':
                                    conn.uid('copy', str(imap_uid), imap_dest)
                                    conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                                    conn.expunge()
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
                    with _Registry(db_name).cursor() as _cr2:
                        env2 = _odoo.api.Environment(_cr2, _odoo.SUPERUSER_ID, {})
                        acc_rec = env2['lugal.email.account'].browse(acc_id)
                        if not acc_rec.exists():
                            raise RuntimeError('account missing')
                        msg_bytes = (
                            raw_message.encode('utf-8')
                            if isinstance(raw_message, str)
                            else raw_message
                        )
                        with acc_rec._imap_session() as _append_conn:
                            sent_folder = acc_rec._get_server_folder_name('sent', existing_conn=_append_conn)
                            typ, data = _append_conn.append(
                                sent_folder, '(\\Seen)', None, msg_bytes,
                            )
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

```

---
---
---
---

## File: `addons/lugal_email/controllers/rules_controller.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/rules_controller.py
# Component: Lugal Email — rules & quick steps REST API (rules_controller.py)
"""
Email Rules  &  Quick Steps REST API
=====================================

Rules endpoints:
  GET    /api/lugal/email/rules            — list current user's rules
  POST   /api/lugal/email/rules            — create a rule
  GET    /api/lugal/email/rules/<id>       — get one rule
  PUT    /api/lugal/email/rules/<id>       — full update
  PATCH  /api/lugal/email/rules/<id>       — partial update
  DELETE /api/lugal/email/rules/<id>       — delete
  POST   /api/lugal/email/rules/<id>/test  — dry-run a rule against a message

Quick Steps endpoints:
  GET    /api/lugal/email/quick_steps            — list
  POST   /api/lugal/email/quick_steps            — create
  GET    /api/lugal/email/quick_steps/<id>       — get one
  PUT    /api/lugal/email/quick_steps/<id>       — update
  DELETE /api/lugal/email/quick_steps/<id>       — delete
  POST   /api/lugal/email/messages/<id>/apply_quick_step — apply to a message
"""
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _imap_exc_text(exc):
    parts = []
    for a in getattr(exc, 'args', ()) or ():
        if isinstance(a, bytes):
            parts.append(a.decode('utf-8', errors='replace'))
        else:
            parts.append(str(a))
    return ' '.join(parts) if parts else str(exc)


def _is_imap_userip_limit(exc) -> bool:
    t = _imap_exc_text(exc).lower()
    return any(
        k in t
        for k in (
            '[limit]', 'mail_max_userip', 'maximum number of connections',
            'too many connections',
        )
    )


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _ensure_jwt():
    """Return user_id from JWT or None."""
    from .email_controller import ensure_jwt_user_id
    return ensure_jwt_user_id()


def _json_ok(data, status=200):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': True, 'data': data})
    return request.make_response(body, headers=headers, status=status)


def _json_err(msg, status=400):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': False, 'error': msg})
    return request.make_response(body, headers=headers, status=status)


def _rule_dict(rule):
    return {
        'id':                 rule.id,
        'name':               rule.name,
        'is_active':          rule.is_active,
        'sequence':           rule.sequence,
        'match_mode':         rule.match_mode,
        'account_id':         rule.account_id.id if rule.account_id else None,
        'conditions':         json.loads(rule.conditions_json or '[]'),
        'actions':            json.loads(rule.actions_json or '[]'),
        'stop_processing':    rule.stop_processing,
        'last_triggered_at':  rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        'trigger_count':      rule.trigger_count,
    }


def _qs_dict(qs):
    return {
        'id':          qs.id,
        'name':        qs.name,
        'description': qs.description or '',
        'sequence':    qs.sequence,
        'icon':        qs.icon or '',
        'steps':       json.loads(qs.steps_json or '[]'),
        'use_count':   qs.use_count,
    }


# ── Rules controller ───────────────────────────────────────────────────────────

class EmailRulesController(http.Controller):

    # ── List ──────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rules = request.env['lugal.email.rule'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_rule_dict(r) for r in rules])
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Create ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['POST'])
    def rules_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            account_id = body.get('account_id')
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _json_err('Account not found', 404)
            rule = request.env['lugal.email.rule'].sudo().create({
                'name':             name,
                'user_id':          uid,
                'account_id':       int(account_id) if account_id else False,
                'is_active':        body.get('is_active', True),
                'sequence':         int(body.get('sequence', 10)),
                'match_mode':       body.get('match_mode', 'all'),
                'conditions_json':  json.dumps(body.get('conditions', [])),
                'actions_json':     json.dumps(body.get('actions', [])),
                'stop_processing':  bool(body.get('stop_processing', False)),
            })
            request.env.cr.commit()
            return _json_ok(_rule_dict(rule), status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Get one ───────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_get(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Update (PUT / PATCH) ──────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def rules_update(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'            in body: write_vals['name']             = (body['name'] or '').strip()
            if 'is_active'       in body: write_vals['is_active']        = bool(body['is_active'])
            if 'sequence'        in body: write_vals['sequence']         = int(body['sequence'])
            if 'match_mode'      in body: write_vals['match_mode']       = body['match_mode']
            if 'conditions'      in body: write_vals['conditions_json']  = json.dumps(body['conditions'])
            if 'actions'         in body: write_vals['actions_json']     = json.dumps(body['actions'])
            if 'stop_processing' in body: write_vals['stop_processing']  = bool(body['stop_processing'])
            if 'account_id'      in body:
                account_id = body['account_id']
                if account_id:
                    acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                    if not acc.exists() or acc.user_id.id != uid:
                        return _json_err('Account not found', 404)
                write_vals['account_id'] = int(account_id) if account_id else False
            if write_vals:
                rule.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Delete ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def rules_delete(self, rule_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            rule.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': rule_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Apply rule to all existing messages ───────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>/apply_all', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_apply_all(self, rule_id, **kwargs):
        """Apply a rule retroactively to all existing inbox messages for the user.

        Body (all optional):
          {
            "account_id": 4,      // limit to one account (default: all user accounts)
            "folder":     "inbox" // limit to one folder   (default: "inbox")
          }

        Response:
          {
            "matched":  15,   // messages the rule conditions matched
            "applied":  15,   // messages actions were applied to
            "skipped":  0     // matched but skipped (e.g. already in target folder)
          }

        Note: runs synchronously — for large mailboxes this may take a few seconds.
        move_folder actions are applied to both the DB and the IMAP server asynchronously.
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)

            body       = json.loads(request.httprequest.data or '{}')
            account_id = body.get('account_id')
            folder     = (body.get('folder') or 'inbox').strip()

            # Build message domain
            domain = [('account_id.user_id', '=', uid), ('is_deleted', '=', False)]
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _json_err('Account not found', 404)
                domain.append(('account_id', '=', int(account_id)))
            if folder:
                domain.append(('folder', '=', folder))

            messages  = request.env['lugal.email.message'].sudo().search(domain, order='id desc', limit=5000)
            RuleModel = request.env['lugal.email.rule'].sudo()

            matched = applied = skipped = 0
            for msg in messages:
                msg_vals = {
                    'from_address':   msg.from_address or '',
                    'to_addresses':   msg.to_addresses or '',
                    'cc_addresses':   msg.cc_addresses or '',
                    'bcc_addresses':  msg.bcc_addresses or '',
                    'subject':        msg.subject or '',
                    'body_text':      msg.body_text or '',
                    'has_attachments': bool(msg.has_attachments if hasattr(msg, 'has_attachments') else False),
                    'is_important':   msg.is_important,
                    'is_read':        msg.is_read,
                    'is_starred':     msg.is_starred,
                    'folder':         msg.folder or '',
                }
                if rule._matches(msg_vals):
                    matched += 1
                    try:
                        RuleModel.apply_inbox_rules(msg, msg_vals)
                        applied += 1
                    except Exception:
                        skipped += 1
                        _logger.warning('rules_apply_all: failed to apply rule %s to msg %s', rule_id, msg.id)

            request.env.cr.commit()
            return _json_ok({'matched': matched, 'applied': applied, 'skipped': skipped})
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Dry-run test ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>/test', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_test(self, rule_id, **kwargs):
        """Dry-run: return whether the rule would match a given message_id (no side effects)."""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body       = json.loads(request.httprequest.data or '{}')
            message_id = body.get('message_id')
            if not message_id:
                return _json_err('message_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(int(message_id))
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            msg_vals = {
                'from_address':   msg.from_address or '',
                'to_addresses':   msg.to_addresses or '',
                'cc_addresses':   msg.cc_addresses or '',
                'bcc_addresses':  msg.bcc_addresses or '',
                'subject':        msg.subject or '',
                'body_text':      msg.body_text or '',
                'has_attachments': False,
                'is_important':   msg.is_important,
                'is_read':        msg.is_read,
                'is_starred':     msg.is_starred,
                'folder':         msg.folder or '',
            }
            matched     = rule._matches(msg_vals)
            would_apply = []
            if matched:
                for act in rule._get_actions():
                    would_apply.append(act)
            return _json_ok({
                'rule_id':      rule_id,
                'message_id':   int(message_id),
                'matched':      matched,
                'would_apply':  would_apply,
                'stop_after':   rule.stop_processing and matched,
            })
        except Exception as exc:
            return _json_err(str(exc), 500)


    # ── Create rule from template (auto-creates IMAP folders) ─────────────────

    @http.route('/api/lugal/email/rules/from_template', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_from_template(self, **kwargs):
        """Create a rule from a predefined template.

        Automatically creates the IMAP folder structure:
          INBOX.<SenderName>/              ← parent (one per sender)
          INBOX.<SenderName>/<RuleType>/  ← child  (one per template)

        Body:
          {
            "template_key":  "move_with_attachments_from_sender",
            "sender_email":  "omar@nooralnibras.com",
            "sender_name":   "Omar",          // used as parent folder name
            "account_id":    4                // required — which account to apply to
          }

        Response:
          {
            "rule":          { ...rule object... },
            "parent_folder": "INBOX.Omar",
            "dest_folder":   "INBOX.Omar.With Attachments",
            "folders_created": ["INBOX.Omar", "INBOX.Omar.With Attachments"]
          }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})

        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)

        try:
            body         = json.loads(request.httprequest.data or '{}')
            template_key = (body.get('template_key') or '').strip()
            sender_email = (
                (body.get('sender_email') or body.get('senderEmail') or '')
            ).strip()
            sender_name = (
                (body.get('sender_name') or body.get('senderName') or sender_email or '')
            ).strip()
            account_id   = body.get('account_id')

            if not template_key:
                return _json_err('template_key is required', 400)
            if not account_id:
                return _json_err('account_id is required', 400)

            acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
            if not acc.exists() or acc.user_id.id != uid:
                return _json_err('Account not found or access denied', 404)

            # Canonical address for rule conditions + folder slug (handles camelCase FE)
            sender_addr = sender_email
            if not sender_addr and sender_name and '@' in sender_name:
                sender_addr = sender_name.strip()
            if not sender_addr:
                return _json_err(
                    'sender_email is required (JSON key sender_email or senderEmail; '
                    'or pass sender_name as a full address containing @)',
                    400,
                )

            # ── Folder path segment: derive from *email*, not display nickname ──
            # Fallback display names: turn "a.b" into "a_b" instead of merging to "ab".
            # Optional body.folder_slug overrides (alphanumeric + _-).
            import re as _re

            def _folder_slug_from_email(addr: str) -> str:
                addr = (addr or '').strip().lower()
                if not addr:
                    return 'sender'
                local, _, domain = addr.partition('@')
                local = (local or (domain.split('.')[0] if domain else '') or 'sender')
                # Dots in local-part become '_' so one hierarchy segment (delimiter is often '.')
                local = local.replace('.', '_')
                slug = _re.sub(r'[^\w\-]+', '_', local, flags=_re.ASCII).strip('_') or 'sender'
                return slug[:60].rstrip('_')

            folder_slug = _folder_slug_from_email(sender_addr)

            slug_override = (body.get('folder_slug') or '').strip()
            if slug_override:
                folder_slug = _re.sub(r'[^\w\-]+', '', slug_override, flags=_re.ASCII)[:60] or folder_slug

            # Human-readable rule title (include name when it is not just the email)
            if sender_name and '@' not in sender_name and sender_name.strip():
                sender_label = f'{sender_name.strip()} ({sender_addr})'
            else:
                sender_label = sender_addr

            # ── Template catalogue ─────────────────────────────────────────────
            TEMPLATES = {
                'move_all_from_sender': {
                    'label':       f'Move all emails from {sender_label}',
                    'child_name':  None,   # goes straight into parent folder
                    'match_mode':  'all',
                    'conditions':  [{'field': 'from_address', 'operator': 'contains',
                                     'value': sender_addr}],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_important_from_sender': {
                    'label':       f'Move all emails from {sender_label} to Important',
                    'child_name':  'Important',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_attachments_from_sender': {
                    'label':       f'Move all emails with attachments from {sender_label}',
                    'child_name':  'With Attachments',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',   'operator': 'contains', 'value': sender_addr},
                        {'field': 'has_attachments', 'operator': 'equals',  'value': 'true'},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_cc_bcc_from_sender': {
                    'label':       f'Move all emails with CC and BCC from {sender_label}',
                    'child_name':  'CC and BCC',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',   'operator': 'contains',     'value': sender_addr},
                        {'field': 'cc_addresses',   'operator': 'is_not_empty', 'value': ''},
                        {'field': 'bcc_addresses',  'operator': 'is_not_empty', 'value': ''},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'mark_important_from_sender': {
                    'label':       f'Mark all emails from {sender_label} as important',
                    'child_name':  None,   # no move; just mark
                    'match_mode':  'all',
                    'conditions':  [{'field': 'from_address', 'operator': 'contains',
                                     'value': sender_addr}],
                    'mark_actions': [{'action': 'mark_important'}],
                    'stop_processing': False,
                },
                'mark_read_from_sender': {
                    'label':       f'Auto-mark all emails from {sender_label} as read',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [{'field': 'from_address', 'operator': 'contains',
                                     'value': sender_addr}],
                    'mark_actions': [{'action': 'mark_read'}],
                    'stop_processing': False,
                },
            }

            tpl = TEMPLATES.get(template_key)
            if not tpl:
                return _json_err(
                    f'Unknown template_key. Valid keys: {list(TEMPLATES)}', 400)

            # ── Build IMAP folder paths ────────────────────────────────────────
            # Detect delimiter + create mailboxes; outer retries on per-IP IMAP limits
            # (multiple Odoo workers can still briefly exceed the server cap).
            import time as _time_mod

            delimiter = '.'
            child_name = tpl['child_name']
            folders_created = []
            is_move_template = bool(child_name) or template_key.startswith('move_')

            parent_path = f'INBOX{delimiter}{folder_slug}'
            dest_path = (f'{parent_path}{delimiter}{child_name}'
                         if child_name else parent_path)

            for outer_attempt in range(6):
                folders_created = []
                try:
                    with acc._imap_session(connect_attempts=14, retry_delay=3.5) as conn_probe:
                        typ_d, listing_d = conn_probe.list('', '')
                        if typ_d == 'OK' and listing_d:
                            first = listing_d[0]
                            if isinstance(first, bytes):
                                first = first.decode('utf-8', errors='replace')
                            import re as _re2
                            m = _re2.search(r'"([./])"', first)
                            if m:
                                delimiter = m.group(1)

                        parent_path = f'INBOX{delimiter}{folder_slug}'
                        dest_path = (f'{parent_path}{delimiter}{child_name}'
                                     if child_name else parent_path)

                        if is_move_template:
                            acc._imap_ensure_folder(parent_path, existing_conn=conn_probe)
                            folders_created.append(parent_path)
                            if child_name:
                                acc._imap_ensure_folder(dest_path, existing_conn=conn_probe)
                                folders_created.append(dest_path)
                    break
                except Exception as fe:
                    if outer_attempt < 5 and _is_imap_userip_limit(fe):
                        _time_mod.sleep(3.0 * (outer_attempt + 1))
                        continue
                    fe_disp = _imap_exc_text(fe)
                    st = 503 if _is_imap_userip_limit(fe) else 500
                    return _json_err(
                        f'Could not prepare IMAP folders under "{parent_path}": {fe_disp}',
                        st,
                    )

            # ── Build actions list ─────────────────────────────────────────────
            actions = list(tpl['mark_actions'])
            if is_move_template:
                actions.append({'action': 'move_folder', 'value': dest_path})

            # ── Create the rule ────────────────────────────────────────────────
            rule = request.env['lugal.email.rule'].sudo().create({
                'name':             tpl['label'],
                'user_id':          uid,
                'account_id':       int(account_id),
                'is_active':        True,
                'sequence':         10,
                'match_mode':       tpl['match_mode'],
                'conditions_json':  json.dumps(tpl['conditions']),
                'actions_json':     json.dumps(actions),
                'stop_processing':  tpl['stop_processing'],
            })
            request.env.cr.commit()

            # ── Auto-apply rule to ALL existing messages in this account ────────
            # This ensures the user sees results immediately in the new folder,
            # not only for future incoming emails.
            # We scan ALL folders (not just inbox) so sent/archive/etc. are covered.
            applied_count  = 0
            skipped_count  = 0
            Msg = request.env['lugal.email.message'].sudo()
            existing = Msg.search([
                ('account_id', '=', int(account_id)),
                ('is_deleted', '=', False),
            ], order='id desc', limit=2000)

            for msg in existing:
                msg_vals = {
                    'from_address':    msg.from_address or '',
                    'to_addresses':    msg.to_addresses or '',
                    'cc_addresses':    msg.cc_addresses or '',
                    'bcc_addresses':   msg.bcc_addresses or '',
                    'subject':         msg.subject or '',
                    'body_text':       msg.body_text or '',
                    'has_attachments': bool(
                        request.env['ir.attachment'].sudo().search_count([
                            ('res_model', '=', 'lugal.email.message'),
                            ('res_id',    '=', msg.id),
                        ])
                    ),
                    'is_important':    msg.is_important,
                    'is_read':         msg.is_read,
                    'is_starred':      msg.is_starred,
                    'folder':          msg.folder or '',
                }
                try:
                    if rule._matches(msg_vals):
                        rule._apply_actions(msg)
                        applied_count += 1
                except Exception:
                    skipped_count += 1
                    _logger.warning('from_template auto-apply: failed for msg %s', msg.id)

            if applied_count:
                try:
                    request.env.cr.commit()
                except Exception:
                    pass

            return _json_ok({
                'rule':            _rule_dict(rule),
                'folder_slug':     folder_slug,
                'sender_label':    sender_label,
                'sender_address':  sender_addr,
                'parent_folder':   parent_path if is_move_template else None,
                'dest_folder':     dest_path   if is_move_template else None,
                'folders_created': folders_created,
                'client_guidance': (
                    'Move templates create IMAP folders on the server in this request. '
                    'You do not need to call POST …/folders/create first unless the UI '
                    'builds a custom path or name outside the template.'
                ),
                'auto_applied':    {
                    'applied': applied_count,
                    'skipped': skipped_count,
                },
            }, status=201)

        except Exception as exc:
            _logger.exception('rules_from_template error')
            return _json_err(str(exc), 500)

    # ── Rule Templates ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/templates', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_templates(self, **kwargs):
        """Return predefined rule templates for the "Create Rule" dropdown.

        Query params (all optional):
          sender_email  — pre-fill sender-based conditions (e.g. "omar@example.com")
          sender_name   — display name to use in the template label (e.g. "Omar")
          folder        — destination IMAP folder for move actions (e.g. "INBOX.Omar")

        Each template object:
          {
            "key":        "move_all_from_sender",
            "label":      "Move all emails from Omar",
            "description": "...",
            "match_mode": "all",
            "conditions": [...],
            "actions":    [...],
            "stop_processing": true
          }

        The FE can display these as a dropdown.  When the user picks one, POST
        /api/lugal/email/rules with the template's conditions/actions (and the
        user-chosen name + destination folder filled in).
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])

        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)

        sender_email = (kwargs.get('sender_email') or '').strip()
        sender_name  = (kwargs.get('sender_name')  or sender_email or 'sender').strip()
        folder       = (kwargs.get('folder')        or '').strip()

        move_action = [{'action': 'move_folder', 'value': folder}] if folder else \
                      [{'action': 'move_folder', 'value': ''}]

        # Helper: build a sender condition if we have an address
        def sender_cond():
            return [{
                'field':    'from_address',
                'operator': 'contains',
                'value':    sender_email,
            }] if sender_email else []

        templates = [
            {
                'key':         'move_all_from_sender',
                'label':       f'Move all emails from {sender_name}' if sender_email
                               else 'Move all emails from a specific sender',
                'description': 'Automatically move every email from this sender to a chosen folder.',
                'match_mode':  'all',
                'conditions':  sender_cond() or [{
                    'field': 'from_address', 'operator': 'contains', 'value': '',
                }],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_important_from_sender',
                'label':       f'Move all emails from {sender_name} to Important folder' if sender_email
                               else 'Move all emails from a sender into an Important subfolder',
                'description': (
                    'Move every email from this sender into the account’s '
                    'INBOX.<slug>.Important folder (the word Important is the mailbox name, '
                    'not the message “starred/important” flag).'
                ),
                'match_mode':  'all',
                'conditions':  sender_cond() or [{
                    'field': 'from_address', 'operator': 'contains', 'value': '',
                }],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_with_attachments_from_sender',
                'label':       f'Move all emails with attachments from {sender_name}' if sender_email
                               else 'Move all emails with attachments from a specific sender',
                'description': 'Move emails that contain attachments or inline images from this sender.',
                'match_mode':  'all',
                'conditions':  sender_cond() + [{
                    'field': 'has_attachments', 'operator': 'equals', 'value': 'true',
                }],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_with_cc_bcc_from_sender',
                'label':       f'Move all emails with CC and BCC from {sender_name}' if sender_email
                               else 'Move all emails with CC and BCC from a specific sender',
                'description': 'Move only when both CC and BCC lists are non-empty (typical forward/reply-all).',
                'match_mode':  'all',
                'conditions':  sender_cond() + [
                    {'field': 'cc_addresses',   'operator': 'is_not_empty', 'value': ''},
                    {'field': 'bcc_addresses',  'operator': 'is_not_empty', 'value': ''},
                ],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'mark_important_from_sender',
                'label':       f'Mark all emails from {sender_name} as important' if sender_email
                               else 'Mark all emails from a specific sender as important',
                'description': 'Automatically flag every email from this sender as high-importance.',
                'match_mode':  'all',
                'conditions':  sender_cond() or [{
                    'field': 'from_address', 'operator': 'contains', 'value': '',
                }],
                'actions':     [{'action': 'mark_important'}],
                'stop_processing': False,
            },
            {
                'key':         'mark_read_from_sender',
                'label':       f'Auto-mark all emails from {sender_name} as read' if sender_email
                               else 'Auto-mark all emails from a specific sender as read',
                'description': 'Silently mark every incoming email from this sender as already read.',
                'match_mode':  'all',
                'conditions':  sender_cond() or [{
                    'field': 'from_address', 'operator': 'contains', 'value': '',
                }],
                'actions':     [{'action': 'mark_read'}],
                'stop_processing': False,
            },
        ]

        return _json_ok(templates)


# ── Quick Steps controller ─────────────────────────────────────────────────────

class EmailQuickStepsController(http.Controller):

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            items = request.env['lugal.email.quick.step'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_qs_dict(q) for q in items])
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['POST'])
    def qs_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            qs = request.env['lugal.email.quick.step'].sudo().create({
                'name':        name,
                'description': body.get('description', ''),
                'user_id':     uid,
                'sequence':    int(body.get('sequence', 10)),
                'icon':        body.get('icon', ''),
                'steps_json':  json.dumps(body.get('steps', [])),
            })
            request.env.cr.commit()
            return _json_ok(_qs_dict(qs), status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_get(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def qs_update(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'        in body: write_vals['name']        = body['name']
            if 'description' in body: write_vals['description'] = body['description']
            if 'sequence'    in body: write_vals['sequence']    = int(body['sequence'])
            if 'icon'        in body: write_vals['icon']        = body['icon']
            if 'steps'       in body: write_vals['steps_json']  = json.dumps(body['steps'])
            if write_vals:
                qs.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def qs_delete(self, qs_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            qs.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/apply_quick_step',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def apply_quick_step(self, message_id, **kwargs):
        """Apply a quick step to a message.

        Body: { "quick_step_id": 5 }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body    = json.loads(request.httprequest.data or '{}')
            qs_id   = body.get('quick_step_id')
            if not qs_id:
                return _json_err('quick_step_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            qs = request.env['lugal.email.quick.step'].sudo().browse(int(qs_id))
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Quick step not found', 404)
            qs.apply_to_message(msg)
            request.env.cr.commit()
            return _json_ok({'applied': True, 'message_id': message_id, 'quick_step_id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

```

---
---
---
---

## File: `addons/lugal_email/controllers/crm_email_controller.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/crm_email_controller.py
"""
Layer 2 — /api/crm/email/*
CRM-context wrappers around the email engine (JSON-RPC format).
"""

import logging
from datetime import timedelta, timezone
from odoo import http
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

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
        'date':         _to_riyadh_iso(msg.date),
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
                    ('folder', '=', 'inbox'),
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
          message_ids: list[int]  — max 50 per call, required.

        Response:
          { "success": true, "data": { "deleted_ids": [...], "skipped_ids": [...] } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not message_ids or not isinstance(message_ids, list):
                return {'success': False, 'error': 'message_ids must be a non-empty list'}
            if len(message_ids) > 50:
                return {'success': False, 'error': 'message_ids may not exceed 50 per request'}

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

```

---
---
---
---

## File: `addons/lugal_email/controllers/settings_email_controller.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/controllers/settings_email_controller.py
"""
Layer 3 — /api/crm/settings/email/*
User-facing CRUD for email account configuration (JSON-RPC).
"""

import logging
from datetime import timedelta, timezone
from odoo import http
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')


def _crm_error(exc, handler=''):
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass
    return {'success': False, 'error': str(exc)}


def _acc_to_dict(acc):
    return {
        'id':             acc.id,
        'name':           acc.name,
        'email_address':  acc.email_address,
        'display_name':   acc.display_name_field or '',
        'imap_host':      acc.imap_host or '',
        'imap_port':      acc.imap_port,
        'imap_use_ssl':   acc.imap_use_ssl,
        'smtp_host':      acc.smtp_host or '',
        'smtp_port':      acc.smtp_port,
        'smtp_use_tls':   acc.smtp_use_tls,
        'is_default':     acc.is_default,
        'is_active':      acc.is_active,
        'sync_status':    acc.sync_status or 'never',
        'last_sync_date': _to_riyadh_iso(acc.last_sync_date),
        'unread_count':   acc.unread_count,
    }


class SettingsEmailController(http.Controller):

    @http.route('/api/crm/settings/email/accounts',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_accounts(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            accs = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid), ('is_deleted', '=', False),
            ])
            return {'success': True, 'data': [_acc_to_dict(a) for a in accs]}
        except Exception as exc:
            return _crm_error(exc, 'list_accounts')

    @http.route('/api/crm/settings/email/accounts/add',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def add_account(self, name, email_address, username=None, password=None,
                    imap_host='imap.gmail.com', imap_port=993, imap_use_ssl=True,
                    smtp_host='smtp.gmail.com', smtp_port=587, smtp_use_tls=True,
                    display_name=None, is_default=False, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().create({
                'user_id':           uid,
                'name':              name,
                'email_address':     email_address,
                'display_name_field': display_name or '',
                'username':          username or email_address,
                'password':          password or '',
                'imap_host':         imap_host,
                'imap_port':         int(imap_port),
                'imap_use_ssl':      imap_use_ssl,
                'smtp_host':         smtp_host,
                'smtp_port':         int(smtp_port),
                'smtp_use_tls':      smtp_use_tls,
                'is_default':        is_default,
            })
            if is_default:
                acc.action_set_default()
            # Trigger IDLE watcher immediately so the new account does not have
            # to wait up to 1 minute for the next supervisor cron run.
            # Also do an initial IMAP sync right now so existing inbox messages
            # are imported and the WS notification fires without delay.
            if (password or '').strip():
                try:
                    acc.action_sync()
                except Exception:
                    _logger.warning('add_account: initial sync failed for account %s', acc.id, exc_info=True)
                acc._schedule_idle_start()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'add_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid or acc.is_deleted:
                return {'success': False, 'error': 'Account not found'}
            allowed = {
                'name', 'email_address', 'display_name_field', 'username', 'password',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls', 'is_active',
            }
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                acc.write(vals)
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'update_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as exc:
            return _crm_error(exc, 'delete_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/test',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def test_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_test_connection()
        except Exception as exc:
            return _crm_error(exc, 'test_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/sync',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def sync_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_sync()
        except Exception as exc:
            return _crm_error(exc, 'sync_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/set_default',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def set_default(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.action_set_default()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'set_default')

```

---
---
---
---

## File: `addons/lugal_email/models/__init__.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/__init__.py
from . import email_account
from . import email_message
from . import email_idle_watcher
from . import email_rule
from . import email_quick_step

```

---
---
---
---

## File: `addons/lugal_email/models/email_account.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_account.py
# Component: Lugal Email — lugal.email.account model (email_account.py)

import json
import logging
import re
import threading
from contextlib import contextmanager
import email as email_lib
from email import policy
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime, parseaddr

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

# Per-account mutex to prevent concurrent _upsert_inbox_message calls for the
# same account from creating duplicate rows when IDLE and polling threads fire
# at the same instant for the same new message.
_upsert_locks: dict = {}
_upsert_locks_guard = threading.Lock()


def _get_upsert_lock(account_id: int) -> threading.Lock:
    with _upsert_locks_guard:
        if account_id not in _upsert_locks:
            _upsert_locks[account_id] = threading.Lock()
        return _upsert_locks[account_id]


# Serialize IMAP logins for the same (host, port, login) within this OS process.
# Parallel HTTP handlers, polling, and fire-and-forget MOVE/STORE threads otherwise
# burst past mail_max_userip_connections on shared mail hosts.
_IMAP_CRED_LOCKS: dict[tuple, threading.Lock] = {}
_IMAP_CRED_LOCKS_GUARD = threading.Lock()

# How many IMAP messages to pull on first / incremental catch-up (per sync call).
SYNC_MAX_MESSAGES = 150
# Auto-sync throttle when inbox already has cached messages (seconds).
# Kept short so the background cron + on-request sync together give near-real-time updates.
SYNC_THROTTLE_SECONDS = 15
# When inbox is empty, sync more aggressively.
SYNC_THROTTLE_EMPTY_SECONDS = 10


class LugalEmailAccount(models.Model):
    """
    IMAP/SMTP email account linked to an Odoo user.
    Each CRM agent can configure one or more personal email accounts.
    """
    _name = 'lugal.email.account'
    _description = 'Lugal Email Account'
    _order = 'is_default desc, name asc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name            = fields.Char(string='Account Label', required=True)
    email_address   = fields.Char(string='Email Address', required=True, index=True)
    display_name_field = fields.Char(string='Display Name (Sender)')
    user_id         = fields.Many2one('res.users', string='Owner', required=True,
                                      default=lambda self: self.env.user, ondelete='cascade', index=True)

    # ── IMAP ──────────────────────────────────────────────────────────────────
    imap_host       = fields.Char(string='IMAP Host', default='imap.gmail.com')
    imap_port       = fields.Integer(string='IMAP Port', default=993)
    imap_use_ssl    = fields.Boolean(string='IMAP SSL', default=True)
    username        = fields.Char(string='Username / Login')
    password        = fields.Char(string='App Password')

    # ── SMTP ──────────────────────────────────────────────────────────────────
    smtp_host       = fields.Char(string='SMTP Host', default='smtp.gmail.com')
    smtp_port       = fields.Integer(string='SMTP Port', default=587)
    smtp_use_tls    = fields.Boolean(string='SMTP TLS', default=True)

    # ── Status ────────────────────────────────────────────────────────────────
    is_default      = fields.Boolean(string='Default Account', default=False, index=True)
    is_active       = fields.Boolean(string='Active', default=True)
    sync_status     = fields.Selection([
        ('ok',       'OK'),
        ('error',    'Error'),
        ('pending',  'Pending'),
        ('never',    'Never Synced'),
    ], string='Sync Status', default='never')
    last_sync_date  = fields.Datetime(string='Last Sync')
    sync_error_msg  = fields.Text(string='Last Sync Error')

    # ── Stats (denormalised for performance) ──────────────────────────────────
    unread_count    = fields.Integer(string='Unread Count', default=0)
    # Highest IMAP UID we have imported for INBOX (incremental sync).
    imap_inbox_max_uid = fields.Integer(string='IMAP Inbox Max UID', default=0)

    active          = fields.Boolean(default=True)
    is_deleted      = fields.Boolean(default=False, index=True)

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if (rec.password or '').strip():
                # Start the IDLE watcher for this account as soon as the
                # transaction commits, without waiting for the 1-minute cron.
                rec_id = rec.id
                rec._schedule_idle_start()
        return records

    @api.constrains('is_default', 'user_id')
    def _check_single_default(self):
        """Enforce at most one default account per user."""
        for rec in self:
            if rec.is_default:
                others = self.search([
                    ('user_id', '=', rec.user_id.id),
                    ('is_default', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    others.write({'is_default': False})

    def action_set_default(self):
        """Mark this account as the user's default, unset others."""
        self.ensure_one()
        self.search([('user_id', '=', self.user_id.id)]).write({'is_default': False})
        self.write({'is_default': True})

    def action_test_connection(self):
        """Test IMAP connection and update sync_status accordingly.

        On success, the IDLE supervisor is triggered immediately so the new
        account starts receiving live notifications without waiting for the
        next supervisor cron run (which fires every minute).
        """
        self.ensure_one()
        try:
            import imaplib
            conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
            conn = conn_cls(self.imap_host, self.imap_port)
            conn.login(self.username or self.email_address, self.password or '')
            conn.logout()
            self.write({'sync_status': 'ok', 'sync_error_msg': False})
            # Trigger the IDLE supervisor in the background so the new account
            # gets its watcher thread immediately (within the owning process).
            self._schedule_idle_start()
            return {'status': 'ok', 'message': 'Connection successful'}
        except Exception as exc:
            self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            return {'status': 'error', 'message': str(exc)}

    def _schedule_idle_start(self):
        """
        Spawn a one-shot background thread that clears any backoff for this
        account's credential group and calls start_all() so the IDLE supervisor
        picks it up immediately.

        If the current OS process is not the IDLE supervisor owner, start_all()
        returns 0 (skips) and the account will be picked up by the owning
        process on its next cron run (≤ 1 minute).
        """
        import threading
        db_name = self.env.cr.dbname
        acc_id  = self.id

        def _trigger():
            import time
            time.sleep(0.5)   # give the write() commit time to propagate
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    env['lugal.email.idle.watcher'].clear_backoff_for_account(acc_id)
            except Exception:
                pass   # cron will catch it within 1 minute

        threading.Thread(target=_trigger, daemon=True, name='idle-on-test').start()

    def _imap_credentials_key(self):
        """Stable tuple for locking IMAP access (same login = one gate)."""
        self.ensure_one()
        host = (self.imap_host or '').strip().lower()
        port = int(self.imap_port or (993 if self.imap_use_ssl else 143))
        user = (self.username or self.email_address or '').strip().lower()
        return host, port, user

    def _imap_connect_unlocked(self):
        """Open IMAP without taking the credential lock (internal use only)."""
        import imaplib
        conn_cls = imaplib.IMAP4_SSL if self.imap_use_ssl else imaplib.IMAP4
        port = int(self.imap_port or (993 if self.imap_use_ssl else 143))
        conn = conn_cls(self.imap_host, port)
        conn.login(self.username or self.email_address, self.password or '')
        return conn

    @contextmanager
    def _imap_session(self, connect_attempts=6, retry_delay=2.0):
        """Serialize IMAP for this account's credentials; login, yield conn, logout.

        Retries with backoff when the server returns connection-limit errors.
        """
        import time as _time
        self.ensure_one()
        key = self._imap_credentials_key()
        with _IMAP_CRED_LOCKS_GUARD:
            lock = _IMAP_CRED_LOCKS.setdefault(key, threading.Lock())
        lock.acquire()
        try:
            for attempt in range(connect_attempts):
                conn = None
                try:
                    conn = self._imap_connect_unlocked()
                    try:
                        yield conn
                    finally:
                        if conn is not None:
                            try:
                                conn.logout()
                            except Exception:
                                try:
                                    conn.shutdown()
                                except Exception:
                                    pass
                    return
                except Exception as exc:
                    if conn is not None:
                        try:
                            conn.logout()
                        except Exception:
                            try:
                                conn.shutdown()
                            except Exception:
                                pass
                    err = str(exc).lower()
                    a0 = getattr(exc, 'args', (None,))[0]
                    if isinstance(a0, bytes):
                        err = a0.decode('utf-8', errors='replace').lower() + ' ' + err
                    if attempt < connect_attempts - 1 and any(
                        kw in err
                        for kw in (
                            'limit', 'maximum', 'too many', 'connection',
                            'eof', 'socket', 'temporarily', 'unavailable',
                        )
                    ):
                        _time.sleep(retry_delay * (attempt + 1))
                        continue
                    raise
        finally:
            lock.release()

    # ── Bidirectional IMAP sync helpers ──────────────────────────────────────

    def _get_server_folder_name(self, purpose, existing_conn=None):
        """Return the IMAP server folder name for a logical purpose.

        purpose: 'trash' | 'archive' | 'sent' | 'drafts' | 'spam'

        Detects per-account folder names via IMAP LIST on first call, then caches
        in ir.config_parameter so subsequent calls are instant (no extra connection).

        ``existing_conn``: when provided, LIST on this connection (caller must
        already hold the credential lock via ``_imap_session``) to avoid nested
        IMAP logins and deadlocks.
        """
        self.ensure_one()
        import re as _re

        cache_key = f'lugal.email.folder.{self.id}.{purpose}'
        ICP = self.env['ir.config_parameter'].sudo()
        cached = ICP.get_param(cache_key, '')
        if cached:
            return cached

        # Provider-aware defaults (avoids an extra IMAP LIST round-trip for known hosts)
        host = (self.imap_host or '').lower()
        if 'gmail.com' in host:
            defaults = {
                'trash': '[Gmail]/Trash', 'archive': '[Gmail]/All Mail',
                'sent': '[Gmail]/Sent Mail', 'drafts': '[Gmail]/Drafts',
                'spam': '[Gmail]/Spam',
            }
        else:
            defaults = {
                'trash': 'Trash', 'archive': 'Archive',
                'sent': 'Sent', 'drafts': 'Drafts', 'spam': 'Spam',
            }

        # Attempt auto-discovery via IMAP LIST
        # LIST response format: (flags) "delimiter" folder_name
        # e.g. (\HasNoChildren \Trash) "." INBOX.Trash
        #      (\Trash) "/" "[Gmail]/Trash"
        keywords = {
            'trash':   ['trash', 'deleted'],
            'archive': ['archive'],
            'sent':    ['sent'],
            'drafts':  ['draft'],
            'spam':    ['spam', 'junk'],
        }

        def _match_folder_from_listing(listing):
            if not listing:
                return None
            for entry in listing:
                if not entry:
                    continue
                raw = entry.decode('utf-8', errors='replace') if isinstance(entry, bytes) else str(entry)
                m = _re.search(r'\(.*?\)\s+"[^"]+"\s+"?(.+?)"?\s*$', raw)
                if not m:
                    m = _re.search(r'\(.*?\)\s+\S+\s+"?(.+?)"?\s*$', raw)
                folder_raw = m.group(1).strip().strip('"') if m else ''
                if not folder_raw:
                    continue
                for kw in keywords.get(purpose, []):
                    if kw in folder_raw.lower():
                        return folder_raw
            return None

        try:
            if existing_conn is not None:
                typ, listing = existing_conn.list()
                if typ == 'OK' and listing:
                    hit = _match_folder_from_listing(listing)
                    if hit:
                        ICP.set_param(cache_key, hit)
                        return hit
            else:
                with self._imap_session() as conn:
                    typ, listing = conn.list()
                    if typ == 'OK' and listing:
                        hit = _match_folder_from_listing(listing)
                        if hit:
                            ICP.set_param(cache_key, hit)
                            return hit
        except Exception:
            pass  # fall through to defaults

        result = defaults.get(purpose, purpose.capitalize())
        ICP.set_param(cache_key, result)
        return result

    def _imap_store_async(self, imap_uid, imap_folder, add_flags=None, remove_flags=None):
        """Push flag changes to the IMAP server in a background thread (fire-and-forget).

        Called after local DB updates so API responses are never blocked by IMAP latency.
        Failures are logged as warnings — the local DB state is always authoritative.
        """
        self.ensure_one()
        if not imap_uid or not (add_flags or remove_flags):
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_store():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    with acc._imap_session() as conn:
                        conn.select(imap_folder, readonly=False)
                        uid_str = str(imap_uid)
                        if add_flags:
                            conn.uid('store', uid_str, '+FLAGS', '(' + ' '.join(add_flags) + ')')
                        if remove_flags:
                            conn.uid('store', uid_str, '-FLAGS', '(' + ' '.join(remove_flags) + ')')
                    _logger.info(
                        'IMAP flags pushed for acc=%s uid=%s folder=%s +%s -%s',
                        acc_id, imap_uid, imap_folder, add_flags, remove_flags,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP flag push failed for acc=%s uid=%s folder=%s: %s',
                    acc_id, imap_uid, imap_folder, exc,
                )

        threading.Thread(target=_do_store, daemon=True,
                         name=f'imap-store-{imap_uid}').start()

    def _imap_append_sent_async(self, raw_message):
        """
        Upload a copy of a just-sent email to the IMAP Sent folder so it appears
        in webmail, Outlook, and any other email client connected to the same account.

        raw_message: the RFC-2822 email as a bytes or str object.
        Runs in a background daemon thread — the HTTP response is never blocked.
        """
        self.ensure_one()

        import threading

        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_append():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo

                with _Registry(db_name).cursor() as _cr:
                    env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    if not acc.exists():
                        return
                    with acc._imap_session() as conn:
                        sent_folder = acc._get_server_folder_name('sent', existing_conn=conn)
                        msg_bytes = (
                            raw_message.encode('utf-8')
                            if isinstance(raw_message, str)
                            else raw_message
                        )
                        typ, data = conn.append(sent_folder, '(\\Seen)', None, msg_bytes)

                    if typ == 'OK':
                        _logger.info(
                            'IMAP APPEND to Sent succeeded: acc=%s folder=%s',
                            acc_id, sent_folder,
                        )
                    else:
                        _logger.warning(
                            'IMAP APPEND to Sent returned %s for acc=%s folder=%s: %s',
                            typ, acc_id, sent_folder, data,
                        )
            except Exception as exc:
                _logger.warning(
                    'IMAP APPEND to Sent failed for acc=%s: %s',
                    acc_id, exc,
                )

        threading.Thread(
            target=_do_append, daemon=True, name=f'imap-append-sent-{acc_id}'
        ).start()

    def _imap_move_async(self, imap_uid, from_folder, to_folder_purpose):
        """Move a message between IMAP folders in a background thread.

        Uses the MOVE extension (RFC 6851, supported by Dovecot and cPanel/WHM).
        Falls back to COPY + STORE(\\Deleted) + EXPUNGE if MOVE is unavailable.

        to_folder_purpose: logical name ('trash'|'archive'|'inbox'|'sent'|'drafts')
        """
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_move():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)

                    with acc._imap_session() as conn:
                        if to_folder_purpose == 'inbox':
                            dest_folder = 'INBOX'
                        else:
                            dest_folder = acc._get_server_folder_name(
                                to_folder_purpose, existing_conn=conn,
                            )
                        conn.select(from_folder, readonly=False)
                        uid_str = str(imap_uid)

                        typ, data = conn.uid('move', uid_str, dest_folder)
                        if typ != 'OK':
                            conn.uid('copy', uid_str, dest_folder)
                            conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                            conn.expunge()

                    _logger.info(
                        'IMAP move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP move failed acc=%s uid=%s: %s',
                    acc_id, imap_uid, exc,
                )

        threading.Thread(target=_do_move, daemon=True,
                         name=f'imap-move-{imap_uid}').start()

    def _imap_move_to_raw_path_async(self, imap_uid, from_folder, dest_folder_path):
        """Move a message to an arbitrary IMAP folder path (e.g. 'INBOX.AllFromUmar').

        Unlike _imap_move_async, this accepts the raw IMAP destination path directly
        instead of a logical purpose name.  Used by inbox rules that target custom folders.
        """
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_move():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    with acc._imap_session() as conn:
                        conn.select(from_folder, readonly=False)
                        uid_str = str(imap_uid)

                        typ, data = conn.uid('move', uid_str, dest_folder_path)
                        if typ != 'OK':
                            conn.uid('copy', uid_str, dest_folder_path)
                            conn.uid('store', uid_str, '+FLAGS', '(\\Deleted)')
                            conn.expunge()

                    _logger.info(
                        'IMAP raw-move acc=%s uid=%s %s → %s',
                        acc_id, imap_uid, from_folder, dest_folder_path,
                    )
            except Exception as exc:
                _logger.warning(
                    'IMAP raw-move failed acc=%s uid=%s: %s',
                    acc_id, imap_uid, exc,
                )

        threading.Thread(target=_do_move, daemon=True,
                         name=f'imap-rawmove-{imap_uid}').start()

    def _imap_ensure_folder(self, path, existing_conn=None):
        """Create *path* on the IMAP server if it does not already exist.

        Returns the final folder path on success, raises on hard failure.
        Safe to call when the folder already exists (no-op in that case).

        ``existing_conn``: optional open connection (same lock as caller's session).
        """

        def _ensure_on_conn(conn):
            typ, listing = conn.list('""', path)
            exists = typ == 'OK' and any(listing)
            if not exists:
                conn.create(path)
                conn.subscribe(path)
                _logger.info('IMAP folder created: acc=%s path=%s', self.id, path)
            else:
                _logger.info('IMAP folder already exists: acc=%s path=%s', self.id, path)
            return path

        self.ensure_one()
        if existing_conn is not None:
            return _ensure_on_conn(existing_conn)
        with self._imap_session() as conn:
            return _ensure_on_conn(conn)

    def _imap_expunge_async(self, imap_uid, imap_folder):
        """Mark a message \\Deleted on the server and EXPUNGE it (permanent delete)."""
        self.ensure_one()
        if not imap_uid:
            return

        import threading
        acc_id  = self.id
        db_name = self.env.cr.dbname

        def _do_expunge():
            try:
                from odoo.modules.registry import Registry as _Registry
                import odoo as _odoo
                with _Registry(db_name).cursor() as cr:
                    env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                    acc = env['lugal.email.account'].browse(acc_id)
                    with acc._imap_session() as conn:
                        conn.select(imap_folder, readonly=False)
                        conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                        conn.expunge()
                    _logger.info('IMAP expunge acc=%s uid=%s folder=%s', acc_id, imap_uid, imap_folder)
            except Exception as exc:
                _logger.warning('IMAP expunge failed acc=%s uid=%s: %s', acc_id, imap_uid, exc)

        threading.Thread(target=_do_expunge, daemon=True,
                         name=f'imap-expunge-{imap_uid}').start()

    @staticmethod
    def _decode_mime_header(value):
        if not value:
            return ''
        out = []
        for frag, enc in decode_header(value):
            if isinstance(frag, bytes):
                out.append(frag.decode(enc or 'utf-8', errors='replace'))
            else:
                out.append(frag)
        return ''.join(out)

    @staticmethod
    def _extract_best_body(msg):
        """Return (body_text, body_html) from an email.message.Message."""
        body_text = ''
        body_html = ''
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == 'text/plain' and not body_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='replace')
                elif ctype == 'text/html' and not body_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_html = payload.decode(charset, errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                decoded = payload.decode(charset, errors='replace')
                if msg.get_content_type() == 'text/html':
                    body_html = decoded
                else:
                    body_text = decoded
        return body_text, body_html

    def _parse_flags_from_fetch_response(self, meta_bytes):
        """Detect \\Seen in IMAP fetch metadata bytes."""
        if not meta_bytes:
            return False
        try:
            s = meta_bytes.decode('utf-8', errors='replace') if isinstance(meta_bytes, bytes) else str(meta_bytes)
        except Exception:
            s = str(meta_bytes)
        return '\\Seen' in s

    def _upsert_inbox_message(self, uid_int, raw_bytes, flags_meta, headers_only=False,
                              folder_key='inbox', run_rules=True):
        """Create or update one mailbox row from raw RFC822 bytes.

        folder_key: logical name ('inbox', 'sent', …) or full IMAP path for custom
                    folders (e.g. 'INBOX.syednaqvi.Important').
        run_rules:  when False, skip apply_inbox_rules (used when importing from
                    a custom folder to avoid re-firing move rules).
        """
        self.ensure_one()
        import email
        msg = email.message_from_bytes(raw_bytes, policy=policy.default)
        message_id = (msg.get('Message-ID') or '').strip() or False
        subject = self._decode_mime_header(msg.get('Subject', ''))
        from_name, from_addr = parseaddr(msg.get('From', ''))
        if from_name:
            from_name = self._decode_mime_header(from_name)
        date_hdr = msg.get('Date')
        dt = None
        if date_hdr:
            try:
                dt = parsedate_to_datetime(date_hdr)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
            except Exception:
                dt = None
        if not dt:
            dt = fields.Datetime.now()
        to_raw = msg.get_all('To', [])
        pairs = getaddresses(to_raw) if to_raw else []
        to_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in pairs if e]
        cc_raw = msg.get_all('Cc', [])
        cc_pairs = getaddresses(cc_raw) if cc_raw else []
        cc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in cc_pairs if e]
        bcc_raw = msg.get_all('Bcc', [])
        bcc_pairs = getaddresses(bcc_raw) if bcc_raw else []
        bcc_list = [{'name': self._decode_mime_header(n or ''), 'email': e} for n, e in bcc_pairs if e]
        # Reply-To: used by reply/reply_all to address the reply correctly
        reply_to_raw = msg.get('Reply-To', '')
        reply_to_addr = ''
        if reply_to_raw:
            rt_pairs = getaddresses([reply_to_raw])
            reply_to_addr = rt_pairs[0][1] if rt_pairs else ''

        # References: chain of ancestor Message-IDs used for thread grouping
        references_raw = (msg.get('References') or msg.get('references') or '').strip()
        references_ids = references_raw.split() if references_raw else []
        # Also consider In-Reply-To in case References is absent (some clients)
        in_reply_to_hdr = (msg.get('In-Reply-To') or '').strip()

        # thread_id = the oldest ancestor Message-ID (first in References chain).
        # If References is absent, use In-Reply-To. If neither present, this
        # message is the root — use its own Message-ID.
        if references_ids:
            thread_id = references_ids[0].strip()
        elif in_reply_to_hdr:
            thread_id = in_reply_to_hdr
        else:
            thread_id = message_id or ''

        body_text, body_html = self._extract_best_body(msg)
        is_read = self._parse_flags_from_fetch_response(flags_meta)

        # is_mentioned: True when the account owner's email is in the To: header
        # (direct recipient, not just CC). Matches Outlook "Mentioned Mail".
        own_email = (self.email_address or '').strip().lower()
        to_emails_lower = [pair[1].lower() for pair in getaddresses(msg.get_all('To', [])) if pair[1]]
        is_mentioned = bool(own_email and own_email in to_emails_lower)

        # is_important: parse standard priority/importance headers sent by the
        # sender. Check in priority order:
        #   1. Importance: high / normal / low  (RFC 2156 / Outlook)
        #   2. X-Priority: 1 or 2 = high (Outlook, many clients)
        #   3. X-MSMail-Priority: High / Normal / Low (Outlook legacy)
        is_important = False
        _importance_hdr = (msg.get('Importance') or '').strip().lower()
        if _importance_hdr == 'high':
            is_important = True
        elif _importance_hdr not in ('', 'normal', 'low'):
            # Some clients send numeric values in this header too
            pass

        if not is_important:
            _xpriority = (msg.get('X-Priority') or '').strip()
            try:
                _xprio_int = int(_xpriority.split()[0]) if _xpriority else 3
                if _xprio_int in (1, 2):
                    is_important = True
            except (ValueError, IndexError):
                pass

        if not is_important:
            _msmail = (msg.get('X-MSMail-Priority') or '').strip().lower()
            if _msmail == 'high':
                is_important = True

        # message_size: approximate RFC-822 size in bytes
        message_size = len(raw_bytes) if raw_bytes else 0

        Message = self.env['lugal.email.message'].sudo()
        # Search by imap_uid first; also check message_id as a secondary key so
        # we never store the same RFC-2822 message twice even if the UID changed.
        domain = [('account_id', '=', self.id), ('folder', '=', folder_key), ('imap_uid', '=', uid_int)]
        existing = Message.search(domain, limit=1)
        if not existing and message_id:
            existing = Message.search(
                [('account_id', '=', self.id), ('message_id', '=', message_id)],
                limit=1,
            )
        vals = {
            'account_id':    self.id,
            'folder':        folder_key,
            'imap_uid':      uid_int,
            'subject':       subject or '(no subject)',
            'from_name':     from_name or '',
            'from_address':  from_addr or '',
            'to_addresses':  json.dumps(to_list),
            'cc_addresses':  json.dumps(cc_list),
            'bcc_addresses': json.dumps(bcc_list),
            'reply_to':      reply_to_addr or False,
            'message_id':    message_id,
            'in_reply_to':   in_reply_to_hdr or False,
            'references':    references_raw or False,
            'thread_id':     thread_id or False,
            'date':          dt,
            'is_read':       is_read,
            'is_deleted':    False,
            'active':        True,
            'is_mentioned':  is_mentioned,
            'is_important':  is_important,
            'message_size':  message_size,
        }
        if headers_only:
            # Do not overwrite body if we already have it from a previous full fetch.
            if not existing:
                vals['body_text']     = ''
                vals['body_html']     = False
                vals['body_fetched']  = False
        else:
            vals['body_text']    = body_text
            vals['body_html']    = body_html or False
            vals['body_fetched'] = True
        if existing:
            # Never downgrade a fully-fetched body to headers-only.
            if headers_only and existing.body_fetched:
                vals.pop('body_text', None)
                vals.pop('body_html', None)
                vals.pop('body_fetched', None)
            existing.write(vals)
            stored_msg = existing
        else:
            # Acquire a per-account mutex before the INSERT to prevent two threads
            # (IDLE push + polling fallback) racing on the same new message and
            # each inserting a separate row for the same imap_uid / message_id.
            _acc_lock = _get_upsert_lock(self.id)
            with _acc_lock:
                # Re-check inside the lock — the other thread may have just created it.
                stored_msg = Message.search(domain, limit=1)
                if not stored_msg and message_id:
                    stored_msg = Message.search(
                        [('account_id', '=', self.id), ('message_id', '=', message_id)],
                        limit=1,
                    )

                if stored_msg:
                    # Another thread won the race — just update.
                    if not (headers_only and stored_msg.body_fetched):
                        stored_msg.write(vals)
                else:
                    # We are the first — create, using a SAVEPOINT so a concurrent
                    # INSERT at the DB level (unlikely but possible) rolls back
                    # only the inner block and leaves the cursor usable.
                    try:
                        with self.env.cr.savepoint():
                            stored_msg = Message.create(vals)
                    except Exception as dup_exc:
                        # Unique-constraint violation from a concurrent INSERT —
                        # fall back to search and update.
                        _logger.warning(
                            '_upsert_inbox_message: duplicate INSERT caught for '
                            'account=%s uid=%s message_id=%s — %s',
                            self.id, uid_int, message_id, dup_exc,
                        )
                        stored_msg = Message.search(domain, limit=1)
                        if not stored_msg and message_id:
                            stored_msg = Message.search(
                                [('account_id', '=', self.id), ('message_id', '=', message_id)],
                                limit=1,
                            )
                        if stored_msg and not (headers_only and stored_msg.body_fetched):
                            stored_msg.write(vals)

                    # Run inbox rules only on genuinely new messages (inbox ingest).
                    if stored_msg and run_rules:
                        try:
                            self.env['lugal.email.rule'].sudo().apply_inbox_rules(stored_msg, vals)
                        except Exception as _re:
                            _logger.warning('Inbox rule execution failed for msg %s: %s', stored_msg.id, _re)

        # Extract and persist file attachments when we have the full body.
        if not headers_only:
            self._store_imap_attachments(stored_msg, msg)

        return stored_msg

    def action_sync_if_stale(self, force=False):
        """
        Run IMAP inbox import unless recently synced (reduces load on mailbox polling).
        If inbox has no rows, sync runs unless the last attempt was very recent.

        Accounts with sync_status='never' (never successfully synced) always bypass
        the throttle — we want the very first sync to happen as soon as possible.
        """
        self.ensure_one()
        if not (self.password or '').strip():
            return {'skipped': True, 'reason': 'no_password'}

        # Always sync if this account has never been synced successfully.
        if not self.last_sync_date or self.sync_status == 'never':
            _logger.info(
                'action_sync_if_stale: account %s has sync_status=%s — forcing immediate sync',
                self.id, self.sync_status,
            )
            return self.action_sync()

        now = fields.Datetime.now()
        Msg = self.env['lugal.email.message'].sudo()
        inbox_count = Msg.search_count([
            ('account_id', '=', self.id),
            ('folder', '=', 'inbox'),
            ('is_deleted', '=', False),
        ])
        if not force:
            delta = (now - self.last_sync_date).total_seconds()
            limit = SYNC_THROTTLE_EMPTY_SECONDS if inbox_count == 0 else SYNC_THROTTLE_SECONDS
            if delta < limit:
                return {'skipped': True, 'reason': 'throttle', 'sync_status': self.sync_status}

        return self.action_sync()

    def _sync_sent_folder(self, conn):
        """
        Incrementally import messages from the IMAP Sent folder into Odoo
        so they appear in the "sent" mailbox view.

        Uses an ir.config_parameter as the UID cursor so no model change is needed.
        Skips messages that already exist in the local DB (e.g. sent via our system).
        Called from action_sync with the already-open IMAP connection.
        """
        import email as _email
        import json as _json

        Msg = self.env['lugal.email.message'].sudo()
        ICP = self.env['ir.config_parameter'].sudo()
        cursor_key = f'lugal.email.sent_max_uid.{self.id}'

        try:
            sent_folder = self._get_server_folder_name('sent', existing_conn=conn)
        except Exception:
            sent_folder = 'Sent'

        try:
            typ, data = conn.select(sent_folder, readonly=True)
            if typ != 'OK' or not data:
                _logger.warning(
                    'Sent folder sync: SELECT %r failed for acc=%s (typ=%s) — '
                    'clearing cached name and retrying discovery',
                    sent_folder, self.id, typ,
                )
                # Clear cached folder name and try auto-discovery again
                cache_key = f'lugal.email.folder.{self.id}.sent'
                self.env['ir.config_parameter'].sudo().set_param(cache_key, '')
                try:
                    sent_folder = self._get_server_folder_name('sent', existing_conn=conn)
                    typ, data = conn.select(sent_folder, readonly=True)
                    if typ != 'OK' or not data:
                        _logger.warning(
                            'Sent folder fallback also failed for acc=%s: folder=%r',
                            self.id, sent_folder,
                        )
                        return
                except Exception:
                    return
        except Exception as exc:
            _logger.warning('Sent folder select failed for acc=%s: %s', self.id, exc)
            return

        try:
            max_uid_cursor = int(ICP.get_param(cursor_key, '0') or '0')
        except (ValueError, TypeError):
            max_uid_cursor = 0

        # Fetch only new UIDs (above our cursor)
        search_criteria = f'UID {max_uid_cursor + 1}:*' if max_uid_cursor else 'ALL'
        try:
            typ, uid_data = conn.uid('search', None, search_criteria)
        except Exception as exc:
            _logger.debug('Sent UID search failed for acc=%s: %s', self.id, exc)
            return

        if typ != 'OK' or not uid_data or not uid_data[0]:
            return

        uid_list = [int(u) for u in uid_data[0].split() if u.isdigit() and int(u) > max_uid_cursor]
        if not uid_list:
            return

        # Fetch in batches of 25 (Sent folder items are usually larger)
        BATCH = 25
        max_seen = max_uid_cursor
        uid_re = re.compile(br'UID\s+(\d+)')

        for i in range(0, len(uid_list), BATCH):
            batch = uid_list[i:i + BATCH]
            uid_set = ','.join(str(u) for u in batch)
            try:
                typ, items = conn.uid('fetch', uid_set, '(FLAGS RFC822.HEADER)')
            except Exception:
                continue
            if typ != 'OK' or not items:
                continue

            for item in items:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                meta, header_bytes = item[0], item[1]
                if not isinstance(meta, bytes):
                    continue
                m = uid_re.search(meta)
                if not m:
                    continue
                uid_int = int(m.group(1))
                if uid_int <= max_uid_cursor:
                    continue

                try:
                    msg = _email.message_from_bytes(header_bytes, policy=policy.default)
                    message_id = (msg.get('Message-ID') or '').strip() or False
                    subject    = self._decode_mime_header(msg.get('Subject', ''))
                    from_name, from_addr = parseaddr(msg.get('From', ''))
                    if from_name:
                        from_name = self._decode_mime_header(from_name)

                    date_hdr = msg.get('Date')
                    dt = None
                    if date_hdr:
                        try:
                            from email.utils import parsedate_to_datetime as _p2d
                            dt = _p2d(date_hdr)
                            if dt.tzinfo is not None:
                                dt = dt.replace(tzinfo=None)
                        except Exception:
                            pass
                    if not dt:
                        dt = fields.Datetime.now()

                    to_raw  = msg.get_all('To', [])
                    to_list = [{'name': self._decode_mime_header(n or ''), 'email': e}
                               for n, e in getaddresses(to_raw) if e]
                    cc_raw  = msg.get_all('Cc', [])
                    cc_list = [{'name': self._decode_mime_header(n or ''), 'email': e}
                               for n, e in getaddresses(cc_raw) if e]

                    # Skip if already in local DB (e.g. sent via our own SMTP send)
                    domain = [
                        ('account_id', '=', self.id),
                        ('folder', '=', 'sent'),
                    ]
                    if message_id:
                        domain.append(('message_id', '=', message_id))
                    else:
                        domain += [('subject', '=', subject or '(no subject)'), ('date', '=', dt)]

                    if not Msg.search_count(domain):
                        Msg.create({
                            'account_id':   self.id,
                            'folder':       'sent',
                            'imap_uid':     uid_int,
                            'subject':      subject or '(no subject)',
                            'from_name':    from_name or '',
                            'from_address': from_addr or '',
                            'to_addresses': _json.dumps(to_list),
                            'cc_addresses': _json.dumps(cc_list),
                            'message_id':   message_id or False,
                            'date':         dt,
                            'is_read':      True,  # sent messages are always read
                            'smtp_delivered': True,
                            'body_fetched': False,
                        })

                    if uid_int > max_seen:
                        max_seen = uid_int

                except Exception as exc:
                    _logger.warning('Sent folder upsert failed uid=%s acc=%s: %s', uid_int, self.id, exc)

        if max_seen > max_uid_cursor:
            ICP.set_param(cursor_key, str(max_seen))
            _logger.info(
                'Sent folder sync: acc=%s new_max_uid=%s (was %s)',
                self.id, max_seen, max_uid_cursor,
            )

    def action_sync(self):
        """Import INBOX and Sent folder messages over IMAP."""
        self.ensure_one()
        Msg = self.env['lugal.email.message'].sudo()
        if not (self.password or '').strip():
            self.write({'sync_status': 'error', 'sync_error_msg': 'Missing app password on email account'})
            return {'sync_status': 'error', 'message': 'Missing app password on email account'}

        # Full re-bootstrap if cache was cleared but UID cursor is stale.
        if not Msg.search_count([
            ('account_id', '=', self.id), ('folder', '=', 'inbox'), ('is_deleted', '=', False),
        ]):
            self.imap_inbox_max_uid = 0

        try:
            import imaplib
            with self._imap_session() as conn:
                typ, data = conn.select('INBOX', readonly=True)
                if typ != 'OK' or not data:
                    raise imaplib.IMAP4.error('INBOX select failed')
                num_msgs = int(data[0])
                max_uid_cursor = self.imap_inbox_max_uid or 0
                uid_re = re.compile(br'UID\s+(\d+)')

                def _parse_batch_fetch(data_list):
                    """
                    Parse an imaplib FETCH response list into [(uid_int, raw_bytes, meta_bytes)].
                    Works for both conn.fetch(...) and conn.uid('fetch', ...) responses.
                    imaplib interleaves (meta, body) tuples with b')' separators; we skip
                    anything that is not a (meta, body) tuple with non-empty payload.
                    """
                    parsed = []
                    for item in data_list:
                        if not isinstance(item, tuple) or len(item) < 2:
                            continue
                        meta, payload = item[0], item[1]
                        if not isinstance(meta, bytes):
                            continue
                        if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                            continue
                        m = uid_re.search(meta)
                        if m:
                            parsed.append((int(m.group(1)), bytes(payload), meta))
                    return parsed

                imported = 0
                max_seen = max_uid_cursor

                def _upsert_batch(items, min_uid=0, headers_only=False):
                    """Upsert a parsed batch, skipping UIDs we already have."""
                    nonlocal imported, max_seen
                    for uid_val, raw, flags_meta in items:
                        if uid_val <= min_uid:
                            continue
                        try:
                            self._upsert_inbox_message(uid_val, raw, flags_meta, headers_only=headers_only)
                            imported += 1
                            if uid_val > max_seen:
                                max_seen = uid_val
                        except Exception:
                            _logger.warning(
                                'IMAP upsert failed uid=%s account=%s', uid_val, self.id, exc_info=True,
                            )

                # IMAP fetch specs:
                # • Header-only (fast, ~1 KB/msg) — used for initial bulk import
                # • Full body  (slow, ~50 KB/msg) — used for incremental (typically 1-10 new msgs)
                HEADERS_FETCH = '(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO CC REPLY-TO DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
                BODY_FETCH    = '(UID FLAGS BODY.PEEK[])'

                if max_uid_cursor == 0:
                    # ── First import: headers only ────────────────────────────────
                    # Avoids downloading MBs of body data for hundreds of old emails.
                    if num_msgs > 0:
                        start_seq = max(1, num_msgs - SYNC_MAX_MESSAGES + 1)
                        seq_range = f'{start_seq}:{num_msgs}'
                        typ, data_list = conn.fetch(seq_range, HEADERS_FETCH)
                        if typ == 'OK' and data_list:
                            _upsert_batch(_parse_batch_fetch(data_list), min_uid=0, headers_only=True)
                else:
                    # ── Incremental: only fetch new UIDs (full body, typically 1-10 msgs) ──
                    typ, uid_data = conn.uid('search', None, 'UID', '%d:*' % (max_uid_cursor + 1))
                    todo = []
                    if typ == 'OK' and uid_data and uid_data[0]:
                        # Filter out Dovecot's quirk: UID N:* returns current max when N > max.
                        todo = [
                            u for u in sorted(int(x) for x in uid_data[0].split())
                            if u > max_uid_cursor
                        ][:SYNC_MAX_MESSAGES]

                    if not todo and num_msgs > 0:
                        # Fallback: server may not support UID range — batch tail scan (headers only).
                        start_seq = max(1, num_msgs - SYNC_MAX_MESSAGES + 1)
                        seq_range = f'{start_seq}:{num_msgs}'
                        typ, data_list = conn.fetch(seq_range, HEADERS_FETCH)
                        if typ == 'OK' and data_list:
                            _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=True)
                    elif todo:
                        # Full body for new messages — few messages, typically fast.
                        uid_set = ','.join(str(u) for u in todo)
                        typ, data_list = conn.uid('fetch', uid_set, BODY_FETCH)
                        if typ == 'OK' and data_list:
                            _upsert_batch(_parse_batch_fetch(data_list), min_uid=max_uid_cursor, headers_only=False)

                # ── Sent folder sync ─────────────────────────────────────────────
                # Reuse the same connection to also pull sent messages so they
                # appear in our "sent" mailbox and match webmail / Outlook.
                try:
                    self._sync_sent_folder(conn)
                except Exception:
                    _logger.warning('Sent folder sync failed for acc=%s', self.id, exc_info=True)


            unread = Msg.search_count([
                ('account_id', '=', self.id),
                ('folder', '=', 'inbox'),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])

            # Use a savepoint so that a concurrent-update / serialization error
            # from updating the account row does NOT abort the outer transaction.
            # Without this, PostgreSQL would roll back all the message INSERTs
            # created above, making newly-arrived emails disappear.
            now_dt = fields.Datetime.now()
            try:
                with self.env.cr.savepoint():
                    self.write({
                        'sync_status':        'ok',
                        'last_sync_date':     now_dt,
                        'unread_count':       unread,
                        'imap_inbox_max_uid': max_seen,
                        'sync_error_msg':     False,
                    })
            except Exception:
                _logger.warning(
                    'action_sync: account %s status write failed (concurrent update) '
                    '— message inserts are preserved', self.id,
                )

            return {
                'sync_status':    'ok',
                'last_sync_date': now_dt.isoformat(),
                'unread_count':   unread,
                'imported':       imported,
            }
        except Exception as exc:
            # Wrap this write in a savepoint too: if the outer exception left the
            # transaction in a bad state (e.g. IMAP connect error after a prior
            # failed SQL), we still want to record the error without aborting again.
            try:
                with self.env.cr.savepoint():
                    self.write({'sync_status': 'error', 'sync_error_msg': str(exc)})
            except Exception:
                pass
            _logger.exception('action_sync failed for account %s', self.id)
            return {'sync_status': 'error', 'message': str(exc)}

    def sync_custom_imap_folder(self, imap_folder_path, headers_only=True):
        """Import messages from a single non-standard IMAP folder into Odoo.

        ``action_sync`` only pulls INBOX + Sent.  User-created folders (rule
        destinations like ``INBOX.syednaqvi.Important``) must be imported here
        so ``GET …/sync?folder=…`` returns rows.

        * ``imap_folder_path`` must match the LIST path (same casing as server).
        * Uses the same header-only tail fetch strategy as first-time INBOX import.
        * Does **not** run inbox rules on imported rows (avoids move loops).
        """
        self.ensure_one()
        if not (self.password or '').strip():
            return {'imported': 0, 'error': 'no password', 'resolved_path': ''}
        if not (imap_folder_path or '').strip():
            return {'imported': 0, 'error': 'empty path', 'resolved_path': ''}

        path = self._resolve_imap_mailbox_path(imap_folder_path.strip())
        _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        if path.lower() in _LOGICAL:
            return {'imported': 0, 'error': 'use action_sync for standard folders', 'resolved_path': path}

        imported = 0
        diag = None
        try:
            import imaplib
            with self._imap_session() as conn:
                typ, data = conn.select(path, readonly=True)
                if typ != 'OK' or not data:
                    return {'imported': 0, 'error': f'select failed typ={typ!r} path={path!r}', 'resolved_path': path}

                uid_re = re.compile(br'UID\s+(\d+)')

                def _parse_batch_fetch(data_list):
                    parsed = []
                    if not data_list:
                        return parsed
                    for item in data_list:
                        if not isinstance(item, tuple) or len(item) < 2:
                            continue
                        meta, payload = item[0], item[1]
                        if not isinstance(meta, bytes):
                            continue
                        if isinstance(payload, str):
                            payload = payload.encode('utf-8', errors='replace')
                        if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                            continue
                        m = uid_re.search(meta)
                        if m:
                            parsed.append((int(m.group(1)), bytes(payload), meta))
                    return parsed

                # Prefer UID SEARCH + UID FETCH — sequence-number FETCH is unreliable on
                # some Dovecot/cPanel builds when the mailbox was just created or after
                # concurrent expunges.  This matches how we incrementally fetch INBOX.
                HEADERS_FETCH = (
                    '(UID FLAGS BODY.PEEK[HEADER.FIELDS '
                    '(FROM TO CC BCC REPLY-TO DATE SUBJECT MESSAGE-ID IN-REPLY-TO REFERENCES)])'
                )
                FULL_HDR_FETCH = '(UID FLAGS BODY.PEEK[HEADER])'

                typ_s, d_s = conn.uid('search', None, 'ALL')
                uids = []
                raw_search = b''
                if typ_s == 'OK' and d_s and d_s[0] is not None:
                    raw_search = d_s[0] if isinstance(d_s[0], (bytes, bytearray)) else str(d_s[0]).encode()
                    parts = raw_search.split()
                    uids = sorted(int(x) for x in parts if x.isdigit())

                diag = {
                    'uid_search_typ': typ_s,
                    'uid_count':      len(uids),
                }

                if not uids:
                    return {
                        'imported': 0,
                        'error':      None,
                        'resolved_path': path,
                        'note':       'mailbox_empty_or_uid_search_empty',
                        'diagnostics': diag,
                    }

                tail = uids[-SYNC_MAX_MESSAGES:]
                diag['fetch_uid_min'] = tail[0] if tail else None
                diag['fetch_uid_max'] = tail[-1] if tail else None

                def _do_fetch(uid_chunk, fetch_macro):
                    nonlocal imported
                    uid_csv = ','.join(str(u) for u in uid_chunk)
                    typ_f, data_list = conn.uid('fetch', uid_csv, fetch_macro)
                    diag.setdefault('fetch_typs', []).append(typ_f)
                    if typ_f != 'OK' or not data_list:
                        return 0
                    parsed = _parse_batch_fetch(data_list)
                    diag.setdefault('parsed_per_fetch', []).append(len(parsed))
                    n = 0
                    for uid_val, raw, flags_meta in parsed:
                        try:
                            self._upsert_inbox_message(
                                uid_val, raw, flags_meta,
                                headers_only=headers_only,
                                folder_key=path,
                                run_rules=False,
                            )
                            n += 1
                        except Exception:
                            _logger.warning(
                                'custom folder upsert failed uid=%s folder=%s acc=%s',
                                uid_val, path, self.id, exc_info=True,
                            )
                    imported += n
                    return n

                # Chunk UID FETCH (some servers reject very long UID sets)
                _BATCH = 45
                for i in range(0, len(tail), _BATCH):
                    _do_fetch(tail[i:i + _BATCH], HEADERS_FETCH)

                # Fallback: HEADER.FIELDS response shape not parsed — try full RFC822 header
                if imported == 0 and tail:
                    for i in range(0, len(tail), _BATCH):
                        _do_fetch(tail[i:i + _BATCH], FULL_HDR_FETCH)

                if imported == 0 and tail:
                    diag['note'] = 'uid_search_ok_but_fetch_or_upsert_yielded_zero'

        except Exception as exc:
            _logger.warning('sync_custom_imap_folder acc=%s path=%s: %s', self.id, path, exc)
            ret = {'imported': imported, 'error': str(exc), 'resolved_path': path}
            if diag is not None:
                ret['diagnostics'] = diag
            return ret
        ret = {'imported': imported, 'error': None, 'resolved_path': path}
        if diag is not None:
            ret['diagnostics'] = diag
        return ret

    def _imap_list_all_mailbox_names(self):
        """Return every mailbox path from IMAP LIST (raw server strings)."""
        self.ensure_one()
        try:
            with self._imap_session() as conn:
                typ, raw_list = conn.list()
            if typ != 'OK' or not raw_list:
                return []
            lr = re.compile(
                r'^\((?P<flags>[^)]*)\)\s+'
                r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                r'(?P<name>.+?)\s*$'
            )
            names = []
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = lr.match(line.strip())
                if not m:
                    continue
                name = m.group('name').strip().strip('"')
                if name:
                    names.append(name)
            return names
        except Exception:
            _logger.warning('_imap_list_all_mailbox_names failed acc=%s', self.id, exc_info=True)
            return []

    def imap_child_mailboxes(self, parent_path):
        """Return full IMAP paths of mailboxes directly under ``parent_path`` (any hierarchy).

        Used when ``parent_path`` is a Dovecot/cPanel *namespace* folder that has
        no messages of its own (UID SEARCH empty) but child folders such as
        ``INBOX.user.Important`` hold the mail.
        """
        self.ensure_one()
        parent = self._resolve_imap_mailbox_path((parent_path or '').strip())
        if not parent:
            return []
        pl = parent.lower()
        all_names = self._imap_list_all_mailbox_names()
        out = []
        for n in all_names:
            nl = n.lower()
            if nl == pl:
                continue
            if nl.startswith(pl + '.') or n.startswith(parent + '/'):
                out.append(n)
        return sorted(set(out))

    def sync_imap_branch_mailboxes(self, parent_path, max_children=40):
        """Run ``sync_custom_imap_folder`` on ``parent_path`` and every child mailbox."""
        self.ensure_one()
        parent = self._resolve_imap_mailbox_path((parent_path or '').strip())
        children = self.imap_child_mailboxes(parent)
        detail = []
        total = 0
        pr = self.sync_custom_imap_folder(parent)
        total += int(pr.get('imported') or 0)
        detail.append({'path': parent, **pr})
        for ch in children[:max_children]:
            r = self.sync_custom_imap_folder(ch)
            total += int(r.get('imported') or 0)
            detail.append({'path': ch, **r})
        return {
            'parent_resolved': parent,
            'children':        children,
            'imported_total':  total,
            'per_mailbox':     detail,
        }

    def _resolve_imap_mailbox_path(self, requested_path: str) -> str:
        """Return the server's exact mailbox name for a path (case / delimiter)."""
        req = (requested_path or '').strip()
        if not req:
            return req
        _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        if req.lower() in _LOGICAL:
            return req
        try:
            with self._imap_session() as conn:
                typ, raw_list = conn.list()
            if typ != 'OK' or not raw_list:
                return req
            # Delimiter may be quoted ("." or "/") or NIL on some servers.
            lr = re.compile(
                r'^\((?P<flags>[^)]*)\)\s+'
                r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                r'(?P<name>.+?)\s*$'
            )
            req_lower = req.lower()
            for item in raw_list:
                if not item:
                    continue
                line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                m = lr.match(line.strip())
                if not m:
                    continue
                name = m.group('name').strip().strip('"')
                if name.lower() == req_lower:
                    return name
        except Exception:
            return req
        return req

    @api.model
    def action_sync_all_accounts(self):
        """
        Background cron entry-point.
        Syncs INBOX for every active account that has a password configured.
        Called by the ir.cron scheduler; runs each account in its own savepoint
        so one failure does not abort the others.

        De-duplicates by IMAP credential so accounts sharing the same login
        only open ONE connection per cron run, preventing per-user connection
        limit errors on the mail server.

        Also detects accounts with a stale sync_status='ok' that have never
        actually imported any messages — these are typically accounts where the
        password was set up during a previous test run but auth has since failed.
        Such accounts are included in the cron run so their status is updated.
        """
        accounts = self.search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])
        synced_creds: set = set()
        for acc in accounts:
            if not (acc.password or '').strip():
                # Mark completely unconfigured accounts clearly
                if acc.sync_status not in ('never',):
                    try:
                        with self.env.cr.savepoint():
                            acc.write({'sync_status': 'never', 'sync_error_msg': False})
                    except Exception:
                        pass
                continue
            cred = (
                (acc.imap_host or '').strip().lower(),
                int(acc.imap_port or (993 if acc.imap_use_ssl else 143)),
                (acc.username or acc.email_address or '').strip().lower(),
            )
            if cred in synced_creds:
                continue  # already synced this mailbox in this cron run
            synced_creds.add(cred)
            try:
                acc.action_sync()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception('Cron IMAP sync failed for account %s (%s)', acc.id, acc.email_address)

    def _store_imap_attachments(self, msg_record, email_msg):
        """Extract MIME attachments from a parsed email and store as ir.attachment.

        Skips parts that are already stored (deduplicates by name + size).
        Called after the full message body is downloaded from IMAP.
        """
        import base64 as _b64
        import uuid as _uuid
        import mimetypes as _mimetypes

        IrAtt = self.env['ir.attachment'].sudo()
        existing_names = {
            a.name
            for a in IrAtt.search([
                ('res_model', '=', 'lugal.email.message'),
                ('res_id',    '=', msg_record.id),
            ])
        }

        for part in email_msg.walk():
            # Only process attachment/inline parts with a filename
            disposition = part.get_content_disposition() or ''
            filename = part.get_filename()
            if not filename and 'attachment' not in disposition and 'inline' not in disposition:
                continue
            if not filename:
                continue
            filename = self._decode_mime_header(filename)
            if filename in existing_names:
                continue

            att_data = part.get_payload(decode=True)
            if not att_data:
                continue

            mime = part.get_content_type() or _mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            att_token = _uuid.uuid4().hex

            # Detect inline (embedded) parts: Content-Disposition = inline AND has Content-ID.
            # These are pasted / drag-dropped / signature images embedded in the body.
            # We tag them with "__inline_cid__:<cid>" in the description field so the
            # API response separates them into `inline_attachments` instead of `attachments`.
            raw_cid = part.get('Content-ID') or ''
            # Content-ID is usually wrapped in angle brackets: <img-abc@lugal.mail>
            cid_value = raw_cid.strip('<> ')
            is_inline_part = ('inline' in disposition) and bool(cid_value)
            description = f'__inline_cid__:{cid_value}' if is_inline_part else None

            try:
                IrAtt.create({
                    'name':         filename,
                    'mimetype':     mime,
                    'datas':        _b64.b64encode(att_data).decode('utf-8'),
                    'type':         'binary',
                    'res_model':    'lugal.email.message',
                    'res_id':       msg_record.id,
                    'access_token': att_token,
                    **(({'description': description}) if description else {}),
                })
                existing_names.add(filename)
                _logger.debug(
                    'Stored IMAP attachment %r (%d bytes) for msg=%s inline=%s',
                    filename, len(att_data), msg_record.id, is_inline_part,
                )
            except Exception:
                _logger.warning(
                    'Failed to store IMAP attachment %r for msg=%s',
                    filename, msg_record.id, exc_info=True,
                )

    def fetch_message_body(self, message_id):
        """
        Fetch the full body of a single message from IMAP on demand.
        Called when the user opens an email that was imported headers-only.
        Returns the updated message record, or None on failure.
        """
        self.ensure_one()
        Msg = self.env['lugal.email.message'].sudo()
        msg = Msg.browse(message_id)
        if not msg.exists() or msg.account_id.id != self.id:
            return None
        if msg.body_fetched:
            return msg
        if not msg.imap_uid:
            return msg

        try:
            import imaplib
            with self._imap_session() as conn:
                _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
                raw_folder = msg.folder or 'inbox'
                if raw_folder == 'inbox':
                    folder = 'INBOX'
                elif raw_folder in _LOGICAL:
                    try:
                        folder = self._get_server_folder_name(raw_folder, existing_conn=conn)
                    except Exception:
                        folder = raw_folder.capitalize()
                else:
                    folder = raw_folder
                typ, _ = conn.select(folder, readonly=True)
                if typ != 'OK':
                    return msg
                typ, data_list = conn.uid('fetch', str(msg.imap_uid), '(FLAGS BODY.PEEK[])')
            if typ != 'OK' or not data_list:
                return msg

            for item in data_list:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                meta, payload = item[0], item[1]
                if not isinstance(payload, (bytes, bytearray)) or len(payload) == 0:
                    continue
                email_msg = email_lib.message_from_bytes(bytes(payload))
                body_text, body_html = self._extract_best_body(email_msg)
                msg.write({
                    'body_text':    body_text or '',
                    'body_html':    body_html or False,
                    'body_fetched': True,
                })
                # Extract and store file attachments
                self._store_imap_attachments(msg, email_msg)
                return msg
        except Exception:
            _logger.exception('fetch_message_body failed for msg=%s account=%s', message_id, self.id)
        return msg

```

---
---
---
---

## File: `addons/lugal_email/models/email_message.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_message.py
# Component: Lugal Email — lugal.email.message model (email_message.py)

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class LugalEmailMessage(models.Model):
    """
    Cached/stored email message.
    Both inbound (fetched via IMAP) and outbound (sent via SMTP) messages land here.
    """
    _name = 'lugal.email.message'
    _description = 'Lugal Email Message'
    _order = 'date desc'
    _rec_name = 'subject'

    # ── Account / Folder ──────────────────────────────────────────────────────
    account_id = fields.Many2one(
        'lugal.email.account', string='Email Account',
        required=True, ondelete='cascade', index=True,
    )
    # Logical folders use lowercase names (inbox, sent, …).  Rules and moves may
    # store a full IMAP path (e.g. INBOX.sender_Important) — must be Char, not
    # Selection, or ORM writes silently fail and mail never leaves the inbox.
    folder = fields.Char(
        string='Folder',
        default='inbox',
        index=True,
        help='Logical mailbox (inbox, sent, …) or full IMAP folder path for custom mailboxes.',
    )

    # IMAP UID within the folder (used for dedup / incremental sync). Null for purely local rows.
    imap_uid       = fields.Integer(string='IMAP UID', index=True)

    # ── Headers ───────────────────────────────────────────────────────────────
    subject        = fields.Char(string='Subject')
    from_name      = fields.Char(string='From Name')
    from_address   = fields.Char(string='From Address', index=True)
    to_addresses   = fields.Text(string='To (JSON list of {name, email})')
    cc_addresses   = fields.Text(string='CC (JSON)')
    bcc_addresses  = fields.Text(string='BCC (JSON)')
    reply_to       = fields.Char(string='Reply-To')
    message_id     = fields.Char(string='Message-ID (IMAP)', index=True)
    in_reply_to    = fields.Char(string='In-Reply-To')
    # Space-separated chain of ancestor Message-IDs (RFC 2822 References header).
    # Column quoted because "references" is a reserved word in PostgreSQL.
    references     = fields.Text(string='References', column='references')
    # Root Message-ID of the conversation thread.  All messages in the same
    # thread share the same thread_id.  Set to the first entry in References
    # (or to the message's own Message-ID when it is the root).
    thread_id      = fields.Char(string='Thread ID', index=True)
    date           = fields.Datetime(string='Date', index=True)

    # ── Body ──────────────────────────────────────────────────────────────────
    body_html = fields.Html(string='Body HTML', sanitize=False)
    body_text = fields.Text(string='Body Text')

    # ── Status ────────────────────────────────────────────────────────────────
    is_read      = fields.Boolean(string='Read',      default=False, index=True)
    is_starred   = fields.Boolean(string='Starred',    default=False)
    is_draft     = fields.Boolean(string='Draft',      default=False)
    # is_flagged maps to the IMAP \Flagged flag — independent of is_starred.
    # is_starred is a UI bookmark; is_flagged is the IMAP protocol flag.
    is_flagged   = fields.Boolean(string='Flagged',    default=False, index=True)
    # is_important stores the "important" marker (Gmail \Important or manual).
    is_important = fields.Boolean(string='Important', default=False, index=True)

    # Timestamp set the first time this message is marked as read.
    # Null for messages that have never been opened.
    read_at    = fields.Datetime(string='Read At', readonly=False)

    # ── CRM Links (generic — no direct Many2one to avoid circular deps) ───────
    linked_model       = fields.Char(string='Linked Model', index=True)
    linked_record_id   = fields.Integer(string='Linked Record ID', index=True)
    linked_record_name = fields.Char(string='Linked Record Name')

    # Convenience integer shortcuts — resolved at API layer, not at ORM layer
    linked_customer_id = fields.Integer(string='Linked Customer ID', index=True)
    linked_customer_name = fields.Char(string='Linked Customer Name')
    linked_ticket_id   = fields.Integer(string='Linked Ticket ID', index=True)
    linked_ticket_name = fields.Char(string='Linked Ticket Name')

    # ── SMTP Delivery Status ───────────────────────────────────────────────────
    smtp_delivered = fields.Boolean(
        string='SMTP Delivered', default=False,
        help='True when the message was successfully handed off to the SMTP server.',
    )
    smtp_error = fields.Char(
        string='SMTP Error',
        help='Last SMTP error message if delivery failed.',
    )
    # smtp_status is the canonical delivery state returned to the FE.
    # 'pending'   = queued in background thread, not yet attempted
    # 'delivered' = SMTP server accepted the message
    # 'failed'    = SMTP server rejected or network error
    # Only meaningful for outbound (sent/draft) messages.
    smtp_status = fields.Selection([
        ('pending',   'Pending'),
        ('delivered', 'Delivered'),
        ('failed',    'Failed'),
    ], string='SMTP Status', default='pending', index=True)

    # True for messages we created locally (sent/reply/forward) or once the full
    # IMAP body has been downloaded on-demand. False for inbox rows that were
    # imported with headers only (body_html/body_text may be blank).
    body_fetched = fields.Boolean(
        string='Full Body Fetched', default=False,
        help='False = only headers synced; body fetched on first open.',
    )

    # ── Mention / direct-address flag ────────────────────────────────────────
    # True when the account owner's email appears in the To: header
    # (i.e. the message was sent directly to them, not just CC'd).
    # Matches Outlook "Mentioned Mail" / Exchange behaviour.
    is_mentioned = fields.Boolean(string='Mentioned', default=False, index=True)

    # ── RFC-822 message size in bytes (approx; populated on full-body sync) ──
    message_size = fields.Integer(string='Message Size (bytes)', default=0)

    # ── Soft delete ───────────────────────────────────────────────────────────
    active     = fields.Boolean(default=True)
    is_deleted = fields.Boolean(default=False, index=True)

    def write(self, vals):
        # Auto-stamp read_at the first time is_read transitions to True.
        if vals.get('is_read') and not vals.get('read_at'):
            for rec in self:
                if not rec.is_read and not rec.read_at:
                    vals = dict(vals, read_at=fields.Datetime.now())
                    break
        return super().write(vals)

```

---
---
---
---

## File: `addons/lugal_email/models/email_rule.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_rule.py
# Component: Lugal Email — lugal.email.rule model (email_rule.py)
"""
lugal.email.rule  — per-user / per-account inbox rules.

A rule has:
  • A set of conditions  (evaluated AND or OR)
  • A list of ordered actions applied when all conditions match
  • Optional stop-processing flag

Conditions JSON schema (list):
  [{"field": "from_address", "operator": "contains", "value": "boss@"}, ...]

  Supported fields:    from_address | to_addresses | cc_addresses | bcc_addresses
                       | subject | body_text
                       has_attachments | is_important | folder
  Supported operators: contains | not_contains | starts_with | ends_with
                       equals | not_equals | is_empty | is_not_empty

Actions JSON schema (list, executed in order):
  [{"action": "move_folder", "value": "archive"}, ...]

  Supported actions:
    mark_read          — set is_read = True
    mark_important     — set is_important = True
    mark_unimportant   — set is_important = False
    mark_starred       — set is_starred = True
    move_folder        — value = folder name (logical or IMAP path)
    forward_to         — value = email address (sends a copy via SMTP)
    stop_processing    — no more rules processed for this message
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalEmailRule(models.Model):
    _name        = 'lugal.email.rule'
    _description = 'Email Inbox Rule'
    _order       = 'sequence asc, id asc'

    name       = fields.Char(string='Rule Name', required=True)
    user_id    = fields.Many2one('res.users', string='Owner', required=True,
                                 default=lambda self: self.env.user, ondelete='cascade', index=True)
    account_id = fields.Many2one('lugal.email.account', string='Account (optional)',
                                 ondelete='cascade', index=True,
                                 help='Leave blank to apply to all accounts of the user.')
    is_active  = fields.Boolean(string='Active', default=True, index=True)
    sequence   = fields.Integer(string='Priority', default=10)

    # "all" = AND logic;  "any" = OR logic across conditions
    match_mode = fields.Selection([
        ('all', 'All conditions match (AND)'),
        ('any', 'Any condition matches (OR)'),
    ], string='Match Mode', default='all', required=True)

    conditions_json = fields.Text(
        string='Conditions (JSON)', default='[]',
        help='List of {field, operator, value} dicts.',
    )
    actions_json = fields.Text(
        string='Actions (JSON)', default='[]',
        help='Ordered list of {action, value} dicts.',
    )
    stop_processing = fields.Boolean(
        string='Stop processing further rules', default=False,
    )

    # Audit
    last_triggered_at = fields.Datetime(string='Last Triggered', readonly=True)
    trigger_count     = fields.Integer(string='Times Triggered', default=0, readonly=True)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_conditions(self):
        try:
            return json.loads(self.conditions_json or '[]') or []
        except Exception:
            return []

    def _get_actions(self):
        try:
            return json.loads(self.actions_json or '[]') or []
        except Exception:
            return []

    # ── Condition evaluation ────────────────────────────────────────────────────

    @staticmethod
    def _eval_condition(cond, msg_vals: dict) -> bool:
        field    = cond.get('field', '')
        operator = cond.get('operator', 'contains')
        value    = str(cond.get('value', '')).lower()

        raw = msg_vals.get(field, '')

        # Boolean-like fields (msg_vals may use real bools or legacy strings)
        if field in ('has_attachments', 'is_important', 'is_read', 'is_starred'):
            if isinstance(raw, bool):
                raw_bool = raw
            else:
                s = str(raw).lower().strip()
                raw_bool = s in ('true', '1', 'yes', 'on')
            if operator == 'equals':
                return raw_bool == (value in ('true', '1', 'yes'))
            if operator == 'not_equals':
                return raw_bool != (value in ('true', '1', 'yes'))
            return False

        raw_str = str(raw).lower() if raw else ''

        if operator == 'contains':
            if value in raw_str:
                return True
            # from_address may be "Name <addr@host>"; match on parsed addr too
            if field == 'from_address' and '@' in value:
                try:
                    from email.utils import parseaddr
                    _, addr = parseaddr(str(raw or ''))
                    if addr and value in addr.lower():
                        return True
                except Exception:
                    pass
            return False
        if operator == 'not_contains':
            return value not in raw_str
        if operator == 'starts_with':
            return raw_str.startswith(value)
        if operator == 'ends_with':
            return raw_str.endswith(value)
        if operator == 'equals':
            return raw_str == value
        if operator == 'not_equals':
            return raw_str != value
        if operator == 'is_empty':
            return not raw_str
        if operator == 'is_not_empty':
            return bool(raw_str)
        return False

    def _matches(self, msg_vals: dict) -> bool:
        conds = self._get_conditions()
        if not conds:
            return True
        results = [self._eval_condition(c, msg_vals) for c in conds]
        if self.match_mode == 'any':
            return any(results)
        return all(results)

    # ── Action execution ────────────────────────────────────────────────────────

    def _apply_actions(self, msg_record):
        """Apply this rule's actions to a lugal.email.message record.

        Returns True if stop_processing should halt further rules.
        """
        write_vals = {}
        stop       = self.stop_processing
        # Track any IMAP move we need to fire after writing the DB row.
        _imap_moves = []   # list of (imap_uid, from_imap_path, to_imap_path)

        LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

        for act in self._get_actions():
            action = act.get('action', '')
            value  = (act.get('value') or '').strip()
            try:
                if action == 'mark_read':
                    write_vals['is_read'] = True
                elif action == 'mark_important':
                    write_vals['is_important'] = True
                elif action == 'mark_unimportant':
                    write_vals['is_important'] = False
                elif action == 'mark_starred':
                    write_vals['is_starred'] = True
                elif action == 'move_folder':
                    if not value:
                        continue
                    if value.lower() in LOGICAL:
                        # Logical folder — just update local DB column.
                        write_vals['folder'] = value.lower()
                        # Also fire the IMAP move for standard folders.
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            from_imap = acc._get_server_folder_name(
                                msg_record.folder) if msg_record.folder not in LOGICAL \
                                else ('INBOX' if msg_record.folder == 'inbox'
                                      else acc._get_server_folder_name(msg_record.folder))
                            _imap_moves.append(('logical', msg_record.imap_uid, from_imap, value.lower()))
                    else:
                        # Custom IMAP folder path (e.g. "INBOX.AllFromUmar").
                        # Store the raw path in the folder field so the messages
                        # list endpoint can query it with folder=INBOX.AllFromUmar.
                        write_vals['folder'] = value
                        # Queue an async IMAP MOVE to the raw path.
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            # Determine the current IMAP folder path for the source.
                            cur_folder = msg_record.folder or 'inbox'
                            if cur_folder.lower() == 'inbox':
                                from_imap = 'INBOX'
                            elif cur_folder.lower() in LOGICAL:
                                try:
                                    from_imap = acc._get_server_folder_name(cur_folder.lower())
                                except Exception:
                                    from_imap = 'INBOX'
                            else:
                                from_imap = cur_folder   # already a raw IMAP path
                            _imap_moves.append(('raw', msg_record.imap_uid, from_imap, value))
                elif action == 'stop_processing':
                    stop = True
            except Exception as _e:
                _logger.warning('Email rule action %r failed: %s', action, _e)

        if write_vals:
            try:
                msg_record.write(write_vals)
            except Exception as _e:
                _logger.warning('Email rule write failed: %s', _e)

        # Fire IMAP moves after the DB write so the row is committed.
        for move in _imap_moves:
            try:
                kind, imap_uid, from_imap, dest = move
                acc = msg_record.account_id
                if kind == 'raw':
                    acc._imap_move_to_raw_path_async(imap_uid, from_imap, dest)
                else:
                    acc._imap_move_async(imap_uid, from_imap, dest)
            except Exception as _me:
                _logger.warning('Email rule IMAP move failed: %s', _me)

        # Audit
        try:
            self.write({
                'last_triggered_at': fields.Datetime.now(),
                'trigger_count':     self.trigger_count + 1,
            })
        except Exception:
            pass

        return stop

    # ── Class-level executor called from _upsert_inbox_message ────────────────

    @api.model
    def apply_inbox_rules(self, msg_record, msg_vals: dict):
        """Run all active rules for the message owner against a freshly-created message.

        msg_vals: plain dict with the same keys as the create() vals dict.
        """
        account_id = msg_vals.get('account_id')
        if not account_id:
            return

        acc = self.env['lugal.email.account'].sudo().browse(account_id)
        if not acc.exists():
            return
        owner_uid = acc.user_id.id

        # Augment vals with boolean has_attachments sentinel (attachments not yet
        # linked when this runs, but rules can test other fields).
        msg_vals_aug = dict(msg_vals, has_attachments=False)

        rules = self.sudo().search([
            ('is_active', '=', True),
            ('user_id',   '=', owner_uid),
            '|',
            ('account_id', '=', account_id),
            ('account_id', '=', False),
        ], order='sequence asc, id asc')

        for rule in rules:
            try:
                if rule._matches(msg_vals_aug):
                    should_stop = rule._apply_actions(msg_record)
                    if should_stop:
                        break
            except Exception as _e:
                _logger.warning('Email rule %s evaluation error: %s', rule.id, _e)

```

---
---
---
---

## File: `addons/lugal_email/models/email_quick_step.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_quick_step.py
"""
lugal.email.quick.step — named action bundles applied in one click.

A quick step bundles several actions (same schema as email rules) under a
user-defined name and optional keyboard shortcut.

Steps JSON schema (list):
  [{"action": "mark_read"}, {"action": "move_folder", "value": "archive"}]

Supported actions (same set as email rules):
  mark_read | mark_important | mark_unimportant | mark_starred
  move_folder (value = logical or IMAP path) | forward_to (value = email)
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalEmailQuickStep(models.Model):
    _name        = 'lugal.email.quick.step'
    _description = 'Email Quick Step'
    _order       = 'sequence asc, id asc'

    name        = fields.Char(string='Quick Step Name', required=True)
    description = fields.Char(string='Description')
    user_id     = fields.Many2one('res.users', string='Owner', required=True,
                                  default=lambda self: self.env.user, ondelete='cascade', index=True)
    sequence    = fields.Integer(string='Display Order', default=10)
    icon        = fields.Char(string='Icon (optional)', help='Icon name hint for FE (e.g. "archive", "star").')
    steps_json  = fields.Text(
        string='Steps (JSON)', default='[]',
        help='Ordered list of {action, value} dicts to execute in sequence.',
    )
    # How many times the user has applied this quick step
    use_count   = fields.Integer(string='Use Count', default=0, readonly=True)

    def _get_steps(self):
        try:
            return json.loads(self.steps_json or '[]') or []
        except Exception:
            return []

    def apply_to_message(self, msg_record):
        """Apply the quick step's actions to a lugal.email.message record."""
        write_vals = {}
        for step in self._get_steps():
            action = step.get('action', '')
            value  = step.get('value', '')
            try:
                if action == 'mark_read':
                    write_vals['is_read'] = True
                elif action == 'mark_important':
                    write_vals['is_important'] = True
                elif action == 'mark_unimportant':
                    write_vals['is_important'] = False
                elif action == 'mark_starred':
                    write_vals['is_starred'] = True
                elif action == 'move_folder':
                    LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
                    if value.lower() in LOGICAL:
                        write_vals['folder'] = value.lower()
            except Exception as _e:
                _logger.warning('Quick step action %r failed: %s', action, _e)

        if write_vals:
            msg_record.write(write_vals)

        try:
            self.write({'use_count': self.use_count + 1})
        except Exception:
            pass

```

---
---
---
---

## File: `addons/lugal_email/models/email_idle_watcher.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/models/email_idle_watcher.py
"""
IMAP poll-based email watcher — simple, reliable inbox notification.

Design (v3 — polling only, no IMAP IDLE)
-----------------------------------------
One polling thread per unique (imap_host, imap_port, username) credential
group.  Every _POLL_INTERVAL_SECS the thread calls action_sync() for every
account in the group.

When new messages are found, action_sync() automatically fires WebSocket
push notifications to the frontend via lugal_email_ws.py — the user sees
new email arrive without hitting sync or refreshing the screen.

Why polling instead of IMAP IDLE
---------------------------------
The mail server enforces a global 20-connection limit per source IP.
With 27 accounts all holding persistent IDLE connections we exceed that
limit, causing [LIMIT] errors and dropped notifications.  Polling opens
a connection, checks for mail, and closes it — so we never hold more than
a handful of connections simultaneously.  Maximum email arrival delay is
≤ _POLL_INTERVAL_SECS (15 s), which is acceptable for a business CRM.

Single-process ownership
------------------------
Odoo runs with workers=N OS processes. Without coordination every cron
worker would start its own duplicate polling threads.

We use a PostgreSQL row-level lock on ir.config_parameter (FOR UPDATE
NOWAIT) to ensure only ONE worker claims ownership.  The owning PID is
stored in the parameter.  When the owner dies the next cron run claims
the role.  _register_hook() clears stale PIDs at module load time.

Thread lifecycle
----------------
  start_all()          — called by the supervisor cron every minute.
  stop_credential(key) — gracefully stop one credential group's thread.
  stop_all()           — called during Odoo shutdown.
  status()             — returns monitoring info.
"""

import logging
import os
import threading
import time

from odoo import api, models

_logger = logging.getLogger(__name__)

# ── Cross-process ownership ───────────────────────────────────────────────────
_I_AM_OWNER: bool = False
_OWNER_PARAM = 'lugal.idle.supervisor.pid'

# ── Thread registry ───────────────────────────────────────────────────────────
# Key: (imap_host, imap_port, username)
_poll_threads:  dict[tuple, threading.Thread] = {}
_stop_events:   dict[tuple, threading.Event]  = {}
_poll_lock = threading.Lock()

# Maps cred_key → current set of account IDs in the thread.
# Updated atomically (under _poll_lock) when start_all() detects new accounts
# for a credential group that already has a live thread — no restart needed.
_thread_acc_ids: dict[tuple, set] = {}

# ── Timing constants ──────────────────────────────────────────────────────────
_POLL_INTERVAL_SECS     = 15   # maximum email arrival delay for any account
_WATCHDOG_INTERVAL_SECS = 30   # how often to detect newly-added accounts
_STAGGER_SECS           = 1.5  # stagger between thread starts on restart

# ── Watchdog ──────────────────────────────────────────────────────────────────
_watchdog_thread: threading.Thread | None = None
_watchdog_db:     str = ''


def _watchdog_loop(db_name: str):
    """
    Long-running background thread (owner process only).
    Calls start_all() every _WATCHDOG_INTERVAL_SECS so newly created
    email accounts start being polled within 30 s instead of up to 60 s
    (the cron interval).
    """
    global _I_AM_OWNER
    while _I_AM_OWNER:
        time.sleep(_WATCHDOG_INTERVAL_SECS)
        if not _I_AM_OWNER:
            break
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo
            with _Registry(db_name).cursor() as cr:
                env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
                env['lugal.email.idle.watcher'].start_all()
        except Exception:
            pass  # non-critical; cron is the fallback
    _logger.info('Poll watcher watchdog exited (pid=%d)', os.getpid())


def _pid_alive(pid: int) -> bool:
    """True if a process with this PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _sync_account(acc_id: int, db_name: str):
    """
    Open a short-lived DB cursor and run action_sync() for one account.
    Auth failures and network errors are logged but never crash the thread.
    """
    try:
        from odoo.modules.registry import Registry as _Registry
        import odoo as _odoo
        with _Registry(db_name).cursor() as cr:
            env = _odoo.api.Environment(cr, _odoo.SUPERUSER_ID, {})
            acc = env['lugal.email.account'].browse(acc_id)
            if acc.exists() and acc.is_active and not acc.is_deleted and (acc.password or '').strip():
                acc.action_sync()
    except Exception:
        _logger.exception('Poll sync failed for account %s', acc_id)


def _run_poll_watcher(
    cred_key:     tuple,   # (imap_host, imap_port, username)
    db_name:      str,
    imap_host:    str,
    username:     str,
    acc_ids:      list,
    stop_event:   threading.Event,
):
    """
    Simple polling loop for one credential group.

    Every _POLL_INTERVAL_SECS seconds:
      1. Sync every account in the group (action_sync checks for new IMAP
         messages and fires WebSocket notifications when new mail arrives).
      2. Sleep until the next interval.

    The thread exits only when stop_event is set (graceful shutdown) or
    _I_AM_OWNER becomes False (ownership transferred to another process).
    Individual sync errors are logged but do not stop the thread.
    """
    _logger.info(
        '[PollWatcher] Thread started for %s@%s (accounts=%s)',
        username, imap_host, acc_ids,
    )

    while not stop_event.is_set():
        if not _I_AM_OWNER:
            _logger.info(
                '[PollWatcher] %s@%s: no longer owner — thread exiting',
                username, imap_host,
            )
            break

        current_acc_ids = list(_thread_acc_ids.get(cred_key, set(acc_ids)))
        for acc_id in current_acc_ids:
            if stop_event.is_set():
                break
            _sync_account(acc_id, db_name)

        # Wait for the next poll cycle. stop_event.wait() wakes immediately
        # on shutdown so we never block a graceful restart for 15 seconds.
        stop_event.wait(_POLL_INTERVAL_SECS)

    with _poll_lock:
        _poll_threads.pop(cred_key, None)
        _stop_events.pop(cred_key, None)
        _thread_acc_ids.pop(cred_key, None)

    _logger.info(
        '[PollWatcher] Thread exited for %s@%s',
        username, imap_host,
    )


class LugalEmailIdleWatcher(models.Model):
    """
    Supervisor model — manages background polling threads that keep every
    user's inbox in sync without any user interaction.

    One thread per unique (imap_host, imap_port, username) credential group.
    """
    _name        = 'lugal.email.idle.watcher'
    _description = 'IMAP Poll Watcher Supervisor'

    def _register_hook(self):
        """
        Called once per process when Odoo loads the registry.

        Clears the stale owner PID from ir.config_parameter if the recorded
        process is no longer alive.  This prevents new workers from being
        blocked by a dead owner after an Odoo restart.
        """
        super()._register_hook()
        try:
            cr = self.env.cr
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                (_OWNER_PARAM,),
            )
            row = cr.fetchone()
            if row and row[0]:
                try:
                    stored_pid = int(row[0])
                    if not _pid_alive(stored_pid):
                        cr.execute(
                            "UPDATE ir_config_parameter SET value = '' WHERE key = %s",
                            (_OWNER_PARAM,),
                        )
                        _logger.info(
                            'Poll supervisor: cleared stale owner pid=%d (process is dead)',
                            stored_pid,
                        )
                except (ValueError, TypeError):
                    cr.execute(
                        "UPDATE ir_config_parameter SET value = '' WHERE key = %s",
                        (_OWNER_PARAM,),
                    )
        except Exception:
            pass

    @api.model
    def start_all(self):
        """
        Start polling threads for every active credential group that does
        not already have a running thread.

        Cross-process ownership: only ONE Odoo worker process runs threads.
        Uses FOR UPDATE NOWAIT on ir.config_parameter for atomic ownership
        claim — eliminates the race where two cron workers both try to claim.

        Called by the supervisor cron every minute and by the watchdog every
        _WATCHDOG_INTERVAL_SECS seconds.
        """
        global _I_AM_OWNER

        my_pid = os.getpid()

        # ── Ownership check / claim ──────────────────────────────────────────
        if _I_AM_OWNER:
            # Verify we still hold the stored PID (guards against zombie workers).
            cr = self.env.cr
            try:
                cr.execute(
                    "SELECT value FROM ir_config_parameter WHERE key = %s",
                    (_OWNER_PARAM,),
                )
                row = cr.fetchone()
                stored_pid_str = (row[0] if row else '') or ''
                stored_pid = int(stored_pid_str) if stored_pid_str.strip().isdigit() else 0
                if stored_pid and stored_pid != my_pid and _pid_alive(stored_pid):
                    _I_AM_OWNER = False
                    _logger.info(
                        'Poll supervisor: pid=%d lost ownership to pid=%d — stopping threads',
                        my_pid, stored_pid,
                    )
                    stop_all()
                    return 0
            except Exception:
                pass

        if not _I_AM_OWNER:
            cr = self.env.cr
            claimed = False
            try:
                with cr.savepoint():
                    cr.execute(
                        "SELECT value FROM ir_config_parameter "
                        "WHERE key = %s FOR UPDATE NOWAIT",
                        (_OWNER_PARAM,),
                    )
                    row = cr.fetchone()
                    stored = (row[0] if row else '') or ''
                    if stored:
                        try:
                            owner_pid = int(stored)
                            if _pid_alive(owner_pid) and owner_pid != my_pid:
                                _logger.debug(
                                    'Poll supervisor: pid=%d owns threads — '
                                    'this worker (pid=%d) skips',
                                    owner_pid, my_pid,
                                )
                                return 0
                        except (ValueError, TypeError):
                            pass
                    # Claim ownership while still holding the row lock.
                    if row:
                        cr.execute(
                            "UPDATE ir_config_parameter SET value = %s WHERE key = %s",
                            (str(my_pid), _OWNER_PARAM),
                        )
                    else:
                        cr.execute(
                            "INSERT INTO ir_config_parameter (key, value) "
                            "VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
                            (_OWNER_PARAM, str(my_pid), str(my_pid)),
                        )
                    claimed = True
            except Exception:
                _logger.debug(
                    'Poll supervisor: pid=%d lost ownership race — skipping', my_pid,
                )
                return 0
            if not claimed:
                return 0

            _I_AM_OWNER = True
            _logger.info('Poll supervisor: pid=%d claimed ownership', my_pid)

            # Start the watchdog so newly added accounts get picked up fast.
            global _watchdog_thread, _watchdog_db
            _watchdog_db = self.env.cr.dbname
            if _watchdog_thread is None or not _watchdog_thread.is_alive():
                _watchdog_thread = threading.Thread(
                    target=_watchdog_loop,
                    args=(_watchdog_db,),
                    daemon=True,
                    name='imap-poll-watchdog',
                )
                _watchdog_thread.start()
                _logger.info(
                    'Poll watchdog started (pid=%d, interval=%ds)',
                    my_pid, _WATCHDOG_INTERVAL_SECS,
                )

        # ── Build credential groups ──────────────────────────────────────────
        db_name  = self.env.cr.dbname
        accounts = self.env['lugal.email.account'].sudo().search([
            ('is_active', '=', True),
            ('is_deleted', '=', False),
        ])

        groups: dict[tuple, tuple] = {}
        for acc in accounts:
            pw = (acc.password or '').strip()
            if not pw:
                continue
            host  = (acc.imap_host or '').strip()
            port  = int(acc.imap_port or 993)
            uname = (acc.username or acc.email_address or '').strip()
            if not host or not uname:
                continue
            key = (host, port, uname)
            if key not in groups:
                groups[key] = ({'imap_host': host, 'imap_port': port,
                                'username': uname, 'password': pw}, [])
            groups[key][1].append(acc.id)

        stagger = 0.0
        started = 0

        # Stop threads for credential groups that no longer have active accounts.
        with _poll_lock:
            orphaned = [k for k in list(_poll_threads.keys()) if k not in groups]
        for key in orphaned:
            ev = _stop_events.get(key)
            if ev:
                ev.set()
                _logger.info(
                    'Poll supervisor: stopping orphaned thread for %s:%s/%s',
                    key[0], key[1], key[2],
                )

        for key, (cfg, acc_ids) in groups.items():
            with _poll_lock:
                existing = _poll_threads.get(key)
                if existing and existing.is_alive():
                    # Thread is healthy — just update the account list if needed.
                    current_ids = _thread_acc_ids.get(key, set())
                    new_ids = set(acc_ids) - current_ids
                    if new_ids:
                        _thread_acc_ids[key] = current_ids | new_ids
                        _logger.info(
                            'Poll supervisor: added %d new account(s) to live thread '
                            'for %s:%s/%s (total=%s)',
                            len(new_ids), key[0], key[1], key[2],
                            sorted(_thread_acc_ids[key]),
                        )
                    continue  # already running

                stop_ev = threading.Event()
                _thread_acc_ids[key] = set(acc_ids)

                def _make_target(k, c, ids, ev, delay):
                    def _target():
                        if delay:
                            time.sleep(delay)
                        _run_poll_watcher(
                            k, db_name,
                            c['imap_host'],
                            c['username'],
                            ids, ev,
                        )
                    return _target

                t = threading.Thread(
                    target=_make_target(key, cfg, list(acc_ids), stop_ev, stagger),
                    daemon=True,
                    name=f'imap-poll-{cfg["username"][:20]}',
                )
                _poll_threads[key] = t
                _stop_events[key]  = stop_ev
                t.start()
                stagger += _STAGGER_SECS
                started += 1

        if started:
            _logger.info(
                'Poll supervisor: started %d new thread(s) '
                '(%d credential group(s) total, poll interval=%ds)',
                started, len(groups), _POLL_INTERVAL_SECS,
            )
        return started

    @api.model
    def clear_backoff_for_account(self, account_id: int):
        """
        Legacy API — kept for compatibility.  With polling there is no backoff
        state to clear, so this simply calls start_all() to ensure the thread
        is running for the given account's credential group.
        """
        self.start_all()

    @api.model
    def stop_credential(self, imap_host, imap_port, username):
        """Stop the polling thread for a specific credential group."""
        key = (imap_host, int(imap_port), username)
        with _poll_lock:
            ev = _stop_events.get(key)
        if ev:
            ev.set()
            _logger.info('Poll supervisor: stop requested for %s:%s/%s', *key)

    @api.model
    def stop_all(self):
        """Signal all polling threads to stop (called on Odoo shutdown)."""
        global _I_AM_OWNER
        _I_AM_OWNER = False  # causes watchdog loop to exit
        with _poll_lock:
            events = list(_stop_events.values())
        for ev in events:
            ev.set()
        _logger.info('Poll supervisor: stop_all — %d thread(s) signalled', len(events))

    @api.model
    def status(self):
        """Return monitoring info for all polling threads."""
        result = []
        with _poll_lock:
            for key, t in _poll_threads.items():
                result.append({
                    'host':     key[0],
                    'port':     key[1],
                    'username': key[2],
                    'alive':    t.is_alive(),
                    'accounts': sorted(_thread_acc_ids.get(key, set())),
                    'mode':     'poll',
                    'interval': _POLL_INTERVAL_SECS,
                })
        return result

```

---
---
---
---

## File: `addons/lugal_email/migrations/1.1.1/pre-clear_folder_selections.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/migrations/1.1.1/pre-clear_folder_selections.py
# Component: Lugal Email — pre-migration 1.1.1 (clear folder field selection rows)
"""Allow lugal.email.message.folder to change from Selection to Char.

Odoo's post-upgrade cleanup of ir.model.fields.selection rows can crash with
AttributeError: 'Char' object has no attribute 'ondelete'.  Drop selection rows
before the field type changes.
"""


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields
            WHERE model = 'lugal.email.message' AND name = 'folder'
        )
        """
    )

```

---
---
---
---

## File: `addons/lugal_email/migrations/1.1.2/pre-clear_folder_selections.py`

```
# -*- coding: utf-8 -*-
# File: addons/lugal_email/migrations/1.1.2/pre-clear_folder_selections.py
# Component: Lugal Email — pre-migration 1.1.2 (clear folder field selection rows)
"""Idempotent: remove folder Selection rows if any remain (failed 1.1.1 upgrades)."""


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields
            WHERE model = 'lugal.email.message' AND name = 'folder'
        )
        """
    )

```

---
---
---
---

## File: `addons/lugal_email/data/cron.xml`

```
<?xml version="1.0" encoding="utf-8"?>
<!-- File: addons/lugal_email/data/cron.xml -->
<odoo>
    <data noupdate="1">
        <!--
            Background IMAP inbox sync — fallback poller (1 minute).
            IMAP IDLE watcher is the primary real-time path; this cron is a safety net.
            Note: Odoo ir.cron does NOT support 'seconds' as interval_type.
            Minimum granularity is 1 minute.
        -->
        <record id="ir_cron_lugal_email_imap_sync" model="ir.cron">
            <field name="name">Lugal Email: IMAP Inbox Sync</field>
            <field name="model_id" ref="lugal_email.model_lugal_email_account"/>
            <field name="state">code</field>
            <field name="code">model.action_sync_all_accounts()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">minutes</field>
            <field name="active">True</field>
            <field name="priority">5</field>
        </record>

        <!--
            IMAP IDLE supervisor — restarts crashed watcher threads (1 minute).
            In-process watchdog thread (5s interval) handles new accounts faster.
        -->
        <record id="ir_cron_lugal_email_idle_supervisor" model="ir.cron">
            <field name="name">Lugal Email: IMAP IDLE Supervisor</field>
            <field name="model_id" ref="lugal_email.model_lugal_email_idle_watcher"/>
            <field name="state">code</field>
            <field name="code">model.start_all()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">minutes</field>
            <field name="active">True</field>
            <field name="priority">5</field>
        </record>
    </data>
</odoo>

```

---
---
---
---

## File: `addons/lugal_email/security/ir.model.access.csv`

```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_lugal_email_account_user,lugal.email.account user,model_lugal_email_account,base.group_user,1,1,1,1
access_lugal_email_message_user,lugal.email.message user,model_lugal_email_message,base.group_user,1,1,1,1
access_lugal_email_idle_watcher_user,lugal.email.idle.watcher user,model_lugal_email_idle_watcher,base.group_user,1,0,0,0

```

---
---
---
---

