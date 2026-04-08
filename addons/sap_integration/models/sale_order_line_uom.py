# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """Extend Sale Order Line to restrict UoM selection based on SAP UoM Groups"""
    _inherit = 'sale.order.line'
    
    # Computed field for available UoMs based on product's SAP UoM Group
    available_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_available_uoms',
        string='Available UoMs',
        help="Available UoMs for this product based on SAP UoM Group"
    )
    
    # Related field to show SAP UoM Group
    sap_uom_group_id = fields.Many2one(
        'sap.uom.group',
        string='SAP UoM Group',
        compute='_compute_sap_uom_group',
        store=False,
        help="SAP UoM Group of the product"
    )
    
    @api.depends('product_id')
    def _compute_sap_uom_group(self):
        """Compute SAP UoM Group from product"""
        for line in self:
            if line.product_id:
                # Get SAP extended info
                extended_info = self.env['sap.product.extended'].search([
                    ('product_id', '=', line.product_id.id)
                ], limit=1)
                
                line.sap_uom_group_id = extended_info.sap_uom_group_id if extended_info else False
            else:
                line.sap_uom_group_id = False
    
    @api.depends('product_id', 'product_id.default_code')
    def _compute_available_uoms(self):
        """Compute available UoMs based on product's SAP UoM Group"""
        for line in self:
            if not line.product_id:
                # No product - allow all UoMs
                line.available_uom_ids = self.env['uom.uom'].search([])
                continue
            
            # Get SAP extended info for the product
            extended_info = self.env['sap.product.extended'].search([
                ('product_id', '=', line.product_id.id)
            ], limit=1)
            
            if not extended_info or not extended_info.sap_uom_group_id:
                # No SAP UoM Group - allow all UoMs (fallback behavior)
                _logger.debug(f"Product {line.product_id.display_name} has no SAP UoM Group - allowing all UoMs")
                line.available_uom_ids = self.env['uom.uom'].search([])
                continue
            
            # Get UoMs from the product's UoM group
            uom_group = extended_info.sap_uom_group_id
            uom_syncs = uom_group.uom_ids
            
            if uom_syncs:
                # Get Odoo UoMs from sync records
                odoo_uoms = uom_syncs.mapped('odoo_uom_id').filtered(lambda u: u.active)
                line.available_uom_ids = odoo_uoms
                _logger.debug(
                    f"Product {line.product_id.display_name} UoM Group {uom_group.name}: "
                    f"{len(odoo_uoms)} UoMs available"
                )
            else:
                # Group has no UoMs - allow all UoMs as fallback
                _logger.warning(
                    f"SAP UoM Group {uom_group.name} has no UoMs - allowing all UoMs as fallback"
                )
                line.available_uom_ids = self.env['uom.uom'].search([])
    
    # Override product_uom_id to add domain restriction
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        domain="[('id', 'in', available_uom_ids)]",  # Restrict to available UoMs
        help="Unit of Measure. Restricted to UoMs in the product's SAP UoM Group."
    )
    
    @api.onchange('product_id')
    def _onchange_product_id_uom_restriction(self):
        """Reset UoM when product changes if current UoM is not in available list"""
        if self.product_id and self.product_uom_id:
            # Check if current UoM is still valid
            if self.product_uom_id.id not in self.available_uom_ids.ids:
                # Current UoM not in available list - reset to product's default
                _logger.info(
                    f"Product changed: resetting UoM from {self.product_uom_id.name} "
                    f"to {self.product_id.uom_id.name}"
                )
                self.product_uom_id = self.product_id.uom_id


