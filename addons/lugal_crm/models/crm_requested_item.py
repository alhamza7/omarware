# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmRequestedItem(models.Model):
    """
    Customer-requested catalog item — when the desired product is not in the price list.
    Agent can tag the customer card and mark it fulfilled when stock arrives.
    """
    _name = 'lugal.crm.requested.item'
    _description = 'CRM Requested Catalog Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'product_name'

    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        ondelete='set null',
        index=True,
        tracking=True,
    )

    product_name = fields.Char(string='Requested Product / المنتج المطلوب', required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product',
        string='Linked Product (when stocked) / المنتج عند التوفر',
        ondelete='set null',
        tracking=True,
    )

    status = fields.Selection([
        ('pending', 'Pending / قيد الانتظار'),
        ('in_stock', 'In Stock / متوفر الآن'),
        ('notified', 'Customer Notified / تم إخطار العميل'),
        ('fulfilled', 'Fulfilled / تمت التلبية'),
        ('cancelled', 'Cancelled / ملغي'),
    ], string='Status / الحالة', default='pending', required=True, index=True, tracking=True)

    requested_by_id = fields.Many2one(
        'res.users',
        string='Requested By / سجّله',
        default=lambda self: self.env.user,
        ondelete='set null',
        tracking=True,
    )
    notes = fields.Text(string='Notes / ملاحظات', tracking=True)

    # Auto-notify customer when product is stocked (future AI/bot integration point)
    auto_notify = fields.Boolean(
        string='Auto-Notify / إخطار تلقائي',
        default=True,
        tracking=True,
        help='When enabled, system will notify the customer automatically when the product is in stock.',
    )

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Soft Deleted', default=False, index=True)

    @api.model
    def _cron_notify_requested_items(self):
        """
        Hourly cron: find pending requested items whose product_id is now in stock,
        mark them as in_stock so agents can follow up with the customer.
        """
        pending = self.search([
            ('status', '=', 'pending'),
            ('product_id', '!=', False),
            ('is_deleted', '=', False),
        ])
        for item in pending:
            try:
                if item.product_id.qty_available > 0:
                    item.write({'status': 'in_stock'})
                    _logger.info(
                        'CRM: Requested item %s is now in stock for customer %s',
                        item.product_name,
                        item.customer_id.name if item.customer_id else '?',
                    )
            except Exception:
                _logger.exception('Error checking stock for requested item %s', item.id)
