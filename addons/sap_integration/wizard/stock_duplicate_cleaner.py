# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockDuplicateCleaner(models.TransientModel):
    _name = 'stock.duplicate.cleaner'
    _description = 'Stock Duplicate Cleaner'
    
    duplicate_count = fields.Integer(string='Duplicate Records', readonly=True)
    duplicate_info = fields.Text(string='Duplicate Details', readonly=True)
    
    def action_check_duplicates(self):
        """Check for duplicate stock.quant records"""
        self.ensure_one()
        
        query = """
            SELECT 
                product_id,
                location_id,
                COUNT(*) as count,
                SUM(quantity) as total_qty,
                ARRAY_AGG(id) as quant_ids
            FROM stock_quant
            WHERE location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
            GROUP BY product_id, location_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        
        self.env.cr.execute(query)
        duplicates = self.env.cr.dictfetchall()
        
        if not duplicates:
            self.write({
                'duplicate_count': 0,
                'duplicate_info': 'لا توجد سجلات مكررة! ✓'
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('نجاح'),
                    'message': _('لا توجد سجلات مخزون مكررة'),
                    'type': 'success',
                }
            }
        
        # Build info text
        info_lines = [f'تم العثور على {len(duplicates)} منتج به سجلات مكررة:\n']
        
        for dup in duplicates[:20]:  # Show first 20
            product = self.env['product.product'].browse(dup['product_id'])
            location = self.env['stock.location'].browse(dup['location_id'])
            
            info_lines.append(
                f"\n• {product.name} [{product.default_code or ''}]"
                f"\n  المخزن: {location.complete_name}"
                f"\n  عدد السجلات المكررة: {dup['count']}"
                f"\n  الكمية الإجمالية: {dup['total_qty']}"
                f"\n  معرفات السجلات: {', '.join(map(str, dup['quant_ids']))}"
            )
        
        self.write({
            'duplicate_count': len(duplicates),
            'duplicate_info': '\n'.join(info_lines)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.duplicate.cleaner',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_clean_duplicates(self):
        """Merge duplicate stock.quant records - keep the newest one"""
        self.ensure_one()
        
        query = """
            SELECT 
                product_id,
                location_id,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id DESC) as quant_ids,
                SUM(quantity) as total_qty
            FROM stock_quant
            WHERE location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
            GROUP BY product_id, location_id
            HAVING COUNT(*) > 1
        """
        
        self.env.cr.execute(query)
        duplicates = self.env.cr.dictfetchall()
        
        if not duplicates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('تنبيه'),
                    'message': _('لا توجد سجلات مكررة للتنظيف'),
                    'type': 'warning',
                }
            }
        
        cleaned = 0
        errors = 0
        
        for dup in duplicates:
            try:
                quant_ids = dup['quant_ids']
                total_qty = dup['total_qty']
                
                # Keep the first (newest) quant, delete the rest
                keep_id = quant_ids[0]
                delete_ids = quant_ids[1:]
                
                # Update the keeper with total quantity
                keeper = self.env['stock.quant'].browse(keep_id)
                keeper.sudo().write({'quantity': total_qty})
                
                # Delete duplicates
                duplicates_to_delete = self.env['stock.quant'].browse(delete_ids)
                duplicates_to_delete.sudo().unlink()
                
                cleaned += len(delete_ids)
                _logger.info(f"Cleaned {len(delete_ids)} duplicate quants for product {dup['product_id']}")
                
            except Exception as e:
                errors += 1
                _logger.error(f"Error cleaning duplicates for product {dup['product_id']}: {e}")
        
        # Re-check after cleaning
        self.action_check_duplicates()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('نجاح'),
                'message': _('تم حذف %s سجل مكرر. الأخطاء: %s') % (cleaned, errors),
                'type': 'success' if errors == 0 else 'warning',
            }
        }






