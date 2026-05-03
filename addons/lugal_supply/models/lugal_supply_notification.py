# -*- coding: utf-8 -*-

from odoo import models, fields


class LugalSupplyNotification(models.Model):
    """Supply-chain push notification for a specific user."""
    _name = 'lugal.supply.notification'
    _description = 'Supply Notification'
    _order = 'create_date desc, id desc'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )
    notif_type = fields.Char(string='Notification Type', required=True, index=True)
    title = fields.Char(string='Title', required=True)
    body = fields.Text(string='Body')
    related_id = fields.Integer(string='Related Record ID')
    related_type = fields.Char(string='Related Model')
    is_read = fields.Boolean(string='Read', default=False, index=True)
    read_at = fields.Datetime(string='Read At')
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
