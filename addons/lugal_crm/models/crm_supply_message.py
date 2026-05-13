# -*- coding: utf-8 -*-

import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalSupplyMessage(models.Model):
    """
    Individual message in a supply team conversation.
    Supports plain text, attachments, reply-to quoting, emoji reactions, and soft delete.
    """
    _name = 'lugal.supply.message'
    _description = 'Supply Message'
    _order = 'create_date asc, id asc'
    _rec_name = 'content'

    conversation_id = fields.Many2one(
        'lugal.supply.conversation',
        string='Conversation',
        required=True,
        ondelete='cascade',
        index=True,
    )

    sender_id = fields.Many2one(
        'res.users', string='Sender',
        ondelete='set null', index=True,
    )

    content = fields.Text(string='Content')

    # Message type — drives rendering on the FE
    kind = fields.Selection([
        ('text',  'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('voice', 'Voice Note'),  # recorded in-app voice message
        ('file',  'File / Document'),
    ], string='Kind', default='text', index=True,
       help='Determines how the FE renders this message.')

    # Duration in seconds for audio/video messages; 0 for other kinds
    duration_seconds = fields.Float(
        string='Duration (s)', default=0.0,
        help='Length of audio or video message in seconds.',
    )

    # Attachments stored as JSON: [{"id":1,"name":"file.pdf","url":"...","mimetype":"...","size":1024,"kind":"file","duration_seconds":0}]
    attachments_json = fields.Text(string='Attachments (JSON)', default='[]')

    # Reply-to (quote)
    reply_to_id = fields.Many2one(
        'lugal.supply.message',
        string='Reply To',
        ondelete='set null',
        index=True,
    )

    # Reactions stored as JSON: {"👍": [1, 5, 9], "❤️": [2]}
    reactions_json = fields.Text(string='Reactions (JSON)', default='{}')
    # Read receipts: {"user_id": "ISO-datetime"} — records WHEN each user read this message
    read_receipts_json = fields.Text(string='Read Receipts (JSON)', default='{}')

    edited_at  = fields.Datetime(string='Edited At')
    is_deleted = fields.Boolean(string='Deleted', default=False, index=True)
    is_pinned  = fields.Boolean(string='Pinned', default=False, index=True)
    pinned_at  = fields.Datetime(string='Pinned At')
    pinned_by_id = fields.Many2one('res.users', string='Pinned By', ondelete='set null')

    # Deduplication key set by the FE sender — echoed back in the WS push so the
    # sender can match the server-confirmed message against their optimistic temp entry
    # without relying on a negative temp ID.
    client_message_id = fields.Char(string='Client Message ID', index=True)

    # Track which users have read this message (per-user read receipts)
    read_user_ids = fields.Many2many(
        'res.users',
        'lugal_supply_message_read_rel',
        'message_id', 'user_id',
        string='Read By',
    )

    # Track which users have received this message on their device (delivery receipts)
    delivered_user_ids = fields.Many2many(
        'res.users',
        'lugal_supply_message_delivered_rel',
        'message_id', 'user_id',
        string='Delivered To',
    )

    # "Delete for me" — message stays for others; hidden for these users in messages/list
    hidden_user_ids = fields.Many2many(
        'res.users',
        'lugal_supply_message_hidden_user_rel',
        'message_id', 'user_id',
        string='Hidden For',
    )

    # Convenience properties
    @property
    def attachments(self):
        try:
            return json.loads(self.attachments_json or '[]')
        except Exception:
            return []

    @property
    def reactions(self):
        try:
            return json.loads(self.reactions_json or '{}')
        except Exception:
            return {}

    @api.model
    def domain_visible_for_user(self, user_id, conversation_id=None):
        """Use in messages/list search: exclude rows this user hid (delete-for-me)."""
        dom = [('hidden_user_ids', 'not in', [int(user_id)])]
        if conversation_id is not None:
            dom.append(('conversation_id', '=', int(conversation_id)))
        return dom
# TODO: remove - cherry-pick marker
