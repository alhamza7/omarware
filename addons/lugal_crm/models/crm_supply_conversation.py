# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalSupplyConversation(models.Model):
    """
    Internal supply-team messaging thread.

    Types:
      team  — broadcast channel for the whole supply team (one per branch, auto-created)
      dm    — direct message between two users (unique pair constraint)
      group — ad-hoc group created by any user, can be renamed/archived
    """
    _name = 'lugal.supply.conversation'
    _description = 'Supply Conversation'
    _order = 'last_activity desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    type = fields.Selection([
        ('team',  'Team Channel'),
        ('dm',    'Direct Message'),
        ('group', 'Group Chat'),
    ], string='Type', required=True, default='group', index=True)

    participant_ids = fields.Many2many(
        'res.users',
        'lugal_supply_conversation_user_rel',
        'conversation_id', 'user_id',
        string='Participants',
    )

    created_by_id = fields.Many2one(
        'res.users', string='Created By',
        default=lambda self: self.env.user,
        ondelete='set null', index=True,
    )

    last_activity = fields.Datetime(string='Last Activity', index=True)
    is_archived   = fields.Boolean(string='Archived', default=False, index=True)
    active        = fields.Boolean(default=True)

    # Unread count per user is tracked at message level
    # (computed on-the-fly via supply messages)
