# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Duplicate Cleaner Wizard

حذف التكرارات في:
- المنتجات (Products)
- قوائم الأسعار (Pricelists)
- بنود قوائم الأسعار (Pricelist Items)
- وحدات القياس (UoM)
- معلومات المخازن (Warehouse Info)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapDuplicateCleaner(models.TransientModel):
    _name = 'sap.duplicate.cleaner'
    _description = 'SAP Duplicate Cleaner Wizard'
    
    # ========== Options ==========
    clean_products = fields.Boolean(
        string='حذف تكرار المنتجات',
        default=True,
        help="حذف المنتجات المكررة بناءً على default_code"
    )
    clean_pricelists = fields.Boolean(
        string='حذف تكرار قوائم الأسعار',
        default=True,
        help="حذف قوائم الأسعار المكررة بناءً على name + currency_id"
    )
    clean_pricelist_items = fields.Boolean(
        string='حذف تكرار بنود قوائم الأسعار',
        default=True,
        help="حذف بنود قوائم الأسعار المكررة من sap.product.pricelist.sync"
    )
    clean_uom = fields.Boolean(
        string='حذف تكرار وحدات القياس',
        default=True,
        help="حذف وحدات القياس المكررة بناءً على name"
    )
    clean_warehouse_info = fields.Boolean(
        string='حذف تكرار معلومات المخازن',
        default=True,
        help="حذف معلومات المخازن المكررة من sap.product.warehouse.info"
    )
    
    # ========== Results ==========
    products_deleted = fields.Integer(string='المنتجات المحذوفة', readonly=True, default=0)
    pricelists_deleted = fields.Integer(string='قوائم الأسعار المحذوفة', readonly=True, default=0)
    pricelist_items_deleted = fields.Integer(string='بنود قوائم الأسعار المحذوفة', readonly=True, default=0)
    uom_deleted = fields.Integer(string='وحدات القياس المحذوفة', readonly=True, default=0)
    warehouse_info_deleted = fields.Integer(string='معلومات المخازن المحذوفة', readonly=True, default=0)
    
    result_log = fields.Text(string='سجل النتائج', readonly=True)
    
    # ========== Methods ==========
    def action_check_duplicates(self):
        """فحص التكرارات قبل الحذف"""
        self.ensure_one()
        
        log_lines = []
        log_lines.append("=" * 80)
        log_lines.append("فحص التكرارات في قاعدة البيانات")
        log_lines.append("=" * 80)
        log_lines.append("")
        
        # 1. Products
        if self.clean_products:
            products_dups = self._check_product_duplicates()
            log_lines.append(f"📦 المنتجات: {len(products_dups)} مجموعة تكرار")
            for dup in products_dups[:10]:  # أول 10
                log_lines.append(f"  • default_code: '{dup['default_code']}' - {dup['count']} منتج")
        
        # 2. Pricelists
        if self.clean_pricelists:
            pricelists_dups = self._check_pricelist_duplicates()
            log_lines.append(f"\n💰 قوائم الأسعار: {len(pricelists_dups)} مجموعة تكرار")
            for dup in pricelists_dups[:10]:
                log_lines.append(f"  • name: '{dup['name']}' - {dup['count']} قائمة")
        
        # 3. Pricelist Items
        if self.clean_pricelist_items:
            pricelist_items_dups = self._check_pricelist_item_duplicates()
            log_lines.append(f"\n📋 بنود قوائم الأسعار: {len(pricelist_items_dups)} مجموعة تكرار")
            for dup in pricelist_items_dups[:10]:
                log_lines.append(f"  • product_id: {dup['product_id']}, pricelist: {dup['pricelist_num']} - {dup['count']} بند")
        
        # 4. UoM
        if self.clean_uom:
            uom_dups = self._check_uom_duplicates()
            log_lines.append(f"\n📏 وحدات القياس: {len(uom_dups)} مجموعة تكرار")
            for dup in uom_dups[:10]:
                log_lines.append(f"  • name: '{dup['name']}' - {dup['count']} وحدة")
        
        # 5. Warehouse Info
        if self.clean_warehouse_info:
            warehouse_info_dups = self._check_warehouse_info_duplicates()
            log_lines.append(f"\n🏭 معلومات المخازن: {len(warehouse_info_dups)} مجموعة تكرار")
            for dup in warehouse_info_dups[:10]:
                log_lines.append(f"  • product_id: {dup['product_id']}, warehouse_id: {dup['warehouse_id']} - {dup['count']} سجل")
        
        log_lines.append("\n" + "=" * 80)
        log_lines.append("انتهى الفحص")
        log_lines.append("=" * 80)
        
        self.write({
            'result_log': '\n'.join(log_lines)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sap.duplicate.cleaner',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_clean_duplicates(self):
        """حذف التكرارات"""
        self.ensure_one()
        
        log_lines = []
        log_lines.append("=" * 80)
        log_lines.append("بدء حذف التكرارات")
        log_lines.append("=" * 80)
        log_lines.append("")
        
        total_deleted = 0
        
        # 1. Products
        if self.clean_products:
            try:
                deleted = self._clean_product_duplicates()
                self.products_deleted = deleted
                log_lines.append(f"✅ المنتجات: تم حذف {deleted} منتج مكرر")
                total_deleted += deleted
            except Exception as e:
                log_lines.append(f"❌ المنتجات: خطأ - {str(e)}")
                _logger.error(f"Error cleaning product duplicates: {e}", exc_info=True)
        
        # 2. Pricelists
        if self.clean_pricelists:
            try:
                deleted = self._clean_pricelist_duplicates()
                self.pricelists_deleted = deleted
                log_lines.append(f"✅ قوائم الأسعار: تم حذف {deleted} قائمة مكررة")
                total_deleted += deleted
            except Exception as e:
                log_lines.append(f"❌ قوائم الأسعار: خطأ - {str(e)}")
                _logger.error(f"Error cleaning pricelist duplicates: {e}", exc_info=True)
        
        # 3. Pricelist Items
        if self.clean_pricelist_items:
            try:
                deleted = self._clean_pricelist_item_duplicates()
                self.pricelist_items_deleted = deleted
                log_lines.append(f"✅ بنود قوائم الأسعار: تم حذف {deleted} بند مكرر")
                total_deleted += deleted
            except Exception as e:
                log_lines.append(f"❌ بنود قوائم الأسعار: خطأ - {str(e)}")
                _logger.error(f"Error cleaning pricelist item duplicates: {e}", exc_info=True)
        
        # 4. UoM
        if self.clean_uom:
            try:
                deleted = self._clean_uom_duplicates()
                self.uom_deleted = deleted
                log_lines.append(f"✅ وحدات القياس: تم حذف {deleted} وحدة مكررة")
                total_deleted += deleted
            except Exception as e:
                log_lines.append(f"❌ وحدات القياس: خطأ - {str(e)}")
                _logger.error(f"Error cleaning UoM duplicates: {e}", exc_info=True)
        
        # 5. Warehouse Info
        if self.clean_warehouse_info:
            try:
                deleted = self._clean_warehouse_info_duplicates()
                self.warehouse_info_deleted = deleted
                log_lines.append(f"✅ معلومات المخازن: تم حذف {deleted} سجل مكرر")
                total_deleted += deleted
            except Exception as e:
                log_lines.append(f"❌ معلومات المخازن: خطأ - {str(e)}")
                _logger.error(f"Error cleaning warehouse info duplicates: {e}", exc_info=True)
        
        log_lines.append("\n" + "=" * 80)
        log_lines.append(f"✅ انتهى الحذف - إجمالي: {total_deleted} سجل محذوف")
        log_lines.append("=" * 80)
        
        self.write({
            'result_log': '\n'.join(log_lines)
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('نجاح'),
                'message': _('تم حذف %s سجل مكرر بنجاح') % total_deleted,
                'type': 'success',
                'sticky': True,
            }
        }
    
    # ========== Check Methods ==========
    def _check_product_duplicates(self):
        """فحص تكرار المنتجات"""
        query = """
            SELECT 
                default_code,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as product_ids
            FROM product_product
            WHERE default_code IS NOT NULL 
              AND default_code != ''
            GROUP BY default_code
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def _check_pricelist_duplicates(self):
        """فحص تكرار قوائم الأسعار"""
        query = """
            SELECT 
                CASE 
                    WHEN jsonb_typeof(name) = 'string' THEN name::text
                    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
                    ELSE name::text
                END as name,
                currency_id,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as pricelist_ids
            FROM product_pricelist
            WHERE CASE 
                    WHEN jsonb_typeof(name) = 'string' THEN name::text LIKE 'SAP Price List%'
                    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US' LIKE 'SAP Price List%'
                    ELSE name::text LIKE 'SAP Price List%'
                END
            GROUP BY CASE 
                    WHEN jsonb_typeof(name) = 'string' THEN name::text
                    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
                    ELSE name::text
                END, currency_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def _check_pricelist_item_duplicates(self):
        """فحص تكرار بنود قوائم الأسعار"""
        query = """
            SELECT 
                product_id,
                backend_id,
                sap_pricelist_num,
                COALESCE(uom_id, 0) as uom_id,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as item_ids
            FROM sap_product_pricelist_sync
            GROUP BY product_id, backend_id, sap_pricelist_num, COALESCE(uom_id, 0)
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def _check_uom_duplicates(self):
        """فحص تكرار وحدات القياس"""
        query = """
            SELECT 
                CASE 
                    WHEN jsonb_typeof(name) = 'string' THEN name::text
                    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
                    ELSE name::text
                END as name,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as uom_ids
            FROM uom_uom
            GROUP BY CASE 
                    WHEN jsonb_typeof(name) = 'string' THEN name::text
                    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
                    ELSE name::text
                END
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def _check_warehouse_info_duplicates(self):
        """فحص تكرار معلومات المخازن"""
        query = """
            SELECT 
                product_id,
                warehouse_id,
                backend_id,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as info_ids
            FROM sap_product_warehouse_info
            GROUP BY product_id, warehouse_id, backend_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    # ========== Clean Methods ==========
    def _clean_product_duplicates(self):
        """حذف تكرار المنتجات - الاحتفاظ بالأحدث"""
        duplicates = self._check_product_duplicates()
        deleted_count = 0
        
        for dup in duplicates:
            product_ids = dup['product_ids']
            # الاحتفاظ بالأول (الأحدث)، حذف الباقي
            keep_id = product_ids[0]
            delete_ids = product_ids[1:]
            
            # حذف التكرارات
            products_to_delete = self.env['product.product'].browse(delete_ids)
            products_to_delete.unlink()
            deleted_count += len(delete_ids)
            
            _logger.info(f"Deleted {len(delete_ids)} duplicate products for default_code: {dup['default_code']}")
        
        return deleted_count
    
    def _clean_pricelist_duplicates(self):
        """حذف تكرار قوائم الأسعار - الاحتفاظ بالأحدث"""
        duplicates = self._check_pricelist_duplicates()
        deleted_count = 0
        
        for dup in duplicates:
            pricelist_ids = dup['pricelist_ids']
            # الاحتفاظ بالأول (الأحدث)، حذف الباقي
            keep_id = pricelist_ids[0]
            delete_ids = pricelist_ids[1:]
            
            # حذف التكرارات
            pricelists_to_delete = self.env['product.pricelist'].browse(delete_ids)
            pricelists_to_delete.unlink()
            deleted_count += len(delete_ids)
            
            _logger.info(f"Deleted {len(delete_ids)} duplicate pricelists for name: {dup['name']}")
        
        return deleted_count
    
    def _clean_pricelist_item_duplicates(self):
        """حذف تكرار بنود قوائم الأسعار - الاحتفاظ بالأحدث"""
        duplicates = self._check_pricelist_item_duplicates()
        deleted_count = 0
        
        for dup in duplicates:
            item_ids = dup['item_ids']
            # الاحتفاظ بالأول (الأحدث)، حذف الباقي
            keep_id = item_ids[0]
            delete_ids = item_ids[1:]
            
            # حذف التكرارات
            items_to_delete = self.env['sap.product.pricelist.sync'].browse(delete_ids)
            items_to_delete.unlink()
            deleted_count += len(delete_ids)
            
            _logger.info(f"Deleted {len(delete_ids)} duplicate pricelist items for product_id: {dup['product_id']}")
        
        return deleted_count
    
    def _clean_uom_duplicates(self):
        """حذف تكرار وحدات القياس - الاحتفاظ بالأحدث"""
        duplicates = self._check_uom_duplicates()
        deleted_count = 0
        
        for dup in duplicates:
            uom_ids = dup['uom_ids']
            # الاحتفاظ بالأول (الأحدث)، حذف الباقي
            keep_id = uom_ids[0]
            delete_ids = uom_ids[1:]
            
            # التحقق من عدم استخدام الوحدات المحذوفة
            # إذا كانت مستخدمة، نتخطاها
            uoms_to_delete = self.env['uom.uom'].browse(delete_ids)
            safe_to_delete = []
            
            for uom in uoms_to_delete:
                # التحقق من الاستخدام
                used_in_products = self.env['product.product'].search_count([('uom_id', '=', uom.id)])
                used_in_pricelists = self.env['sap.product.pricelist.sync'].search_count([('uom_id', '=', uom.id)])
                
                if used_in_products == 0 and used_in_pricelists == 0:
                    safe_to_delete.append(uom.id)
            
            if safe_to_delete:
                uoms_to_delete = self.env['uom.uom'].browse(safe_to_delete)
                uoms_to_delete.unlink()
                deleted_count += len(safe_to_delete)
            
            _logger.info(f"Deleted {len(safe_to_delete)} duplicate UoMs for name: {dup['name']}")
        
        return deleted_count
    
    def _clean_warehouse_info_duplicates(self):
        """حذف تكرار معلومات المخازن - الاحتفاظ بالأحدث"""
        duplicates = self._check_warehouse_info_duplicates()
        deleted_count = 0
        
        for dup in duplicates:
            info_ids = dup['info_ids']
            # الاحتفاظ بالأول (الأحدث)، حذف الباقي
            keep_id = info_ids[0]
            delete_ids = info_ids[1:]
            
            # حذف التكرارات
            infos_to_delete = self.env['sap.product.warehouse.info'].browse(delete_ids)
            infos_to_delete.unlink()
            deleted_count += len(delete_ids)
            
            _logger.info(f"Deleted {len(delete_ids)} duplicate warehouse info records")
        
        return deleted_count

