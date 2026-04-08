# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmSupplyNotification(models.Model):
    _name = 'lugal.crm.supply.notification'
    _description = 'Supply chain in-app notification'
    _order = 'create_date desc, id desc'

    user_id = fields.Many2one(
        'res.users',
        string='Recipient',
        required=True,
        ondelete='cascade',
        index=True,
    )
    notif_type = fields.Selection(
        [
            ('po_created', 'PO Created'),
            ('container_arrived', 'Container Arrived'),
            ('clearance_done', 'Clearance Done'),
            ('low_stock', 'Low Stock'),
            ('negotiation_update', 'Negotiation Update'),
            ('item_request_update', 'Item Request Update'),
            ('general', 'General'),
        ],
        string='Type',
        required=True,
        default='general',
        index=True,
    )
    title = fields.Char(required=True)
    body = fields.Text()
    related_id = fields.Integer(string='Related record id')
    related_model = fields.Char(string='Related model technical name')
    is_read = fields.Boolean(default=False, index=True)
