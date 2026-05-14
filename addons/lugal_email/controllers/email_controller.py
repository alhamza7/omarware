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
from odoo import http, fields
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

def _imap_quote_mailbox(path):
    """Return an IMAP-safe quoted mailbox name for use in raw imaplib commands.

    Python's imaplib does NOT quote mailbox names automatically.  Folder names
    that contain spaces, parentheses, or other IMAP atom-special characters MUST
    be wrapped in double-quotes before being sent to the server.  Without quoting,
    ``conn.create("INBOX.MailsFrom Weird guy")`` sends::

        C: TAG CREATE INBOX.MailsFrom Weird guy

    …and the server sees ``INBOX.MailsFrom`` as the mailbox name, truncating at
    the first space.  Quoting fixes this::

        C: TAG CREATE "INBOX.MailsFrom Weird guy"

    Only characters that require quoting trigger the wrapper; plain names are
    returned as-is so there is no regression for existing clean folder paths.
    """
    # IMAP atom-specials that force quoting (RFC 3501 §9)
    _NEEDS_QUOTE = set(' \t()\\"[]%*\x00\r\n')
    if any(c in _NEEDS_QUOTE for c in path):
        escaped = path.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return path


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
_cred_wait_timeout = 25.0

# Throttle mirrors (kept here so the controller doesn't import from the model).
_IMAP_THROTTLE_SECONDS = 30        # min gap between syncs when inbox has messages
_IMAP_THROTTLE_EMPTY_SECONDS = 20  # min gap when inbox is empty


def _truthy(v):
    return str(v or '').lower() in ('1', 'true', 'yes', 'on')


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

                # Credential-level gate: wait briefly instead of dropping the
                # sync request. Under load, silently skipping here makes the FE
                # depend on a later manual resync even though a notification was
                # already delivered.
                import time as _time
                wait_started = _time.monotonic()
                while True:
                    with _cred_sync_lock:
                        if cred_key not in _syncing_credentials:
                            _syncing_credentials.add(cred_key)
                            break
                    if _time.monotonic() - wait_started >= _cred_wait_timeout:
                        _logger.warning(
                            'Timed out waiting for IMAP credential sync gate '
                            'acc=%s credential=%s',
                            acc_id, cred_key,
                        )
                        cred_key = None
                        return
                    _time.sleep(0.25)

                if force:
                    acc.action_sync()
                else:
                    acc.action_sync_if_stale()
                cr.commit()

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

    Logical names ('inbox', 'sent', 'trash', …) are resolved through the
    account's cached per-server mapping so Gmail/Dovecot/cPanel differences
    are handled transparently.

    Custom IMAP paths (anything not in _LOGICAL_FOLDERS, e.g.
    'INBOX.syed_naqvi.Important') are returned AS-IS — they are already the
    correct server-side path and must NEVER be passed to _get_server_folder_name
    which would `capitalize()` them and produce a wrong name like
    'Inbox.syed_naqvi.important', causing silent IMAP flag-push failures.
    """
    _LOGICAL_FOLDERS = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    if local_folder.lower() == 'inbox':
        return 'INBOX'
    if local_folder.lower() in _LOGICAL_FOLDERS:
        try:
            return account.sudo()._get_server_folder_name(local_folder.lower())
        except Exception:
            return local_folder.capitalize()
    # Custom folder — the raw IMAP path is stored verbatim in the DB; use it directly.
    return local_folder


def _account_to_dict(acc):
    unread_count = acc.unread_count
    try:
        unread_count = acc.env['lugal.email.message'].sudo().search_count([
            ('account_id', '=', acc.id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
    except Exception:
        pass
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
        'unread_count':        unread_count,
        # password_set lets the FE know whether the app password has been entered
        # without ever exposing the actual credential value.
        'password_set':        bool(acc.password),
    }


def _refresh_account_unread_count(account):
    """Keep cached account unread_count aligned after read/unread actions."""
    if not account:
        return 0
    unread_count = account.env['lugal.email.message'].sudo().search_count([
        ('account_id', '=', account.id),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('is_read', '=', False),
        ('is_deleted', '=', False),
    ])
    account.sudo().write({'unread_count': unread_count})
    return unread_count


def _propagate_read_to_sent_copies(env, message_id, read_at):
    """
    When a recipient marks an inbox message as read, find the matching sent-folder
    copy (same RFC 2822 Message-ID) in any Lugal account and mark it read too.

    This is what drives is_read/read_at on *sent* messages — they track whether the
    recipient has read the message, not whether the sender opened their own copy.
    """
    if not message_id:
        return
    try:
        sent_copies = env['lugal.email.message'].sudo().search([
            ('message_id', '=', message_id),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        sent_copies = sent_copies.filtered(lambda msg: _is_sent_folder(msg.folder))
        if sent_copies:
            sent_copies.with_context(lugal_recipient_read=True).write({
                'is_read': True,
                'read_at': read_at,
            })
            _logger.info(
                '_propagate_read_to_sent_copies: marked %d sent copy(s) read '
                'for message_id=%s', len(sent_copies), message_id,
            )
    except Exception as exc:
        _logger.warning(
            '_propagate_read_to_sent_copies failed message_id=%s: %s', message_id, exc,
        )


def _folder_tail(folder_path):
    return (folder_path or '').replace('/', '.').split('.')[-1].lower()


def _folder_move_vals(folder_path):
    vals = {'folder': folder_path}
    if _folder_tail(folder_path) == 'important':
        vals['is_important'] = True
    return vals


def _extract_email_address(raw):
    try:
        from email.utils import parseaddr
        return (parseaddr(raw or '')[1] or raw or '').strip().lower()
    except Exception:
        return (raw or '').strip().lower()


def _rewrite_folder_references(env, account_id, old_path, new_path):
    """Rewrite DB message folders and rule destinations after an IMAP rename."""
    Msg = env['lugal.email.message'].sudo()
    Rule = env['lugal.email.rule'].sudo()
    renamed_msgs = 0
    rules_updated = 0
    seen_msg_ids = set()
    seps = []
    for sep in ('.', '/', '/' if '.' in old_path else '.'):
        if sep not in seps:
            seps.append(sep)

    exact_msgs = Msg.search([
        ('account_id', '=', account_id),
        ('folder', '=', old_path),
    ])
    if exact_msgs:
        seen_msg_ids.update(exact_msgs.ids)
        exact_msgs.write(_folder_move_vals(new_path))

    for sep in seps:
        old_prefix = old_path + sep
        new_prefix = new_path + sep
        child_msgs = Msg.search([
            ('account_id', '=', account_id),
            ('folder', 'like', old_prefix + '%'),
        ])
        for child_msg in child_msgs:
            if child_msg.id in seen_msg_ids:
                continue
            child_msg.write(_folder_move_vals(new_prefix + child_msg.folder[len(old_prefix):]))
            seen_msg_ids.add(child_msg.id)

    renamed_msgs = len(seen_msg_ids)

    for rule in Rule.search([('account_id', '=', account_id)]):
        try:
            actions = json.loads(rule.actions_json or '[]')
        except Exception:
            continue
        changed = False
        for act in actions:
            if act.get('action') != 'move_folder':
                continue
            value = (act.get('value') or '').strip()
            if value == old_path:
                act['value'] = new_path
                changed = True
            else:
                for sep in seps:
                    old_prefix = old_path + sep
                    if value.startswith(old_prefix):
                        act['value'] = new_path + sep + value[len(old_prefix):]
                        changed = True
                        break
        if changed:
            rule.write({'actions_json': json.dumps(actions)})
            rules_updated += 1

    return {'messages_updated': renamed_msgs, 'rules_updated': rules_updated}


def _find_or_create_sender_move_rule(msg, target_folder):
    """Manual custom-folder moves become sender rules for future mail."""
    sender_addr = _extract_email_address(msg.from_address)
    if not sender_addr or not msg.account_id:
        return None
    Rule = msg.env['lugal.email.rule'].sudo()
    conditions = [{'field': 'from_address', 'operator': 'contains', 'value': sender_addr}]
    actions = [{'action': 'move_folder', 'value': target_folder}]
    for rule in Rule.search([
        ('user_id', '=', msg.account_id.user_id.id),
        ('account_id', '=', msg.account_id.id),
        ('is_active', '=', True),
    ], order='sequence asc, id asc'):
        try:
            if (
                json.loads(rule.conditions_json or '[]') == conditions
                and json.loads(rule.actions_json or '[]') == actions
            ):
                return rule
        except Exception:
            continue
    return Rule.create({
        'name':            f'Move all emails from {sender_addr} to {target_folder}',
        'user_id':         msg.account_id.user_id.id,
        'account_id':      msg.account_id.id,
        'is_active':       True,
        'sequence':        90,
        'match_mode':      'all',
        'conditions_json': json.dumps(conditions),
        'actions_json':    json.dumps(actions),
        'stop_processing': True,
    })


def _apply_sender_move_to_existing(msg, target_folder):
    """Move historical inbound messages from the same sender into target_folder."""
    sender_addr = _extract_email_address(msg.from_address)
    if not sender_addr or not msg.account_id:
        return {'rule_id': None, 'applied_existing': 0}

    rule = _find_or_create_sender_move_rule(msg, target_folder)
    mirrored_rules = []
    try:
        from odoo.addons.lugal_email.controllers.rules_controller import (
            _mirror_sender_move_rule_to_user_accounts,
        )
        if rule:
            mirrored_rules = _mirror_sender_move_rule_to_user_accounts(
                rule, msg.account_id.user_id.id, msg.account_id.id)
    except Exception:
        _logger.warning('manual sender move rule mirror failed msg=%s', msg.id, exc_info=True)
    Msg = msg.env['lugal.email.message'].sudo()
    LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    matches = Msg.search([
        ('account_id', '=', msg.account_id.id),
        ('from_address', 'ilike', sender_addr),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('folder', '!=', target_folder),
        ('is_deleted', '=', False),
    ], limit=5000)

    imap_tasks = [(m.imap_uid, m.folder) for m in matches if m.imap_uid]
    if matches:
        matches.write(_folder_move_vals(target_folder))

    if imap_tasks and (msg.account_id.password or '').strip():
        db_name = msg.env.cr.dbname
        acc_id = msg.account_id.id

        def _bg_bulk_sender_move():
            try:
                from collections import defaultdict
                from odoo.modules.registry import Registry as _Registry
                from odoo.api import Environment as _Env
                by_src = defaultdict(list)
                for uid_val, src_folder in imap_tasks:
                    by_src[src_folder].append(str(uid_val))
                with _Registry(db_name).cursor() as _cr:
                    _env = _Env(_cr, 1, {})
                    _acc = _env['lugal.email.account'].browse(acc_id)
                    with _acc._imap_session() as conn:
                        for src_folder, uid_list in by_src.items():
                            try:
                                if (src_folder or '').lower() == 'inbox':
                                    imap_src = 'INBOX'
                                elif (src_folder or '').lower() in LOGICAL:
                                    imap_src = _acc._get_server_folder_name(src_folder.lower(), existing_conn=conn)
                                else:
                                    imap_src = src_folder
                                conn.select(_imap_quote_mailbox(imap_src), readonly=False)
                                uid_set = ','.join(uid_list)
                                dest = _imap_quote_mailbox(target_folder)
                                res = conn.uid('move', uid_set, dest)
                                if res[0] != 'OK':
                                    conn.uid('copy', uid_set, dest)
                                    conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                    conn.expunge()
                            except Exception as exc:
                                _logger.warning(
                                    'manual move rule IMAP batch failed src=%s dest=%s: %s',
                                    src_folder, target_folder, exc,
                                )
            except Exception as exc:
                _logger.warning('manual move rule background thread failed: %s', exc)

        threading.Thread(
            target=_bg_bulk_sender_move,
            daemon=True,
            name=f'imap-sender-rule-{msg.account_id.id}',
        ).start()

    unread_count = _refresh_account_unread_count(msg.account_id)
    return {
        'rule_id': rule.id if rule else None,
        'applied_existing': len(matches),
        'unread_count': unread_count,
        'mirrored_rules': mirrored_rules,
    }


def _sync_unread_custom_folders(accounts, max_folders=12):
    """Refresh IMAP flags for custom folders that currently have unread badges."""
    if not accounts:
        return []
    Msg = accounts.env['lugal.email.message'].sudo()
    ICP = accounts.env['ir.config_parameter'].sudo()
    rows = Msg.search([
        ('account_id', 'in', accounts.ids),
        ('folder', 'not in', ['inbox', 'sent', 'drafts', 'trash', 'archive', 'spam']),
        ('is_read', '=', False),
        ('is_deleted', '=', False),
    ], order='write_date desc', limit=500)
    pairs = []
    seen = set()
    for row in rows:
        key = (row.account_id.id, row.folder)
        if key not in seen:
            seen.add(key)
            pairs.append((row.account_id, row.folder))
        if len(pairs) >= max_folders:
            break

    synced = []
    import time as _time
    now = int(_time.time())
    for acc, folder in pairs:
        if not (acc.password or '').strip():
            continue
        throttle_key = f'lugal_email.custom_unread_sync.{acc.id}.{folder}'
        try:
            last = int(ICP.get_param(throttle_key, '0') or '0')
        except Exception:
            last = 0
        if now - last < 45:
            continue
        try:
            ICP.set_param(throttle_key, str(now))
            res = acc.sudo().sync_custom_imap_folder(folder, headers_only=True)
            _refresh_account_unread_count(acc)
            synced.append({'account_id': acc.id, 'folder': folder, 'result': res})
        except Exception:
            _logger.warning(
                'notifications custom unread sync failed acc=%s folder=%s',
                acc.id, folder, exc_info=True,
            )
    return synced


def _folder_role(folder):
    """Canonical role name the client can use across list/detail/realtime rows."""
    value = (folder or 'inbox').strip()
    low = value.lower()
    logical = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
    return low if low in logical else 'custom'


def _is_sent_folder(folder):
    value = (folder or '').strip().lower()
    tail = value.replace('\\', '/').replace('.', '/').split('/')[-1]
    return value in {'sent', 'sent items', 'sent messages'} or tail in {
        'sent',
        'sent items',
        'sent messages',
    }


def _attachment_payload(att, inline=False, cid_value=None):
    url = (
        f'/web/content/{att.id}?access_token={att.access_token}'
        if att.access_token
        else f'/web/content/{att.id}?download=true'
    )
    data = {
        'id':       att.id,
        'name':     att.name or 'attachment',
        'mimetype': att.mimetype or 'application/octet-stream',
        'size':     att.file_size or 0,
        'url':      url,
        'inline':   bool(inline),
    }
    if cid_value:
        data['cid'] = f'cid:{cid_value}'
        data['content_id'] = cid_value
    return data


def _message_attachment_buckets(msg):
    """Return (regular_attachments, inline_attachments) with CID metadata."""
    _CID_PREFIX = '__inline_cid__:'
    att_list = []
    inline_list = []
    try:
        atts = msg.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', msg.id),
        ])
        for att in atts:
            desc = att.description or ''
            if desc.startswith(_CID_PREFIX):
                cid_value = desc[len(_CID_PREFIX):].strip()
                inline_list.append(_attachment_payload(att, inline=True, cid_value=cid_value))
            else:
                att_list.append(_attachment_payload(att, inline=False))
    except Exception:
        pass
    return att_list, inline_list


def _resolve_cid_refs(body_html, inline_attachments):
    """Replace cid:<content_id> references in body_html with real attachment URLs.

    Called when building the full message payload so the frontend can render
    inline images directly without any client-side CID substitution.

    Handles two common encoding variants:
      • cid:img-abc123@lugal.mail           (no angle brackets — standard)
      • cid:<img-abc123@lugal.mail>         (with angle brackets — some clients)
    """
    if not body_html or not inline_attachments:
        return body_html
    resolved = body_html
    for att in inline_attachments:
        url = att.get('url')
        if not url:
            continue
        cid_raw = att.get('content_id') or ''
        if not cid_raw:
            continue
        # Replace both encoding variants
        for pattern in (f'cid:{cid_raw}', f'cid:<{cid_raw}>'):
            if pattern in resolved:
                resolved = resolved.replace(pattern, url)
    return resolved


def _message_to_dict(msg, full=False):
    data = {
        'id':             msg.id,
        'account_id':     msg.account_id.id,
        'folder':         msg.folder,
        'folder_role':    _folder_role(msg.folder),
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
        'written_in_arabic': bool(getattr(msg, 'written_in_arabic', False)),
        'message_size':   msg.message_size or 0,
        'smtp_delivered': msg.smtp_delivered,
        'smtp_error':     msg.smtp_error or None,
        'smtp_status':    msg.smtp_status or 'pending',
        'thread_id':      msg.thread_id or None,
        'in_reply_to':    msg.in_reply_to or None,
        'version':        _to_riyadh_iso(msg.write_date),
        'write_date':     _to_riyadh_iso(msg.write_date),
        # Read receipt tracking fields
        'request_read_receipt': bool(msg.request_read_receipt),
        'recipient_read_at':    _to_riyadh_iso(msg.recipient_read_at) if msg.recipient_read_at else None,
        'crm_links': {
            'customer': {'id': msg.linked_customer_id, 'name': msg.linked_customer_name}
                        if msg.linked_customer_id else None,
            'ticket':   {'id': msg.linked_ticket_id, 'name': msg.linked_ticket_name}
                        if msg.linked_ticket_id else None,
        },
    }
    att_list, inline_list = _message_attachment_buckets(msg)

    # These counters are always in the response (list view needs them for icons)
    data['has_attachments']         = bool(att_list)
    data['attachment_count']        = len(att_list)
    data['has_inline_attachments']  = bool(inline_list)
    data['inline_attachment_count'] = len(inline_list)

    if full:
        raw_html = msg.body_html or ''
        # Resolve cid: references in the HTML so the FE can render inline images
        # without any client-side processing. body_html_resolved replaces every
        # cid:<content_id> (and cid:<content_id> with angle brackets) with the
        # corresponding /web/content/<id>?access_token=... URL.
        # body_html is kept as-is for legacy FE code; body_html_resolved is the
        # preferred field for rendering.
        data['body_html']          = raw_html
        data['body_html_resolved'] = _resolve_cid_refs(raw_html, inline_list)
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
            notification_folder_domain = [
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ]
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
                        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
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
            query       = (
                params.get('query')
                or params.get('q')
                or params.get('search')
                or ''
            ).strip()
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
            focus_raw   = params.get('message_id') or params.get('focus_message_id')
            focus_message_id = 0
            if focus_raw:
                try:
                    focus_message_id = int(str(focus_raw).strip())
                except (TypeError, ValueError):
                    return _json_response({'success': False, 'error': 'message_id must be an integer'}, 400)

            def _first_param(*names):
                for name in names:
                    if name in params:
                        return params.get(name)
                return None

            # Optional server-side filter params.  Support both legacy short
            # names and FE contract names (`filter_*`) used by ConversationsEmail.
            filter_unread         = _first_param('filter_unread', 'unread')
            filter_flagged        = _first_param('filter_flagged', 'flagged')
            filter_starred        = _first_param('filter_starred', 'starred')
            filter_important      = _first_param('filter_important', 'important')
            filter_has_attachment = _first_param(
                'filter_has_attachment', 'filter_has_attachments', 'has_attachments',
            )
            filter_mentioned      = _first_param('filter_mentioned', 'mentioned')
            filter_sent_to_me     = _first_param('filter_sent_to_me', 'sent_to_me')

            # scope to this user's accounts
            user_accounts = _get_user_accounts(uid)
            account_ids   = user_accounts.ids
            try:
                requested_account_id = int(str(account_id).strip()) if account_id else None
            except (TypeError, ValueError):
                return _json_response({'success': False, 'error': 'account_id must be an integer'}, 400)
            if requested_account_id and requested_account_id not in account_ids:
                return _json_response({'success': False, 'error': 'Account not found'}, 404)

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
                aid = requested_account_id
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
                    # Determine if this is a namespace parent using the DB only —
                    # no IMAP call needed and avoids connection limit issues.
                    # A folder is a namespace parent when child folders exist,
                    # regardless of whether the parent also has direct messages.
                    # Example:
                    #   INBOX.syed_naqvi              -> all Syed mail
                    #   INBOX.syed_naqvi.Important    -> only important Syed mail
                    Msg = request.env['lugal.email.message'].sudo()
                    has_child_messages = Msg.search_count([
                        ('account_id', '=', acc.id),
                        ('folder',     'like', folder_raw + '.%'),
                        ('is_deleted', '=', False),
                    ]) > 0
                    is_namespace_parent = has_child_messages
                    children_paths = []  # only used for imap_folder_sync reporting

                    try:
                        # Keep custom-folder sync isolated.  IMAP/body import can
                        # hit uniqueness or server-state errors; if that happens,
                        # the list endpoint must still return cached DB rows
                        # instead of leaving the request cursor aborted.
                        with request.env.cr.savepoint():
                            if is_namespace_parent:
                                # Namespace parent — expand query to all children.
                                # No IMAP sync needed; messages already in DB from leaf syncs.
                                folder_branch_expand = True
                                folder_q = folder_raw
                                imap_folder_sync.append({
                                    'account_id':      acc.id,
                                    'branch':          True,
                                    'child_mailboxes': [],
                                    'imported':        0,
                                    'error':           None,
                                    'resolved_path':   folder_raw,
                                    'per_mailbox':     [],
                                })
                            else:
                                # Leaf folder or folder with its own messages — exact match only
                                res = acc.sudo().sync_custom_imap_folder(folder_raw)
                                imap_folder_sync.append({'account_id': acc.id, **res})
                                # Only accept resolved_path if it matches the requested folder
                                # exactly (case differences only). Never allow it to become a
                                # parent path which would expand the query to sibling folders.
                                resolved = (res.get('resolved_path') or '').strip()
                                if resolved and resolved.lower() == folder_raw.lower():
                                    folder_q = resolved
                    except Exception:
                        try:
                            request.env.cr.rollback()
                        except Exception:
                            pass
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
                base_domain.append(('account_id', '=', requested_account_id))
            if query:
                base_domain += ['|', ('subject', 'ilike', query), ('body_text', 'ilike', query)]
            if linked_model and linked_id:
                base_domain += [('linked_model', '=', linked_model), ('linked_record_id', '=', int(linked_id))]

            # Optional server-side filters
            filter_domain = []
            if _truthy(filter_unread):
                filter_domain.append(('is_read', '=', False))
            if _truthy(filter_flagged):
                filter_domain.append(('is_flagged', '=', True))
            if _truthy(filter_starred):
                filter_domain.append(('is_starred', '=', True))
            if _truthy(filter_important):
                filter_domain.append(('is_important', '=', True))
            # Folder paths created by the "important from sender" template must
            # not display stale/non-important duplicates.  This keeps
            # INBOX.<sender>.Important semantically consistent even if older
            # rows were imported before the rule/move hardening landed.
            if is_custom_mailbox:
                _folder_tail = (folder_q or '').replace('/', '.').split('.')[-1].lower()
                if _folder_tail == 'important':
                    filter_domain.append(('is_important', '=', True))
            if _truthy(filter_mentioned):
                filter_domain.append(('is_mentioned', '=', True))
            if _truthy(filter_has_attachment):
                attachment_account_ids = (
                    [requested_account_id] if requested_account_id else account_ids
                )
                request.env.cr.execute(
                    """
                    SELECT DISTINCT a.res_id
                    FROM ir_attachment a
                    JOIN lugal_email_message m ON m.id = a.res_id
                    WHERE a.res_model = 'lugal.email.message'
                      AND COALESCE(a.description, '') NOT LIKE '__inline_cid__:%'
                      AND m.account_id = ANY(%s)
                      AND m.is_deleted = FALSE
                    """,
                    (attachment_account_ids,),
                )
                att_msg_ids = [row[0] for row in request.env.cr.fetchall()]
                filter_domain.append(('id', 'in', att_msg_ids))
            if _truthy(filter_sent_to_me):
                user_emails = [a.email_address for a in user_accounts if a.email_address]
                if user_emails:
                    to_clauses = [('to_addresses', 'ilike', e) for e in user_emails]
                    if len(to_clauses) == 1:
                        filter_domain += to_clauses
                    else:
                        or_clause = ['|'] * (len(to_clauses) - 1) + to_clauses
                        filter_domain += or_clause

            base_domain += filter_domain

            Msg   = request.env['lugal.email.message'].sudo()
            total = Msg.search_count(base_domain)

            # Default inbox sorting uses create_date so brand-new arrivals appear
            # first even if a sender has a bad clock.  Custom rule folders are
            # different: historical/stale DB rows may be re-used during IMAP
            # custom-folder sync, so create_date can be old while the email Date
            # is current.  For custom folders, sort by the email Date first.
            sort_order = (
                'date desc, create_date desc, id desc'
                if is_custom_mailbox
                else 'create_date desc, id desc'
            )

            new_msgs = Msg.browse()
            if since_id:
                since_account_ids = [requested_account_id] if requested_account_id else account_ids
                all_accs_domain = [
                    ('account_id', 'in', since_account_ids),
                    ('is_deleted', '=', False),
                ] + _folder_domain + [
                    ('id',         '>',  since_id),
                ]
                new_msgs = Msg.search(all_accs_domain, order='id desc')

            page_msgs = Msg.search(base_domain, limit=limit, offset=offset, order=sort_order)
            focus_msg = Msg.browse()
            if focus_message_id:
                focus_domain = [
                    ('id',         '=',  focus_message_id),
                    ('account_id', 'in', [requested_account_id] if requested_account_id else account_ids),
                    ('is_deleted', '=',  False),
                ] + _folder_domain
                focus_msg = Msg.search(focus_domain, limit=1)

            include_thread = params.get('include_thread', '0') == '1'

            pinned_msgs = list(new_msgs)
            if focus_msg and focus_msg.id not in {m.id for m in pinned_msgs}:
                # Notification/open-from-link safety net: pin the exact requested
                # message for this mailbox even if optional filters like unread=1
                # or pagination would otherwise hide it after it is opened/read.
                pinned_msgs.insert(0, focus_msg)

            if pinned_msgs:
                pinned_ids = {m.id for m in pinned_msgs}
                combined = pinned_msgs + [m for m in page_msgs if m.id not in pinned_ids]
                display_msgs = combined[:limit]
            else:
                display_msgs = list(page_msgs)

            # ── Thread enrichment ─────────────────────────────────────────────
            # Collect unique thread_ids from this page so we can batch-count
            # (and optionally batch-fetch) thread messages in one DB round-trip.
            thread_ids_on_page = list({
                m.thread_id for m in display_msgs if m.thread_id
            })

            # thread_count per thread_id (across all user accounts, all folders)
            thread_count_map: dict = {}
            thread_msgs_map: dict = {}   # populated only when include_thread=1

            if thread_ids_on_page:
                # Batch fetch all thread members across all folders in one query.
                all_thread_members = Msg.search([
                    ('account_id', 'in', account_ids),
                    ('is_deleted', '=', False),
                    ('thread_id',  'in', thread_ids_on_page),
                ] + filter_domain, order='date asc, id asc')

                # Group by thread_id in Python — O(n) over thread members
                from collections import defaultdict as _defaultdict
                _groups: dict = _defaultdict(list)
                for tm in all_thread_members:
                    _groups[tm.thread_id].append(tm)

                for tid, members in _groups.items():
                    thread_count_map[tid] = len(members)
                    if include_thread:
                        thread_msgs_map[tid] = [_message_to_dict(tm, full=False) for tm in members]

            def _enrich(m):
                d = _message_to_dict(m)
                tid = m.thread_id or None
                d['thread_count'] = thread_count_map.get(tid, 1) if tid else 1
                if include_thread and tid and tid in thread_msgs_map:
                    d['thread_messages'] = thread_msgs_map[tid]
                return d

            items = [_enrich(m) for m in display_msgs]

            # Include the highest message ID in the current account scope so
            # account-scoped sent/inbox requests never receive cross-account rows.
            all_max = Msg.search([
                ('account_id', 'in', [requested_account_id] if requested_account_id else account_ids),
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
                    'focused_message_id': focus_message_id or None,
                    'focused_message_found': bool(focus_msg),
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

                sent_read_noop = False
                if 'is_read' in body:
                    is_read = bool(body['is_read'])
                    if _is_sent_folder(msg.folder):
                        # Sent-folder: is_read/read_at track RECIPIENT read status.
                        # Sender patching their own sent copy is cosmetic-only; push
                        # \Seen to IMAP but do not alter DB is_read/read_at.
                        sent_read_noop = True
                        if imap_uid and is_read:
                            msg.account_id.sudo()._imap_store_async(
                                imap_uid, imap_folder, add_flags=['\\Seen']
                            )
                    else:
                        was_already_read = bool(msg.read_at)
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
                        # Propagate read confirmation to the sender's sent copy.
                        if is_read and not was_already_read and msg.message_id:
                            _propagate_read_to_sent_copies(
                                request.env, msg.message_id,
                                msg.read_at or fields.Datetime.now()
                            )
                        # Send MDN if marking inbox message as read for the first time
                        # and sender requested a read receipt.
                        if (is_read and not was_already_read
                                and msg.request_read_receipt
                                and msg.folder in ('inbox',)
                                and msg.from_address
                                and msg.message_id):
                            try:
                                _send_mdn_async(
                                    acc=msg.account_id,
                                    to_address=msg.from_address,
                                    original_message_id=msg.message_id,
                                    original_subject=msg.subject or '',
                                    recipient_email=msg.account_id.email_address,
                                )
                            except Exception as _mdn_exc:
                                _logger.warning('MDN trigger failed (patch): %s', _mdn_exc)

                if not vals:
                    if sent_read_noop:
                        return _json_response({'success': True, 'data': _message_to_dict(msg)})
                    return _json_response(
                        {'success': False, 'error': 'Provide at least one of: is_flagged, is_starred, is_important, is_read'},
                        400,
                    )
                msg.write(vals)
                if 'is_read' in vals:
                    _refresh_account_unread_count(msg.account_id)
                return _json_response({'success': True, 'data': _message_to_dict(msg)})

            if request.httprequest.method == 'DELETE':
                prev_folder = msg.folder
                msg.write({'folder': 'trash'})
                _refresh_account_unread_count(msg.account_id)
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

            items = []
            for msg in msgs:
                attachments, inline_attachments = _message_attachment_buckets(msg)
                raw_html = msg.body_html or ''
                items.append({
                    'id':                  msg.id,
                    'account_id':          msg.account_id.id,
                    'folder':              msg.folder,
                    'folder_role':         _folder_role(msg.folder),
                    'is_read':             msg.is_read,
                    'read_at':             _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                    'version':             _to_riyadh_iso(msg.write_date),
                    'write_date':          _to_riyadh_iso(msg.write_date),
                    'body_html':           raw_html,
                    'body_html_resolved':  _resolve_cid_refs(raw_html, inline_attachments),
                    'body_text':           msg.body_text or '',
                    'attachments':         attachments,
                    'inline_attachments':  inline_attachments,
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
            notification_folder_domain = [
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ]

            # ── Auto-sync for accounts that are stale/never synced/errored ─
            # The notifications endpoint is often called before the inbox is opened.
            # Without this, notifications can show stale counts/messages until
            # the user manually hits resync.
            db_name = request.env.cr.dbname
            sync_threads = []
            for acc in accs:
                needs_urgent_sync = (
                    (acc.password or '').strip() and
                    (
                        acc.sync_status in ('never', 'error')
                        or not acc.last_sync_date
                        or _needs_imap_sync(acc)
                    )
                )
                if needs_urgent_sync:
                    try:
                        force_now = acc.sync_status in ('never', 'error') or not acc.last_sync_date
                        t = _run_imap_sync_bg(acc.id, db_name, force=force_now)
                        if t:
                            sync_threads.append(t)
                            _logger.info(
                                'notifications: triggered freshness sync for account %s '
                                '(sync_status=%s)', acc.id, acc.sync_status,
                            )
                    except Exception:
                        _logger.exception(
                            'notifications: urgent sync kick failed for account %s', acc.id,
                        )

            # Wait briefly for syncs so the response contains fresh counts.
            # If the sync takes longer the FE will get the cached (possibly stale) counts
            # and the sync will complete in the background.
            has_cold_sync = any(
                a.sync_status in ('never', 'error') or not a.last_sync_date
                for a in accs
            )
            wait_timeout = 8.0 if has_cold_sync else 3.0
            for t in sync_threads:
                t.join(timeout=wait_timeout)

            # Re-read accounts after sync to pick up updated unread_count / sync_status.
            accs = _get_user_accounts(uid)
            custom_folder_sync = _sync_unread_custom_folders(accs)

            per_account = []
            total_unread = 0
            for acc in accs:
                # Count unread inbound messages from DB (source of truth).
                # Includes custom rule folders such as INBOX.syed_naqvi and
                # INBOX.syed_naqvi.Important, not only literal inbox.
                unread = request.env['lugal.email.message'].sudo().search_count([
                    ('account_id', '=', acc.id),
                    ('is_read', '=', False),
                    ('is_deleted', '=', False),
                ] + notification_folder_domain)
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
            per_folder['inbound'] = request.env['lugal.email.message'].sudo().search_count([
                ('account_id', 'in', account_ids),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ] + notification_folder_domain)

            last_sync = None
            if accs:
                dates = [a.last_sync_date for a in accs if a.last_sync_date]
                if dates:
                    last_sync = _to_riyadh_iso(max(dates))

            Msg = request.env['lugal.email.message'].sudo()

            # ── New inbound messages (for browser/in-app notifications) ────────
            # Returns up to 10 most recent UNREAD inbound messages, including
            # custom rule folders.
            # If `?since=<ISO datetime>` is supplied only messages received after
            # that timestamp are returned, so the FE can detect new arrivals
            # without comparing counts.
            new_msg_domain = [
                ('account_id', 'in', account_ids),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ] + notification_folder_domain
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
                    'folder':       m.folder or 'inbox',
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
                    'smtp_status':    m.smtp_status or 'pending',
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
                    'custom_folder_sync': custom_folder_sync,
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
            written_in_arabic = _truthy(body.get('written_in_arabic'))
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

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))

            # Store in sent folder
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses':        json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':           body_html,
                'body_text':           body_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
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

            # Fire SMTP in background — all file I/O + network happens in daemon
            # thread; the HTTP response is returned without waiting.
            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text, cc_emails, bcc_emails,
                msg_id=msg.id, attachment_ids=attachment_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
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
            written_in_arabic = _truthy(body.get('written_in_arabic'))

            # skip_auto_quote=true → FE has already embedded the quoted block
            # inside body_html itself.  In that case, don't append it a second
            # time or the email will contain double quoted sections and double
            # signatures.  FE should set this flag whenever it places the
            # quoted_body_html from the GET prefill directly into the editable
            # composer field that it sends back on POST.
            skip_auto_quote = bool(body.get('skip_auto_quote', False))

            # Heuristic safety-net: even without the explicit flag, if the
            # submitted body_html already contains a blockquote we assume the
            # FE included the quote and skip appending it again.
            if not skip_auto_quote and user_html:
                skip_auto_quote = '</blockquote>' in user_html.lower()

            if skip_auto_quote:
                final_html = user_html
                final_text = user_text
            else:
                quoted_html = _build_quoted_html(orig)
                quoted_text = _build_quoted_text(orig)
                final_html  = (user_html + quoted_html) if user_html else quoted_html
                final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            thread_vals = _thread_vals_for_reply(orig)
            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            vals = {
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_addr]),
                'cc_addresses':        json.dumps([{'email': e} for e in _norm_addr_list(body.get('cc', []))]),
                'bcc_addresses':       json.dumps([{'email': e} for e in _norm_addr_list(body.get('bcc', []))]),
                'body_html':           final_html,
                'body_text':           final_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
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
                written_in_arabic=written_in_arabic,
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
            written_in_arabic = _truthy(body.get('written_in_arabic'))

            skip_auto_quote = bool(body.get('skip_auto_quote', False))
            if not skip_auto_quote and user_html:
                skip_auto_quote = '</blockquote>' in user_html.lower()

            if skip_auto_quote:
                final_html = user_html
                final_text = user_text
            else:
                quoted_html = _build_quoted_html(orig)
                quoted_text = _build_quoted_text(orig)
                final_html  = (user_html + quoted_html) if user_html else quoted_html
                final_text  = (user_text + '\n\n' + quoted_text) if user_text else quoted_text

            importance_raw       = (body.get('importance') or 'normal').lower()
            request_read_receipt = bool(body.get('request_read_receipt', False))
            thread_vals = _thread_vals_for_reply(orig)
            vals = {
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps(to_entries),
                'cc_addresses':        json.dumps(cc_entries),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_addrs]),
                'body_html':           final_html,
                'body_text':           final_text,
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
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
                written_in_arabic=written_in_arabic,
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
            written_in_arabic = _truthy(body.get('written_in_arabic'))
            # Combine the user's intro text (if any) with the properly formatted
            # quoted original message.  Using _build_quoted_html gives a consistent
            # "---------- Forwarded message ----------" style header.
            fwd_user_html = (body.get('body_html', '') or '').strip()
            fwd_quoted    = _build_quoted_html(orig)
            fwd_body      = (fwd_user_html + fwd_quoted) if fwd_user_html else fwd_quoted
            fwd_thread = _thread_vals_for_forward(orig)
            fwd_attachment_ids   = body.get('attachment_ids', [])
            request_read_receipt = bool(body.get('request_read_receipt', False))
            msg = request.env['lugal.email.message'].sudo().create({
                'account_id':          acc.id,
                'folder':              'sent',
                'subject':             subject,
                'from_name':           acc.display_name_field or acc.email_address,
                'from_address':        acc.email_address,
                'to_addresses':        json.dumps([{'email': e} for e in to_fwd]),
                'cc_addresses':        json.dumps([{'email': e} for e in cc_fwd]),
                'bcc_addresses':       json.dumps([{'email': e} for e in bcc_fwd]),
                'body_html':           fwd_body,
                'body_text':           body.get('body_text', ''),
                'written_in_arabic':   written_in_arabic,
                'body_fetched':        True,
                'is_important':        importance_raw == 'high',
                'date':                __import__('odoo').fields.Datetime.now(),
                'request_read_receipt': request_read_receipt,
                **fwd_thread,
            })
            # Forward is the root of a new thread on OUR side — use its own msg-id
            if not msg.thread_id and msg.message_id:
                msg.write({'thread_id': msg.message_id})
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
                written_in_arabic=written_in_arabic,
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

            # ── Sent-folder messages: is_read/read_at track RECIPIENT read status ──
            # The sender viewing their own sent copy must NOT update is_read/read_at.
            # We still push \Seen to IMAP so the sender's client clears the unread
            # badge, but the DB fields remain driven solely by recipient activity
            # (_propagate_read_to_sent_copies, MDN handler).
            if _is_sent_folder(msg.folder):
                if msg.imap_uid and is_read:
                    imap_folder = _resolve_imap_folder(msg.account_id, msg.folder)
                    msg.account_id.sudo()._imap_store_async(
                        msg.imap_uid, imap_folder, add_flags=['\\Seen']
                    )
                unread_count = _refresh_account_unread_count(msg.account_id)
                return _json_response({'success': True, 'data': {
                    'is_read': msg.is_read,
                    'read_at': _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                    'unread_count': unread_count,
                }})

            # ── Inbox / custom-folder messages: normal read handling ──────────────
            # Capture pre-write state before the write() override may stamp read_at
            was_already_read = bool(msg.read_at)
            msg.write({'is_read': is_read})
            unread_count = _refresh_account_unread_count(msg.account_id)
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
            # Propagate read confirmation to the sender's sent-folder copy so the
            # sender sees is_read=True once any recipient actually reads the message.
            if is_read and not was_already_read and msg.message_id:
                _propagate_read_to_sent_copies(
                    request.env, msg.message_id, msg.read_at or fields.Datetime.now()
                )
            # Send MDN if: marking as read for the first time, the original
            # sender requested a receipt, and this is an inbox message.
            if (is_read and not was_already_read
                    and msg.request_read_receipt
                    and msg.folder in ('inbox',)
                    and msg.from_address
                    and msg.message_id):
                try:
                    _send_mdn_async(
                        acc=msg.account_id,
                        to_address=msg.from_address,
                        original_message_id=msg.message_id,
                        original_subject=msg.subject or '',
                        recipient_email=msg.account_id.email_address,
                    )
                except Exception as _mdn_exc:
                    _logger.warning('MDN trigger failed (toggle_read): %s', _mdn_exc)
            return _json_response({'success': True, 'data': {
                'is_read': is_read,
                'read_at': _to_riyadh_iso(msg.read_at) if msg.read_at else None,
                'unread_count': unread_count,
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
            unread_count = _refresh_account_unread_count(msg.account_id)
            # Move back to INBOX on the IMAP server
            if msg.imap_uid:
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'inbox')
            return _json_response({'success': True, 'unread_count': unread_count})
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
            unread_count = _refresh_account_unread_count(msg.account_id)
            # Move to Archive folder on the IMAP server
            if msg.imap_uid:
                imap_from = _resolve_imap_folder(msg.account_id, prev_folder)
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_from, 'archive')
            return _json_response({'success': True, 'unread_count': unread_count})
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
            unread_count = _refresh_account_unread_count(msg.account_id)
            if msg.imap_uid:
                imap_archive = _resolve_imap_folder(msg.account_id, 'archive')
                msg.account_id.sudo()._imap_move_async(msg.imap_uid, imap_archive, 'inbox')
            return _json_response({'success': True, 'unread_count': unread_count})
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
            unread_count = _refresh_account_unread_count(acc)
            # Expunge from IMAP Trash folder so webmail also removes it permanently
            if imap_uid:
                trash_folder = acc._get_server_folder_name('trash')
                acc._imap_expunge_async(imap_uid, trash_folder)
            return _json_response({'success': True, 'deleted_id': message_id, 'unread_count': unread_count})
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
          { "message_ids": [1, 2, 3] }   — max 1000 IDs per call.

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
            if len(message_ids) > 1000:
                return _json_response(
                    {'success': False, 'error': 'message_ids may not exceed 1000 per request'},
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
            affected_accounts = to_delete.mapped('account_id')
            to_delete.unlink()
            unread_counts = {
                str(acc.id): _refresh_account_unread_count(acc)
                for acc in affected_accounts
            }

            return _json_response({
                'success': True,
                'data': {
                    'deleted_ids': deleted_ids,
                    'skipped_ids': skipped_ids,
                    'unread_counts': unread_counts,
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
            written_in_arabic = _truthy(body.get('written_in_arabic'))
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
                'written_in_arabic': written_in_arabic,
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
            if 'written_in_arabic' in body:
                vals['written_in_arabic'] = _truthy(body.get('written_in_arabic'))

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
            requested_account_id = body.get('account_id')
            if requested_account_id not in (None, '', False):
                try:
                    requested_account_id = int(requested_account_id)
                except (TypeError, ValueError):
                    return _json_response(
                        {'success': False, 'error': 'account_id must be an integer'},
                        400,
                    )
                if requested_account_id != draft.account_id.id:
                    return _json_response(
                        {
                            'success': False,
                            'error': (
                                'Draft account_id mismatch: this draft belongs to '
                                f'account {draft.account_id.id}'
                            ),
                        },
                        409,
                    )

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
            written_in_arabic = (
                _truthy(body.get('written_in_arabic'))
                if 'written_in_arabic' in body
                else bool(draft.written_in_arabic)
            )
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
            acc = draft.account_id
            draft.write({
                'folder':                'sent',
                'is_draft':              False,
                'is_read':               False,
                'read_at':               False,
                'subject':               subject,
                'from_name':             acc.display_name_field or acc.email_address,
                'from_address':          acc.email_address,
                'to_addresses':          json.dumps([{'email': e} for e in to_emails]),
                'cc_addresses':          json.dumps([{'email': e} for e in cc_emails]),
                'bcc_addresses':         json.dumps([{'email': e} for e in bcc_emails]),
                'body_html':             body_html,
                'body_text':             body_text,
                'written_in_arabic':     written_in_arabic,
                'is_important':          importance_raw == 'high',
                'date':                  _odoo.fields.Datetime.now(),
                'request_read_receipt':  request_read_receipt,
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

            _send_via_smtp_async(
                acc, to_emails, subject, body_html, body_text,
                cc=cc_emails, bcc=bcc_emails,
                msg_id=draft.id, attachment_ids=all_att_ids,
                importance=importance_raw,
                request_read_receipt=request_read_receipt,
                written_in_arabic=written_in_arabic,
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
                _INTERNAL_KEYWORDS = {'dovecot', 'sieve', 'courier', 'cyrus', '.subscriptions'}
                if any(kw in raw_name.lower() for kw in _INTERNAL_KEYWORDS):
                    continue
                role = _resolve_role(raw_name, m.group('flags'))

                # ── Count messages ──────────────────────────────────────────────
                # Standard folders: DB stores logical key ('inbox', 'sent', …)
                # Custom folders:   DB stores the raw IMAP path ('INBOX.omar.Important').
                # Namespace parents (e.g. INBOX.syed_naqvi) represent the whole
                # sender folder, so their counts include child folders.  Important
                # child folders only count important rows.
                local_folder_key = role if role in _STANDARD_ROLES else raw_name
                folder_domain = [('folder', '=', local_folder_key)]
                if role == 'custom':
                    child_count = Msg.search_count([
                        ('account_id', '=', acc.id),
                        ('is_deleted', '=', False),
                        '|',
                        ('folder', 'like', raw_name + delimiter + '%'),
                        ('folder', 'like', raw_name + ('/' if delimiter != '/' else '.') + '%'),
                    ])
                    if child_count:
                        folder_domain = [
                            '|', '|',
                            ('folder', '=', local_folder_key),
                            ('folder', 'like', raw_name + delimiter + '%'),
                            ('folder', 'like', raw_name + ('/' if delimiter != '/' else '.') + '%'),
                        ]
                    if raw_name.replace('/', '.').split('.')[-1].lower() == 'important':
                        folder_domain = [('folder', '=', local_folder_key), ('is_important', '=', True)]

                total  = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('is_deleted', '=', False),
                ] + folder_domain)
                unread = Msg.search_count([
                    ('account_id', '=', acc.id),
                    ('is_read',    '=', False),
                    ('is_deleted', '=', False),
                ] + folder_domain)

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

                    typ, data = conn.create(_imap_quote_mailbox(folder_path))
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

            import imaplib, time as _time, re as _re
            rename_status = 'renamed'
            try:
                with acc._imap_session() as conn:
                    def _list_names():
                        names = {}
                        typ_l, raw_l = conn.list()
                        if typ_l != 'OK' or not raw_l:
                            return names
                        lr = _re.compile(
                            r'^\((?P<flags>[^)]*)\)\s+'
                            r'(?:"(?P<delim>[^"]*)"|NIL)\s+'
                            r'(?P<name>.+?)\s*$'
                        )
                        for item in raw_l:
                            if not item:
                                continue
                            line = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
                            m = lr.match(line.strip())
                            if not m:
                                continue
                            name = m.group('name').strip().strip('"')
                            if name:
                                names[name.lower()] = name
                        return names

                    names_before = _list_names()
                    old_exists = old_path.lower() in names_before
                    new_existing = names_before.get(new_path.lower())
                    if not old_exists and new_existing:
                        # The user may have renamed the folder directly in
                        # webmail.  Treat this as success and reconcile DB/rules.
                        new_path = new_existing
                        typ, data = 'OK', []
                        rename_status = 'already_renamed_on_server'
                    else:
                        typ, data = conn.rename(
                            _imap_quote_mailbox(old_path),
                            _imap_quote_mailbox(new_path),
                        )
                        if typ != 'OK':
                            names_after = _list_names()
                            new_existing = names_after.get(new_path.lower())
                            if new_existing:
                                new_path = new_existing
                                typ, data = 'OK', []
                                rename_status = 'server_renamed_despite_non_ok_response'
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

            rewrite = _rewrite_folder_references(request.env, account_id, old_path, new_path)
            _refresh_account_unread_count(acc)
            request.env.cr.commit()

            return _json_response({'success': True, 'data': {
                'old_path': old_path,
                'new_path': new_path,
                'rename_status': rename_status,
                'messages_updated': rewrite['messages_updated'],
                'rules_updated': rewrite['rules_updated'],
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
                            conn.unsubscribe(_imap_quote_mailbox(folder_path))
                        except Exception:
                            pass
                        typ_d, data_d = conn.delete(_imap_quote_mailbox(folder_path))
                        if typ_d == 'OK':
                            deleted_paths.append(folder_path)
                            # Remove DB records for this folder so they stop appearing in
                            # the messages list.
                            try:
                                # Restore messages to inbox instead of marking deleted.
                                # Messages only get is_deleted when the user explicitly
                                # deletes them — not when a folder container is removed.
                                orphaned = request.env['lugal.email.message'].sudo().search([
                                    ('account_id', '=', account_id),
                                    ('folder',     '=', folder_path),
                                    ('is_deleted', '=', False),
                                ])
                                if orphaned:
                                    orphaned.write({'folder': 'inbox'})
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

            # ── Cleanup: delete rules + restore messages when folder deleted ──
            # Rules pointing at a deleted folder silently drop future emails.
            # Delete them now and fire async IMAP to put orphaned messages back.
            rules_deleted = 0
            msgs_restored = 0
            if deleted_paths:
                deleted_set = set(p.lower() for p in deleted_paths)

                # 1. Delete rules whose move_folder destination is now gone
                Rule = request.env['lugal.email.rule'].sudo()
                rules_to_del = Rule.browse()
                for rule in Rule.search([('account_id', '=', account_id)]):
                    try:
                        actions = json.loads(rule.actions_json or '[]')
                        for act in actions:
                            if act.get('action') == 'move_folder':
                                if (act.get('value') or '').lower() in deleted_set:
                                    rules_to_del |= rule
                                    break
                    except Exception:
                        pass
                if rules_to_del:
                    rules_deleted = len(rules_to_del)
                    _logger.info(
                        'folder_delete: removing %d rule(s) targeting deleted path(s): %s',
                        rules_deleted, [r.id for r in rules_to_del],
                    )
                    rules_to_del.unlink()

                # 2. Any messages still under deleted paths → restore to inbox
                Msg = request.env['lugal.email.message'].sudo()
                still_orphaned = Msg.search([
                    ('account_id', '=', account_id),
                    ('folder',     'in', deleted_paths),
                    ('is_deleted', '=', False),
                ])
                if still_orphaned:
                    msgs_restored = len(still_orphaned)
                    to_imap = [(m.imap_uid, m.folder) for m in still_orphaned if m.imap_uid]
                    still_orphaned.write({'folder': 'inbox'})
                    _refresh_account_unread_count(acc)

                    # Async IMAP: physically move messages back to INBOX on server
                    import collections as _col, threading as _thr
                    _db  = request.env.cr.dbname
                    _aid = account_id
                    by_src = _col.defaultdict(list)
                    for uid, src in to_imap:
                        by_src[src].append(uid)

                    def _bg(_by_src=by_src, _db=_db, _aid=_aid):
                        try:
                            from odoo.modules.registry import Registry as _Reg
                            import odoo as _odoo
                            with _Reg(_db).cursor() as _cr:
                                _env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                                _acc = _env['lugal.email.account'].browse(_aid)
                                with _acc._imap_session() as _conn:
                                    for _src, _uids in _by_src.items():
                                        try:
                                            _conn.select(_src, readonly=False)
                                            _uid_set = ','.join(str(u) for u in _uids)
                                            _t, _ = _conn.uid('move', _uid_set, 'INBOX')
                                            if _t != 'OK':
                                                _conn.uid('copy', _uid_set, 'INBOX')
                                                _conn.uid('store', _uid_set, '+FLAGS', '(\\Deleted)')
                                                _conn.expunge()
                                            _logger.info(
                                                'folder_delete restore: %d msgs %s→INBOX', len(_uids), _src)
                                        except Exception as _me:
                                            _logger.warning('folder_delete restore %s: %s', _src, _me)
                        except Exception as _e:
                            _logger.warning('folder_delete restore thread: %s', _e)

                    if to_imap:
                        _thr.Thread(target=_bg, daemon=True,
                                    name=f'imap-restore-{_aid}').start()

                try:
                    _refresh_account_unread_count(acc)
                    request.env.cr.commit()
                except Exception:
                    pass

            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
                'rules_deleted': rules_deleted,
                'msgs_restored': msgs_restored,
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
                if (msg.account_id.password or '').strip():
                    try:
                        with msg.account_id.sudo()._imap_session(connect_attempts=6, retry_delay=2.0) as _conn:
                            msg.account_id.sudo()._imap_ensure_folder(imap_dest, existing_conn=_conn)
                    except Exception:
                        _logger.warning(
                            'message_move: could not ensure destination folder %s',
                            imap_dest, exc_info=True,
                        )

            prev_folder = msg.folder
            imap_from   = _resolve_imap_folder(msg.account_id, prev_folder)

            # Update local DB record
            # For logical folders store the logical key; for custom IMAP paths
            # store the raw path so the messages_list query can find them.
            new_folder = target_logical if target_logical != 'custom' else target_raw
            write_vals = {'folder': new_folder}
            if new_folder.replace('/', '.').split('.')[-1].lower() == 'important':
                write_vals['is_important'] = True
            msg.write(write_vals)
            rule_info = {'rule_id': None, 'applied_existing': 0}
            if target_logical == 'custom':
                rule_info = _apply_sender_move_to_existing(msg, new_folder)
                unread_count = rule_info.get('unread_count', _refresh_account_unread_count(msg.account_id))
            else:
                unread_count = _refresh_account_unread_count(msg.account_id)

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
                                conn.select(_imap_quote_mailbox(imap_from))
                                result = conn.uid(
                                    'move', str(imap_uid),
                                    _imap_quote_mailbox(imap_dest),
                                )
                                if result[0] != 'OK':
                                    conn.uid('copy', str(imap_uid),
                                             _imap_quote_mailbox(imap_dest))
                                    conn.uid('store', str(imap_uid), '+FLAGS', '(\\Deleted)')
                                    conn.expunge()
                    except Exception as _e:
                        _logger.warning('message_move IMAP failed uid=%s: %s', imap_uid, _e)

                threading.Thread(target=_bg_move, daemon=True, name=f'imap-move-{message_id}').start()

            return _json_response({'success': True, 'data': {
                'id': msg.id,
                'folder': target_raw,
                'is_important': msg.is_important,
                'unread_count': unread_count,
                'rule_id': rule_info.get('rule_id'),
                'applied_existing': rule_info.get('applied_existing', 0),
                'mirrored_rules': rule_info.get('mirrored_rules', []),
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': str(exc)}, 500)

    # ── Bulk move by sender ────────────────────────────────────────────────────

    @http.route('/api/lugal/email/messages/bulk_move_by_sender',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def bulk_move_by_sender(self, **kwargs):
        """Move ALL messages from one or more senders into a target folder.

        Body (JSON):
          {
            "account_id":    22,                           // required
            "senders":       ["foo@bar.com", "baz@x.com"], // required, 1–50 addresses
            "target_folder": "INBOX.MailsFrom Weird guy",  // required — raw IMAP path
                                                           // OR logical name (inbox/sent/…)
            "source_folder": "inbox"                       // optional — restrict to one folder
                                                           //   (default: all non-deleted msgs)
          }

        Returns:
          { "success": true, "data": { "moved": 42, "senders": [...], "target_folder": "..." } }

        The DB is updated synchronously; IMAP moves are executed asynchronously
        in a background thread (fire-and-forget, best-effort).
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_response({})
        uid = ensure_jwt_user_id()
        if not uid:
            return _unauthorized()
        try:
            body = json.loads(request.httprequest.data or '{}')

            account_id    = body.get('account_id')
            senders_raw   = body.get('senders') or []
            target_folder = (body.get('target_folder') or '').strip()
            source_folder = (body.get('source_folder') or '').strip() or None

            # ── Validate inputs ──────────────────────────────────────────────
            if not account_id:
                return _json_response({'success': False, 'error': 'account_id is required'}, 400)
            if not isinstance(senders_raw, list) or not senders_raw:
                return _json_response({'success': False, 'error': 'senders must be a non-empty array'}, 400)
            if len(senders_raw) > 50:
                return _json_response({'success': False, 'error': 'senders may not exceed 50 per request'}, 400)
            if not target_folder:
                return _json_response({'success': False, 'error': 'target_folder is required'}, 400)

            senders = [s.strip().lower() for s in senders_raw if isinstance(s, str) and s.strip()]
            if not senders:
                return _json_response({'success': False, 'error': 'senders contains no valid email addresses'}, 400)

            # ── Authorise account ────────────────────────────────────────────
            try:
                aid = int(account_id)
            except (TypeError, ValueError):
                return _json_response({'success': False, 'error': 'account_id must be an integer'}, 400)

            acc = request.env['lugal.email.account'].sudo().browse(aid)
            if not acc.exists() or acc.user_id.id != uid:
                return _not_found('Account not found')

            # ── Resolve logical → IMAP folder name ──────────────────────────
            _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            if target_folder.lower() in _LOGICAL:
                target_logical = target_folder.lower()
                imap_dest      = acc.sudo()._get_server_folder_name(target_logical)
                db_folder      = target_logical
            else:
                target_logical = 'custom'
                imap_dest      = target_folder
                db_folder      = target_folder   # raw IMAP path stored in DB
                # Be forgiving for FE flows that create a rule/folder and then
                # immediately bulk-move.  Ensure the destination exists before
                # the DB move so async IMAP MOVE has a valid target.
                if (acc.password or '').strip():
                    try:
                        with acc.sudo()._imap_session(connect_attempts=6, retry_delay=2.0) as _conn:
                            acc.sudo()._imap_ensure_folder(imap_dest, existing_conn=_conn)
                    except Exception as _ensure_exc:
                        _logger.warning(
                            'bulk_move_by_sender: could not ensure IMAP folder %s: %s',
                            imap_dest, _ensure_exc,
                        )

            # ── Find messages matching any of the senders ────────────────────
            Msg = request.env['lugal.email.message'].sudo()

            # Build OR domain: ('from_address', 'ilike', s1) OR ('from_address', 'ilike', s2) …
            sender_clauses = [('from_address', 'ilike', s) for s in senders]
            if len(sender_clauses) == 1:
                sender_domain = sender_clauses
            else:
                or_prefix     = ['|'] * (len(sender_clauses) - 1)
                sender_domain = or_prefix + sender_clauses

            base = [
                ('account_id', '=', aid),
                ('is_deleted', '=', False),
            ]
            if source_folder:
                base.append(('folder', '=', source_folder))

            msgs = Msg.search(base + sender_domain)

            if not msgs:
                return _json_response({'success': True, 'data': {
                    'moved': 0, 'senders': senders, 'target_folder': target_folder,
                }})

            # ── Capture per-message IMAP state before writing ────────────────
            # Store (imap_uid, current_imap_folder_key) pairs for IMAP moves.
            imap_tasks = []
            for m in msgs:
                if m.imap_uid:
                    imap_tasks.append((m.imap_uid, m.folder))

            # ── Update DB atomically ──────────────────────────────────────────
            write_vals = {'folder': db_folder}
            if db_folder.replace('/', '.').split('.')[-1].lower() == 'important':
                write_vals['is_important'] = True
            msgs.write(write_vals)
            unread_count = _refresh_account_unread_count(acc)

            moved_count = len(msgs)

            # ── Async IMAP moves (best-effort, fire-and-forget) ───────────────
            if imap_tasks and (acc.password or '').strip():
                db_name = request.env.cr.dbname

                def _bg_bulk_move():
                    try:
                        from odoo.modules.registry import Registry as _Registry
                        with _Registry(db_name).cursor() as _cr:
                            from odoo.api import Environment as _Env
                            _env = _Env(_cr, 1, {})
                            _acc = _env['lugal.email.account'].browse(aid)
                            with _acc._imap_session() as conn:
                                # Group UIDs by source folder so we do one SELECT per folder
                                from collections import defaultdict as _dd
                                by_src = _dd(list)
                                for uid_val, src_folder in imap_tasks:
                                    # Resolve logical folder key → IMAP path
                                    if src_folder in _LOGICAL:
                                        imap_src = _acc._get_server_folder_name(src_folder)
                                    else:
                                        imap_src = src_folder
                                    by_src[imap_src].append(str(uid_val))

                                _quoted_dest = _imap_quote_mailbox(imap_dest)
                                for imap_src, uid_list in by_src.items():
                                    try:
                                        conn.select(_imap_quote_mailbox(imap_src))
                                        uid_set = ','.join(uid_list)
                                        res = conn.uid('move', uid_set, _quoted_dest)
                                        if res[0] != 'OK':
                                            # Fallback: COPY + DELETE
                                            conn.uid('copy', uid_set, _quoted_dest)
                                            conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                            conn.expunge()
                                    except Exception as _se:
                                        _logger.warning(
                                            'bulk_move_by_sender IMAP src=%s: %s', imap_src, _se)
                    except Exception as _e:
                        _logger.warning('bulk_move_by_sender IMAP thread error: %s', _e)

                import threading as _thr
                _thr.Thread(
                    target=_bg_bulk_move, daemon=True,
                    name=f'imap-bulk-move-{aid}',
                ).start()

            return _json_response({'success': True, 'data': {
                'moved':         moved_count,
                'senders':       senders,
                'target_folder': target_folder,
                'db_folder':     db_folder,
                'unread_count':  unread_count,
            }})
        except Exception as exc:
            _logger.exception('bulk_move_by_sender error')
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
                        inline_parts=None, request_read_receipt=False,
                        written_in_arabic=False):
    """
    Build a MIME message from pre-loaded data.

    Returns a tuple (raw_rfc2822_string, generated_message_id) so callers can
    persist the Message-ID back to the DB record and enable IMAP deduplication.

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

    generated_msg_id = make_msgid(
        domain=from_address.split('@')[-1] if '@' in from_address else 'mail'
    )
    mime_msg['Subject']    = subject
    mime_msg['From']       = from_header
    mime_msg['To']         = ', '.join(to_list)
    mime_msg['Date']       = formatdate(localtime=True)
    mime_msg['Message-ID'] = generated_msg_id
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

    # Propagate Arabic-compose flag to the recipient's inbox so the FE can
    # render the body RTL.  This is a private Lugal extension header; non-Lugal
    # clients silently ignore it.
    if written_in_arabic:
        mime_msg['X-Written-In-Arabic'] = 'true'

    return mime_msg.as_string(), generated_msg_id


def _do_smtp_send(smtp_host, smtp_port, smtp_use_tls, username, password,
                  from_address, all_recipients, raw_message, msg_id, db_name,
                  generated_msg_id=None):
    """
    Perform the actual SMTP send and write result back to lugal.email.message.
    Safe to call from a background thread — uses its own Registry cursor for
    the write-back so it never touches the HTTP request cursor.

    generated_msg_id – the RFC-2822 Message-ID that was embedded in the outgoing
                       MIME message.  Written back to the DB record so that when
                       the IMAP Sent folder is synced the upsert logic can match
                       on message_id and update the existing row instead of
                       creating a duplicate.

    Returns (delivered: bool, error_msg: str|None, refused: dict).
    """
    import smtplib
    import socket
    import time

    delivered = False
    error_msg = None
    refused   = {}

    def _connect_and_send(host, port, use_tls):
        # Port 465 = implicit TLS (SMTP_SSL).
        # smtp_use_tls + other ports = STARTTLS (explicit TLS, common on 587).
        # No TLS + non-465 = plain SMTP (port 25 or custom relay).
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
            server.ehlo()
        elif use_tls:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()

        try:
            server.login(username, password)
            return server.sendmail(from_address, all_recipients, raw_message)
        finally:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass

    transient_errors = (
        ConnectionResetError,
        ConnectionAbortedError,
        BrokenPipeError,
        TimeoutError,
        socket.timeout,
        OSError,
        smtplib.SMTPServerDisconnected,
    )

    attempts = [(int(smtp_port or 587), bool(smtp_use_tls))]
    if attempts[0][0] == 465:
        attempts.append((587, True))
    elif attempts[0][0] == 587:
        attempts.append((465, False))

    try:
        last_exc = None
        partial_refused = {}
        sent_ok = False
        for idx, (attempt_port, attempt_tls) in enumerate(attempts, start=1):
            for retry in range(1, 3):
                try:
                    partial_refused = _connect_and_send(
                        smtp_host, attempt_port, attempt_tls,
                    )
                    if attempt_port != int(smtp_port or 587):
                        _logger.warning(
                            'SMTP delivered via fallback route: from=%s to=%s '
                            'primary=%s:%s fallback=%s:%s',
                            from_address, all_recipients, smtp_host, smtp_port,
                            smtp_host, attempt_port,
                        )
                    last_exc = None
                    sent_ok = True
                    break
                except smtplib.SMTPRecipientsRefused:
                    raise
                except smtplib.SMTPAuthenticationError:
                    raise
                except transient_errors as exc:
                    last_exc = exc
                    _logger.warning(
                        'SMTP transient failure attempt=%s.%s from=%s to=%s '
                        'host=%s:%s tls=%s error=%s',
                        idx, retry, from_address, all_recipients,
                        smtp_host, attempt_port, attempt_tls, exc,
                    )
                    if retry < 2:
                        time.sleep(0.75)
                        continue
                    break
            if sent_ok:
                break
        if not sent_ok and last_exc:
            raise last_exc

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
                    write_vals = {
                        'smtp_delivered': final_delivered,
                        'smtp_error':     error_msg or False,
                        'smtp_status':    'delivered' if final_delivered else 'failed',
                    }
                    # Persist the generated RFC-2822 Message-ID so the IMAP Sent
                    # folder sync can find this exact row by message_id and update
                    # it (stamping imap_uid) instead of creating a duplicate record.
                    if generated_msg_id and not record.message_id:
                        write_vals['message_id'] = generated_msg_id
                        # Bootstrap thread_id from message_id if not yet set.
                        if not record.thread_id:
                            write_vals['thread_id'] = generated_msg_id
                    record.write(write_vals)
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


def _send_mdn_async(acc, to_address, original_message_id, original_subject, recipient_email):
    """
    Send a Message Disposition Notification (MDN / read receipt) asynchronously.

    Called when a user marks an inbox message as read and the original sender
    requested a receipt (Disposition-Notification-To header, RFC 3798).

    acc                  – lugal.email.account (sender's / recipient's account)
    to_address           – RFC-2822 address to deliver the MDN to (original From / DNT)
    original_message_id  – Message-ID of the email being acknowledged
    original_subject     – Subject of the original email
    recipient_email      – Email address of the person who read the message
    """
    import threading

    db_name      = acc.env.cr.dbname
    acc_id       = acc.id
    smtp_host    = acc.smtp_host
    smtp_port    = acc.smtp_port
    smtp_use_tls = acc.smtp_use_tls
    username     = acc.username or acc.email_address
    password     = acc.password or ''
    from_address = acc.email_address
    display_name = (acc.display_name_field or '').strip()

    def _bg():
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email.utils import formatdate, make_msgid

        try:
            # RFC 3798 MDN structure:
            #   multipart/report; report-type=disposition-notification
            #     ├── text/plain            (human-readable notice)
            #     └── message/disposition-notification  (machine-readable fields)
            mdn = MIMEMultipart('report', report_type='disposition-notification')
            from_hdr = f'{display_name} <{from_address}>' if display_name else from_address
            mdn['From']       = from_hdr
            mdn['To']         = to_address
            mdn['Subject']    = f'Read: {original_subject}' if original_subject else 'Read: (no subject)'
            mdn['Date']       = formatdate(localtime=True)
            mdn['Message-ID'] = make_msgid(
                domain=from_address.split('@')[-1] if '@' in from_address else 'mail'
            )

            # Part 1: Human-readable text (required by RFC 3798)
            human_text = (
                f'Your message "{original_subject}" was read by {recipient_email}.'
            )
            mdn.attach(MIMEText(human_text, 'plain', 'utf-8'))

            # Part 2: Machine-readable notification
            notif_body = (
                f'Reporting-UA: LugalAI Mail Server\r\n'
                f'Final-Recipient: rfc822; {recipient_email}\r\n'
                f'Original-Recipient: rfc822; {recipient_email}\r\n'
                f'Original-Message-ID: {original_message_id}\r\n'
                f'Disposition: manual-action/MDN-sent-automatically; displayed\r\n'
            )
            notif_part = MIMEBase('message', 'disposition-notification')
            notif_part.set_payload(notif_body)
            mdn.attach(notif_part)

            raw_mdn = mdn.as_string()

            # Send via SMTP (same credentials as the receiver's outbound SMTP)
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
            server.sendmail(from_address, [to_address], raw_mdn)
            server.quit()
            _logger.info(
                'MDN sent: from=%s to=%s orig_mid=%s',
                from_address, to_address, original_message_id,
            )
        except Exception as exc:
            _logger.warning(
                'MDN send failed: from=%s to=%s orig_mid=%s error=%s',
                from_address, to_address, original_message_id, exc,
            )

    threading.Thread(target=_bg, daemon=True, name=f'mdn-acc{acc_id}').start()


def _send_via_smtp_async(acc, to_list, subject, body_html, body_text, cc=None, bcc=None,
                         msg_id=None, attachment_ids=None, importance='normal',
                         request_read_receipt=False, written_in_arabic=False):
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
    att_ids          = [int(i) for i in (attachment_ids or [])]
    all_recipients   = list(to_list) + list(cc or []) + list(bcc or [])
    _written_arabic  = bool(written_in_arabic)   # capture primitive before thread

    _logger.info(
        'SMTP async queued: from=%s to=%s attachments=%s msg_id=%s written_in_arabic=%s',
        from_address, all_recipients, att_ids, msg_id, _written_arabic,
    )

    def _bg():
        """Background worker: reads files, builds MIME, sends, then appends to IMAP Sent."""
        try:
            from odoo.modules.registry import Registry as _Registry
            import odoo as _odoo

            # Open a fresh cursor to read attachment binary data.
            with _Registry(db_name).cursor() as _cr:
                att_parts, inline_parts = _read_att_parts(att_ids, _cr, db_name)

            raw_message, generated_msg_id = _build_mime_message(
                from_header, to_list, subject, body_html, body_text, cc, att_parts,
                from_address, importance=importance,
                inline_parts=inline_parts,
                request_read_receipt=request_read_receipt,
                written_in_arabic=_written_arabic,
            )

            delivered, error_msg, refused = _do_smtp_send(
                smtp_host, smtp_port, smtp_use_tls, username, password,
                from_address, all_recipients, raw_message, msg_id, db_name,
                generated_msg_id=generated_msg_id,
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
    raw_message, generated_msg_id = _build_mime_message(
        from_header, to_list, subject, body_html, body_text, cc, att_parts, from_address,
        inline_parts=inline_parts,
    )
    return _do_smtp_send(
        smtp_host, smtp_port, smtp_use_tls, username, password,
        from_address, all_recipients, raw_message, msg_id, db_name,
        generated_msg_id=generated_msg_id,
    )
# TODO: remove - cherry-pick marker
