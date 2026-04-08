# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class LugalSupplyVendor(models.Model):
    """Supply vendor card — specific CRM/supply context for each vendor including WhatsApp & WeChat."""
    _name = 'lugal.supply.vendor'
    _description = 'Lugal Supply Vendor'
    _order = 'name asc, id asc'
    _rec_name = 'name'

    name = fields.Char(string='Vendor Name / اسم المورد', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='اسم المورد (عربي)', tracking=True)

    # Link to Odoo standard partner (optional — for accounting / PO integration)
    partner_id = fields.Many2one(
        'res.partner',
        string='Odoo Partner / شريك أودو',
        ondelete='set null',
        index=True,
        tracking=True,
        help='Link to res.partner for accounting and standard PO flow.',
    )

    division = fields.Selection([
        ('europe', 'Europe / أوروبا'),
        ('china', 'China / الصين'),
        ('other', 'Other / أخرى'),
    ], string='Division / القسم', index=True, tracking=True)

    country_id = fields.Many2one('res.country', string='Country / الدولة', ondelete='set null', tracking=True)
    city = fields.Char(string='City / المدينة', tracking=True)
    address = fields.Text(string='Address / العنوان', tracking=True)

    # Primary contacts
    contact_name = fields.Char(string='Contact Person / اسم جهة الاتصال', tracking=True)
    phone = fields.Char(string='Phone / الهاتف', tracking=True)
    email = fields.Char(string='Email / البريد الإلكتروني', tracking=True)
    website = fields.Char(string='Website / الموقع', tracking=True)

    # Messaging channels — essential for China office workflow
    whatsapp = fields.Char(string='WhatsApp / واتساب', tracking=True)
    wechat = fields.Char(string='WeChat / وي شات', tracking=True)
    telegram = fields.Char(string='Telegram / تيليجرام', tracking=True)

    # Commercial details
    payment_terms = fields.Char(string='Payment Terms / شروط الدفع', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency / العملة', ondelete='set null', tracking=True)
    lead_time_days = fields.Integer(string='Lead Time (days) / مدة التوريد (أيام)', tracking=True)
    min_order_value = fields.Float(string='Min Order Value / الحد الأدنى للطلب', digits=(16, 2), tracking=True)

    notes = fields.Text(string='Notes / ملاحظات', tracking=True)

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
