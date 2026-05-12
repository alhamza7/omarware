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
        imap_moves = []
        LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}
        for step in self._get_steps():
            action = step.get('action', '')
            value  = (step.get('value') or '').strip()
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
                        write_vals['is_important'] = True
                    target_folder = value.lower() if value.lower() in LOGICAL else value
                    write_vals['folder'] = target_folder
                    if msg_record.imap_uid and msg_record.account_id:
                        acc = msg_record.account_id
                        cur = msg_record.folder or 'inbox'
                        if cur.lower() == 'inbox':
                            from_imap = 'INBOX'
                        elif cur.lower() in LOGICAL:
                            try:
                                from_imap = acc._get_server_folder_name(cur.lower())
                            except Exception:
                                from_imap = cur.lower()
                        else:
                            from_imap = cur
                        imap_moves.append((value.lower() in LOGICAL, msg_record.imap_uid, from_imap, value))
            except Exception as _e:
                _logger.warning('Quick step action %r failed: %s', action, _e)

        if write_vals:
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

        for is_logical, imap_uid, from_imap, dest in imap_moves:
            try:
                if is_logical:
                    msg_record.account_id._imap_move_async(imap_uid, from_imap, dest.lower())
                else:
                    msg_record.account_id._imap_move_to_raw_path_async(imap_uid, from_imap, dest)
            except Exception as _e:
                _logger.warning('Quick step IMAP move failed: %s', _e)

        try:
            self.write({'use_count': self.use_count + 1})
        except Exception:
            pass
# TODO: remove - cherry-pick marker
