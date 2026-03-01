# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    foreign_name = fields.Char(
        string='Foreign Name',
        help='اسم المنتج الأجنبي'
    )
    
    price_iqd = fields.Monetary(
        string='Price (IQD)',
        compute='_compute_price_iqd',
        currency_field='currency_iqd_id',
        store=False
    )
    
    currency_iqd_id = fields.Many2one(
        'res.currency',
        string='IQD Currency',
        default=lambda self: self.env.ref('base.IQD', raise_if_not_found=False),
        store=False
    )
    
    @api.depends('list_price')
    def _compute_price_iqd(self):
        """Convert USD price to IQD using fixed exchange rate"""
        exchange_rate = 1600.0  # 1 USD = 1,530 IQD
        for product in self:
            product.price_iqd = product.list_price * exchange_rate
    
    def _sync_foreign_name_from_extended(self):
        """Sync foreign_name from sap.product.extended to product.template if not set"""
        if 'sap.product.extended' not in self.env:
            return
        
        for template in self:
            # Only sync if foreign_name is not set in template
            if not template.foreign_name:
                try:
                    # Get first product variant
                    if template.product_variant_ids:
                        product = template.product_variant_ids[0]
                        extended = self.env['sap.product.extended'].search([
                            ('product_id', '=', product.id)
                        ], limit=1)
                        
                        if extended and extended.foreign_name:
                            template.write({'foreign_name': extended.foreign_name})
                            _logger.info(f"Synced foreign_name '{extended.foreign_name}' from sap.product.extended to product.template {template.id}")
                except Exception as e:
                    _logger.warning(f"Error syncing foreign_name from sap.product.extended: {e}")
    
    @api.model
    def sync_all_foreign_names_from_extended(self):
        """
        Sync foreign_name from sap.product.extended to all product.template records
        This method can be called to update all existing products at once
        """
        if 'sap.product.extended' not in self.env:
            _logger.warning("sap.product.extended model not available")
            return {'status': 'error', 'message': 'SAP Integration module not installed'}
        
        try:
            # Get all templates that don't have foreign_name set
            templates_without_foreign_name = self.search([
                ('foreign_name', '=', False)
            ])
            
            synced_count = 0
            for template in templates_without_foreign_name:
                if template.product_variant_ids:
                    product = template.product_variant_ids[0]
                    extended = self.env['sap.product.extended'].search([
                        ('product_id', '=', product.id)
                    ], limit=1)
                    
                    if extended and extended.foreign_name:
                        template.write({'foreign_name': extended.foreign_name})
                        synced_count += 1
                        _logger.info(f"Synced foreign_name '{extended.foreign_name}' from sap.product.extended to product.template {template.id}")
            
            _logger.info(f"Synced foreign_name for {synced_count} product template(s) from sap.product.extended")
            return {
                'status': 'success',
                'message': f'Successfully synced foreign_name for {synced_count} product(s)',
                'synced_count': synced_count
            }
        except Exception as e:
            _logger.error(f"Error syncing all foreign_names: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def read(self, fields=None, load='_classic_read'):
        """Override read to sync foreign_name from sap.product.extended if not set"""
        result = super().read(fields=fields, load=load)
        
        # Sync foreign_name from extended if not set
        if fields is None or 'foreign_name' in fields:
            templates_to_sync = []
            for record, res_dict in zip(self, result):
                if not res_dict.get('foreign_name'):
                    templates_to_sync.append(record)
            
            if templates_to_sync:
                # Sync in batch
                self.browse([t.id for t in templates_to_sync])._sync_foreign_name_from_extended()
                # Re-read to get updated values
                result = super().read(fields=fields, load=load)
        
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Inherit from template
    foreign_name = fields.Char(related='product_tmpl_id.foreign_name', string='Foreign Name', readonly=False, store=True, copy=False)
    price_iqd = fields.Monetary(related='product_tmpl_id.price_iqd', string='Price (IQD)')
    
    def read(self, fields=None, load='_classic_read'):
        """Override read to sync foreign_name from sap.product.extended if not set"""
        result = super().read(fields=fields, load=load)
        
        # Sync foreign_name from extended if not set
        if fields is None or 'foreign_name' in fields:
            templates_to_sync = []
            for record, res_dict in zip(self, result):
                if not res_dict.get('foreign_name'):
                    templates_to_sync.append(record.product_tmpl_id)
            
            if templates_to_sync:
                # Sync in batch
                self.env['product.template'].browse(list(set(t.id for t in templates_to_sync)))._sync_foreign_name_from_extended()
                # Re-read to get updated values
                result = super().read(fields=fields, load=load)
        
        return result

