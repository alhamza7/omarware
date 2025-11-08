# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Adarsh K(odoo@cybrosys.com)
#    Updated for Odoo 19.0 compatibility
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
from odoo import fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    """
    Extension of 'sale.order.line' with an additional
    field 'product_warehouse_id'.
    """
    _inherit = 'sale.order.line'

    product_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        help='Warehouse where product taken from',
        domain="[('company_id', '=', company_id)]"
    )

    def _get_procurement_group(self):
        """Get or create procurement group for the order line.
        
        Returns:
            False: In Odoo 19, procurement.group doesn't exist as a model
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
        vals = {
            'name': order.name or 'New',
        }
        
        # Add move_type if picking_policy exists
        if hasattr(order, 'picking_policy'):
            vals['move_type'] = order.picking_policy or 'direct'
        
        # Add partner_id (use partner_shipping_id or fallback to partner_id)
        partner_id = False
        if hasattr(order, 'partner_shipping_id') and order.partner_shipping_id:
            partner_id = order.partner_shipping_id.id
        elif order.partner_id:
            partner_id = order.partner_id.id
        if partner_id:
            vals['partner_id'] = partner_id
        
        # Add sale_id only if order is saved (has ID)
        if order.id:
            vals['sale_id'] = order.id
        
        return vals

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Overwriting the function for adding functionalities of multiple
        warehouses in the sale order line.
        
        Args:
            previous_product_uom_qty: Uom quantity of previous product
            
        Returns:
            bool: Returns True, if the picking created.
        """
        if self._context.get("skip_procurement"):
            return True
            
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        
        for line in self:
            line = line.with_company(line.company_id)
            
            # Skip if not in 'sale' state or not a storable product
            if line.state != 'sale' or line.product_id.type not in ('consu', 'product'):
                continue
                
            qty = line._get_qty_procurement(previous_product_uom_qty)
            
            # Skip if quantity is unchanged
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue
                
            # In Odoo 19, procurement.group doesn't exist
            # Prepare procurement values without group_id
            values = line._prepare_procurement_values()
            
            # ⭐ Set warehouse from line if specified
            if line.product_warehouse_id:
                values['warehouse_id'] = line.product_warehouse_id
            
            # Check if product has routes configured
            # Get routes from values, line, or product
            route_ids = values.get('route_ids', False)
            
            # Check if route_ids is empty (could be empty recordset, empty list, or False)
            has_routes = False
            if route_ids:
                # If it's a recordset, check if it has records
                if hasattr(route_ids, '__len__') and hasattr(route_ids, '__iter__'):
                    if len(route_ids) > 0:
                        has_routes = True
                elif isinstance(route_ids, (list, tuple)) and len(route_ids) > 0:
                    has_routes = True
                elif route_ids:  # Other truthy values
                    has_routes = True
            
            # Try to get routes from line or product if not found in values
            if not has_routes:
                if hasattr(line, 'route_ids') and line.route_ids and len(line.route_ids) > 0:
                    has_routes = True
                elif line.product_id.route_ids and len(line.product_id.route_ids) > 0:
                    has_routes = True
            
            # Skip if no routes are configured (will cause "No rule has been found" error)
            if not has_routes:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Skipping procurement for product {line.product_id.display_name} (ID: {line.product_id.id}) - no routes configured")
                continue
                
            # Calculate product quantity
            product_qty = line.product_uom_qty - qty
            # Get UoM: use product_uom_id (Odoo 19) if available, otherwise fallback to product_id.uom_id
            if hasattr(line, 'product_uom_id') and line.product_uom_id:
                line_uom = line.product_uom_id
            else:
                line_uom = line.product_id.uom_id
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                product_qty, quant_uom
            )
            
            # Create procurement using stock.rule.Procurement (Odoo 19)
            # Use _get_location_final() if available, otherwise use partner_shipping_id.property_stock_customer
            location_final = line._get_location_final() if hasattr(line, '_get_location_final') else line.order_id.partner_shipping_id.property_stock_customer
            procurements.append(
                self.env['stock.rule'].Procurement(
                    line.product_id,
                    product_qty,
                    procurement_uom,
                    location_final,
                    line.product_id.display_name,
                    line.order_id.name,
                    line.order_id.company_id,
                    values
                )
            )
            
        # Run procurements
        if procurements:
            try:
                self.env['stock.rule'].run(procurements)
            except Exception as e:
                # Log the error but don't fail the order confirmation
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error running procurements: {e}")
                # Re-raise the exception to show the user the error
                raise
            
        # Confirm pickings
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done']
            )
            if pickings_to_confirm:
                pickings_to_confirm.action_confirm()
                
        return True
