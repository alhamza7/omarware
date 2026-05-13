# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LugalSupplyNegotiation(models.Model):
    """Price negotiation with a vendor — linked to supply vendor and optional product."""
    _name = 'lugal.supply.negotiation'
    _description = 'Lugal Supply Negotiation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.dynamic.extra.mixin']
    _order = 'write_date desc, id desc'
    _rec_name = 'name'

    # ── Reference ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Reference / المرجع',
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        index=True,
        tracking=True,
    )
    title = fields.Char(string='Title / العنوان', index=True, tracking=True)

    # ── Item details ────────────────────────────────────────────────────────────
    item_request_id = fields.Many2one(
        'lugal.supply.item.request',
        string='Item Request / طلب الصنف',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product / المنتج',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_name = fields.Char(string='Product Name (free) / اسم المنتج', tracking=True)
    item_name = fields.Char(string='Item Name / اسم الصنف', tracking=True)
    description = fields.Text(string='Description / الوصف', tracking=True)
    quantity = fields.Float(string='Quantity / الكمية', digits=(16, 4), tracking=True)
    uom = fields.Char(string='Unit of Measure / وحدة القياس', tracking=True)
    capacity = fields.Char(string='Capacity / السعة', tracking=True)
    packing_pcs_per_carton = fields.Float(
        string='Packing (pcs/carton) / عدد القطع بالكرتون',
        digits=(16, 4),
        tracking=True,
    )

    # ── Vendor & agent ──────────────────────────────────────────────────────────
    supply_vendor_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Supply Vendor / المورد',
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        'res.partner',
        string='Odoo Partner / شريك أودو',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.partner',
        string='Agent / الوكيل',
        ondelete='set null',
        index=True,
        tracking=True,
    )

    # ── Pricing ─────────────────────────────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency / العملة',
        ondelete='set null',
        tracking=True,
    )
    expected_price = fields.Float(
        string='Expected Price / السعر المتوقع',
        digits=(16, 4),
        tracking=True,
    )
    offered_price = fields.Float(
        string='Offered Price / السعر المعروض',
        digits=(16, 4),
        tracking=True,
    )
    agreed_price = fields.Float(
        string='Agreed Price / السعر المتفق عليه',
        digits=(16, 4),
        tracking=True,
    )
    final_agreed_price = fields.Float(
        string='Final Agreed Price / السعر النهائي',
        digits=(16, 4),
        tracking=True,
    )
    final_currency_id = fields.Many2one(
        'res.currency',
        string='Final Currency / عملة السعر النهائي',
        ondelete='set null',
        tracking=True,
    )

    # ── Workflow state ──────────────────────────────────────────────────────────
    state = fields.Selection([
        ('ongoing', 'Ongoing / جارٍ'),
        ('finalized', 'Finalized / مُنجز'),
        ('cancelled', 'Cancelled / ملغي'),
    ], string='State / الحالة', default='ongoing', required=True, index=True, tracking=True)

    # ── Approval status ──────────────────────────────────────────────────────────
    status = fields.Selection([
        ('open', 'Open / مفتوح'),
        ('pending', 'Pending / معلق'),
        ('closed', 'Closed / مغلق'),
    ], string='Approval Status / حالة الموافقة', default='open', index=True, tracking=True)

    due_date = fields.Date(string='Due Date / تاريخ الاستحقاق', tracking=True)

    # ── Finalization ─────────────────────────────────────────────────────────────
    finalized_by_id = fields.Many2one(
        'res.users',
        string='Finalized By / أنجزه',
        ondelete='set null',
        tracking=True,
    )
    finalized_date = fields.Datetime(string='Finalized At / وقت الإنجاز', tracking=True)

    # ── Lead time ────────────────────────────────────────────────────────────────
    expected_lead_time_days = fields.Integer(
        string='Expected Lead Time (days) / المهلة المتوقعة',
        tracking=True,
    )
    quoted_delivery_date = fields.Date(
        string='Quoted Delivery Date / تاريخ التسليم المعروض',
        tracking=True,
    )

    # ── Notes & terms ────────────────────────────────────────────────────────────
    notes = fields.Text(string='Notes / ملاحظات', tracking=True)
    terms = fields.Text(string='Terms & Conditions / الشروط والأحكام', tracking=True)

    # ── People ────────────────────────────────────────────────────────────────────
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )

    # ── Offer history (price rounds) ─────────────────────────────────────────────
    offer_ids = fields.One2many(
        'lugal.supply.negotiation.offer',
        'negotiation_id',
        string='Offer History / سجل العروض',
    )

    # ── Attachments ──────────────────────────────────────────────────────────────
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_negotiation_attachment_rel',
        'record_id',
        'attachment_id',
        string='Attachments / المرفقات',
    )
    attachment_count = fields.Integer(compute='_compute_attachment_count', store=False)

    # ── Soft delete / archive ────────────────────────────────────────────────────
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    # ── Computed ─────────────────────────────────────────────────────────────────
    order_count = fields.Integer(compute='_compute_order_count', store=False)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(getattr(rec, 'supply_po_ids', self.env['lugal.crm.supply.po'].browse()))

    # ── Workflow actions ──────────────────────────────────────────────────────────
    def action_e_sign_approve(self):
        self.write({'state': 'finalized', 'finalized_by_id': self.env.uid, 'finalized_date': fields.Datetime.now()})

    def action_finalize(self):
        self.write({'state': 'finalized', 'finalized_by_id': self.env.uid, 'finalized_date': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_ongoing(self):
        self.write({'state': 'ongoing'})

    def get_negotiation_e_sign_api_payload(self):
        """Return e-sign metadata for the API; extended by lugal_crm if e-sign module is active."""
        return {
            'e_sign_user_id': None,
            'e_sign_user_name': '',
            'e_sign_date': None,
        }
