# -*- coding: utf-8 -*-
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
        """Apply a rule retroactively to all existing inbox messages for the user."""
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

        Automatically creates the IMAP folder structure and immediately moves
        any existing matching messages into the destination folder (both in the
        DB and on the IMAP server synchronously — no fire-and-forget).

        Body:
          {
            "template_key":  "move_important_from_sender",
            "sender_email":  "omar@nooralnibras.com",
            "sender_name":   "Omar",
            "account_id":    4
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

            # Canonical address for rule conditions + folder slug
            sender_addr = sender_email
            if not sender_addr and sender_name and '@' in sender_name:
                sender_addr = sender_name.strip()
            if not sender_addr:
                return _json_err(
                    'sender_email is required (JSON key sender_email or senderEmail; '
                    'or pass sender_name as a full address containing @)',
                    400,
                )

            # ── Folder slug: always from email local-part, dots → underscores ──
            import re as _re

            def _folder_slug_from_email(addr: str) -> str:
                addr = (addr or '').strip().lower()
                if not addr:
                    return 'sender'
                local, _, domain = addr.partition('@')
                local = (local or (domain.split('.')[0] if domain else '') or 'sender')
                # Dots in local-part become '_' so the slug is one IMAP hierarchy segment
                local = local.replace('.', '_')
                slug = _re.sub(r'[^\w\-]+', '_', local, flags=_re.ASCII).strip('_') or 'sender'
                return slug[:60].rstrip('_')

            folder_slug = _folder_slug_from_email(sender_addr)

            slug_override = (body.get('folder_slug') or '').strip()
            if slug_override:
                folder_slug = _re.sub(r'[^\w\-]+', '', slug_override, flags=_re.ASCII)[:60] or folder_slug

            # Human-readable rule label
            if sender_name and '@' not in sender_name and sender_name.strip():
                sender_label = f'{sender_name.strip()} ({sender_addr})'
            else:
                sender_label = sender_addr

            # ── Template catalogue ─────────────────────────────────────────────
            # IMPORTANT: move_important_from_sender uses only from_address condition.
            # The word "Important" is the FOLDER NAME, not the is_important flag.
            # Requiring is_important=true would silently skip most emails because
            # very few senders set Importance: high headers.
            TEMPLATES = {
                'move_all_from_sender': {
                    'label':       f'Move all emails from {sender_label}',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_important_from_sender': {
                    'label':       f'Move all emails from {sender_label} to Important',
                    'child_name':  'Important',
                    'match_mode':  'all',
                    # Only match on sender address — "Important" is the folder name,
                    # NOT the is_important flag. Do not add is_important condition here.
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
                        {'field': 'from_address',    'operator': 'contains', 'value': sender_addr},
                        {'field': 'has_attachments', 'operator': 'equals',   'value': 'true'},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_cc_bcc_from_sender': {
                    'label':       f'Move all emails with CC and BCC from {sender_label}',
                    'child_name':  'CC and BCC',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',  'operator': 'contains',     'value': sender_addr},
                        {'field': 'cc_addresses',  'operator': 'is_not_empty', 'value': ''},
                        {'field': 'bcc_addresses', 'operator': 'is_not_empty', 'value': ''},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'mark_important_from_sender': {
                    'label':       f'Mark all emails from {sender_label} as important',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                    ],
                    'mark_actions': [{'action': 'mark_important'}],
                    'stop_processing': False,
                },
                'mark_read_from_sender': {
                    'label':       f'Auto-mark all emails from {sender_label} as read',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_addr},
                    ],
                    'mark_actions': [{'action': 'mark_read'}],
                    'stop_processing': False,
                },
            }

            tpl = TEMPLATES.get(template_key)
            if not tpl:
                return _json_err(
                    f'Unknown template_key. Valid keys: {list(TEMPLATES)}', 400)

            # ── Build IMAP folder paths ────────────────────────────────────────
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
                        # Detect delimiter by listing all folders.
                        # Do NOT use conn.list('', '') — some servers (cPanel/Dovecot)
                        # reject an empty reference string with "Invalid reference".
                        typ_d, listing_d = conn_probe.list()
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

            # ── Auto-apply: update DB immediately, move on IMAP in background ──
            # Moving 100+ messages via individual IMAP round-trips inside an HTTP
            # request reliably times out. Instead:
            #   1. Update the DB folder field for all matching messages RIGHT NOW
            #      so the FE sees them in the correct folder instantly.
            #   2. Fire a single background thread that opens one IMAP connection
            #      and moves all messages using UID MOVE in batches.
            applied_count = 0
            skipped_count = 0

            if is_move_template:
                Msg = request.env['lugal.email.message'].sudo()
                existing = Msg.search([
                    ('account_id', '=', int(account_id)),
                    ('is_deleted', '=', False),
                ], order='id desc', limit=2000)

                # Find matching messages and collect (msg_id, imap_uid, from_folder)
                to_move_db  = []   # ORM records for DB update
                to_move_imap = []  # (imap_uid, from_imap_path) for background thread
                _LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

                for msg in existing:
                    msg_vals = {
                        'from_address':    msg.from_address or '',
                        'to_addresses':    msg.to_addresses or '',
                        'cc_addresses':    msg.cc_addresses or '',
                        'bcc_addresses':   msg.bcc_addresses or '',
                        'subject':         msg.subject or '',
                        'body_text':       msg.body_text or '',
                        'has_attachments': False,
                        'is_important':    msg.is_important,
                        'is_read':         msg.is_read,
                        'is_starred':      msg.is_starred,
                        'folder':          msg.folder or '',
                    }
                    try:
                        if rule._matches(msg_vals):
                            to_move_db.append(msg)
                            # Determine IMAP source path for this message
                            cur = msg.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                imap_from = 'INBOX'
                            elif cur.lower() in _LOGICAL:
                                # We'll resolve the actual server name in the bg thread
                                imap_from = cur.lower()
                            else:
                                imap_from = cur
                            if msg.imap_uid:
                                to_move_imap.append((msg.imap_uid, imap_from))
                    except Exception:
                        skipped_count += 1

                # Step 1: update DB immediately so FE sees messages in new folder
                if to_move_db:
                    try:
                        # Batch write is much faster than one write() per record
                        Msg.browse([m.id for m in to_move_db]).write({'folder': dest_path})
                        request.env.cr.commit()
                        applied_count = len(to_move_db)
                    except Exception as dbe:
                        _logger.warning('from_template DB batch update failed: %s', dbe)
                        for msg in to_move_db:
                            try:
                                msg.write({'folder': dest_path})
                                applied_count += 1
                            except Exception:
                                skipped_count += 1
                        try:
                            request.env.cr.commit()
                        except Exception:
                            pass

                # Step 2: fire background thread for IMAP moves
                # Groups UIDs by source folder so we only SELECT each mailbox once.
                if to_move_imap:
                    import threading as _threading
                    import collections as _collections
                    db_name = request.env.cr.dbname
                    acc_id  = acc.id
                    _dest   = dest_path

                    # Group by source folder for efficiency
                    by_folder = _collections.defaultdict(list)
                    for uid, from_folder in to_move_imap:
                        by_folder[from_folder].append(uid)

                    def _bg_imap_move():
                        try:
                            from odoo.modules.registry import Registry as _Reg
                            import odoo as _odoo
                            with _Reg(db_name).cursor() as _cr:
                                _env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                                _acc = _env['lugal.email.account'].browse(acc_id)
                                with _acc._imap_session() as conn:
                                    for src_folder, uids in by_folder.items():
                                        # Resolve logical names to real IMAP paths
                                        if src_folder.lower() == 'inbox':
                                            imap_src = 'INBOX'
                                        elif src_folder.lower() in _LOGICAL:
                                            imap_src = _acc._get_server_folder_name(
                                                src_folder.lower(), existing_conn=conn)
                                        else:
                                            imap_src = src_folder

                                        try:
                                            conn.select(imap_src, readonly=False)
                                        except Exception as se:
                                            _logger.warning(
                                                'bg_imap_move: SELECT %s failed: %s', imap_src, se)
                                            continue

                                        # Move in batches of 50 UIDs at a time
                                        _BATCH = 50
                                        for i in range(0, len(uids), _BATCH):
                                            batch = uids[i:i + _BATCH]
                                            uid_set = ','.join(str(u) for u in batch)
                                            try:
                                                typ_m, _ = conn.uid('move', uid_set, _dest)
                                                if typ_m != 'OK':
                                                    # Fallback: COPY + mark deleted + expunge
                                                    conn.uid('copy', uid_set, _dest)
                                                    conn.uid('store', uid_set, '+FLAGS', '(\\Deleted)')
                                                    conn.expunge()
                                                _logger.info(
                                                    'bg_imap_move: moved %d uids from %s → %s',
                                                    len(batch), imap_src, _dest,
                                                )
                                            except Exception as me:
                                                _logger.warning(
                                                    'bg_imap_move: batch move failed %s → %s: %s',
                                                    imap_src, _dest, me,
                                                )
                        except Exception as exc:
                            _logger.warning('bg_imap_move thread failed acc=%s: %s', acc_id, exc)

                    _threading.Thread(
                        target=_bg_imap_move, daemon=True,
                        name=f'imap-bulk-move-{acc_id}',
                    ).start()

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
                'auto_applied': {
                    'applied':          applied_count,
                    'skipped':          skipped_count,
                    'imap_move_queued': bool(to_move_imap) if is_move_template else False,
                },
            }, status=201)

        except Exception as exc:
            _logger.exception('rules_from_template error')
            return _json_err(str(exc), 500)

    # ── Rule Templates ────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/templates', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_templates(self, **kwargs):
        """Return predefined rule templates for the 'Create Rule' dropdown."""
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
                'conditions':  sender_cond() or [{'field': 'from_address', 'operator': 'contains', 'value': ''}],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_important_from_sender',
                'label':       f'Move all emails from {sender_name} to Important folder' if sender_email
                               else 'Move all emails from a sender into an Important subfolder',
                'description': (
                    'Move every email from this sender into the account\'s '
                    'INBOX.<slug>.Important folder. Note: "Important" is the mailbox '
                    'name — all emails from this sender are moved, not just flagged ones.'
                ),
                'match_mode':  'all',
                'conditions':  sender_cond() or [{'field': 'from_address', 'operator': 'contains', 'value': ''}],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_with_attachments_from_sender',
                'label':       f'Move all emails with attachments from {sender_name}' if sender_email
                               else 'Move all emails with attachments from a specific sender',
                'description': 'Move emails that contain attachments from this sender.',
                'match_mode':  'all',
                'conditions':  sender_cond() + [{'field': 'has_attachments', 'operator': 'equals', 'value': 'true'}],
                'actions':     move_action,
                'stop_processing': True,
            },
            {
                'key':         'move_with_cc_bcc_from_sender',
                'label':       f'Move all emails with CC and BCC from {sender_name}' if sender_email
                               else 'Move all emails with CC and BCC from a specific sender',
                'description': 'Move only when both CC and BCC lists are non-empty.',
                'match_mode':  'all',
                'conditions':  sender_cond() + [
                    {'field': 'cc_addresses',  'operator': 'is_not_empty', 'value': ''},
                    {'field': 'bcc_addresses', 'operator': 'is_not_empty', 'value': ''},
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
                'conditions':  sender_cond() or [{'field': 'from_address', 'operator': 'contains', 'value': ''}],
                'actions':     [{'action': 'mark_important'}],
                'stop_processing': False,
            },
            {
                'key':         'mark_read_from_sender',
                'label':       f'Auto-mark all emails from {sender_name} as read' if sender_email
                               else 'Auto-mark all emails from a specific sender as read',
                'description': 'Silently mark every incoming email from this sender as already read.',
                'match_mode':  'all',
                'conditions':  sender_cond() or [{'field': 'from_address', 'operator': 'contains', 'value': ''}],
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
        """Apply a quick step to a message. Body: { "quick_step_id": 5 }"""
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