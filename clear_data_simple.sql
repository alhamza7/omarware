-- ============================================
-- Simple SQL Script to Clear Products and Orders
-- ============================================

-- Connect to database: lugal
-- User: odoo_user
-- Password: root

BEGIN;

-- تفريغ طلبات البيع
DELETE FROM sale_order_line;
DELETE FROM sale_order;

-- تفريغ طلبات POS Perfume
DELETE FROM pos_perfume_order_line;
DELETE FROM pos_perfume_order;

-- تفريغ الفواتير
DELETE FROM account_move_line WHERE move_id IN (SELECT id FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'));
DELETE FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund');

-- تفريغ المنتجات
DELETE FROM product_product;
DELETE FROM product_template;

-- تفريغ المخزون
DELETE FROM stock_move;
DELETE FROM stock_quant;
DELETE FROM stock_picking;

-- إعادة تعيين التسلسلات
SELECT setval('sale_order_line_id_seq', 1, false);
SELECT setval('sale_order_id_seq', 1, false);
SELECT setval('pos_perfume_order_line_id_seq', 1, false);
SELECT setval('pos_perfume_order_id_seq', 1, false);
SELECT setval('account_move_line_id_seq', 1, false);
SELECT setval('account_move_id_seq', 1, false);
SELECT setval('product_product_id_seq', 1, false);
SELECT setval('product_template_id_seq', 1, false);
SELECT setval('stock_move_id_seq', 1, false);
SELECT setval('stock_quant_id_seq', 1, false);
SELECT setval('stock_picking_id_seq', 1, false);

COMMIT;

-- ملاحظة: تأكد من إيقاف Odoo قبل تنفيذ هذا الأمر!

