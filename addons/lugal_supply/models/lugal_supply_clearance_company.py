# -*- coding: utf-8 -*-

from odoo import models, fields


class LugalSupplyClearanceCompany(models.Model):
    """Customs clearance company used in container shipments."""
    _name = 'lugal.supply.clearance.company'
    _description = 'Supply Clearance Company'
    _order = 'name asc, id asc'

    name = fields.Char(string='Company Name', required=True, index=True)
    contact_name = fields.Char(string='Contact Name')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    whatsapp = fields.Char(string='WhatsApp')
    telegram = fields.Char(string='Telegram')
    country_id = fields.Many2one('res.country', string='Country', ondelete='set null')
    city = fields.Char(string='City')
    address = fields.Text(string='Address')
    license_number = fields.Char(string='License Number')
    license_expiry = fields.Date(string='License Expiry')
    notes = fields.Text(string='Notes')
    is_active = fields.Boolean(string='Active', default=True, index=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
    active = fields.Boolean(default=True)
