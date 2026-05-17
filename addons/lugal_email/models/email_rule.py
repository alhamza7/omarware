# -*- coding: utf-8 -*-
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

# Folders that are valid sources for inbox rule execution.
# Rules only fire when a message arrives in one of these folders.
# This prevents rules from re-firing on messages that were already
# moved to a custom folder (e.g. by a previous rule application).
_RULE_SOURCE_FOLDERS = {'inbox'}


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

    @api.model
    def _message_has_attachments(self, msg_record=None, msg_vals=None) -> bool:
        """Return whether a message has stored or MIME-detected attachments.

        Attachment rules are evaluated in two places:
        - live IMAP import, where attachments may only exist in the parsed MIME
          payload at rule-evaluation time;
        - retroactive apply-all/template flows, where attachments are already
          stored as ir.attachment rows.
        """
        msg_vals = msg_vals or {}
        raw = msg_vals.get('has_attachments')
        if isinstance(raw, bool) and raw:
            return True
        if isinstance(raw, str) and raw.strip().lower() in ('1', 'true', 'yes', 'on'):
            return True
        if msg_record and msg_record.exists():
            return bool(self.env['ir.attachment'].sudo().search_count([
                ('res_model', '=', 'lugal.email.message'),
                ('res_id', '=', msg_record.id),
            ]))
        return False

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
        _imap_moves = []   # list of (kind, imap_uid, from_imap_path, dest)

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
                    if value.replace('/', '.').split('.')[-1].lower() == 'important':
                        # Folder semantics are authoritative.  Anything routed
                        # into an Important child folder must remain visible in
                        # that folder's API, which filters on is_important.
                        write_vals['is_important'] = True
                    if value.lower() in LOGICAL:
                        write_vals['folder'] = value.lower()
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            cur = msg_record.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                from_imap = 'INBOX'
                            elif cur.lower() in LOGICAL:
                                from_imap = acc._get_server_folder_name(cur.lower())
                            else:
                                from_imap = cur
                            _imap_moves.append(('logical', msg_record.imap_uid, from_imap, value.lower()))
                    else:
                        # Custom IMAP path — store raw path in folder field
                        write_vals['folder'] = value
                        if msg_record.imap_uid and msg_record.account_id:
                            acc = msg_record.account_id
                            cur = msg_record.folder or 'inbox'
                            if cur.lower() == 'inbox':
                                from_imap = 'INBOX'
                            elif cur.lower() in LOGICAL:
                                try:
                                    from_imap = acc._get_server_folder_name(cur.lower())
                                except Exception:
                                    from_imap = 'INBOX'
                            else:
                                from_imap = cur
                            _imap_moves.append(('raw', msg_record.imap_uid, from_imap, value))
                elif action == 'stop_processing':
                    stop = True
            except Exception as _e:
                _logger.warning('Email rule action %r failed: %s', action, _e)

        if write_vals:
            # Use a savepoint so that a DB-level constraint violation (e.g.
            # (account_id, imap_uid, folder) unique index when the destination
            # folder was already synced independently) does NOT leave the outer
            # PostgreSQL transaction in an aborted state.  Without this, the
            # caught exception silently corrupts the parent savepoint in
            # _upsert_batch, causing the entire message insert to be rolled
            # back and the IMAP max-uid cursor to stall — emails end up re-
            # appearing in inbox on every sync.
            try:
                with self.env.cr.savepoint():
                    msg_record.write(write_vals)
                if msg_record.account_id and (
                    'folder' in write_vals or 'is_read' in write_vals
                ):
                    unread_count = self.env['lugal.email.message'].sudo().search_count([
                        ('account_id', '=', msg_record.account_id.id),
                        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                        ('is_read', '=', False),
                        ('is_deleted', '=', False),
                    ])
                    msg_record.account_id.sudo().write({'unread_count': unread_count})
            except Exception as _e:
                _logger.warning('Email rule write failed for msg %s: %s',
                                getattr(msg_record, 'id', '?'), _e)

        # Fire IMAP moves after the DB write
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

        # Audit — use savepoint so a concurrent write failure doesn't
        # abort the caller's transaction.
        try:
            with self.env.cr.savepoint():
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
        """Run all active rules for the message owner against a freshly-imported message.

        Rules only fire when the message is landing in the inbox folder.
        This prevents rules from re-firing on messages already moved to custom
        folders by a previous rule pass.

        msg_vals: plain dict with the same keys as the create() vals dict.
        """
        # Guard: only run rules on messages landing in inbox.
        # Messages imported into sent, custom folders, etc. should not
        # trigger move rules — they are already where they belong.
        current_folder = (msg_vals.get('folder') or '').lower().strip()
        if current_folder not in _RULE_SOURCE_FOLDERS:
            _logger.debug(
                'apply_inbox_rules: skipping msg %s — folder=%r not in rule source folders',
                getattr(msg_record, 'id', '?'), current_folder,
            )
            return

        account_id = msg_vals.get('account_id')
        if not account_id:
            _logger.debug('apply_inbox_rules: skipping msg %s — no account_id in vals',
                          getattr(msg_record, 'id', '?'))
            return

        acc = self.env['lugal.email.account'].sudo().browse(account_id)
        if not acc.exists():
            _logger.debug('apply_inbox_rules: skipping msg %s — account %s not found',
                          getattr(msg_record, 'id', '?'), account_id)
            return
        owner_uid = acc.user_id.id
        if not owner_uid:
            _logger.debug(
                'apply_inbox_rules: skipping msg %s — account %s has no user_id',
                getattr(msg_record, 'id', '?'), account_id,
            )
            return

        # Augment vals with a real attachment sentinel.  This must not default
        # to False blindly, otherwise attachment rules never match during IMAP
        # import or retroactive apply-all.
        msg_vals_aug = dict(
            msg_vals,
            has_attachments=self._message_has_attachments(msg_record, msg_vals),
        )

        rules = self.sudo().search([
            ('is_active', '=', True),
            ('user_id',   '=', owner_uid),
            '|',
            ('account_id', '=', account_id),
            ('account_id', '=', False),
        ], order='sequence asc, id asc')

        if not rules:
            _logger.debug(
                'apply_inbox_rules: no active rules found for user_id=%s account_id=%s',
                owner_uid, account_id,
            )
            return

        _logger.debug(
            'apply_inbox_rules: evaluating %d rule(s) for msg %s '
            '(from=%r folder=%r)',
            len(rules), getattr(msg_record, 'id', '?'),
            msg_vals_aug.get('from_address', ''), current_folder,
        )

        for rule in rules:
            try:
                if rule._matches(msg_vals_aug):
                    _logger.debug(
                        'apply_inbox_rules: rule %s matched msg %s — applying actions',
                        rule.id, getattr(msg_record, 'id', '?'),
                    )
                    should_stop = rule._apply_actions(msg_record)
                    if should_stop:
                        break
            except Exception as _e:
                _logger.warning('Email rule %s evaluation error: %s', rule.id, _e)

    # ── Retroactive apply for all inbound messages of a user ───────────────────

    @api.model
    def apply_all_rules_for_user(self, user_id, account_id=None, limit=10000):
        """Retroactively apply all active move-rules for a user to their inbound mail.

        Processes messages in ALL inbound folders (inbox + custom) so emails
        already sitting in the wrong folder also get re-sorted.

        Args:
            user_id:    res.users id of the target user.
            account_id: optional — restrict to a single lugal.email.account.
            limit:      max messages to scan (default 10000).

        Returns:
            dict with keys: matched, moved, skipped, rules_considered.
        """
        Rule = self.sudo()
        Msg  = self.env['lugal.email.message'].sudo()

        rule_domain = [('user_id', '=', user_id), ('is_active', '=', True)]
        msg_domain  = [
            ('account_id.user_id', '=', user_id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_deleted', '=', False),
        ]
        if account_id:
            aid = int(account_id)
            rule_domain.append(('account_id', '=', aid))
            msg_domain.append(('account_id',  '=', aid))

        rules = Rule.search(rule_domain, order='sequence asc, id asc')
        move_rules = rules.filtered(lambda r: any(
            act.get('action') == 'move_folder' and (act.get('value') or '').strip()
            for act in (self._safe_json(r.actions_json))
        ))

        if not move_rules:
            _logger.info(
                'apply_all_rules_for_user: no active move-rules for user_id=%s', user_id,
            )
            return {'matched': 0, 'moved': 0, 'skipped': 0, 'rules_considered': 0}

        matched = moved = skipped = 0
        affected_accounts = self.env['lugal.email.account'].sudo().browse()

        for msg in Msg.search(msg_domain, order='date desc, id desc', limit=limit):
            msg_vals = {
                'from_address':  msg.from_address or '',
                'to_addresses':  msg.to_addresses or '',
                'cc_addresses':  msg.cc_addresses or '',
                'bcc_addresses': msg.bcc_addresses or '',
                'subject':       msg.subject or '',
                'body_text':     msg.body_text or '',
                'has_attachments': self._message_has_attachments(msg),
                'is_important':  msg.is_important,
                'is_read':       msg.is_read,
                'is_starred':    msg.is_starred,
                'folder':        msg.folder or '',
                'account_id':    msg.account_id.id,
            }
            for rule in move_rules:
                try:
                    if not rule._matches(msg_vals):
                        continue

                    # Determine destination folder
                    dest = next(
                        (
                            act.get('value', '').strip()
                            for act in self._safe_json(rule.actions_json)
                            if act.get('action') == 'move_folder'
                            and (act.get('value') or '').strip()
                        ),
                        None,
                    )
                    if not dest:
                        continue

                    # Skip if already in the correct folder branch
                    cur = (msg.folder or '').strip()
                    already_there = (
                        cur == dest
                        or cur.startswith(dest + '.')
                        or cur.startswith(dest + '/')
                    )
                    if already_there:
                        if rule.stop_processing:
                            break
                        continue

                    matched += 1
                    before_folder = msg.folder
                    affected_accounts |= msg.account_id
                    rule._apply_actions(msg)
                    msg.invalidate_recordset()
                    if msg.folder != before_folder:
                        moved += 1
                        _logger.info(
                            'apply_all_rules_for_user: moved msg %s '
                            '(%r) %r → %r via rule %s',
                            msg.id, msg.subject, before_folder, msg.folder, rule.id,
                        )
                    if rule.stop_processing:
                        break
                except Exception as exc:
                    skipped += 1
                    _logger.warning(
                        'apply_all_rules_for_user: rule %s / msg %s failed: %s',
                        rule.id, msg.id, exc,
                    )
                    break

        # Refresh unread counts
        for acc in affected_accounts:
            unread = Msg.search_count([
                ('account_id', '=', acc.id),
                ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                ('is_read', '=', False),
                ('is_deleted', '=', False),
            ])
            acc.write({'unread_count': unread})

        _logger.info(
            'apply_all_rules_for_user: user_id=%s rules=%d '
            'matched=%d moved=%d skipped=%d',
            user_id, len(move_rules), matched, moved, skipped,
        )
        return {
            'matched': matched,
            'moved': moved,
            'skipped': skipped,
            'rules_considered': len(move_rules),
        }

    @staticmethod
    def _safe_json(raw):
        """Parse a JSON field, returning [] on any error."""
        try:
            return json.loads(raw or '[]') or []
        except Exception:
            return []
