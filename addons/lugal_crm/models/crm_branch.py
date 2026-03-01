# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmBranch(models.Model):
    """Company branch — isolates tickets, reports, and user access."""
    _name = 'lugal.crm.branch'
    _description = 'CRM Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    _rec_name = 'name'

    name = fields.Char(string='Branch Name / اسم الفرع', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='الاسم بالعربي', tracking=True)
    code = fields.Char(string='Branch Code', index=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    city = fields.Char(string='City / المدينة')
    address = fields.Text(string='Address / العنوان')
    phone = fields.Char(string='Phone / الهاتف')
    email = fields.Char(string='Email')

    manager_id = fields.Many2one('res.users', string='Branch Manager / مدير الفرع', tracking=True)
    user_ids = fields.Many2many(
        'res.users',
        'lugal_crm_branch_user_rel',
        'branch_id', 'user_id',
        string='Authorized Users / المستخدمون المخولون',
    )

    note = fields.Text(string='Notes / ملاحظات')

    customer_count = fields.Integer(string='Customers', compute='_compute_customer_count', store=False)

    def _compute_customer_count(self):
        """Count customers linked to this branch."""
        Customer = self.env.get('lugal.crm.customer')
        if not Customer:
            for branch in self:
                branch.customer_count = 0
            return
        for branch in self:
            branch.customer_count = Customer.search_count([
                ('branch_ids', 'in', branch.id),
                ('is_deleted', '=', False),
            ])
