# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmKbNotification(models.Model):
    """Admin push notification — events, surveys, announcements to branches."""
    _name = 'lugal.crm.kb.notification'
    _description = 'CRM Knowledge Base Notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sent_at desc, id desc'
    _rec_name = 'title'

    title = fields.Char(string='Title / العنوان', required=True, index=True, tracking=True)
    body = fields.Text(string='Body / المحتوى', tracking=True)
    sent_by_id = fields.Many2one(
        'res.users',
        string='Sent By / أرسله',
        default=lambda self: self.env.user,
        ondelete='set null',
        index=True,
        tracking=True,
    )
    branch_ids = fields.Many2many(
        'lugal.crm.branch',
        'lugal_crm_kb_notification_branch_rel',
        'notification_id', 'branch_id',
        string='Branches / الفروع',
        help='Empty = all branches.',
        tracking=True,
    )
    sent_at = fields.Datetime(string='Sent At / وقت الإرسال', default=fields.Datetime.now, required=True, index=True, tracking=True)
    notification_type = fields.Selection([
        ('event', 'Event / حدث'),
        ('survey', 'Survey / استبيان'),
        ('announcement', 'Announcement / إعلان'),
    ], string='Type / النوع', default='announcement', index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
