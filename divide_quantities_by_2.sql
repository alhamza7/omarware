-- ============================================
-- تقسيم جميع الكميات على 2 في جميع المخازن
-- Divide all quantities by 2 in all warehouses
-- ============================================

-- ⚠️ تحذير: هذا الأمر سيعدل جميع الكميات في قاعدة البيانات
-- ⚠️ Warning: This command will modify all quantities in the database
-- 
-- يُنصح بعمل نسخة احتياطية قبل التنفيذ
-- It's recommended to backup the database before execution

BEGIN;

-- تقسيم الكمية (quantity) على 2
-- Divide quantity by 2
UPDATE stock_quant
SET quantity = quantity / 2.0
WHERE quantity > 0;

-- تقسيم الكمية المحجوزة (reserved_quantity) على 2
-- Divide reserved_quantity by 2
UPDATE stock_quant
SET reserved_quantity = reserved_quantity / 2.0
WHERE reserved_quantity > 0;

-- عرض إحصائيات بعد التحديث
-- Show statistics after update
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN quantity > 0 THEN 1 END) as records_with_quantity,
    SUM(quantity) as total_quantity,
    SUM(reserved_quantity) as total_reserved_quantity
FROM stock_quant;

-- للتراجع عن التغييرات (إذا لزم الأمر):
-- To rollback changes (if needed):
-- ROLLBACK;

-- لحفظ التغييرات:
-- To commit changes:
COMMIT;

