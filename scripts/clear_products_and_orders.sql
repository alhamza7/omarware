-- ============================================
-- SQL Script to Clear Products and Invoices/Orders
-- قاعدة البيانات: lugal
-- ============================================

-- Warning: This will DELETE all data from products, invoices, and orders
-- تحذير: هذا سيقوم بحذف جميع البيانات من المنتجات والفواتير والطلبات

BEGIN;

-- ============================================
-- 1. Delete Sale Order Lines (تفريغ سطور طلبات البيع)
-- ============================================
DELETE FROM sale_order_line;
SELECT setval('sale_order_line_id_seq', 1, false);

-- ============================================
-- 2. Delete Sale Orders (تفريغ طلبات البيع)
-- ============================================
DELETE FROM sale_order;
SELECT setval('sale_order_id_seq', 1, false);

-- ============================================
-- 3. Delete POS Perfume Order Lines (تفريغ سطور طلبات POS Perfume)
-- ============================================
DELETE FROM pos_perfume_order_line;
SELECT setval('pos_perfume_order_line_id_seq', 1, false);

-- ============================================
-- 4. Delete POS Perfume Orders (تفريغ طلبات POS Perfume)
-- ============================================
DELETE FROM pos_perfume_order;
SELECT setval('pos_perfume_order_id_seq', 1, false);

-- ============================================
-- 5. Delete Invoice Lines (تفريغ سطور الفواتير)
-- ============================================
DELETE FROM account_move_line WHERE move_id IN (SELECT id FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'));
SELECT setval('account_move_line_id_seq', 1, false);

-- ============================================
-- 6. Delete Invoices (تفريغ الفواتير)
-- ============================================
DELETE FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund');
SELECT setval('account_move_id_seq', 1, false);

-- ============================================
-- 7. Delete Product Variants (تفريغ متغيرات المنتجات)
-- ============================================
DELETE FROM product_product;
SELECT setval('product_product_id_seq', 1, false);

-- ============================================
-- 8. Delete Product Templates (تفريغ قوالب المنتجات)
-- ============================================
DELETE FROM product_template;
SELECT setval('product_template_id_seq', 1, false);

-- ============================================
-- 9. Delete Product Categories (اختياري - تفريغ فئات المنتجات)
-- ============================================
-- Uncomment if you want to delete categories too
-- قم بإلغاء التعليق إذا كنت تريد حذف الفئات أيضاً
-- DELETE FROM product_category WHERE id > 1; -- Keep default category
-- SELECT setval('product_category_id_seq', 1, false);

-- ============================================
-- 10. Delete Stock Moves (تفريغ حركات المخزون)
-- ============================================
DELETE FROM stock_move;
SELECT setval('stock_move_id_seq', 1, false);

-- ============================================
-- 11. Delete Stock Quant (تفريغ كميات المخزون)
-- ============================================
DELETE FROM stock_quant;
SELECT setval('stock_quant_id_seq', 1, false);

-- ============================================
-- 12. Delete Stock Picking (تفريغ عمليات النقل)
-- ============================================
DELETE FROM stock_picking;
SELECT setval('stock_picking_id_seq', 1, false);

-- ============================================
-- 13. Reset Sequences (إعادة تعيين التسلسلات)
-- ============================================
-- Reset product sequences
SELECT setval('product_product_id_seq', 1, false);
SELECT setval('product_template_id_seq', 1, false);

-- Reset order sequences  
SELECT setval('sale_order_id_seq', 1, false);
SELECT setval('sale_order_line_id_seq', 1, false);
SELECT setval('pos_perfume_order_id_seq', 1, false);
SELECT setval('pos_perfume_order_line_id_seq', 1, false);

-- Reset invoice sequences
SELECT setval('account_move_id_seq', 1, false);
SELECT setval('account_move_line_id_seq', 1, false);

COMMIT;

-- ============================================
-- Usage Instructions (تعليمات الاستخدام)
-- ============================================
-- 1. Connect to PostgreSQL:
--    psql -U odoo_user -d lugal
--
-- 2. Run this script:
--    \i clear_products_and_orders.sql
--
--    OR copy and paste the SQL commands
--
-- 3. Or use pgAdmin to execute the script
--
-- ============================================
-- IMPORTANT NOTES (ملاحظات مهمة)
-- ============================================
-- ⚠️  This will DELETE ALL products and orders
-- ⚠️  Make sure to backup your database first!
-- ⚠️  This action is IRREVERSIBLE!
--
-- Backup command:
-- pg_dump -U odoo_user -d lugal > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

