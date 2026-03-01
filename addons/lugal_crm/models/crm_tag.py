# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmTag(models.Model):
    """Flexible customer tags — VIP, Enterprise, Lead, Loyal, etc. No hardcoding."""
    _name = 'lugal.crm.tag'
    _description = 'CRM Tag'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, name asc'
    _rec_name = 'name'

    name = fields.Char(string='Tag Name / اسم التاغ', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='الاسم بالعربي', tracking=True)
    color = fields.Integer(string='Color Index')
    sequence = fields.Integer(string='Sequence', default=10)
    tag_type = fields.Selection([
        ('vip', 'VIP'),
        ('enterprise', 'Enterprise'),
        ('lead', 'Lead'),
        ('loyal', 'Loyal'),
        ('stale', 'Stale'),
        ('active', 'Active'),
        ('custom', 'Custom'),
    ], string='Tag Type / نوع التاغ', default='custom', index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
