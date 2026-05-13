# -*- coding: utf-8 -*-
from odoo import models, fields


class LugalSupplyNotification(models.Model):
    """In-app supply-chain notifications pushed to individual users."""
    _name = 'lugal.supply.notification'
    _description = 'Lugal Supply Notification'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    user_id = fields.Many2one(
        'res.users',
        string='User / المستخدم',
        required=True,
        ondelete='cascade',
        index=True,
    )
    notif_type = fields.Selection([
        ('po_created', 'PO Created'),
        ('po_status_change', 'PO Status Changed'),
        ('container_arrived', 'Container Arrived'),
        ('clearance_done', 'Clearance Done'),
        ('low_stock', 'Low Stock'),
        ('negotiation_update', 'Negotiation Update'),
        ('item_request_update', 'Item Request Update'),
        ('general', 'General'),
    ], string='Type / النوع', default='general', required=True, index=True)
    title = fields.Char(string='Title / العنوان', required=True)
    body = fields.Text(string='Body / النص')
    related_type = fields.Char(string='Related Model / النموذج المرتبط', index=True)
    related_id = fields.Integer(string='Related ID / معرّف المرتبط', index=True)
    is_read = fields.Boolean(string='Read / مقروء', default=False, index=True)
    read_at = fields.Datetime(string='Read At / وقت القراءة')
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)
