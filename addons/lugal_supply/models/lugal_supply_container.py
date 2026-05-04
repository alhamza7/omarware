# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalSupplyContainer(models.Model):
    """Supply container — B/L, clearance, tracking, status (Searates). موردين وحاويات."""
    _name = 'lugal.supply.container'
    _description = 'Lugal Supply Container'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'lugal.supply.attachment.sync.mixin']
    _order = 'departure_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Container Name / اسم الحاوية', required=True, index=True, tracking=True)
    shipment_ref = fields.Char(
        string='Shipment ID',
        readonly=True,
        copy=False,
        index=True,
        help='Auto-generated shipment reference (e.g. SHP-00001).',
    )
    container_number = fields.Char(string='Container Number / رقم الحاوية', index=True, tracking=True)
    bl_number = fields.Char(string='B/L Number / رقم بوليصة الشحن', index=True, tracking=True)
    clearance_company = fields.Char(string='Clearance Company / شركة التخليص', tracking=True)
    origin_location = fields.Char(string='Origin / المنشأ', tracking=True)
    departure_date = fields.Date(
        string='ETD (Departure) / تاريخ المغادرة',
        index=True,
        tracking=True,
    )
    eta = fields.Date(string='ETA / الموعد المتوقع', tracking=True)
    arrived_at = fields.Datetime(string='Arrived At / وقت الوصول', tracking=True)
    status = fields.Selection([
        ('waiting', 'Waiting / في الانتظار'),
        ('active', 'In Transit / في الطريق'),
        ('at_port', 'At Port / في الميناء'),
        ('completed', 'Completed / مكتمل'),
    ], string='Status / الحالة', default='waiting', index=True, tracking=True)
    division = fields.Selection([
        ('europe', 'Europe / أوروبا'),
        ('china', 'China / الصين'),
    ], string='Division / القسم', index=True, tracking=True)

    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To / مُعيَّن لـ',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    po_uploaded_by_id = fields.Many2one(
        'res.users',
        string='PO Uploaded By / رُفع الـ PO بواسطة',
        ondelete='set null',
        index=True,
        tracking=True,
    )

    tracking_url = fields.Char(string='Tracking URL (Searates)', tracking=True)
    # Optional JSON payload (e.g. carrier API snapshot) — read by GET .../tracking/view, written by tracking/update
    tracking_data = fields.Json(
        string='Tracking data (JSON)',
        default=False,
    )

    # --- Clearance delivery status (highlighted flag in UI) ---
    clearance_info_delivered = fields.Boolean(
        string='Clearance Info Delivered / تم إرسال المعلومات للمخلص',
        default=False,
        tracking=True,
    )
    clearance_info_delivered_at = fields.Datetime(
        string='Clearance Delivered At / تاريخ تسليم المعلومات',
        readonly=True,
        tracking=True,
    )
    clearance_info_delivered_by_id = fields.Many2one(
        'res.users',
        string='Delivered By / أرسلها',
        ondelete='set null',
        readonly=True,
        tracking=True,
    )

    # --- Attachments (B/L copies, customs docs, etc.) ---
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lugal_supply_container_attachment_rel',
        'container_id', 'attachment_id',
        string='Attachments / المرفقات',
    )
    penalty_ids = fields.One2many(
        'lugal.supply.container.penalty',
        'container_id',
        string='Penalties / الغرامات',
    )

    notes = fields.Text(string='Notes / ملاحظات', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    # --- Shipment tracking (supply chain workflow; complements legacy status above) ---
    supplier_id = fields.Many2one(
        'lugal.supply.vendor',
        string='Supplier',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    agent_id = fields.Many2one(
        'res.partner',
        string='Agent',
        ondelete='set null',
        index=True,
        tracking=True,
    )
    transport_mode = fields.Selection(
        [
            ('sea', 'Sea'),
            ('air', 'Air'),
            ('land', 'Land'),
            ('other', 'Other'),
        ],
        string='Shipping Method',
        tracking=True,
    )
    destination_location = fields.Char(string='Destination', tracking=True)
    shipping_line = fields.Char(
        string='Shipping Line',
        help='Carrier / line name (e.g. MSC, COSCO).',
        tracking=True,
    )
    shipment_tracking_state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('in_transit', 'In Transit'),
            ('transshipment', 'Transshipment'),
            ('arrived', 'Arrived'),
        ],
        string='Shipment Status',
        default='pending',
        tracking=True,
        index=True,
    )
    received_date = fields.Date(
        string='Received Date',
        help='Actual receipt date (goods arrived).',
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if not vals.get('shipment_ref'):
                vals['shipment_ref'] = seq.next_by_code('lugal.supply.shipment') or 'SHP-NEW'
        records = super().create(vals_list)
        records._lugal_sync_linked_attachments_res()
        return records

    def init(self):
        """Backfill Shipment ID for rows created before this field existed (no env in init)."""
        self._cr.execute(
            """
            UPDATE lugal_supply_container
            SET shipment_ref = 'SHP-L' || lpad(id::text, 6, '0')
            WHERE shipment_ref IS NULL OR btrim(COALESCE(shipment_ref, '')) = ''
            """
        )

    def action_mark_clearance_delivered(self):
        """Mark clearance info as delivered to the clearance company, recording who and when."""
        from odoo.fields import Datetime
        for rec in self:
            rec.write({
                'clearance_info_delivered': True,
                'clearance_info_delivered_at': Datetime.now(),
                'clearance_info_delivered_by_id': self.env.uid,
            })
