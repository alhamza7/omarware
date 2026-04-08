# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ClearSapPricelistWizard(models.TransientModel):
    _name = 'sap.clear.pricelist.wizard'
    _description = 'Clear SAP Pricelist Items'
    
    confirm = fields.Boolean(
        string='I understand this will delete all SAP pricelist items',
        default=False
    )
    
    def action_clear_pricelists(self):
        """Clear all SAP pricelist items"""
        self.ensure_one()
        
        if not self.confirm:
            raise UserError("Please confirm that you want to delete all SAP pricelist items")
        
        try:
            # Delete all pricelist items from SAP pricelists
            pricelists = self.env['product.pricelist'].search([
                ('name', 'like', 'SAP Price List%')
            ])
            
            total_items = 0
            for pricelist in pricelists:
                items_count = len(pricelist.item_ids)
                total_items += items_count
                _logger.info(f"Deleting {items_count} items from {pricelist.name}")
                pricelist.item_ids.unlink()
            
            # Delete sync records
            sync_records = self.env['sap.product.pricelist.sync'].search([])
            sync_count = len(sync_records)
            _logger.info(f"Deleting {sync_count} sync records")
            sync_records.unlink()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': f'Deleted {total_items} pricelist items and {sync_count} sync records',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error clearing pricelists: {str(e)}")
            raise UserError(f"Error: {str(e)}")



