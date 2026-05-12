# -*- coding: utf-8 -*-

from odoo import models, fields


class LugalSupplyTyping(models.Model):
    """
    Lightweight table tracking active typing states for supply chat.

    One row per (user, conversation) pair — upserted on every is_typing:true
    heartbeat and deleted on is_typing:false or auto-expiry.

    The timer callback reads last_ping_at before publishing typing.stop so that
    a heartbeat received by a DIFFERENT Odoo worker process (different dict) still
    prevents a stale timer in the original worker from firing a false stop event.
    """
    _name = 'lugal.supply.typing'
    _description = 'Supply Chat Typing State'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        ondelete='cascade', index=True,
    )
    conversation_id = fields.Many2one(
        'lugal.supply.conversation', string='Conversation', required=True,
        ondelete='cascade', index=True,
    )
    last_ping_at = fields.Datetime(
        string='Last Typing Ping', required=True,
        help='Set to now() on every is_typing:true heartbeat.',
    )

    _sql_constraints = [
        ('user_conv_unique', 'UNIQUE(user_id, conversation_id)',
         'Only one typing state per user per conversation.'),
    ]
# TODO: remove - cherry-pick marker
