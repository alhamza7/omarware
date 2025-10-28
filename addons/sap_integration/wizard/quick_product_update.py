# -*- coding: utf-8 -*-
"""Quick Product Update Wizard - Fast SQL Update"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class QuickProductUpdate(models.TransientModel):
    """Quick update of products from SAP Extended data"""
    _name = 'sap.quick.product.update'
    _description = 'Quick Product Update from SAP'
    
    result_message = fields.Text(string='Results', readonly=True)
    state = fields.Selection([
        ('draft', 'Ready'),
        ('done', 'Completed')
    ], default='draft')
    
    def action_update_products(self):
        """Update products using direct SQL for speed"""
        self.ensure_one()
        
        results = []
        
        try:
            # 1. Update Foreign Name
            _logger.info("Updating foreign names...")
            
            query1 = """
                UPDATE product_product pp
                SET foreign_name = spe.foreign_name,
                    write_date = NOW(),
                    write_uid = %s
                FROM sap_product_extended spe
                WHERE spe.product_id = pp.id
                AND spe.foreign_name IS NOT NULL
                AND spe.foreign_name != ''
                AND (pp.foreign_name IS NULL OR pp.foreign_name = '' OR pp.foreign_name != spe.foreign_name)
            """
            
            self.env.cr.execute(query1, (self.env.uid,))
            count1 = self.env.cr.rowcount
            results.append(f"✅ تم تحديث Foreign Name لـ {count1} منتج")
            _logger.info(f"Updated foreign names for {count1} products")
            
            # 2. Update Prices from SAP Price List 1
            _logger.info("Updating prices...")
            
            query2 = """
                UPDATE product_product pp
                SET list_price = pli.fixed_price,
                    write_date = NOW(),
                    write_uid = %s
                FROM product_pricelist_item pli
                INNER JOIN product_pricelist pl ON pli.pricelist_id = pl.id
                WHERE pli.product_id = pp.id
                AND pl.name = 'SAP Price List 1'
                AND pli.fixed_price > 0
                AND (pp.list_price = 0 OR pp.list_price IS NULL OR pp.list_price != pli.fixed_price)
            """
            
            self.env.cr.execute(query2, (self.env.uid,))
            count2 = self.env.cr.rowcount
            results.append(f"✅ تم تحديث الأسعار لـ {count2} منتج")
            _logger.info(f"Updated prices for {count2} products")
            
            # 3. Get statistics
            self.env.cr.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != ''),
                    COUNT(*) FILTER (WHERE list_price > 0),
                    COUNT(*)
                FROM product_product
            """)
            
            stats = self.env.cr.fetchone()
            results.append(f"\n📊 الإحصائيات:")
            results.append(f"   • إجمالي المنتجات: {stats[2]}")
            results.append(f"   • لديها Foreign Name: {stats[0]}")
            results.append(f"   • لديها سعر > 0: {stats[1]}")
            
            self.result_message = '\n'.join(results)
            self.state = 'done'
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sap.quick.product.update',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error updating products: {e}")
            self.result_message = f"❌ خطأ: {str(e)}"
            self.state = 'done'
            raise

