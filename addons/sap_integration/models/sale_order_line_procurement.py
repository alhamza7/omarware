# -*- coding: utf-8 -*-

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_procurement_group(self):
        """Compatibility shim for modules expecting this method on lines.

        In Odoo 19, procurement.group doesn't exist as a model.
        Procurement is handled through stock.rule.Procurement (NamedTuple).
        Return False to indicate no group is needed.
        """
        # In Odoo 19, procurement.group doesn't exist as a model
        # Procurement is handled through stock.rule.Procurement (NamedTuple)
        # Return False to indicate no group is needed
        # The procurement system will handle grouping automatically
        return False

    def _prepare_procurement_group_vals(self):
        """Prepare values for creating a procurement group.
        
        Returns:
            dict: Values for creating procurement.group
        """
        self.ensure_one()
        order = self.order_id
        return {
            'name': order.name,
            'move_type': getattr(order, 'picking_policy', 'direct'),
            'partner_id': order.partner_shipping_id.id if order.partner_shipping_id else False,
            'sale_id': order.id,
        }


