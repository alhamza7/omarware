# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmCallQueue(models.Model):
    """Call queue — multiple incoming calls from same or different channels."""
    _name = 'lugal.crm.call.queue'
    _description = 'CRM Call Queue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'queue_position asc, queued_at asc, id asc'
    _rec_name = 'caller_number'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    channel = fields.Char(string='Channel / القناة', index=True, tracking=True)
    caller_number = fields.Char(string='Caller Number / رقم المتصل', index=True, tracking=True)
    queue_position = fields.Integer(string='Queue Position / ترتيب الانتظار', default=1, tracking=True)
    status = fields.Selection([
        ('waiting', 'Waiting / في الانتظار'),
        ('assigned', 'Assigned / مُعيَّن'),
        ('answered', 'Answered / تم الرد'),
        ('abandoned', 'Abandoned / مُلغى'),
    ], string='Status / الحالة', default='waiting', required=True, index=True, tracking=True)
    assigned_to_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    queued_at = fields.Datetime(string='Queued At / وقت الدخول', default=fields.Datetime.now, required=True, index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
