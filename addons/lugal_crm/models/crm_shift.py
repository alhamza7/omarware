# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmShift(models.Model):
    """
    Work shift definition — configurable per branch.
    Two shifts supported (morning / evening / night).
    """
    _name = 'lugal.crm.shift'
    _description = 'CRM Work Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'branch_id asc, shift_type asc, id asc'
    _rec_name = 'name'

    name = fields.Char(string='Shift Name / اسم الوردية', required=True, tracking=True)
    name_ar = fields.Char(string='اسم الوردية بالعربي', tracking=True)

    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='cascade',
        required=True,
        index=True,
        tracking=True,
    )

    shift_type = fields.Selection([
        ('morning', 'Morning / صباحي'),
        ('evening', 'Evening / مسائي'),
        ('night', 'Night / ليلي'),
        ('custom', 'Custom / مخصص'),
    ], string='Shift Type / نوع الوردية', default='morning', required=True, tracking=True)

    start_time = fields.Float(
        string='Start Time / وقت البداية',
        required=True,
        default=8.0,
        help='Hour of day in 24h decimal (e.g. 8.5 = 08:30)',
        tracking=True,
    )
    end_time = fields.Float(
        string='End Time / وقت النهاية',
        required=True,
        default=17.0,
        help='Hour of day in 24h decimal (e.g. 17.0 = 17:00)',
        tracking=True,
    )

    # Users assigned to this shift
    user_ids = fields.Many2many(
        'res.users',
        'lugal_crm_shift_user_rel',
        'shift_id', 'user_id',
        string='Assigned Employees / الموظفون',
        tracking=True,
    )

    is_active = fields.Boolean(string='Active / نشط', default=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
