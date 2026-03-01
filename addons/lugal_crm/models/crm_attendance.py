# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmAttendance(models.Model):
    """
    Employee attendance record — check-in/out, device/IP/location capture.
    Supervisor can view remote work status in the Admin Dashboard.
    """
    _name = 'lugal.crm.attendance'
    _description = 'CRM Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_in desc, id desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'res.users',
        string='Employee / الموظف',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    shift_id = fields.Many2one(
        'lugal.crm.shift',
        string='Shift / الوردية',
        ondelete='set null',
        tracking=True,
    )

    check_in = fields.Datetime(string='Check In / وقت الحضور', required=True, index=True, tracking=True)
    check_out = fields.Datetime(string='Check Out / وقت الانصراف', index=True, tracking=True)
    duration_hours = fields.Float(string='Duration (hours) / المدة (ساعات)', digits=(6, 2), tracking=True)

    work_type = fields.Selection([
        ('office', 'Office / مكتب'),
        ('remote', 'Remote / عن بُعد'),
        ('field', 'Field / ميداني'),
    ], string='Work Type / نوع العمل', default='office', index=True, tracking=True)

    # IP / device / location captured at check-in
    ip_address = fields.Char(string='IP Address / عنوان IP', tracking=True)
    device_type = fields.Char(string='Device Type / نوع الجهاز', tracking=True)
    location_lat = fields.Float(string='Latitude / خط العرض', digits=(9, 6), tracking=True)
    location_lng = fields.Float(string='Longitude / خط الطول', digits=(9, 6), tracking=True)
    location_label = fields.Char(string='Location / الموقع', tracking=True)

    notes = fields.Text(string='Notes / ملاحظات', tracking=True)
    is_late = fields.Boolean(string='Late / متأخر', default=False, tracking=True)

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
