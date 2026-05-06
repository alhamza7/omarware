# -*- coding: utf-8 -*-
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
            sender_email = (body.get('sender_email') or '').strip()
            sender_name  = (body.get('sender_name')  or sender_email or '').strip()
            account_id   = body.get('account_id')

            if not template_key:
                return _json_err('template_key is required', 400)
            if not account_id:
                return _json_err('account_id is required', 400)

            acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
            if not acc.exists() or acc.user_id.id != uid:
                return _json_err('Account not found or access denied', 404)

            # ── Folder path segment: derive from *email*, not display nickname ──
            # Using sender_name alone strips dots ("syed.naqvi" → "syednaqvi") and
            # breaks expectations; IMAP segments must stay stable and match the
            # mailbox owner.  Optional body.folder_slug overrides (alphanumeric + _-).
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

            if sender_email:
                folder_slug = _folder_slug_from_email(sender_email)
            else:
                folder_slug = _re.sub(r'[^\w\s\-]', '', (sender_name or 'Sender')).strip()
                folder_slug = _re.sub(r'\s+', '_', folder_slug) or 'Sender'

            slug_override = (body.get('folder_slug') or '').strip()
            if slug_override:
                folder_slug = _re.sub(r'[^\w\-]+', '', slug_override, flags=_re.ASCII)[:60] or folder_slug

            # Human-readable name in rule titles (prefer real name; else email)
            if sender_name and '@' not in sender_name:
                sender_label = sender_name.strip()
            else:
                sender_label = (sender_email or sender_name or 'Sender').strip()

            # ── Template catalogue ─────────────────────────────────────────────
            LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
            TEMPLATES = {
                'move_all_from_sender': {
                    'label':       f'Move all emails from {sender_label}',
                    'child_name':  None,   # goes straight into parent folder
                    'match_mode':  'all',
                    'conditions':  [{'field': 'from_address', 'operator': 'contains',
                                     'value': sender_email}],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_important_from_sender': {
                    'label':       f'Move all important emails from {sender_label}',
                    'child_name':  'Important',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address', 'operator': 'contains', 'value': sender_email},
                        {'field': 'is_important', 'operator': 'equals',   'value': 'true'},
                    ],
                    'mark_actions': [],
                    'stop_processing': True,
                },
                'move_with_attachments_from_sender': {
                    'label':       f'Move all emails with attachments from {sender_label}',
                    'child_name':  'With Attachments',
                    'match_mode':  'all',
                    'conditions':  [
                        {'field': 'from_address',   'operator': 'contains', 'value': sender_email},
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
                        {'field': 'from_address',   'operator': 'contains',     'value': sender_email},
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
                                     'value': sender_email}],
                    'mark_actions': [{'action': 'mark_important'}],
                    'stop_processing': False,
                },
                'mark_read_from_sender': {
                    'label':       f'Auto-mark all emails from {sender_label} as read',
                    'child_name':  None,
                    'match_mode':  'all',
                    'conditions':  [{'field': 'from_address', 'operator': 'contains',
                                     'value': sender_email}],
                    'mark_actions': [{'action': 'mark_read'}],
                    'stop_processing': False,
                },
            }

            tpl = TEMPLATES.get(template_key)
            if not tpl:
                return _json_err(
                    f'Unknown template_key. Valid keys: {list(TEMPLATES)}', 400)

            # ── Build IMAP folder paths ────────────────────────────────────────
            # Detect the IMAP hierarchy delimiter (usually '.' or '/').
            delimiter = '.'
            child_name = tpl['child_name']
            folders_created = []
            is_move_template = bool(child_name) or template_key.startswith('move_')
            with acc._imap_session() as conn_probe:
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

                # ── Create IMAP folders if needed (move templates only) ─────
                if is_move_template:
                    try:
                        acc._imap_ensure_folder(parent_path, existing_conn=conn_probe)
                        folders_created.append(parent_path)
                    except Exception as fe:
                        return _json_err(f'Could not create parent folder "{parent_path}": {fe}', 500)

                    if child_name:
                        try:
                            acc._imap_ensure_folder(dest_path, existing_conn=conn_probe)
                            folders_created.append(dest_path)
                        except Exception as fe:
                            return _json_err(f'Could not create child folder "{dest_path}": {fe}', 500)

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
                'label':       f'Move all important emails from {sender_name}' if sender_email
                               else 'Move all important emails from a specific sender',
                'description': 'Move emails marked as high-importance from this sender to a chosen folder.',
                'match_mode':  'all',
                'conditions':  sender_cond() + [{
                    'field': 'is_important', 'operator': 'equals', 'value': 'true',
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
