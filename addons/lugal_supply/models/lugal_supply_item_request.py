# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LugalSupplyItemRequest(models.Model):
    """Request from a branch/agent to replenish inventory of a specific product."""
    _name = 'lugal.supply.item.request'
    _description = 'Lugal Supply Item Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.dynamic.extra.mixin']
    _order = 'request_date desc, id desc'
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

    # ── Item details ────────────────────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='Product / المنتج',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    product_name = fields.Char(string='Product Name / اسم المنتج', tracking=True)
    item_name = fields.Char(string='Item Name / اسم الصنف', tracking=True)
    item_code = fields.Char(string='Item Code / رمز الصنف', index=True, tracking=True)
    description = fields.Text(string='Description / الوصف', tracking=True)
    quantity = fields.Float(string='Quantity / الكمية', digits=(16, 4), default=1.0, tracking=True)
    uom = fields.Char(string='Unit of Measure / وحدة القياس', tracking=True)
    capacity = fields.Char(string='Capacity / السعة', tracking=True)
    packing_pcs_per_carton = fields.Float(
        string='Packing (pcs/carton) / عدد القطع بالكرتون',
        digits=(16, 4),
        tracking=True,
    )

    # ── Requester ───────────────────────────────────────────────────────────────
    # Integer instead of Many2one('lugal.crm.branch') to avoid circular dependency:
    # lugal_crm depends on lugal_supply, so lugal_supply cannot depend on lugal_crm.
    branch_id = fields.Integer(string='Branch ID / معرّف الفرع', index=True, tracking=True)
    requested_by_id = fields.Many2one(
        'res.users',
        string='Requested By / طلب بواسطة',
        ondelete='set null',
        default=lambda self: self.env.uid,
        index=True,
        tracking=True,
    )
    request_date = fields.Date(
        string='Request Date / تاريخ الطلب',
        default=fields.Date.today,
        index=True,
        tracking=True,
    )

    # ── Workflow state ──────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft / مسودة'),
        ('in_progress', 'In Progress / قيد التنفيذ'),
        ('completed', 'Completed / مكتمل'),
        ('cancelled', 'Cancelled / ملغي'),
    ], string='State / الحالة', default='draft', required=True, index=True, tracking=True)

    # ── Approval status (separate from workflow state) ──────────────────────────
    status = fields.Selection([
        ('pending', 'Pending / معلق'),
        ('approved', 'Approved / موافق عليه'),
        ('rejected', 'Rejected / مرفوض'),
        ('fulfilled', 'Fulfilled / منجز'),
    ], string='Approval Status / حالة الموافقة', default='pending', index=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low / منخفض'),
        ('normal', 'Normal / عادي'),
        ('high', 'High / عالي'),
        ('urgent', 'Urgent / عاجل'),
    ], string='Priority / الأولوية', default='normal', tracking=True)

    # ── Notes ───────────────────────────────────────────────────────────────────
    note = fields.Text(string='Internal Note / ملاحظة داخلية', tracking=True)
    notes = fields.Text(string='Notes / ملاحظات', tracking=True)

    # ── Review ──────────────────────────────────────────────────────────────────
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By / راجعه',
        ondelete='set null',
        tracking=True,
    )
    reviewed_at = fields.Datetime(string='Reviewed At / وقت المراجعة', tracking=True)

    # ── Confirmation ─────────────────────────────────────────────────────────────
    requester_confirm_user_id = fields.Many2one(
        'res.users',
        string='Confirmed By (requester) / أكده المُقدِّم',
        ondelete='set null',
        tracking=True,
    )
    requester_confirm_date = fields.Datetime(
        string='Confirmed At / وقت التأكيد',
        tracking=True,
    )

    # ── Attachments ──────────────────────────────────────────────────────────────
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_item_request_attachment_rel',
        'record_id',
        'attachment_id',
        string='Attachments / المرفقات',
    )
    attachment_count = fields.Integer(compute='_compute_attachment_count', store=False)

    # ── Soft delete / archive ────────────────────────────────────────────────────
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    # ── Computed ─────────────────────────────────────────────────────────────────
    negotiation_count = fields.Integer(compute='_compute_negotiation_count', store=False)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def _compute_negotiation_count(self):
        Neg = self.env['lugal.supply.negotiation'].sudo()
        for rec in self:
            rec.negotiation_count = Neg.search_count([
                ('item_request_id', '=', rec.id),
                ('is_deleted', '=', False),
            ]) if 'item_request_id' in Neg._fields else 0

    # ── Workflow actions (base implementations, extended by lugal_crm workflow) ──
    def action_start_progress(self):
        self.write({'state': 'in_progress'})

    def action_mark_completed(self):
        self.write({'state': 'completed'})

    def action_requester_confirm(self):
        self.write({
            'requester_confirm_user_id': self.env.uid,
            'requester_confirm_date': fields.Datetime.now(),
        })

    def action_reset_draft(self):
        self.write({'state': 'draft'})
