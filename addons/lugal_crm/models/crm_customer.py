# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmCustomer(models.Model):
    """360° customer card — identity, classification, commerce, samples, branches, loyalty."""
    _name = 'lugal.crm.customer'
    _description = 'CRM Customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'name'

    # --- Identity ---
    name = fields.Char(string='Name / الاسم', required=True, index=True, tracking=True)
    name_ar = fields.Char(string='الاسم بالعربي', tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Odoo Partner / الشريك',
        help='Link to res.partner used by POS/ERP for invoices and orders.',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    phone_1 = fields.Char(string='Phone 1 / الهاتف 1', index=True, tracking=True)
    phone_2 = fields.Char(string='Phone 2 / الهاتف 2', tracking=True)
    phone_3 = fields.Char(string='Phone 3 / الهاتف 3', tracking=True)
    email = fields.Char(string='Email', index=True, tracking=True)
    address = fields.Text(string='Address / العنوان', tracking=True)
    city = fields.Char(string='City / المدينة', tracking=True)
    country_id = fields.Many2one('res.country', string='Country / الدولة', ondelete='set null', tracking=True)
    photo = fields.Binary(string='Photo / الصورة', attachment=True)

    # --- Classification ---
    stage_id = fields.Many2one(
        'lugal.crm.customer.stage',
        string='Stage / المرحلة',
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'lugal.crm.tag',
        'lugal_crm_customer_tag_rel',
        'customer_id', 'tag_id',
        string='Tags / التاغات',
        tracking=True,
    )
    vip_status = fields.Boolean(string='VIP', default=False, tracking=True)
    is_enterprise = fields.Boolean(string='Enterprise / شركة', default=False, tracking=True)
    lifetime_value = fields.Float(string='Lifetime Value / القيمة الدائمة', digits=(16, 2), tracking=True)
    credit_debt = fields.Float(string='Credit Debt / الذمم', digits=(16, 2), tracking=True)
    credit_limit = fields.Float(string='Credit Limit / حد الائتمان', digits=(16, 2), tracking=True)

    # --- Dates ---
    member_since = fields.Date(string='Member Since / عضو منذ', tracking=True)
    last_call_date = fields.Datetime(string='Last Call / آخر مكالمة', tracking=True)
    last_purchase_date = fields.Date(string='Last Purchase / آخر شراء', tracking=True)
    days_since_purchase = fields.Integer(
        string='Days Since Purchase / أيام منذ آخر شراء',
        compute='_compute_days_since_purchase',
        store=False,
    )

    # --- Commerce (status text for display) ---
    open_invoice_status = fields.Char(string='Open Invoice Status / حالة الفواتير المفتوحة', tracking=True)
    delivery_status = fields.Char(string='Delivery Status / حالة التوصيل', tracking=True)
    most_purchased_item_ids = fields.Many2many(
        'product.product',
        'lugal_crm_customer_product_rel',
        'customer_id', 'product_id',
        string='Most Purchased Items / الأكثر شراءً',
    )

    # --- Location / Shop ---
    shop_name = fields.Char(string='Shop Name / اسم المحل', tracking=True)
    shop_location = fields.Char(string='Shop Location / موقع المحل', tracking=True)
    favorite_shipping_address = fields.Text(string='Favorite Shipping Address / عنوان الشحن المفضل', tracking=True)
    billing_address = fields.Text(string='Billing Address / عنوان الفوترة', tracking=True)
    billing_method = fields.Char(string='Billing Method / طريقة الفوترة', tracking=True)

    # --- Extended Address ---
    state = fields.Char(string='State / Province / المحافظة', tracking=True)
    district = fields.Char(string='District / الحي', tracking=True)
    building = fields.Char(string='Building / المبنى', tracking=True)
    postal_code = fields.Char(string='Postal Code / الرمز البريدي', tracking=True)

    # --- Preferences ---
    favorite_fragrance = fields.Char(string='Favorite Fragrance / العطر المفضل', tracking=True)

    # --- Samples ---
    sample_version = fields.Char(string='Sample Version / نسخة العينة', tracking=True)
    sample_date = fields.Date(string='Sample Date / تاريخ العينة', tracking=True)
    sample_image = fields.Binary(string='Sample Image / صورة العينة', attachment=True)

    # --- Attachments (ID documents / وثائق الهوية) ---
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_crm_customer_attachment_rel',
        'customer_id', 'attachment_id',
        string='ID Documents / وثائق الهوية',
    )

    # --- Relations ---
    branch_ids = fields.Many2many(
        'lugal.crm.branch',
        'lugal_crm_customer_branch_rel',
        'customer_id', 'branch_id',
        string='Branches / الفروع',
        tracking=True,
    )
    account_manager_id = fields.Many2one(
        'res.users',
        string='Account Manager / مدير الحساب',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    referral_source = fields.Char(string='Referral Source / مصدر الإحالة', tracking=True)

    # --- Loyalty ---
    loyalty_points = fields.Float(string='Loyalty Points / نقاط الولاء', digits=(16, 2), tracking=True)
    preferred_contact_time = fields.Char(string='Preferred Contact Time / وقت التواصل المفضل', tracking=True)
    preferred_contact_channel = fields.Char(string='Preferred Channel / القناة المفضلة', tracking=True)

    # --- Flags ---
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    # --- Extended Classification ---
    activity_type = fields.Char(string='Activity Type / نوع النشاط', tracking=True)
    customer_strength = fields.Char(string='Customer Strength / قوة العميل', tracking=True)
    dealing_method = fields.Char(string='Dealing Method / طريقة التعامل', tracking=True)
    customer_rating = fields.Integer(string='Customer Rating / تقييم العميل', default=0, tracking=True)
    assigned_agent = fields.Char(string='Assigned Agent / الوكيل المعين', tracking=True)
    notes = fields.Text(string='Notes / الملاحظات', tracking=True)

    # --- Media (stored as JSON arrays) ---
    shop_images = fields.Text(string='Shop Images / صور المحل', help='JSON array of image URLs')
    customer_docs = fields.Text(string='Customer Docs / وثائق العميل', help='JSON array of {type, name, url}')

    # --- Reverse relations ---
    channel_identity_ids = fields.One2many(
        'lugal.crm.channel.identity',
        'customer_id',
        string='Channel Identities',
        domain=[('is_deleted', '=', False)],
    )

    @api.depends('last_purchase_date')
    def _compute_days_since_purchase(self):
        """Compute days since last purchase from today."""
        from datetime import date
        today = date.today()
        for rec in self:
            if rec.last_purchase_date:
                delta = today - rec.last_purchase_date
                rec.days_since_purchase = delta.days
            else:
                rec.days_since_purchase = 0

    # ── Partner synchronisation ──────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        """
        When creating a CRM customer:
        - If no partner_id, look for an existing active res.partner with the same
          name + phone before creating a new one (prevents duplicates).
        - If partner_id provided, ensure customer_rank >= 1.
        Always keeps the two records in sync.
        """
        Partner = self.env['res.partner'].sudo()
        Customer = self.env['lugal.crm.customer'].sudo()
        for vals in vals_list:
            if vals.get('_skip_partner_sync'):
                vals.pop('_skip_partner_sync', None)
                continue
            if not vals.get('partner_id'):
                name  = vals.get('name', '').strip()
                phone = (vals.get('phone_1') or vals.get('phone') or '').strip()

                # Prevent duplicate CRM entries: reuse partner if name+phone match
                existing_partner = None
                if name and phone:
                    existing_partner = Partner.search([
                        ('name', '=', name),
                        ('phone', '=', phone),
                        ('active', '=', True),
                    ], limit=1)
                elif name:
                    existing_partner = Partner.search([
                        ('name', '=', name),
                        ('phone', '=', False),
                        ('active', '=', True),
                    ], limit=1)

                # If a partner already has an active (non-deleted) CRM record, block creation
                if existing_partner:
                    crm_exists = Customer.with_context(active_test=False).search([
                        ('partner_id', '=', existing_partner.id),
                        ('is_deleted', '=', False),
                        ('active', '=', True),
                    ], limit=1)
                    if crm_exists:
                        raise ValueError(
                            f"Customer '{name}' with phone '{phone}' already exists (id={crm_exists.id})"
                        )
                    else:
                        # Partner exists but CRM record was deleted — reuse partner
                        existing_partner.write({'customer_rank': 1, 'active': True})
                        vals['partner_id'] = existing_partner.id
                else:
                    partner = Partner.create({
                        'name':          vals.get('name', 'Unnamed'),
                        'email':         vals.get('email', ''),
                        'phone':         vals.get('phone_1', ''),
                        'city':          vals.get('city', ''),
                        'country_id':    vals.get('country_id', False),
                        'customer_rank': 1,
                        'is_company':    False,
                    })
                    vals['partner_id'] = partner.id
            else:
                partner = Partner.browse(vals['partner_id'])
                if partner.exists() and partner.customer_rank == 0:
                    partner.write({'customer_rank': 1})
        return super().create(vals_list)

    def write(self, vals):
        """
        When key identity fields change on a CRM customer, mirror them to
        the linked res.partner so Odoo always has fresh data.
        """
        result = super().write(vals)
        if self.env.context.get('_skip_partner_sync'):
            return result
        partner_map = {
            'name':       'name',
            'email':      'email',
            'phone_1':    'phone',
            'city':       'city',
            'country_id': 'country_id',
        }
        partner_vals = {
            pf: vals[cf] for cf, pf in partner_map.items() if cf in vals
        }
        if partner_vals:
            for rec in self.filtered('partner_id'):
                rec.partner_id.sudo().with_context(_skip_crm_sync=True).write(partner_vals)
        return result

    def unlink(self):
        """Soft-delete only — sets is_deleted = True instead of removing the record."""
        return self.write({'is_deleted': True, 'active': False})
