# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmCustomerStage(models.Model):
    """Customer pipeline stage — configurable via table (lead → interested → active → vip → dormant)."""
    _name = 'lugal.crm.customer.stage'
    _description = 'CRM Customer Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, id asc'
    _rec_name = 'name'

    name = fields.Char(string='Stage Name / المرحلة', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='الاسم بالعربي', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_type = fields.Selection([
        ('lead', 'Lead / عميل محتمل'),
        ('interested', 'Interested / مهتم'),
        ('active', 'Active / نشط'),
        ('vip', 'VIP'),
        ('dormant', 'Dormant / خامل'),
    ], string='Stage Type', default='lead', required=True, index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
