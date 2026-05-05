# -*- coding: utf-8 -*-
from odoo import models, fields


class LugalSupplyClearanceCompany(models.Model):
    """Customs clearance company — used to link containers to their تخليص شركة."""
    _name = 'lugal.supply.clearance.company'
    _description = 'Lugal Supply Clearance Company'
    _order = 'name asc, id asc'
    _rec_name = 'name'

    name = fields.Char(string='Company Name / اسم الشركة', required=True, index=True)
    contact_name = fields.Char(string='Contact Person / مسؤول الاتصال')
    phone = fields.Char(string='Phone / الهاتف')
    email = fields.Char(string='Email')
    whatsapp = fields.Char(string='WhatsApp')
    telegram = fields.Char(string='Telegram')
    country_id = fields.Many2one('res.country', string='Country / الدولة', ondelete='set null')
    city = fields.Char(string='City / المدينة')
    address = fields.Text(string='Address / العنوان')
    license_number = fields.Char(string='License Number / رقم الترخيص')
    license_expiry = fields.Date(string='License Expiry / انتهاء الترخيص')
    notes = fields.Text(string='Notes / ملاحظات')
    is_active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
