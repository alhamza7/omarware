-- ============================================
-- تقسيم جميع الكميات على 2 - أمر محسّن
-- Divide All Quantities by 2 - Enhanced Command
-- ============================================

-- التحقق من الكميات الحالية قبل التحديث
-- Check current quantities before update
SELECT 
    'BEFORE UPDATE' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN quantity > 0 THEN 1 END) as records_with_quantity,
    SUM(quantity) as total_quantity,
    SUM(reserved_quantity) as total_reserved_quantity
FROM stock_quant;

-- بدء المعاملة
-- Begin transaction
BEGIN;

-- طريقة 1: تحديث مباشر للكمية
-- Method 1: Direct quantity update
UPDATE stock_quant 
SET quantity = ROUND((quantity / 2.0)::numeric, 2)
WHERE quantity > 0;

-- طريقة 2: تحديث الكمية المحجوزة
-- Method 2: Update reserved quantity
UPDATE stock_quant 
SET reserved_quantity = ROUND((reserved_quantity / 2.0)::numeric, 2)
WHERE reserved_quantity > 0;

-- التحقق من النتائج بعد التحديث
-- Verify results after update
SELECT 
    'AFTER UPDATE' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN quantity > 0 THEN 1 END) as records_with_quantity,
    SUM(quantity) as total_quantity,
    SUM(reserved_quantity) as total_reserved_quantity
FROM stock_quant;

-- عرض عينة من السجلات المحدثة
-- Show sample of updated records
SELECT 
    sq.id,
    pp.default_code as product_code,
    pt.name as product_name,
    sl.name as location_name,
    sq.quantity,
    sq.reserved_quantity
FROM stock_quant sq
JOIN product_product pp ON sq.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN stock_location sl ON sq.location_id = sl.id
WHERE sq.quantity > 0
ORDER BY sq.id
LIMIT 10;

-- حفظ التغييرات
-- Commit changes
COMMIT;

