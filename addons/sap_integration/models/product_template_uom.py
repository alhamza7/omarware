# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """Extend Product Template with SAP UoM Group fields"""
    _inherit = 'product.template'
    
    # Related fields from sap.product.extended
    sap_uom_group_id = fields.Many2one(
        'sap.uom.group',
        string='SAP UoM Group',
        compute='_compute_sap_extended_fields',
        inverse='_inverse_sap_uom_group',
        store=True,
        help="SAP Unit of Measure Group that this product belongs to"
    )
    
    sap_uom_group_entry = fields.Integer(
        string='SAP UoM Group Entry',
        compute='_compute_sap_extended_fields',
        store=True,
        help="SAP UoMGroupEntry number"
    )
    
    available_product_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_available_product_uoms',
        string='Available UoMs',
        help="Available UoMs based on SAP UoM Group"
    )
    
    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_sap_extended_fields(self):
        """Compute SAP extended fields from first variant"""
        for template in self:
            # Get first variant's extended info
            if template.product_variant_ids:
                first_variant = template.product_variant_ids[0]
                extended_info = self.env['sap.product.extended'].search([
                    ('product_id', '=', first_variant.id)
                ], limit=1)
                
                if extended_info:
                    template.sap_uom_group_id = extended_info.sap_uom_group_id
                    template.sap_uom_group_entry = extended_info.sap_uom_group_entry
                else:
                    template.sap_uom_group_id = False
                    template.sap_uom_group_entry = 0
            else:
                template.sap_uom_group_id = False
                template.sap_uom_group_entry = 0
    
    def _inverse_sap_uom_group(self):
        """Update SAP extended info when UoM group is changed"""
        for template in self:
            if template.product_variant_ids:
                for variant in template.product_variant_ids:
                    extended_info = self.env['sap.product.extended'].search([
                        ('product_id', '=', variant.id)
                    ], limit=1)
                    
                    if extended_info:
                        extended_info.sap_uom_group_id = template.sap_uom_group_id
                    # Don't create if doesn't exist - will be created by SAP sync
    
    @api.depends('sap_uom_group_id', 'sap_uom_group_id.uom_ids')
    def _compute_available_product_uoms(self):
        """Compute available UoMs from SAP UoM Group"""
        for template in self:
            if template.sap_uom_group_id:
                # Get UoMs from group
                uom_syncs = template.sap_uom_group_id.uom_ids
                odoo_uoms = uom_syncs.mapped('odoo_uom_id').filtered(lambda u: u.active)
                template.available_product_uom_ids = odoo_uoms
            else:
                # No group - all UoMs available
                template.available_product_uom_ids = self.env['uom.uom'].search([])


class ProductProduct(models.Model):
    """Extend Product Variant with SAP UoM Group field"""
    _inherit = 'product.product'
    
    sap_uom_group_id = fields.Many2one(
        'sap.uom.group',
        string='SAP UoM Group',
        compute='_compute_sap_uom_group',
        store=True,
        help="SAP Unit of Measure Group (from extended info)"
    )
    
    @api.depends('default_code')
    def _compute_sap_uom_group(self):
        """Compute SAP UoM Group from extended info"""
        for product in self:
            extended_info = self.env['sap.product.extended'].search([
                ('product_id', '=', product.id)
            ], limit=1)
            
            product.sap_uom_group_id = extended_info.sap_uom_group_id if extended_info else False


