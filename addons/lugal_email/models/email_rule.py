# -*- coding: utf-8 -*-
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
